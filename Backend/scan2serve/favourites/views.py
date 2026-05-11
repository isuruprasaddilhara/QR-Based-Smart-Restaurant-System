from rest_framework import generics
from rest_framework.permissions import IsAuthenticated

from users.permissions import IsCustomer

from .models import FavoriteMenuItem
from .serializers import FavoriteMenuItemSerializer


class FavoriteListCreateView(generics.ListCreateAPIView):
    """GET/POST /favourites/ — list or add a favourite (customers only)."""

    permission_classes = [IsAuthenticated, IsCustomer]
    serializer_class = FavoriteMenuItemSerializer

    def get_queryset(self):
        return FavoriteMenuItem.objects.filter(user=self.request.user).select_related(
            "menu_item__category"
        )

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)


class FavoriteDestroyView(generics.DestroyAPIView):
    """DELETE /favourites/<pk>/ — remove a favourite row owned by the customer."""

    permission_classes = [IsAuthenticated, IsCustomer]
    serializer_class = FavoriteMenuItemSerializer

    def get_queryset(self):
        return FavoriteMenuItem.objects.filter(user=self.request.user)
