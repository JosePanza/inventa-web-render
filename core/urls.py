from django.urls import path
from django.views.generic import RedirectView
from . import views
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('', RedirectView.as_view(url='/login/', permanent=False)),
    path('login/', views.login_view, name='login'),
    path('registro/', views.registro_view, name='registro'),
    path('logout/', views.logout_view, name='logout'),
    path('dashboard/', views.dashboard_view, name='dashboard'),
    path('inventario/', views.inventario_view, name='inventario'),
    path('inventario/agregar_producto/', views.crear_producto, name='agregar_producto'),
    path('inventario/editar/<int:producto_id>/', views.editar_producto, name='editar_producto'),
    path('inventario/eliminar/<int:producto_id>/', views.eliminar_producto, name='eliminar_producto'),
    path('inventario/config-stock/', views.guardar_config_stock, name='guardar_config_stock'),
    path('ventas/', views.ventas_view, name='ventas'),
    path('ventas/agregar/<int:producto_id>/', views.agregar_al_carrito, name='agregar_al_carrito'),
    path('ventas/quitar/<int:producto_id>/', views.quitar_del_carrito, name='quitar_del_carrito'),
    path('ventas/finalizar/', views.finalizar_venta, name='finalizar_venta'),
    path('ventas/checkout/', views.checkout_ventas, name='checkout_ventas'),
    path('ventas/finalizar/', views.finalizar_venta, name='finalizar_venta'),
    path('ventas/detalle/<int:venta_id>/', views.detalle_venta, name='detalle_venta'),
    path('logout/', views.logout_view, name='logout'),
    path('perfil/', views.editar_perfil, name='editar_perfil'),
    path('panel-admin/', views.admin_panel, name='admin_panel'),
    path('panel-admin/usuarios/', views.gestion_usuarios, name='gestion_usuarios'),
    path('panel-admin/usuarios/editar/<int:user_id>/', views.editar_usuario_admin, name='editar_usuario_admin'),
    path('ventas/carrito/<int:producto_id>/<str:accion>/',views.actualizar_cantidad_carrito,name='actualizar_cantidad_carrito'),
    path('ventas/agregar-peso/<int:producto_id>/', views.agregar_producto_peso, name='agregar_producto_peso'),
    path('ventas/carrito/cambiar/<int:producto_id>/',views.cambiar_cantidad_carrito,name='cambiar_cantidad_carrito'),
    path('proveedores/', views.proveedores, name='proveedores'),
    path('informes/', views.informes_view, name='informes'),
    path('recepcion-inventario/', views.recepcion_inventario_view, name='recepcion_inventario'),
]
