import base64
import json
import os
import uuid
from datetime import timedelta

from django.conf import settings
from django.db.models import Avg, Count, Q, Sum
from django.http import Http404
from django.shortcuts import get_object_or_404, redirect
from django.utils import timezone
from django.utils.dateparse import parse_datetime
from django.views import View
from google.oauth2 import service_account
from googleapiclient.discovery import build
from rest_framework import serializers, status, viewsets
from rest_framework.decorators import action
from rest_framework.exceptions import ValidationError
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from .authentication import HybridAuthentication, StrictHybridAuthentication
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
from .permissions import IsAffiliate, IsTenantAdmin, IsTenantOrAdmin
from .serializers import (
    AffiliateSerializer,
    CommissionRuleSerializer,
    CommissionSerializer,
    PayoutSerializer,
    ReferralActionSerializer,
    ReferralLinkSerializer,
    TenantSerializer,
)
from .services.tracking import process_tracking_event


class SimpleDebugView(APIView):
    """
    A simple view for debugging GET and POST requests.
    No authentication or permissions required.
    """

    def get(self, request, format=None):
        # Handle GET request
        response_data = {
            "message": "GET request received",
            "request_data": {
                "query_params": dict(request.query_params),
                "headers": dict(request.headers),
                "user": str(request.user),  # Will show 'AnonymousUser' if not authenticated
            },
        }
        return Response(response_data, status=status.HTTP_200_OK)

    def post(self, request, format=None):
        # Handle POST request
        response_data = {
            "message": "POST request received",
            "request_data": {
                "body_data": request.data,
                "query_params": dict(request.query_params),
                "headers": dict(request.headers),
                "user": str(request.user),
            },
        }
        return Response(response_data, status=status.HTTP_201_CREATED)


class TenantViewSet(viewsets.ModelViewSet):
    queryset = Tenant.objects.all()
    serializer_class = TenantSerializer
    authentication_classes = [HybridAuthentication]
    permission_classes = [IsTenantOrAdmin]

    def get_queryset(self):
        if self.request.user.is_superuser:
            return super().get_queryset()
        if self.request.user.is_authenticated:
            return Tenant.objects.filter(owner=self.request.user)
        return Tenant.objects.none()  # Safety fallback

    def perform_create(self, serializer):
        # Automatically set the creator as owner
        serializer.save(owner=self.request.user)

    @action(detail=True, methods=["post"])
    def regenerate_api_key(self, request, pk=None):
        tenant = self.get_object()
        tenant.api_key = uuid.uuid4()
        tenant.save()
        return Response({"api_key": tenant.api_key})


