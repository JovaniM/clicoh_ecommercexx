from rest_framework.permissions import IsAuthenticated


class IsAuthenticatedStaffUser(IsAuthenticated):
    def has_permission(self, request, view):
        authenticated = super().has_permission(request, view)
        return authenticated and request.user and request.user.staff


class IsAuthenticatedAdminUser(IsAuthenticated):
    def has_permission(self, request, view):
        authenticated = super().has_permission(request, view)
        return authenticated and request.user and request.user.admin


class IsAuthenticatedSuperUser(IsAuthenticated):
    def has_permission(self, request, view):
        authenticated = super().has_permission(request, view)
        return authenticated and request.user and request.user.is_superuser
