# signals.py
from django.conf import settings
from django.contrib.auth import get_user_model
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.utils import timezone

from .models import Affiliate, Commission, ReferralAction, Tenant

User = get_user_model()


@receiver(post_save, sender=User)
def track_referred_signup(sender, instance, created, **kwargs):
    if not created:
        return

    # Check for referral cookie
    for tenant in Tenant.objects.filter(is_active=True):
        cookie_name = f"ref_{tenant.slug}"
        affiliate_code = instance.request.COOKIES.get(cookie_name)
        if not affiliate_code:
            continue

        try:
            affiliate = Affiliate.objects.get(tenant=tenant, code=affiliate_code, is_active=True)
        except Affiliate.DoesNotExist:
            continue

        # Create conversion action
        ReferralAction.objects.create(
            tenant=tenant,
            referral_link=None,  # We don't know which specific link was used
            action_type="signup",
            ip_address=instance.request.META.get("REMOTE_ADDR"),
            user_agent=instance.request.META.get("HTTP_USER_AGENT", ""),
            converted_at=timezone.now(),
            conversion_value=0,  # Signups might have no immediate value
            is_converted=True,
            metadata={
                "user_id": instance.id,
            },
        )

        # Clear the cookie
        instance.request.COOKIES.pop(cookie_name, None)
        break
