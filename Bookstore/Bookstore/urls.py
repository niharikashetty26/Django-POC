from django.contrib import admin
from django.urls import path, include, re_path
from rest_framework import permissions
from drf_yasg.views import get_schema_view
from drf_yasg import openapi

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

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/', include('books.urls')),
    re_path(r'^swagger(?P<format>\.json|\.yaml)$', schema_view.without_ui(cache_timeout=0), name='schema-json'),
    path('swagger/', schema_view.with_ui('swagger', cache_timeout=0), name='schema-swagger-ui'),
    path('redoc/', schema_view.with_ui('redoc', cache_timeout=0), name='schema-redoc'),
]
<<<<<<< HEAD

# Include authentication URLs within i18n_patterns
urlpatterns += i18n_patterns(
    path('', include('books.urls')),
    path('accounts/', include('django.contrib.auth.urls')),
)

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
=======
>>>>>>> d58946e5a629e15bc3d65d1ccb4f9ba76722a2b1
