"""邮箱后缀白名单（ADR-0023）：域名判定 + 绑定 / 注册两处闸门 + 祖父条款 + 文案契约。

不回溯是刻意的：白名单上线前留下的地址（含非白名单后缀）仍可重发、仍可完成验证；
只有「新地址」会被拦。
"""
import json
from pathlib import Path

from django.contrib.auth.models import User
from django.core import mail
from django.core.cache import cache
from django.test import Client, TestCase

from accounts.email_domains import (
    ALLOWED_EMAIL_DOMAINS,
    EMAIL_DOMAIN_BLOCKED_MESSAGE,
    EMAIL_DOMAIN_BLOCKED_REASON,
    PROVIDER_DOMAINS,
    email_domain,
    is_allowed_email_domain,
)
from accounts.models import Verification

BIND = "/auth/verification/email/bind/"
REPO_ROOT = Path(__file__).resolve().parents[1]


class WhitelistUnitTest(TestCase):
    def test_every_provider_domain_allowed(self):
        for provider, domains in PROVIDER_DOMAINS.items():
            for domain in domains:
                self.assertTrue(is_allowed_email_domain(f"member@{domain}"), f"{provider} 漏了 {domain}")

    def test_required_providers_covered(self):
        """需求点名的服务商都在名单内（网易 / QQ / Outlook / Apple / 三大运营商 / 新浪）。"""
        for domain in (
            "163.com", "qq.com", "outlook.com", "privaterelay.appleid.com",
            "139.com", "wo.cn", "189.cn", "sina.com",
        ):
            self.assertIn(domain, ALLOWED_EMAIL_DOMAINS)

    def test_case_and_whitespace_insensitive(self):
        self.assertTrue(is_allowed_email_domain("  Member@163.COM  "))

    def test_exact_match_not_suffix(self):
        # 精确匹配：不因「包含白名单域」而放行
        for domain in ("evil163.com", "163.com.evil.com", "qq.com.cn", "notqq.com"):
            self.assertFalse(is_allowed_email_domain(f"a@{domain}"), domain)

    def test_common_non_whitelisted_domains_rejected(self):
        for domain in ("gmail.com", "example.com", "yahoo.com", "hotmail.co.uk", "mail.ru"):
            self.assertFalse(is_allowed_email_domain(f"member@{domain}"), domain)

    def test_missing_at_sign_rejected(self):
        for raw in ("", "163.com", "member@", "@163.com"):
            self.assertFalse(is_allowed_email_domain(raw), raw)

    def test_email_domain_helper(self):
        self.assertEqual(email_domain(" Member@QQ.com "), "qq.com")
        self.assertEqual(email_domain("no-at-sign"), "")


