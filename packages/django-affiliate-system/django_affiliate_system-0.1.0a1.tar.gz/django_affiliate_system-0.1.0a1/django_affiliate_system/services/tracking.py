# services/tracking.py

from django.utils import timezone
from rest_framework.exceptions import ValidationError

from django_affiliate_system.models import (
    Affiliate,
    ReferralAction,
    ReferralLink,
    ReferralSession,
)
from django_affiliate_system.services.commision import create_commission


def resolve_referral_link(referral_code=None, referral_slug=None):
    if referral_code:
        try:
            affiliate = Affiliate.objects.get(code=referral_code)
        except Affiliate.DoesNotExist:
            raise ValidationError("Invalid referral code")

        link = ReferralLink.objects.filter(affiliate=affiliate, is_active=True).first()
    elif referral_slug:
        link = ReferralLink.objects.filter(slug=referral_slug, is_active=True).first()
    else:
        raise ValidationError("Referral code or slug required")

    if not link:
        raise ValidationError("No active referral link found")

    return link


def process_tracking_event(data, meta, use_sessions=False, attribution_model="last_click"):
    referral_code = data.get("referral_code")
    referral_slug = data.get("referral_link_slug")
    event_type = data.get("event_type", "click")
    session_id = data.get("session_id")

    referral_link = resolve_referral_link(referral_code, referral_slug)
    affiliate = referral_link.affiliate

    session = None
    session_created = False

    if use_sessions and session_id:
        session, session_created = ReferralSession.objects.get_or_create(
            session_id=session_id,
            defaults={
                "affiliate": affiliate,
                "first_referral_link": referral_link,
                "last_referral_link": referral_link,
                "ip_address": meta.get("REMOTE_ADDR"),
                "user_agent": meta.get("HTTP_USER_AGENT", ""),
            },
        )
        if not session_created:
            session.last_referral_link = referral_link
            session.last_touch = timezone.now()
            session.save()

    metadata = {
        **data.get("metadata", {}),
        "session_created": session_created if use_sessions else False,
        "attribution_model": attribution_model,
    }
    action = ReferralAction.objects.create(
        tenant=affiliate.tenant,
        referral_link=referral_link,
        action_type=event_type,
        session_id=session_id if use_sessions else None,
        ip_address=meta.get("REMOTE_ADDR"),
        user_agent=meta.get("HTTP_USER_AGENT", ""),
        referring_url=data.get("metadata", {}).get("referrer", ""),
        conversion_value=data.get("conversion_value", 0),
        metadata=metadata,
    )

    if event_type in ["purchase"] or data.get("is_conversion"):
        action.is_converted = True
        action.converted_at = timezone.now()
        action.save()

        if use_sessions and session:
            session.is_converted = True
            session.conversion_value = action.conversion_value
            session.save()

            return create_attributed_commission(action, session)

        create_commission(action)

    return action


def create_attributed_commission(action, session):
    attribution_model = action.metadata.get("attribution_model", "last_click")
    if attribution_model == "first_click":
        affiliate = session.first_referral_link.affiliate
        referral_link = session.first_referral_link
    else:
        affiliate = session.last_referral_link.affiliate
        referral_link = session.last_referral_link

    action.referral_link = referral_link
    action.save(update_fields=["referral_link"])

    return create_commission(action)
