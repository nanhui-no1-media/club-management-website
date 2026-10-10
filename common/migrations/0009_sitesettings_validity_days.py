import django.core.validators
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("common", "0008_sitesettings_authcode_redeem_per_user_per_hour"),
    ]

    operations = [
        migrations.AddField(
            model_name="sitesettings",
            name="verification_valid_days",
            field=models.PositiveIntegerField(
                default=365,
                validators=[django.core.validators.MinValueValidator(1)],
                verbose_name="认证有效期（天）",
            ),
        ),
        migrations.AddField(
            model_name="sitesettings",
            name="admin_valid_days",
            field=models.PositiveIntegerField(
                default=730,
                validators=[django.core.validators.MinValueValidator(1)],
                verbose_name="管理员身份有效期（天）",
            ),
        ),
        migrations.AddField(
            model_name="sitesettings",
            name="registration_verify_days",
            field=models.PositiveIntegerField(
                default=60,
                validators=[django.core.validators.MinValueValidator(1)],
                verbose_name="注册后验证宽限（天）",
            ),
        ),
    ]
