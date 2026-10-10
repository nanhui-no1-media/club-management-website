"""邮箱后缀白名单（ADR-0023）：只接受认可的服务商域名。

为什么有白名单：站点用第三方邮箱发验证信（``settings.EMAIL_HOST_*``），成员普遍
在用的服务商到达率稳定、出问题也好排查；放开任意后缀只会增加「收不到验证信」的
支持成本。名单是**代码级策略**（不接受用户输入），改名单 = 改这里 + 走 PR。

判定只发生在**接收新地址**的两处：
  - ``accounts.views.register_view``（注册带邮箱）；
  - ``accounts.views.verification_email_bind_view``（验证面板绑定 / 换绑）。
不回溯：已绑定地址、重发验证信（``/auth/resend-verification/``）、Django admin
里管理员手填的邮箱不受影响（见 ADR-0023 决策 4）。

注意：企业 / 教育自建域名邮箱（如 ``@某公司.com``、学校域）无法穷举，故不在名单内；
这类成员走人工审批 / 认证码通道完成验证。
"""

from __future__ import annotations

#: 按服务商分组（便于人工核对与增设）；判定只看拍平后的域名集合。
PROVIDER_DOMAINS: dict[str, tuple[str, ...]] = {
    "网易": (
        "163.com", "126.com", "yeah.net", "188.com", "vip.163.com", "vip.126.com",
    ),
    "QQ": ("qq.com", "foxmail.com", "vip.qq.com"),
    "微软 Outlook": ("outlook.com", "hotmail.com", "live.com", "live.cn", "msn.com"),
    # Apple：「隐藏我的邮件」转发地址（@privaterelay.appleid.com）也属 Apple 邮箱，
    # 否则用 Apple 账号登录 / 转发的成员永远绑不上。
    "Apple iCloud": ("icloud.com", "me.com", "mac.com", "privaterelay.appleid.com"),
    "中国移动": ("139.com",),
    "中国联通": ("wo.cn",),
    "中国电信": ("189.cn", "21cn.com"),
    "新浪": ("sina.com", "sina.cn", "sina.com.cn", "vip.sina.com"),
}

#: 拍平后的允许域名集合（判定用；精确匹配，非后缀包含）。
ALLOWED_EMAIL_DOMAINS: frozenset[str] = frozenset(
    domain for domains in PROVIDER_DOMAINS.values() for domain in domains
)

#: 被拦时的固定文案：前端 NoticeModal 弹窗逐字展示，契约测试钉死（勿改字）。
EMAIL_DOMAIN_BLOCKED_MESSAGE = "该邮箱后缀暂不可用，请换用其他邮箱。详询社长或服务器管理员"


#: 后端 reason 串：前端按它映射成类型化 `email_domain_not_allowed`（见 shared.ts）。
EMAIL_DOMAIN_BLOCKED_REASON = "email_domain_not_allowed"


def email_domain(email: str) -> str:
    """取邮箱域名（小写、去空白）；无 ``@`` 或 ``@`` 在首尾 → 空串。"""
    _, sep, domain = (email or "").strip().lower().rpartition("@")
    return domain if sep else ""


def is_allowed_email_domain(email: str) -> bool:
    """域名是否在白名单内。**精确匹配**：``evil163.com`` / ``163.com.evil.com`` 不放行。"""
    return email_domain(email) in ALLOWED_EMAIL_DOMAINS
