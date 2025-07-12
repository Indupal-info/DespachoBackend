from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import cambiar_estado_maquina, listar_mecanicos_sucursal, registrar_llamada
from . import views
from .views import (
    BranchViewSet, ClientViewSet, MachineEntryViewSet,
    RepairHistoryViewSet, CallLogViewSet, SystemUserViewSet,
    crear_usuario_con_rol
)
from .views import generar_comprobante_pdf
router = DefaultRouter()
router.register(r'branches', BranchViewSet)
router.register(r'clients', ClientViewSet)
router.register(r'machine-entries', MachineEntryViewSet)
router.register(r'repair-history', RepairHistoryViewSet)
router.register(r'call-logs', CallLogViewSet)
router.register(r'system-users', SystemUserViewSet)
from .views import enviar_pdf_view
from .views import generar_y_enviar_comprobante

urlpatterns = [
    path('', include(router.urls)),
    path('usuarios/crear/', crear_usuario_con_rol, name='crear_usuario_con_rol'),
    path('maquinas/buscar/', views.buscar_maquina, name='buscar_maquina'),
    path('maquinas/registrar/', views.registrar_maquina, name='registrar_maquina'),
    path('maquinas/activas/', views.listar_maquinas_activas, name='listar_maquinas_activas'),
    path('maquinas/<uuid:machine_id>/editar/', views.editar_maquina, name='editar_maquina'),
    path('maquinas/<uuid:machine_id>/detalle-completo/', views.detalle_maquina_completo, name='detalle_maquina_completo'),
    path('current_user/', views.current_user_view, name='current_user'),
    path('api/maquinas/cambiar_estado/', cambiar_estado_maquina),
    path('api/maquinas/registrar_llamada/', registrar_llamada),
    path("api/mecanicos/", listar_mecanicos_sucursal),
    path('comprobante/<str:comprobante_id>/pdf/', generar_comprobante_pdf, name='generar_comprobante_pdf'),
    path("enviar-pdf/", enviar_pdf_view),
    path("generar-enviar-comprobante/", generar_y_enviar_comprobante),
    path('maquinas/comprobante/<str:comprobante_id>/', generar_comprobante_pdf, name='generar_comprobante_pdf'),


]
