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

class IsAdminOrCashierOrReadOnly(BasePermission):
    """
    - Read (GET, HEAD, OPTIONS): Allow anyone
    - Write (POST, PUT, PATCH, DELETE): Only admin & cashier
    """
    message = "Write access restricted to admin and cashier roles."

    def has_permission(self, request, view):
        # Allow read for everyone (even unauthenticated)
        if request.method in SAFE_METHODS:
            return True

        # Write access → only admin or cashier
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

class IsStaff(BasePermission):
    """
    Allows full access to staff users:
    - admin
    - kitchen
    - cashier
    """
    message = "Access restricted to staff only."

    STAFF_ROLES = {'admin', 'kitchen', 'cashier'}

    def has_permission(self, request, view):
        return (
            request.user
            and request.user.is_authenticated
            and getattr(request.user, 'role', None) in self.STAFF_ROLES
        )

class OrderPermission(BasePermission):
    """
    Custom permission for Order endpoints:
    - POST → Allow anyone (guest or authenticated)
    - GET/HEAD/OPTIONS → Only admin, kitchen, cashier
    - Others (PUT/PATCH/DELETE) → Admin only
    """

    def has_permission(self, request, view):
        # Allow anyone to create orders
        if request.method == 'POST':
            return True

        # Read operations → staff roles only
        if request.method in SAFE_METHODS:
            return (
                request.user
                and request.user.is_authenticated
                and getattr(request.user, 'role', None) in ['admin', 'kitchen', 'cashier']
            )

        # Write operations → admin only
        return (
            request.user
            and request.user.is_authenticated
            and getattr(request.user, 'role', None) == 'admin'
        )