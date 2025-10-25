import enum
from uuid import uuid4

from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.validators import MinValueValidator
from django.db import models
from django.utils import timezone

User = get_user_model()


class Tenant(models.Model):
    """Platforms using the affiliate system"""

    name = models.CharField(max_length=255)
    slug = models.SlugField(unique=True)
    destination_url = models.URLField()
    subdomain = models.URLField(blank=True)
    api_key = models.UUIDField(default=uuid4, unique=True)
    created_at = models.DateTimeField(auto_now_add=True)
    owner = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        # related_name="",
        null=True,
        blank=True,
    )
    # admins = models.ManyToManyField(
    #     settings.AUTH_USER_MODEL,
    #     related_name="tenants",
    #     blank=True
    # )
    is_active = models.BooleanField(default=True)

    # Commission settings
    default_commission_rate = models.DecimalField(
        max_digits=5, decimal_places=2, default=10.0
    )  # 10%
    cookie_duration_days = models.PositiveIntegerField(default=30)  # How long to track referrals

    def __str__(self):
        return self.name


class Affiliate(models.Model):
    """Users who refer others"""

    tenant = models.ForeignKey(Tenant, on_delete=models.CASCADE, related_name="affiliates")
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="affiliate")
    # user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="affiliates")
    code = models.CharField(max_length=50, unique=True)
    is_active = models.BooleanField(default=True)
    joined_at = models.DateTimeField(auto_now_add=True)
    balance = models.DecimalField(max_digits=10, decimal_places=2, default=0.0)

    # Payout settings
    payout_threshold = models.DecimalField(max_digits=10, decimal_places=2, default=50.0)
    payout_method = models.CharField(max_length=50, blank=True)  # stripe, paypal, etc.
    payout_details = models.JSONField(default=dict)  # Payment method details

    class Meta:
        unique_together = ("tenant", "user")

    def __str__(self):
        return f"{self.user.email} ({self.tenant})"


class ReferralLink(models.Model):
    """Unique referral links for affiliates"""

    affiliate = models.ForeignKey(
        Affiliate, on_delete=models.CASCADE, related_name="referral_links"
    )
    slug = models.SlugField(unique=True)
    destination_url = models.URLField()
    created_at = models.DateTimeField(auto_now_add=True)
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return f"{self.slug} -> {self.destination_url}"


class ReferralActionType(enum.Enum):
    CLICK = "click"
    SIGNUP = "signup"
    PURCHASE = "purchase"
    OTHER = "other"


class ReferralAction(models.Model):
    """Track all referral actions (clicks, signups, purchases)"""

    tenant = models.ForeignKey(Tenant, on_delete=models.CASCADE)
    referral_link = models.ForeignKey(
        ReferralLink, on_delete=models.CASCADE, related_name="actions"
    )
    action_type = models.CharField(
        max_length=20, choices=[(tag.value, tag.name) for tag in ReferralActionType]
    )
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.TextField(blank=True)
    referring_url = models.URLField(blank=True)
    timestamp = models.DateTimeField(auto_now_add=True)
    metadata = models.JSONField(default=dict)  # Additional tracking data

    # For conversion actions
    converted_at = models.DateTimeField(null=True, blank=True)
    conversion_value = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    is_converted = models.BooleanField(default=False)
    session_id = models.CharField(max_length=100, blank=True)

    class Meta:
        indexes = [
            models.Index(fields=["referral_link", "action_type"]),
            models.Index(fields=["tenant", "is_converted"]),
        ]

    def __str__(self):
        return f"{self.action_type} via {self.referral_link}"


class Commission(models.Model):
    """Commissions earned from referrals"""

    affiliate = models.ForeignKey(Affiliate, on_delete=models.CASCADE, related_name="commissions")
    referral_action = models.OneToOneField(
        ReferralAction, on_delete=models.CASCADE, related_name="commission"
    )
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    rate = models.DecimalField(max_digits=5, decimal_places=2)  # Commission rate at time of action
    calculated_at = models.DateTimeField(auto_now_add=True)
    status = models.CharField(
        max_length=20,
        choices=[
            ("pending", "Pending"),
            ("approved", "Approved"),
            ("rejected", "Rejected"),
            ("paid", "Paid"),
        ],
        default="pending",
    )

    def __str__(self):
        return f"${self.amount} for {self.affiliate}"


class Payout(models.Model):
    """Payments to affiliates"""

    tenant = models.ForeignKey(Tenant, on_delete=models.CASCADE, related_name="payouts")
    affiliate = models.ForeignKey(Affiliate, on_delete=models.CASCADE, related_name="payouts")
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    created_at = models.DateTimeField(auto_now_add=True)
    processed_at = models.DateTimeField(null=True, blank=True)
    status = models.CharField(
        max_length=20,
        choices=[
            ("pending", "Pending"),
            ("processing", "Processing"),
            ("paid", "Paid"),
            ("failed", "Failed"),
        ],
        default="pending",
    )
    method = models.CharField(max_length=50)  # stripe, paypal, etc.
    reference = models.CharField(max_length=255, blank=True)  # External reference ID
    metadata = models.JSONField(default=dict)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"Payout #{self.id} - ${self.amount} to {self.affiliate}"


class CommissionRule(models.Model):
    """Rules for calculating commissions"""

    tenant = models.ForeignKey(Tenant, on_delete=models.CASCADE, related_name="commission_rules")
    name = models.CharField(max_length=255)
    action_type = models.CharField(
        max_length=20, choices=[(tag.value, tag.name) for tag in ReferralActionType]
    )
    is_percentage = models.BooleanField(default=True)
    value = models.DecimalField(max_digits=10, decimal_places=2)  # Fixed amount or percentage
    min_value = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    max_value = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return f"{self.name} ({self.tenant})"


class ReferralSession(models.Model):
    """Track user sessions across multiple touchpoints"""

    session_id = models.CharField(max_length=100, unique=True)
    affiliate = models.ForeignKey(Affiliate, on_delete=models.CASCADE)
    first_referral_link = models.ForeignKey(
        ReferralLink, on_delete=models.CASCADE, related_name="first_sessions"
    )
    last_referral_link = models.ForeignKey(
        ReferralLink, on_delete=models.CASCADE, related_name="last_sessions"
    )
    first_touch = models.DateTimeField(auto_now_add=True)
    last_touch = models.DateTimeField(auto_now=True)
    is_converted = models.BooleanField(default=False)
    conversion_value = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.TextField(blank=True)

    class Meta:
        db_table = "affiliates_referralsession"
