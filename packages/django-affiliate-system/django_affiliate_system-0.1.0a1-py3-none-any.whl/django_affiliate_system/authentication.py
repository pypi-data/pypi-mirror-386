# authentication.py
import logging
import uuid

from django.contrib.auth import get_user_model
from rest_framework.authentication import BaseAuthentication
from rest_framework.exceptions import AuthenticationFailed
from rest_framework_simplejwt.authentication import JWTAuthentication

from .models import Affiliate, Tenant

logger = logging.getLogger(__name__)
User = get_user_model()


class TenantAPIKeyAuthentication(BaseAuthentication):
    """Authentication using tenant API keys"""

    def authenticate(self, request):
        api_key = request.META.get("HTTP_X_API_KEY")
        if not api_key:
            return None

        try:
            tenant = Tenant.objects.get(api_key=uuid.UUID(api_key), is_active=True)
            request.tenant = tenant  # Attach tenant to request
            return (tenant.owner, None)  # Return owner as user
        except (Tenant.DoesNotExist, ValueError) as e:
            logger.warning(f"Invalid API key: {api_key}, Error: {e}")
            raise AuthenticationFailed("Invalid API key")

    def authenticate_header(self, request):
        return "X-API-Key"


class HybridAuthentication(BaseAuthentication):
    """Support both JWT (for user auth) and API key (for tenant auth)"""

    def __init__(self):
        self.jwt_auth = JWTAuthentication()
        self.api_key_auth = TenantAPIKeyAuthentication()

    def authenticate(self, request):
        # Try JWT first
        user_auth = self.jwt_auth.authenticate(request)
        if user_auth:
            user, token = user_auth
            request.user = user

            # Always try to set tenant for affiliate users
            try:
                affiliate = Affiliate.objects.filter(user=user).first()
                if affiliate:
                    request.tenant = affiliate.tenant
                    logger.debug(f"Tenant set from user affiliate: {request.tenant}")
                elif not hasattr(request, "tenant"):
                    # Optionally set tenant from user's other relationships if needed
                    request.tenant = getattr(user, "tenant", None)
            except Exception as e:
                logger.warning(f"Could not set tenant from user: {e}")
            return user_auth

        # Fall back to API key
        tenant_auth = self.api_key_auth.authenticate(request)
        if tenant_auth:
            tenant, key = tenant_auth
            request.user = None  # Explicitly set user to None for API key auth
            request.tenant = tenant
            return (None, tenant)  # Return consistent format

        return None

    def authenticate_header(self, request):
        return self.jwt_auth.authenticate_header(request)


class StrictHybridAuthentication(BaseAuthentication):
    """Requires both JWT (user) and API key (tenant) for authentication."""

    def __init__(self):
        self.jwt_auth = JWTAuthentication()
        self.api_key_auth = TenantAPIKeyAuthentication()

    def authenticate(self, request):
        # Try JWT authentication (user)
        user_auth = self.jwt_auth.authenticate(request)
        if not user_auth:
            raise AuthenticationFailed("JWT authentication failed (required).")

        # Try API key authentication (tenant)
        # This will set request.tenant automatically
        tenant_auth = self.api_key_auth.authenticate(request)
        if not tenant_auth:
            raise AuthenticationFailed("API key authentication failed (required).")

        # Both succeeded
        user, token = user_auth  # JWT user and token

        # The tenant was already set on the request by TenantAPIKeyAuthentication
        # So we just need to verify it exists
        if not hasattr(request, "tenant"):
            raise AuthenticationFailed("Tenant not properly set during authentication")

        logger.debug(f"Hybrid auth succeeded. User: {user.id}, Tenant: {request.tenant.id}")

        return (user, token)  # DRF expects (user, auth)

    def authenticate_header(self, request):
        # Uses JWT's WWW-Authenticate header (e.g., "Bearer")
        return self.jwt_auth.authenticate_header(request)
