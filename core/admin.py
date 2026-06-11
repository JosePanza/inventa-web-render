from django.contrib import admin
from .models import Producto, Proveedor, PedidoProveedor, DetallePedidoProveedor, Movimiento, Venta, DetalleVenta

admin.site.register(Producto)
admin.site.register(Proveedor)
admin.site.register(PedidoProveedor)
admin.site.register(DetallePedidoProveedor)
admin.site.register(Movimiento)
admin.site.register(Venta)
admin.site.register(DetalleVenta)