# services/commissions.py

from django.db import transaction
from django.utils import timezone

from django_affiliate_system.models import Commission, CommissionRule


def create_commission(action):
    """Calculate and create commission for a converted action."""
    tenant = action.tenant
    affiliate = action.referral_link.affiliate

    rule = (
        CommissionRule.objects.filter(
            tenant=tenant, action_type=action.action_type, is_active=True
        ).first()
        or CommissionRule.objects.filter(tenant=tenant, action_type="other", is_active=True).first()
    )

    if not rule:
        return None

    if rule.is_percentage:
        amount = (action.conversion_value or 0) * (rule.value / 100)
        if rule.min_value is not None:
            amount = max(amount, rule.min_value)
        if rule.max_value is not None:
            amount = min(amount, rule.max_value)
        rate = rule.value
    else:
        amount = rule.value
        rate = 0

    with transaction.atomic():
        commission = Commission.objects.create(
            affiliate=affiliate,
            referral_action=action,
            amount=amount,
            rate=rate,
            status="pending",
        )
        affiliate.balance += amount
        affiliate.save()

    return commission
