# middleware.py (simplified)
import logging

from django.conf import settings
from django.http import HttpResponse
from django.utils.deprecation import MiddlewareMixin

from django_affiliate_system.models import Tenant

logger = logging.getLogger(__name__)


# class CORSMiddleware:
#     print("this is my custom cors MIDDLEWARE")
#     print("this is my custom cors MIDDLEWARE")
#     print("this is my custom cors MIDDLEWARE")
#     print("this is my custom cors MIDDLEWARE")

#     def __init__(self, get_response):
#         self.get_response = get_response

#     def __call__(self, request):
#         # Process the request before the view
#         response = self.get_response(request)

#         # Add CORS headers to the response
#         self._add_cors_headers(response)

#         return response

#     def process_view(self, request, view_func, view_args, view_kwargs):
#         # Handle OPTIONS (preflight) requests
#         if request.method == "OPTIONS":
#             # Create a new response instead of calling get_response again
#             response = HttpResponse()
#             self._add_cors_headers(response)
#             response.status_code = 200
#             return response

#         return None

#     def _add_cors_headers(self, response):
#         # Helper method to add CORS headers
#         response["Access-Control-Allow-Origin"] = "http://localhost:3000"
#         response["Access-Control-Allow-Methods"] = (
#             "GET, POST, PUT, PATCH, DELETE, OPTIONS"
#         )
#         response["Access-Control-Allow-Headers"] = (
#             "Content-Type, Authorization, X-Requested-With"
#         )
#         response["Access-Control-Allow-Credentials"] = "true"
#         response["Access-Control-Max-Age"] = "86400"  # 24 hours


class CORSMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # Process the request before the view
        response = self.get_response(request)
        self._add_cors_headers(request, response)
        return response

    def process_view(self, request, view_func, view_args, view_kwargs):
        if request.method == "OPTIONS":
            response = HttpResponse()
            self._add_cors_headers(request, response)
            response.status_code = 200
            return response
        return None

    def _add_cors_headers(self, request, response):
        # Check the request's origin against allowed origins
        # allowed_origins = [
        #     "http://localhost:3000",
        #     "https://nextrole.co.uk",
        #     "https://api.nextrole.co.uk",
        # ]
        allowed_origins = settings.AFFILIATE_SYSTEM.get("ALLOWED_CORS_ORIGINS", [])

        origin = request.headers.get("Origin")

        if origin in allowed_origins:
            response["Access-Control-Allow-Origin"] = origin
        else:
            # You might want to set a default or leave it out
            pass

        response["Access-Control-Allow-Methods"] = "GET, POST, PUT, PATCH, DELETE, OPTIONS"
        response["Access-Control-Allow-Headers"] = (
            "Content-Type, Authorization, X-Requested-With, X-API-Key"
        )
        response["Access-Control-Allow-Credentials"] = "true"
        response["Access-Control-Max-Age"] = "86400"


class TenantMiddleware(MiddlewareMixin):
    """Set tenant context based on subdomain only"""

    def process_request(self, request):
        logger.debug("Processing tenant middleware")

        # Skip if already set by authentication
        if hasattr(request, "tenant"):
            logger.debug("Tenant already set by authentication")
            return

        # Check subdomain (primary responsibility of middleware)
        host = request.get_host()
        if "." in host:
            subdomain = host.split(".")[0]
            if subdomain and subdomain != "www":
                try:
                    request.tenant = Tenant.objects.get(subdomain=subdomain, is_active=True)
                    logger.debug(f"Tenant set from subdomain: {request.tenant}")
                    return
                except Tenant.DoesNotExist:
                    logger.warning(f"No tenant found for subdomain: {subdomain}")

        # Set default behavior for requests without tenant context
        logger.debug("No tenant found, using default behavior")
        request.tenant = None
