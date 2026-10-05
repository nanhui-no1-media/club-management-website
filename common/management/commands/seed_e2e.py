"""E2E 种子数据：为 Playwright 测试准备确定性环境（幂等，可重复执行）。

内容：
- ``e2e_info``：超管账号（具备全部管理权限；发布即过审）——E2E 主账号；
- ``e2e_plain``：普通账号（无管理权限）——登录流程等用例使用；
- 标签「E2E公告 / E2E活动」+ 一条已过审的已发布新闻（首页动态可见）；
- 重置两个账号的登录会话：登录保护窗口会把 10 分钟内的「再次登录」拒掉，
  每次跑 E2E 前必须清掉旧会话，否则第二次运行会 409。

密码：环境变量 ``E2E_PASSWORD``，默认 ``e2e-pass-123``（测试环境固定值，非机密）。
生产环境（DEBUG=False）需显式 ``--force`` 才可执行。
"""
import os

from django.conf import settings
from django.contrib.auth.models import User
from django.core.management.base import BaseCommand, CommandError
from django.utils import timezone

from accounts.models import UserSession
from news.models import News
from reviews.models import Review
from tasks.models import Tag

E2E_USERS = ("e2e_info", "e2e_plain")
DEFAULT_PASSWORD = "e2e-pass-123"


class Command(BaseCommand):
    help = "为 Playwright E2E 准备种子数据（幂等；含登录会话重置）"

    def add_arguments(self, parser):
        parser.add_argument("--force", action="store_true", help="非 DEBUG 环境下强制执行（仅供测试）")

    def handle(self, *args, **options):
        if not settings.DEBUG and not options["force"]:
            raise CommandError("当前环境 DEBUG=False；确需执行请加 --force（仅供测试）。")

        password = os.environ.get("E2E_PASSWORD", DEFAULT_PASSWORD)

        info, _ = User.objects.get_or_create(username="e2e_info", defaults={"email": "e2e_info@example.test"})
        info.is_superuser = True
        info.is_staff = True
        info.is_active = True
        info.set_password(password)
        info.save()

        plain, _ = User.objects.get_or_create(username="e2e_plain", defaults={"email": "e2e_plain@example.test"})
        plain.is_superuser = False
        plain.is_staff = False
        plain.is_active = True
        plain.set_password(password)
        plain.save()

        # 登录保护：清掉旧会话，保证每次运行的首次登录都被放行
        UserSession.objects.filter(user__username__in=E2E_USERS).delete()

        tag_notice, _ = Tag.objects.get_or_create(name="E2E公告")
        tag_event, _ = Tag.objects.get_or_create(name="E2E活动")

        news, _ = News.objects.get_or_create(
            title="E2E 种子新闻",
            defaults={
                "summary": "种子数据：E2E 首页动态可见。",
                "author": info,
                "is_published": True,
                "published_at": timezone.now(),
            },
        )
        news.tags.set([tag_notice, tag_event])
        if news.published_at is None:
            news.published_at = timezone.now()
            news.save(update_fields=["published_at"])
        Review.objects.update_or_create(news=news, defaults={"status": Review.STATUS_APPROVED})

        self.stdout.write(self.style.SUCCESS(
            f"seed_e2e 完成：账号 {'/'.join(E2E_USERS)}（密码 {password}）+ 标签 + 种子新闻 #{news.pk}"
        ))
