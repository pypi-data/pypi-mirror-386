from django.apps import AppConfig
from django.conf import settings


class DjangoAffiliateSystemConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "django_affiliate_system"
    verbose_name = "Django Affiliate System"

    def ready(self):
        from . import signals  # noqa

        self.validate_settings()

    def validate_settings(self):
        affiliate_settings = getattr(settings, "AFFILIATE_SYSTEM", {})
        defaults = {
            "DOMAIN_PROTOCOL": "https",
            "DOMAIN": "localhost",
            "DEFAULT_COMMISSION_RATE": 10.0,
            "COOKIE_DURATION_DAYS": 30,
            "ENABLE_GOOGLE_CALENDAR": False,
            "ALLOWED_CORS_ORIGINS": [],
        }
        for key, default_value in defaults.items():
            if key not in affiliate_settings:
                affiliate_settings[key] = default_value
        settings.AFFILIATE_SYSTEM = affiliate_settings
