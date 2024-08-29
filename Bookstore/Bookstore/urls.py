from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.conf.urls.i18n import i18n_patterns

urlpatterns = [
    path('admin/', admin.site.urls),
    path('i18n/', include('django.conf.urls.i18n')),  # For language switching
    path('api/', include('books.drf.urls')),  # Include DRF API URLs from the books app
]

# Include authentication URLs within i18n_patterns
urlpatterns += i18n_patterns(
    path('', include('books.urls')),  # Include your book app URLs
    path('accounts/', include('django.contrib.auth.urls')),  # Default auth URLs
)

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
