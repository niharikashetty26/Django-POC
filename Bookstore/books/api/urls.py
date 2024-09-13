from django.urls import path
from .views import CustomTokenObtainPairView, RegisterView, BookViewSet, CartViewSet, OrderViewSet
from rest_framework.routers import DefaultRouter

router = DefaultRouter()
router.register(r'books', BookViewSet)
router.register(r'cart', CartViewSet)
router.register(r'orders', OrderViewSet, basename='order')

urlpatterns = [
    path('login/', CustomTokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('api/register/', RegisterView.as_view(), name='api_register'),
    path('cart/add_books/', CartViewSet.as_view({'post': 'add_books'}), name='add_books_to_cart'),
]

urlpatterns += router.urls
