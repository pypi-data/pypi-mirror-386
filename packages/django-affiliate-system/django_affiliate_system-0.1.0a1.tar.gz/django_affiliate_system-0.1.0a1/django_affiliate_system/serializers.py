import re

from django.conf import settings
from django.contrib.auth import get_user_model
from rest_framework import serializers

from .models import (
    Affiliate,
    Commission,
    CommissionRule,
    Payout,
    ReferralAction,
    ReferralLink,
    ReferralSession,
    Tenant,
)

User = get_user_model()


class TenantSerializer(serializers.ModelSerializer):
    class Meta:
        model = Tenant
        fields = ["id", "name", "slug", "created_at", "default_commission_rate"]
        read_only_fields = ["slug", "created_at"]


class AffiliateSerializer(serializers.ModelSerializer):
    user = serializers.PrimaryKeyRelatedField(
        read_only=True, default=serializers.CurrentUserDefault()
    )
    tenant = serializers.PrimaryKeyRelatedField(read_only=True)

    class Meta:
        model = Affiliate
        fields = [
            "id",
            "tenant",
            "user",
            "code",
            "is_active",
            "balance",
            "payout_threshold",
            "payout_method",
        ]
        read_only_fields = ["code", "balance", "user", "tenant"]


class ReferralLinkSerializer(serializers.ModelSerializer):
    full_url = serializers.SerializerMethodField()
    destination_url = serializers.SerializerMethodField()
    total_clicks = serializers.SerializerMethodField()
    total_signups = serializers.SerializerMethodField()
    total_page_views = serializers.SerializerMethodField()
    total_conversions = serializers.SerializerMethodField()
    conversion_rate = serializers.SerializerMethodField()

    class Meta:
        model = ReferralLink
        fields = [
            "id",
            "affiliate",
            "slug",
            "destination_url",
            "full_url",
            "is_active",
            "created_at",
            "total_clicks",
            "total_page_views",
            "total_signups",
            "total_conversions",
            "conversion_rate",
        ]
        read_only_fields = fields  # All fields are read-only

    # def get_full_url(self, obj):
    #     request = self.context.get("request")
    #     return (
    #         f"{settings.DOMAIN_PROTOCOL}://{settings.DOMAIN}/?ref={obj.slug}"
    #         if request
    #         else None
    #     )

    def get_full_url(self, obj):
        config = settings.AFFILIATE_SYSTEM
        return f"{config['DOMAIN_PROTOCOL']}://{config['DOMAIN']}/?ref={obj.slug}"

    def get_destination_url(self, obj):
        return obj.affiliate.tenant.destination_url

    def _get_filtered_actions(self, obj, filters):
        """Helper method to get filtered actions for the link"""
        request = self.context.get("request")
        if not request:
            return ReferralAction.objects.none()

        queryset = ReferralAction.objects.filter(referral_link=obj, **filters)

        if start_date := request.query_params.get("start_date"):
            end_date = request.query_params.get("end_date")
            if end_date:
                queryset = queryset.filter(timestamp__range=[start_date, end_date])

        return queryset

    def get_total_clicks(self, obj):
        return self._get_filtered_actions(obj, {"action_type": "click"}).count()

    def get_total_signups(self, obj):
        return self._get_filtered_actions(obj, {"action_type": "signup"}).count()

    def get_total_page_views(self, obj):
        return self._get_filtered_actions(obj, {"action_type": "page_view"}).count()

    def get_total_conversions(self, obj):
        return self._get_filtered_actions(obj, {"is_converted": True}).count()

    def get_conversion_rate(self, obj):
        clicks = self.get_total_clicks(obj)
        conversions = self.get_total_conversions(obj)
        return (conversions / clicks * 100) if clicks > 0 else 0

    def validate_slug(self, value):
        """
        Ensure slug is unique within the tenant and validate format
        Now allows capital letters but preserves case sensitivity
        """
        instance = getattr(self, "instance", None)

        # If we're updating and slug hasn't changed, no validation needed
        if instance and instance.slug == value:
            return value

        tenant = self.context["request"].tenant
        if not tenant:
            raise serializers.ValidationError("Tenant context required")

        # Validate slug format - now allows A-Z, a-z, 0-9, and hyphens
        if not re.match(r"^[A-Za-z0-9-]+$", value):
            raise serializers.ValidationError(
                "Slug can only contain letters (A-Z, a-z), numbers, and hyphens"
            )

        # Check uniqueness within tenant (case-sensitive)
        if (
            ReferralLink.objects.filter(slug=value, affiliate__tenant=tenant)
            .exclude(pk=getattr(instance, "pk", None))
            .exists()
        ):
            raise serializers.ValidationError("This slug is already in use")

        return value


# class ReferralLinkSerializer(serializers.ModelSerializer):
#     full_url = serializers.SerializerMethodField()
#     destination_url = serializers.SerializerMethodField()

#     class Meta:
#         model = ReferralLink
#         fields = ["id", "affiliate", "slug", "destination_url", "full_url", "is_active"]
#         read_only_fields = [
#             "slug",
#             "affiliate",
#         ]

#     def get_full_url(self, obj):
#         request = self.context.get("request")
#         return request.build_absolute_uri(f"/r/{obj.slug}") if request else None

#     def get_destination_url(self, obj):
#         return obj.affiliate.tenant.destination_url
#         # return "https://testurl.com"
#         # request = self.context.get("request")
#         # return request.build_absolute_uri(f"/r/{obj.slug}") if request else None


class ReferralActionSerializer(serializers.ModelSerializer):
    class Meta:
        model = ReferralAction
        fields = [
            "id",
            "tenant",
            "referral_link",
            "action_type",
            "timestamp",
            "converted_at",
            "conversion_value",
            "is_converted",
        ]
        read_only_fields = ["tenant", "timestamp"]


class CommissionSerializer(serializers.ModelSerializer):
    referral_action_type = serializers.CharField(
        source="referral_action.action_type", read_only=True
    )

    class Meta:
        model = Commission
        fields = [
            "id",
            "affiliate",
            "referral_action",
            "referral_action_type",
            "amount",
            "rate",
            "calculated_at",
            "status",
        ]
        read_only_fields = ["amount", "rate", "calculated_at"]


class PayoutSerializer(serializers.ModelSerializer):
    class Meta:
        model = Payout
        fields = [
            "id",
            "tenant",
            "affiliate",
            "amount",
            "status",
            "created_at",
            "processed_at",
            "method",
        ]
        read_only_fields = ["tenant", "created_at", "processed_at"]


class CommissionRuleSerializer(serializers.ModelSerializer):
    class Meta:
        model = CommissionRule
        fields = [
            "id",
            "tenant",
            "name",
            "action_type",
            "is_percentage",
            "value",
            "min_value",
            "max_value",
            "is_active",
        ]


class ReferralSessionSerializer(serializers.ModelSerializer):
    class Meta:
        model = ReferralSession
        fields = "__all__"