class EmailBindWhitelistTest(TestCase):
    def setUp(self):
        cache.clear()
        self.user = User.objects.create_user(username="u", password="p", is_active=True)

    def _client(self):
        c = Client()
        c.force_login(self.user)
        return c

    def _bind(self, email):
        return self._client().post(
            BIND, data=json.dumps({"email": email}), content_type="application/json",
        )

    def test_bind_rejects_disallowed_domain_with_fixed_message(self):
        resp = self._bind("member@gmail.com")
        self.assertEqual(resp.status_code, 400, resp.content)
        body = resp.json()
        self.assertEqual(body["reason"], EMAIL_DOMAIN_BLOCKED_REASON)
        self.assertEqual(body["error"], EMAIL_DOMAIN_BLOCKED_MESSAGE)
        self.assertEqual(body["domain"], "gmail.com")
        # 未建通道、未发信
        self.assertFalse(Verification.objects.filter(user=self.user).exists())
        self.assertEqual(len(mail.outbox), 0)

    def test_bind_allows_whitelisted_domain(self):
        resp = self._bind("member@qq.com")
        self.assertEqual(resp.status_code, 200, resp.content)
        v = Verification.objects.get(user=self.user, channel=Verification.CHANNEL_EMAIL)
        self.assertEqual(v.identifier, "member@qq.com")
        self.assertEqual(len(mail.outbox), 1)

    def test_change_email_to_disallowed_domain_rejected_keeps_old(self):
        # 已绑定白名单内邮箱 → 想换绑 gmail：拒绝，通道与 User.email 均不动
        self.user.email = "member@163.com"
        self.user.save()
        Verification.objects.create(
            user=self.user, channel=Verification.CHANNEL_EMAIL,
            status=Verification.STATUS_APPROVED, identifier="member@163.com",
        )
        resp = self._bind("member@gmail.com")
        self.assertEqual(resp.status_code, 400)
        v = Verification.objects.get(user=self.user, channel=Verification.CHANNEL_EMAIL)
        self.assertEqual(v.status, Verification.STATUS_APPROVED)
        self.assertEqual(v.identifier, "member@163.com")

    def test_existing_disallowed_pending_identifier_may_resend(self):
        # 祖父条款：白名单上线前留下的 pending 地址（非白名单后缀）仍可重发完成验证
        Verification.objects.create(
            user=self.user, channel=Verification.CHANNEL_EMAIL,
            status=Verification.STATUS_PENDING, identifier="old@gmail.com",
        )
        resp = self._bind("old@gmail.com")
        self.assertEqual(resp.status_code, 200, resp.content)
        self.assertEqual(len(mail.outbox), 1)

    def test_existing_disallowed_approved_email_is_noop(self):
        # 祖父条款：已通过的旧地址同址再绑 → 走既有 no-op 分支（不因白名单报错）
        self.user.email = "old@gmail.com"
        self.user.save()
        Verification.objects.create(
            user=self.user, channel=Verification.CHANNEL_EMAIL,
            status=Verification.STATUS_APPROVED, identifier="old@gmail.com",
        )
        resp = self._bind("old@gmail.com")
        self.assertEqual(resp.status_code, 200, resp.content)
        self.assertEqual(len(mail.outbox), 0)


class RegisterWhitelistTest(TestCase):
    def setUp(self):
        cache.clear()

    def _register(self, email):
        return self.client.post("/auth/register/", data={
            "username": "newbie",
            "password": "StrongPass123!",
            "password2": "StrongPass123!",
            "real_name": "张三",
            "identity": "student",
            "email": email,
            "turnstile_token": "dummy",
        })

    def test_register_rejects_disallowed_domain(self):
        resp = self._register("newbie@gmail.com")
        self.assertEqual(resp.status_code, 400, resp.content)
        body = resp.json()
        self.assertEqual(body["reason"], EMAIL_DOMAIN_BLOCKED_REASON)
        self.assertEqual(body["error"], EMAIL_DOMAIN_BLOCKED_MESSAGE)
        self.assertFalse(User.objects.filter(username="newbie").exists())

    def test_register_allows_whitelisted_domain(self):
        resp = self._register("newbie@outlook.com")
        self.assertEqual(resp.status_code, 201, resp.content)
        v = Verification.objects.get(user__username="newbie", channel=Verification.CHANNEL_EMAIL)
        self.assertEqual(v.identifier, "newbie@outlook.com")

    def test_register_without_email_still_ok(self):
        resp = self.client.post("/auth/register/", data={
            "username": "noemail",
            "password": "StrongPass123!",
            "password2": "StrongPass123!",
            "real_name": "张三",
            "identity": "student",
            "turnstile_token": "dummy",
        })
        self.assertEqual(resp.status_code, 201, resp.content)


class EmailDomainFrontendContractTest(TestCase):
    """前后端文案与 reason 逐字一致（前端弹窗照原样展示后端固定文案）。"""

    def _read(self, *parts):
        path = REPO_ROOT.joinpath(*parts)
        if not path.exists():
            self.skipTest(f"前端源码不在本机检出：{path}")
        return path.read_text(encoding="utf-8")

    def test_shared_ts_mirrors_message_and_reason(self):
        src = self._read("frontend", "src", "api", "shared.ts")
        self.assertIn(EMAIL_DOMAIN_BLOCKED_MESSAGE, src)
        self.assertIn(EMAIL_DOMAIN_BLOCKED_REASON, src)

    def test_verification_panel_shows_notice_modal(self):
        src = self._read("frontend", "src", "components", "profile", "VerificationPanel.tsx")
        self.assertIn("NoticeModal", src)
        self.assertIn(EMAIL_DOMAIN_BLOCKED_REASON, src)