class AffiliateViewSet(viewsets.ModelViewSet):
    serializer_class = AffiliateSerializer
    authentication_classes = [StrictHybridAuthentication]
    permission_classes = [IsTenantOrAdmin | IsAffiliate]

    def get_queryset(self):
        tenant = self.request.tenant  # Access the tenant set by the auth class

        # tenant = self.request.tenant
        if not tenant:
            if self.request.user.is_authenticated:
                return Affiliate.objects.filter(user=self.request.user)
            return Affiliate.objects.none()

        queryset = Affiliate.objects.filter(tenant=tenant)

        # Affiliates can only see their own record
        if not (
            IsTenantOrAdmin().has_permission(self.request, self)
            or IsTenantAdmin().has_permission(self.request, self)
        ):
            queryset = queryset.filter(user=self.request.user)

        return queryset

    def list(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_queryset())

        # If user should only see their own record, return single object
        if not (
            IsTenantOrAdmin().has_permission(request, self)
            or IsTenantAdmin().has_permission(request, self)
        ):
            instance = queryset.first()
            if not instance:
                raise Http404("No Affiliate found for this user")
            serializer = self.get_serializer(instance)
            return Response(serializer.data)

        # Otherwise return full list
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=["get"])
    def stats(self, request):
        """Get affiliate statistics"""
        if not request.user.is_authenticated:
            return Response(
                {"detail": "Authentication required"},
                status=status.HTTP_401_UNAUTHORIZED,
            )

        try:
            affiliate = Affiliate.objects.get(user=request.user)
        except Affiliate.DoesNotExist:
            return Response(
                {"detail": "Affiliate profile not found"},
                status=status.HTTP_404_NOT_FOUND,
            )

        # Get date range (default to last 30 days)
        end_date = timezone.now()
        start_date = end_date - timedelta(days=30)

        date_from = request.query_params.get("date_from")
        date_to = request.query_params.get("date_to")

        if date_from:
            start_date = parse_datetime(date_from) or start_date
        if date_to:
            end_date = parse_datetime(date_to) or end_date

        # Get referral actions for this affiliate
        actions = ReferralAction.objects.filter(
            referral_link__affiliate=affiliate, timestamp__range=[start_date, end_date]
        )

        # Calculate stats
        total_clicks = actions.filter(action_type="click").count()
        total_page_views = actions.filter(action_type="page_view").count()
        total_signups = actions.filter(action_type="signup").count()
        total_conversions = actions.filter(is_converted=True).count()
        conversion_rate = (total_conversions / total_clicks * 100) if total_clicks > 0 else 0

        # Commission stats
        commissions = Commission.objects.filter(affiliate=affiliate)
        total_earnings = commissions.aggregate(total=Sum("amount"))["total"] or 0
        pending_earnings = (
            commissions.filter(status="pending").aggregate(total=Sum("amount"))["total"] or 0
        )
        paid_earnings = (
            commissions.filter(status="paid").aggregate(total=Sum("amount"))["total"] or 0
        )

        # Top performing links
        top_links = (
            ReferralLink.objects.filter(affiliate=affiliate)
            .annotate(
                clicks_count=Count("actions", filter=Q(actions__action_type="click")),
                conversions_count=Count("actions", filter=Q(actions__is_converted=True)),
            )
            .order_by("created_at__date")
        )

        # Traffic sources
        traffic_sources = (
            actions.values("referring_url").annotate(count=Count("id")).order_by("-count")[:10]
        )

        # Device/Browser stats
        device_stats = (
            actions.values("user_agent").annotate(count=Count("id")).order_by("-count")[:10]
        )

        # Geographic data
        geographic_stats = (
            actions.values("ip_address").annotate(count=Count("id")).order_by("-count")[:10]
        )

        return Response(
            {
                "total_clicks": total_clicks,
                "total_page_views": total_page_views,
                "total_signups": total_signups,
                "total_conversions": total_conversions,
                "conversion_rate": conversion_rate,
                "total_earnings": total_earnings,
                "pending_earnings": pending_earnings,
                "paid_earnings": paid_earnings,
                "total_revenue": actions.filter(is_converted=True).aggregate(
                    total=Sum("conversion_value")
                )["total"]
                or 0,
                "traffic_sources": list(traffic_sources),
                "device_stats": list(device_stats),
                "geographic_stats": list(geographic_stats),
                "date_range": {
                    "start": start_date.isoformat(),
                    "end": end_date.isoformat(),
                },
            }
        )


class ReferralLinkViewSet(viewsets.ModelViewSet):
    serializer_class = ReferralLinkSerializer
    authentication_classes = [HybridAuthentication]
    permission_classes = [IsTenantOrAdmin | IsAffiliate]

    def get_queryset(self):
        tenant = self.request.tenant
        if not tenant:
            return ReferralLink.objects.none()

        queryset = ReferralLink.objects.filter(affiliate__tenant=tenant)

        # Affiliates can only see their own links
        if not (
            IsTenantOrAdmin().has_permission(self.request, self)
            or IsTenantAdmin().has_permission(self.request, self)
        ):
            queryset = queryset.filter(affiliate__user=self.request.user)

        return queryset.select_related("affiliate")

    def perform_create(self, serializer):
        print("PERFORM CREATE REFERRAL LINK")
        tenant = self.request.tenant
        if not tenant:
            raise serializers.ValidationError("Tenant context required")

        # affiliate = serializer.validated_data.get("affiliate")
        print("request user", self.request.user)
        affiliate = Affiliate.objects.get(user=self.request.user)
        if affiliate.tenant != tenant:
            raise serializers.ValidationError("Affiliate does not belong to tenant")

        # Verify affiliate is current user unless admin
        if not (
            IsTenantOrAdmin().has_permission(self.request, self)
            or IsTenantAdmin().has_permission(self.request, self)
        ):
            if affiliate.user != self.request.user:
                raise serializers.ValidationError("Cannot create links for other affiliates")

        serializer.save(affiliate=affiliate)


