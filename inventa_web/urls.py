from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('admin/', admin.site.urls),
    # Aquí le decimos al proyecto que busque las URLs de tu app core
    path('', include('core.urls')), 
]

# AQUÍ SÍ FUNCIONA: En la puerta principal del proyecto
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)