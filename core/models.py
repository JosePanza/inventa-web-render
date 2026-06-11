from django.db import models
from django.contrib.auth.models import User



MEDIOS_PAGO = [
    ('efectivo', 'Efectivo'),
    ('debito', 'Tarjeta Débito'),
    ('credito', 'Tarjeta Crédito'),
    ('transferencia', 'Transferencia'),
]

CATEGORIAS_PRODUCTO = [
    ('fruta', 'Fruta'),
    ('verdura', 'Verdura'),
    ('abarrote', 'Abarrote'),
    ('bebida', 'Bebida'),
    ('limpieza', 'Limpieza'),
    ('lacteo', 'Lácteo'),
    ('mascotas', 'Mascotas'),
    ('panaderia', 'Panadería'),
    ('otros', 'Otros'),
]
TIPO_VENTA = [
    ('unidad', 'Por unidad'),
    ('peso', 'Por peso'),
]


class Producto(models.Model):
    codigo = models.CharField(max_length=20, unique=True, editable=False)

    nombre = models.CharField(max_length=100)
    descripcion = models.TextField()
    categoria = models.CharField(max_length=50,choices=CATEGORIAS_PRODUCTO,default='otros')
    imagen = models.ImageField(upload_to='productos/', null=True, blank=True)

    precio_costo = models.IntegerField(default=0) # Lo que nos cobra el proveedor
    precio_venta = models.IntegerField(default=0) # A lo que lo vendemos al cliente

    #precio = models.IntegerField()

    stock = models.DecimalField(max_digits=10,decimal_places=3,default=0)
    fecha = models.DateTimeField(auto_now_add=True)

    usuario = models.ForeignKey(User, on_delete=models.CASCADE)
    proveedor = models.ForeignKey('Proveedor', on_delete=models.SET_NULL, null=True, blank=True)
    tipo_venta = models.CharField(max_length=10,choices=TIPO_VENTA,default='unidad')

    def save(self, *args, **kwargs):
        if not self.codigo:
            ultimo = Producto.objects.order_by('-id').first()

            if ultimo:
                numero = int(ultimo.codigo.split('-')[1]) + 1
            else:
                numero = 1

            self.codigo = f"APT-{numero:03d}"

        super().save(*args, **kwargs)

    def __str__(self):
        return self.nombre


class Proveedor(models.Model):
    nombre = models.CharField(max_length=100)
    correo = models.EmailField()
    telefono = models.CharField(max_length=20)

    def __str__(self):
        return str(self.nombre)


class PedidoProveedor(models.Model):
    proveedor = models.ForeignKey(
        Proveedor,
        on_delete=models.CASCADE,
        related_name='pedidos'
    )
    usuario = models.ForeignKey(User, on_delete=models.CASCADE)
    fecha = models.DateTimeField(auto_now_add=True)
    total = models.IntegerField()

    def __str__(self):
        return f"Pedido #{self.id} - {self.proveedor.nombre}"


class DetallePedidoProveedor(models.Model):
    pedido = models.ForeignKey(
        PedidoProveedor,
        on_delete=models.CASCADE,
        related_name='detalles'
    )
    producto = models.ForeignKey(Producto, on_delete=models.CASCADE)
    cantidad = models.IntegerField()
    precio_unitario = models.IntegerField()
    subtotal = models.IntegerField()

    def __str__(self):
        return f"{self.producto.nombre} x {self.cantidad}"


class Movimiento(models.Model):
    TIPOS = [
        ('entrada', 'Entrada'),
        ('salida', 'Salida'),
    ]

    producto = models.ForeignKey(
        Producto,
        on_delete=models.CASCADE,
        related_name='movimientos'
    )
    tipo = models.CharField(max_length=10, choices=TIPOS)
    cantidad = models.IntegerField()
    fecha = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.tipo} - {self.producto.nombre} ({self.cantidad})"


class Venta(models.Model):
    usuario = models.ForeignKey(User, on_delete=models.CASCADE)
    fecha = models.DateTimeField(auto_now_add=True)
    subtotal = models.IntegerField()
    iva = models.IntegerField()
    total = models.IntegerField()
    medio_pago = models.CharField(max_length=20, choices=MEDIOS_PAGO, blank=True, null=True)

    def __str__(self):
        return f"Venta #{self.id} - {self.fecha.strftime('%d/%m/%Y %H:%M')}"

class DetalleVenta(models.Model):
    venta = models.ForeignKey(Venta, on_delete=models.CASCADE, related_name='detalles')
    producto = models.ForeignKey('Producto', on_delete=models.CASCADE)
    cantidad = models.DecimalField(max_digits=10,decimal_places=3,default=1)
    precio_unitario = models.IntegerField()

    def subtotal(self):
        return self.cantidad * self.precio_unitario

    def __str__(self):
        return f"{self.producto.nombre} x {self.cantidad}"
    
class configuracionInv(models.Model):
    usuario = models.OneToOneField(User, on_delete=models.CASCADE)
    limite_stock = models.PositiveIntegerField(default=5)
    
    def __str__(self):
        return f"configuracion de {self.usuario.username}"
    
class ConfiguracionSistema(models.Model):
    TEMAS_VISUALES = [
    ('claro', 'Claro'),
    ('arena', 'Arena'),
    ('azul_corporativo', 'Azul corporativo'),
    ('verde_bosque', 'Verde bosque'),
    ('oscuro', 'Oscuro'),
]

    nombre_empresa = models.CharField(max_length=100, default="Empresa")
    rut_empresa = models.CharField(max_length=20, blank=True, null=True)
    giro_empresa = models.CharField(max_length=150, blank=True, null=True)
    direccion_empresa = models.CharField(max_length=200, blank=True, null=True)
    comuna_empresa = models.CharField(max_length=100, blank=True, null=True)
    ciudad_empresa = models.CharField(max_length=100, blank=True, null=True)

    limite_stock = models.IntegerField(default=5)

    color_principal = models.CharField(max_length=20, default="#2563eb")

    tema_visual = models.CharField(
        max_length=30,
        choices=TEMAS_VISUALES,
        default='claro'
    )

    def __str__(self):
        return self.nombre_empresa