class ReferralActionViewSet(viewsets.ModelViewSet):
    serializer_class = ReferralActionSerializer
    authentication_classes = [HybridAuthentication]
    permission_classes = [IsTenantOrAdmin | IsAffiliate]

    def get_queryset(self):
        tenant = self.request.tenant
        if not tenant:
            return ReferralAction.objects.none()

        queryset = ReferralAction.objects.filter(tenant=tenant)

        # Filter by referral link if provided
        referral_link = self.request.query_params.get("referral_link")
        if referral_link:
            queryset = queryset.filter(referral_link=referral_link)

        # Filter by action type if provided
        action_type = self.request.query_params.get("action_type")
        if action_type:
            queryset = queryset.filter(action_type=action_type)

        # Filter by conversion status if provided
        is_converted = self.request.query_params.get("is_converted")
        if is_converted:
            queryset = queryset.filter(is_converted=is_converted.lower() == "true")

        return queryset.select_related("referral_link", "referral_link__affiliate")

    @action(detail=False, methods=["post"])
    def track_click(self, request):
        """Endpoint for tracking referral link clicks"""
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        referral_link = get_object_or_404(
            ReferralLink, slug=serializer.validated_data["referral_link_slug"]
        )

        action = ReferralAction.objects.create(
            tenant=referral_link.affiliate.tenant,
            referral_link=referral_link,
            action_type="click",
            ip_address=request.META.get("REMOTE_ADDR"),
            user_agent=request.META.get("HTTP_USER_AGENT", ""),
            referring_url=request.META.get("HTTP_REFERER", ""),
            metadata={
                "headers": dict(request.headers),
                "query_params": dict(request.query_params),
            },
        )

        return Response(self.get_serializer(action).data, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=["post"])
    def convert(self, request, pk=None):
        """Mark an action as converted (e.g., signup or purchase)"""
        action = self.get_object()

        if action.is_converted:
            return Response(
                {"detail": "Action already converted"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        action.is_converted = True
        action.converted_at = timezone.now()
        action.conversion_value = request.data.get("conversion_value", 0)
        action.save()

        # Calculate and create commission
        self._create_commission(action)

        return Response(self.get_serializer(action).data, status=status.HTTP_200_OK)

    @action(detail=False, methods=["post"], permission_classes=[AllowAny])
    def track_click(self, request):
        """Tracks a click event."""
        try:
            data = request.data.copy()
            data["event_type"] = "click"
            action = process_tracking_event(data, request.META)
            return Response(self.get_serializer(action).data, status=201)
        except ValidationError as e:
            return Response({"detail": str(e)}, status=400)

    @action(detail=False, methods=["post"], permission_classes=[AllowAny])
    def track_event(self, request):
        """Tracks any custom event including conversions."""
        try:
            action = process_tracking_event(request.data, request.META)
            return Response(self.get_serializer(action).data, status=201)
        except ValidationError as e:
            return Response({"detail": str(e)}, status=400)


class CommissionViewSet(viewsets.ModelViewSet):
    serializer_class = CommissionSerializer
    authentication_classes = [HybridAuthentication]
    permission_classes = [IsTenantOrAdmin | IsAffiliate]

    def get_queryset(self):
        tenant = self.request.tenant
        if not tenant:
            return Commission.objects.none()

        queryset = Commission.objects.filter(affiliate__tenant=tenant)

        # Affiliates can only see their own commissions
        if not (
            IsTenantOrAdmin().has_permission(self.request, self)
            or IsTenantAdmin().has_permission(self.request, self)
        ):
            queryset = queryset.filter(affiliate__user=self.request.user)

        # Filter by status if provided
        status_param = self.request.query_params.get("status")
        if status_param:
            queryset = queryset.filter(status=status_param.lower())

        return queryset.select_related("affiliate", "referral_action")


class PayoutViewSet(viewsets.ModelViewSet):
    serializer_class = PayoutSerializer
    authentication_classes = [HybridAuthentication]
    permission_classes = [IsTenantOrAdmin | IsAffiliate]

    def get_queryset(self):
        tenant = self.request.tenant
        if not tenant:
            return Payout.objects.none()

        queryset = Payout.objects.filter(tenant=tenant)

        # Affiliates can only see their own payouts
        if not (
            IsTenantOrAdmin().has_permission(self.request, self)
            or IsTenantAdmin().has_permission(self.request, self)
        ):
            queryset = queryset.filter(affiliate__user=self.request.user)

        # Filter by status if provided
        status_param = self.request.query_params.get("status")
        if status_param:
            queryset = queryset.filter(status=status_param.lower())

        return queryset.select_related("affiliate")

    @action(detail=False, methods=["post"])
    def request_payout(self, request):
        """Allow affiliates to request a payout"""
        tenant = self.request.tenant
        if not tenant:
            return Response(
                {"detail": "Tenant context required"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        affiliate = get_object_or_404(Affiliate, tenant=tenant, user=request.user)

        if affiliate.balance < affiliate.payout_threshold:
            return Response(
                {"detail": f"Balance must be at least {affiliate.payout_threshold}"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if not affiliate.payout_method:
            return Response(
                {"detail": "Payout method not configured"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Create payout (actual processing would be async via Celery)
        payout = Payout.objects.create(
            tenant=tenant,
            affiliate=affiliate,
            amount=affiliate.balance,
            status="pending",
            method=affiliate.payout_method,
        )

        # Reset affiliate balance
        affiliate.balance = 0
        affiliate.save()

        return Response(self.get_serializer(payout).data, status=status.HTTP_201_CREATED)


class CommissionRuleViewSet(viewsets.ModelViewSet):
    serializer_class = CommissionRuleSerializer
    authentication_classes = [HybridAuthentication]
    permission_classes = [IsTenantAdmin]

    def get_queryset(self):
        tenant = self.request.tenant
        if not tenant:
            return CommissionRule.objects.none()
        return CommissionRule.objects.filter(tenant=tenant)

    def perform_create(self, serializer):
        tenant = self.request.tenant
        if not tenant:
            raise serializers.ValidationError("Tenant context required")
        serializer.save(tenant=tenant)


class ReferralLinkRedirectView(View):
    """Handle referral link clicks and redirect to destination"""

    def get(self, request, slug):
        try:
            referral_link = ReferralLink.objects.select_related("affiliate").get(
                slug=slug, is_active=True
            )
        except ReferralLink.DoesNotExist:
            return redirect("/")  # Or custom 404

        # Track the click
        ReferralAction.objects.create(
            tenant=referral_link.affiliate.tenant,
            referral_link=referral_link,
            action_type="click",
            ip_address=request.META.get("REMOTE_ADDR"),
            user_agent=request.META.get("HTTP_USER_AGENT", ""),
            referring_url=request.META.get("HTTP_REFERER", ""),
            metadata={
                "query_params": dict(request.GET),
            },
        )

        # Set referral cookie
        response = redirect(referral_link.destination_url)
        cookie_name = f"ref_{referral_link.affiliate.tenant.slug}"
        response.set_cookie(
            cookie_name,
            referral_link.affiliate.code,
            max_age=60 * 60 * 24 * referral_link.affiliate.tenant.cookie_duration_days,
            httponly=True,
            secure=not settings.DEBUG,
        )

        return response


# Enhanced tracking view with session management
class EnhancedTrackingView(APIView):
    """Advanced tracking with session management and attribution"""

    permission_classes = [AllowAny]

    def post(self, request):
        try:
            action = process_tracking_event(
                request.data,
                request.META,
                use_sessions=True,
                attribution_model="last_click",
            )
            return Response(
                {
                    "action_id": action.id,
                    "session_id": action.session_id,
                    "affiliate_code": action.referral_link.affiliate.code,
                    "status": "tracked",
                },
                status=201,
            )
        except ValidationError as e:
            return Response({"detail": str(e)}, status=400)

    # def post(self, request):
    #     data = request.data
    #     session_id = data.get("session_id")
    #     referral_code = data.get("referral_code")
    #     event_type = data.get("event_type", "click")

    #     if not referral_code:
    #         return Response(
    #             {"detail": "Referral code required"}, status=status.HTTP_400_BAD_REQUEST
    #         )

    #     try:
    #         affiliate = Affiliate.objects.get(code=referral_code)
    #         referral_link = ReferralLink.objects.filter(
    #             affiliate=affiliate, is_active=True
    #         ).first()

    #         if not referral_link:
    #             return Response(
    #                 {"detail": "No active referral link found"},
    #                 status=status.HTTP_400_BAD_REQUEST,
    #             )
    #     except Affiliate.DoesNotExist:
    #         return Response(
    #             {"detail": "Invalid referral code"}, status=status.HTTP_400_BAD_REQUEST
    #         )

    #     # Get or create session
    #     session, created = ReferralSession.objects.get_or_create(
    #         session_id=session_id,
    #         defaults={
    #             "affiliate": affiliate,
    #             "first_referral_link": referral_link,
    #             "last_referral_link": referral_link,
    #             "ip_address": request.META.get("REMOTE_ADDR"),
    #             "user_agent": request.META.get("HTTP_USER_AGENT", ""),
    #         },
    #     )

    #     # Update session with latest touch
    #     if not created:
    #         session.last_referral_link = referral_link
    #         session.last_touch = timezone.now()
    #         session.save()

    #     # Create referral action
    #     action = ReferralAction.objects.create(
    #         tenant=affiliate.tenant,
    #         referral_link=referral_link,
    #         action_type=event_type,
    #         session_id=session_id,
    #         ip_address=request.META.get("REMOTE_ADDR"),
    #         user_agent=request.META.get("HTTP_USER_AGENT", ""),
    #         referring_url=data.get("metadata", {}).get("referrer", ""),
    #         conversion_value=data.get("conversion_value", 0),
    #         metadata={
    #             **data.get("metadata", {}),
    #             "session_created": created,
    #             "attribution_model": "last_click",  # or 'first_click', 'linear', etc.
    #         },
    #     )

    #     # Handle conversions
    #     if event_type in ["purchase"] or data.get("is_conversion", False):
    #         action.is_converted = True
    #         action.converted_at = timezone.now()
    #         action.save()

    #         # Update session
    #         session.is_converted = True
    #         session.conversion_value = data.get("conversion_value", 0)
    #         session.save()

    #         # Create commission using attribution model
    #         self._create_attributed_commission(action, session)

    #     return Response(
    #         {
    #             "action_id": action.id,
    #             "session_id": session.session_id,
    #             "affiliate_code": affiliate.code,
    #             "status": "tracked",
    #         },
    #         status=status.HTTP_201_CREATED,
    #     )

    # def _create_attributed_commission(self, action, session):
    #     """Create commission with proper attribution"""
    #     tenant = action.tenant

    #     # Determine which affiliate gets credit based on attribution model
    #     attribution_model = action.metadata.get("attribution_model", "last_click")

    #     if attribution_model == "first_click":
    #         credited_affiliate = session.first_referral_link.affiliate
    #         credited_link = session.first_referral_link
    #     else:  # last_click (default)
    #         credited_affiliate = session.last_referral_link.affiliate
    #         credited_link = session.last_referral_link

    #     # Find commission rule
    #     rule = CommissionRule.objects.filter(
    #         tenant=tenant, action_type=action.action_type, is_active=True
    #     ).first()

    #     if not rule:
    #         rule = CommissionRule.objects.filter(
    #             tenant=tenant, action_type="other", is_active=True
    #         ).first()

    #     if not rule:
    #         return None

    #     # Calculate commission
    #     if rule.is_percentage:
    #         amount = (action.conversion_value or 0) * (rule.value / 100)
    #         if rule.min_value is not None:
    #             amount = max(amount, rule.min_value)
    #         if rule.max_value is not None:
    #             amount = min(amount, rule.max_value)
    #     else:
    #         amount = rule.value

    #     # Create commission
    #     commission = Commission.objects.create(
    #         affiliate=credited_affiliate,
    #         referral_action=action,
    #         amount=amount,
    #         rate=rule.value if rule.is_percentage else 0,
    #         status="pending",
    #         # metadata={
    #         #     "attribution_model": attribution_model,
    #         #     "session_id": session.session_id,
    #         #     "credited_link_id": credited_link.id,
    #         # },
    #     )

    #     # Update affiliate balance
    #     credited_affiliate.balance += amount
    #     credited_affiliate.save()

    #     return commission
