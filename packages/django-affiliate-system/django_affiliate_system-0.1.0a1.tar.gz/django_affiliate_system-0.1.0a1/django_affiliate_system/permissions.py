# permissions.py
import logging

from django.contrib.auth import get_user_model

User = get_user_model()
from rest_framework.permissions import BasePermission

from .models import Affiliate, Tenant

logger = logging.getLogger(__name__)


class IsTenantAdmin(BasePermission):
    """Check if user is admin for the tenant"""

    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False

        # For views that need tenant context
        tenant = getattr(request, "tenant", None)
        if tenant:
            return tenant.owner == request.user

        return False


class IsAffiliate(BasePermission):
    """Check if user is an affiliate"""

    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            logger.error("USER IS NOT LOGGED")
            logger.error("USER IS NOT LOGGED")
            return False

        return Affiliate.objects.filter(user=request.user).exists()

        # tenant = getattr(request, "tenant", None)
        # if tenant:
        #     return Affiliate.objects.filter(tenant=tenant, user=request.user).exists()

        # logger.error("CANT FIND TENANT")

        # return False


class IsTenantOrAdmin(BasePermission):
    """Allow access if:
    - Authenticated via API key (tenant exists)
    - JWT user is tenant owner OR superuser
    """

    def has_permission(self, request, view):
        # Case 1: API Key Authentication (user=None but tenant exists)
        if request.user is None:
            has_tenant = hasattr(request, "tenant") and request.tenant is not None
            logger.info(f"API Key Auth - Tenant exists: {has_tenant}")
            return has_tenant

        # Case 2: Verify we have a User object
        if not isinstance(request.user, User):
            logger.error(f"Invalid user type: {type(request.user)}")
            return False

        # Case 3: Superuser check
        if request.user.is_superuser:
            logger.info("Superuser access granted")
            return True

        # Case 4: Tenant owner check
        tenant = getattr(request, "tenant", None)
        if tenant:
            is_owner = getattr(tenant, "owner_id", None) == request.user.id
            logger.info(f"Tenant owner check: {is_owner}")
            return is_owner

        logger.info("No valid access conditions met")
        return False
