from django.urls import path

from .views import FavoriteDestroyView, FavoriteListCreateView

urlpatterns = [
    path("", FavoriteListCreateView.as_view(), name="favourite-list-create"),
    path("<int:pk>/", FavoriteDestroyView.as_view(), name="favourite-destroy"),
]
