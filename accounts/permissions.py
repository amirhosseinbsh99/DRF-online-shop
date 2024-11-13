from rest_framework.permissions import BasePermission
import logging

logger = logging.getLogger(__name__)

class IsCustomAdminUser(BasePermission):
    def has_permission(self, request, view):
        # Log to check if user is authenticated and is_admin
        if request.user.is_authenticated:
            logger.info(f"User authenticated: {request.user}, is_admin: {request.user.is_admin}")
        return request.user and request.user.is_authenticated and request.user.is_admin
    

    