from django.urls import include, path
from rest_framework.routers import DefaultRouter
from rest_framework_simplejwt.views import (
    TokenObtainPairView,
    TokenRefreshView,
)

from .views import (
    AffiliateViewSet,
    CommissionRuleViewSet,
    CommissionViewSet,
    EnhancedTrackingView,
    PayoutViewSet,
    ReferralActionViewSet,
    ReferralLinkViewSet,
    SimpleDebugView,
    TenantViewSet,
)

router = DefaultRouter()
# router.register(r"affiliates", AffiliateViewSet)
router.register(r"", AffiliateViewSet, basename="affiliates")
router.register(r"tenants", TenantViewSet)
router.register(r"referral-links", ReferralLinkViewSet, basename="referral-links")
router.register(r"referral-actions", ReferralActionViewSet, basename="referral-actions")
router.register(r"payouts", PayoutViewSet, basename="payouts")
router.register(r"commissions", CommissionViewSet, basename="commissions")
router.register(r"commission-rules", CommissionRuleViewSet, basename="commission-rules")

urlpatterns = [
    path("affiliates/", include(router.urls)),
    path("debug/", SimpleDebugView.as_view(), name="debug-view"),
    path("api/auth/token/", TokenObtainPairView.as_view(), name="token_obtain_pair"),
    path("api/auth/token/refresh/", TokenRefreshView.as_view(), name="token_refresh"),
    # Webhook for external conversions
    path(
        "api/webhook/conversion/",
        ReferralActionViewSet.as_view({"post": "convert"}),
        name="conversion-webhook",
    ),
    path("api/track/", EnhancedTrackingView.as_view(), name="enhanced-tracking"),
    # path('api/analytics/', analytics_dashboard, name='analytics-dashboard'),
]
