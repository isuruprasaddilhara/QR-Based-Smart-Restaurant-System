from rest_framework.permissions import BasePermission, SAFE_METHODS


def make_role_permission(role_name):
    """Factory that creates a permission class for a given role."""
    class RolePermission(BasePermission):
        message = f"Only {role_name}s can perform this action."

        def has_permission(self, request, view):
            return (
                request.user and
                request.user.is_authenticated and
                getattr(request.user, 'role', None) == role_name
            )
    RolePermission.__name__ = f"Is{role_name.capitalize()}"
    return RolePermission


IsAdmin    = make_role_permission('admin')
IsKitchen  = make_role_permission('kitchen')
IsCashier  = make_role_permission('cashier')
IsCustomer = make_role_permission('customer')


class IsAdminOrReadOnly(BasePermission):
    """
    - Unauthenticated (anonymous): read-only
    - Authenticated non-admin:     read-only
    - Admin:                       full access
    """
    def has_permission(self, request, view):
        if request.method in SAFE_METHODS:
            return True                          # anonymous can read
        return (
            request.user and
            request.user.is_authenticated and
            getattr(request.user, 'role', None) == 'admin'
        )


class HasAnyRole(BasePermission):
    """Allows access to any authenticated user with a known role."""
    ALLOWED_ROLES = {'admin', 'kitchen', 'cashier', 'customer'}

    def has_permission(self, request, view):
        return (
            request.user and
            request.user.is_authenticated and
            getattr(request.user, 'role', None) in self.ALLOWED_ROLES
        )


class AllowAnonymous(BasePermission):
    """
    Explicitly allows any request through, authenticated or not.
    Use on fully public endpoints (e.g. menu browsing, customer registration).
    """
    def has_permission(self, request, view):
        return True


class IsAuthenticatedOrAnonymousReadOnly(BasePermission):
    """
    - Unauthenticated: read-only
    - Authenticated:   full access regardless of role
    Useful for endpoints where any logged-in user can write (e.g. placing an order).
    """
    def has_permission(self, request, view):
        if request.method in SAFE_METHODS:
            return True
        return bool(request.user and request.user.is_authenticated)