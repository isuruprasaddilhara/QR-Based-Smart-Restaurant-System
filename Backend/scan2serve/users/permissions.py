# from rest_framework.permissions import BasePermission

# class IsAdmin(BasePermission):
#     def has_permission(self, request, view):
#         if not request.user.is_authenticated:
#             return False
#         return request.user.role == 'admin'


# class IsKitchen(BasePermission):
#     def has_permission(self, request, view):
#         if not request.user.is_authenticated:
#             return False
#         return request.user.role == 'kitchen'


# class IsCashier(BasePermission):
#     def has_permission(self, request, view):
#         if not request.user.is_authenticated:
#             return False
#         return request.user.role == 'cashier'

# class IsCustomer(BasePermission):
#     def has_permission(self, request, view):
#         if not request.user.is_authenticated:
#             return False
#         return request.user.role == 'customer'

from rest_framework.permissions import BasePermission, SAFE_METHODS

def make_role_permission(role_name):
    """Factory that creates a permission class for a given role."""
    class RolePermission(BasePermission):
        def has_permission(self, request, view):
            return (
                request.user.is_authenticated and
                request.user.role == role_name
            )
    RolePermission.__name__ = f"Is{role_name.capitalize()}"
    return RolePermission

IsAdmin    = make_role_permission('admin')
IsKitchen  = make_role_permission('kitchen')
IsCashier  = make_role_permission('cashier')
IsCustomer = make_role_permission('customer')


class IsAdminOrReadOnly(BasePermission):
    """Admin has full access; other authenticated users can only read."""
    def has_permission(self, request, view):
        if not request.user.is_authenticated:
            return False
        if request.method in SAFE_METHODS:
            return True
        return request.user.role == 'admin'


class HasAnyRole(BasePermission):
    """Allows access to any authenticated user with a known role."""
    ALLOWED_ROLES = {'admin', 'kitchen', 'cashier', 'customer'}

    def has_permission(self, request, view):
        return (
            request.user.is_authenticated and
            request.user.role in self.ALLOWED_ROLES
        )