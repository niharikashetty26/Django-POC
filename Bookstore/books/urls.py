from django.urls import path, include, re_path
from rest_framework.routers import DefaultRouter
from drf_yasg.views import get_schema_view
from drf_yasg import openapi
from rest_framework import permissions
from .views import CustomTokenObtainPairView, RegisterView, BookViewSet, CartViewSet, OrderViewSet

# Initialize the router
router = DefaultRouter()
router.register(r'books', BookViewSet)
router.register(r'cart', CartViewSet)
router.register(r'orders', OrderViewSet, basename='order')

# Swagger schema view
schema_view = get_schema_view(
    openapi.Info(
        title="Bookstore API",
        default_version='v1',
        description="API documentation for the Bookstore application",
        terms_of_service="https://www.google.com/policies/terms/",
        contact=openapi.Contact(email="contact@bookstore.local"),
        license=openapi.License(name="BSD License"),
    ),
    public=True,
    permission_classes=(permissions.AllowAny,),
)

# URL patterns
urlpatterns = [
    path('login/', CustomTokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('register/', RegisterView.as_view(), name='register'),
    path('cart/add_books/', CartViewSet.as_view({'post': 'add_books'}), name='add_books_to_cart'),

    # Swagger URLs
    re_path(r'^swagger(?P<format>\.json|\.yaml)$', schema_view.without_ui(cache_timeout=0), name='schema-json'),
    path('swagger/', schema_view.with_ui('swagger', cache_timeout=0), name='schema-swagger-ui'),
    path('redoc/', schema_view.with_ui('redoc', cache_timeout=0), name='schema-redoc'),
]

# Include the router URLs
urlpatterns += router.urls
