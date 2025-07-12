from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

from despacho.views import (
    CustomLoginView, cambiar_estado_maquina, custom_logout_view,
    current_user_view, listar_mecanicos_sucursal, test_token_cookie
)
from rest_framework_simplejwt.views import TokenRefreshView

urlpatterns = [
    path('admin/', admin.site.urls),

    # 🔐 Autenticación
    path('api/token/', CustomLoginView.as_view(), name='token_obtain_pair'),
    path('api/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('api/logout/', custom_logout_view, name='logout'),
    path('api/current_user/', current_user_view, name='current_user'),
    path('api/test-token/', test_token_cookie),

    # 🛠 Funciones personalizadas
    path('api/maquinas/cambiar_estado/', cambiar_estado_maquina),
    path('api/mecanicos/', listar_mecanicos_sucursal),

    # 📦 Rutas de la app despacho
    path('api/', include('despacho.urls')),
]

# ✅ Archivos estáticos (media) en desarrollo
urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

print(">>> cargando backendapi.urls correctamente")
