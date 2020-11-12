from rest_framework import permissions


class SettingsPermission(permissions.BasePermission):
    def has_permission(self, request, view):
        if request.method == "GET" or request.user.is_staff:
            return True
        return False
