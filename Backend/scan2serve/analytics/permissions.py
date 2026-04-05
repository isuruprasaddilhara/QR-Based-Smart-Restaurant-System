from rest_framework.permissions import BasePermission


class IsAdminOrCashier(BasePermission):
    """
    Allows access only to users with role 'admin' or 'cashier'.
    """
    message = "Access restricted to admin and cashier roles."

    def has_permission(self, request, view):
        return (
            request.user
            and request.user.is_authenticated
            and getattr(request.user, 'role', None) in ('admin', 'cashier')
        )


class IsAdminOnly(BasePermission):
    """
    Allows access only to admin users.
    """
    message = "Access restricted to admin role only."

    def has_permission(self, request, view):
        return (
            request.user
            and request.user.is_authenticated
            and getattr(request.user, 'role', None) == 'admin'
        )