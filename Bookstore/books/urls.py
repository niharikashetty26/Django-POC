from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import CustomTokenObtainPairView, RegisterView, BookViewSet, CartViewSet

router = DefaultRouter()
router.register(r'books', BookViewSet)
router.register(r'cart', CartViewSet, basename='cart')

urlpatterns = [
    path('login/', CustomTokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('register/', RegisterView.as_view(), name='register'),
]

# Include the router URLs
urlpatterns += router.urls
