from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.models import User
from django.contrib import messages
from django.contrib.auth import authenticate, login, logout, update_session_auth_hash
from django.contrib.auth.decorators import login_required
from django.db.models import F, Sum, Q
from .models import Producto, Proveedor, configuracionInv, DetalleVenta, Venta, ConfiguracionSistema
from decimal import Decimal
from django.contrib.messages import get_messages
from django.utils import timezone
from datetime import timedelta
import requests 
from django.core.files.base import ContentFile
import json
from django.http import JsonResponse



IVA = Decimal('0.19')


def login_view(request):
    if request.method == 'POST':
        correo = request.POST.get('email')
        clave = request.POST.get('password')

        user = authenticate(request, username=correo, password=clave)

        if user is not None:
            login(request, user)
            return redirect('dashboard')
        else:
            messages.error(request, "Correo o contraseña incorrectos.")

    return render(request, 'auth/login.html')


def registro_view(request):
    if request.method == 'POST':
        first_name = request.POST.get('first_name')
        last_name = request.POST.get('last_name')
        correo = request.POST.get('email')
        clave = request.POST.get('password')
        confirmacion = request.POST.get('confirm_password')

        if clave != confirmacion:
            messages.error(request, "Las contraseñas no coinciden.")
            return render(request, 'auth/registro.html')

        if User.objects.filter(username=correo).exists():
            messages.error(request, "Este correo ya está registrado.")
            return render(request, 'auth/registro.html')

        try:
            nuevo_usuario = User.objects.create_user(
                username=correo,
                email=correo,
                password=clave,
                first_name=first_name,
                last_name=last_name
            )
            nuevo_usuario.save()

            messages.success(request, "¡Registro exitoso! Ya puedes iniciar sesión.")
            return redirect('login')

        except Exception:
            messages.error(request, "Hubo un error al crear la cuenta. Intenta de nuevo.")

    return render(request, 'auth/registro.html')

@login_required
def dashboard_view(request):
    productos = Producto.objects.filter(usuario=request.user)

    config, _ = ConfiguracionSistema.objects.get_or_create(id=1)
    limite = config.limite_stock

    stock_critico = productos.filter(stock__lte=limite).count()

    hoy = timezone.localdate()
    periodo = request.GET.get('periodo', '7dias')
    ayer = hoy - timedelta(days=1)

    ventas_hoy = Venta.objects.filter(
        usuario=request.user,
        fecha__date=hoy
    ).aggregate(total=Sum('total'))['total'] or 0

    ventas_ayer = Venta.objects.filter(
        usuario=request.user,
        fecha__date=ayer
    ).aggregate(total=Sum('total'))['total'] or 0

    if ventas_ayer > 0:
        variacion = ((ventas_hoy - ventas_ayer) / ventas_ayer) * 100
    else:
        variacion = 100 if ventas_hoy > 0 else 0
        
    inicio_mes_actual = hoy.replace(day=1)

    fin_mes_pasado = inicio_mes_actual - timedelta(days=1)

    inicio_mes_pasado = fin_mes_pasado.replace(day=1)

    ventas_mes_actual = Venta.objects.filter(
        usuario=request.user,
        fecha__date__gte=inicio_mes_actual,
        fecha__date__lte=hoy
    ).aggregate(total=Sum('total'))['total'] or 0

    ventas_mes_pasado = Venta.objects.filter(
        usuario=request.user,
        fecha__date__gte=inicio_mes_pasado,
        fecha__date__lte=fin_mes_pasado
    ).aggregate(total=Sum('total'))['total'] or 0

    if ventas_mes_pasado > 0:
        variacion_mes = ((ventas_mes_actual - ventas_mes_pasado) / ventas_mes_pasado) * 100
    else:
        variacion_mes = 100 if ventas_mes_actual > 0 else 0
    

    ventas_grafico = []

    if periodo == 'mes':
        for i in range(29, -1, -1):
            dia = hoy - timedelta(days=i)

            total_dia = Venta.objects.filter(
                usuario=request.user,
                fecha__date=dia
            ).aggregate(total=Sum('total'))['total'] or 0

            ventas_grafico.append({
                'label': dia.strftime('%d/%m'),
                'total': int(total_dia)
            })

    elif periodo == '6meses':
        for i in range(5, -1, -1):
            mes = hoy.month - i
            anio = hoy.year

            while mes <= 0:
                mes += 12
                anio -= 1

            total_mes = Venta.objects.filter(
                usuario=request.user,
                fecha__year=anio,
                fecha__month=mes
            ).aggregate(total=Sum('total'))['total'] or 0

            ventas_grafico.append({
                'label': f'{mes:02d}/{anio}',
                'total': int(total_mes)
            })

    else:
        periodo = '7dias'

        for i in range(6, -1, -1):
            dia = hoy - timedelta(days=i)

            total_dia = Venta.objects.filter(
                usuario=request.user,
                fecha__date=dia
            ).aggregate(total=Sum('total'))['total'] or 0

            ventas_grafico.append({
                'label': dia.strftime('%d/%m'),
                'total': int(total_dia)
            })

    ventas_max = max([v['total'] for v in ventas_grafico]) or 1
    
    total_grafico = sum(v['total'] for v in ventas_grafico)

    dias_con_ventas = sum(1 for v in ventas_grafico if v['total'] > 0)

    promedio_grafico = int(total_grafico / len(ventas_grafico)) if ventas_grafico else 0

    mejor = max(ventas_grafico, key=lambda v: v['total']) if ventas_grafico else None
    mejor_dia = mejor['label'] if mejor and mejor['total'] > 0 else '-'

    inicio_mes = hoy.replace(day=1)

    top_productos = (
        DetalleVenta.objects
        .filter(
            venta__usuario=request.user,
            venta__fecha__date__gte=inicio_mes,
            venta__fecha__date__lte=hoy
        )
        .values('producto__nombre')
        .annotate(
            total_vendido=Sum('cantidad'),
            total_ventas=Sum(F('cantidad') * F('precio_unitario'))
        )
        .order_by('-total_vendido')[:5]
    )

    # =============================================================
    # NUEVA LÓGICA 1: CÁLCULO MARGEN DE GANANCIA (PONDERADO POR STOCK)
    # =============================================================
    costo_total_inventario = 0
    venta_total_inventario = 0

    for p in productos:
        # Solo calculamos si el producto tiene precio y además tiene stock
        if p.precio_venta > 0 and p.precio_costo > 0 and p.stock > 0:
            # Multiplicamos los precios por la cantidad de productos reales
            costo_total_inventario += (p.precio_costo * p.stock)
            venta_total_inventario += (p.precio_venta * p.stock)
    
    # Aplicamos la fórmula sobre el total del dinero en bodega
    if venta_total_inventario > 0:
        margen = ((venta_total_inventario - costo_total_inventario) / venta_total_inventario) * 100
        margen_promedio = round(margen, 1)
    else:
        margen_promedio = 0


    url_api = "https://69f3f2debd2396bf53107ea4.mockapi.io/api/v1/Productos"

    try:
        response = requests.get(url_api, timeout=5)
        api_conectada = response.status_code == 200
    except Exception as e:
        print("Error API:", e)
        api_conectada = False

    return render(request, 'dashboard.html', {
        'stock_critico': stock_critico,
        'ventas_dia': int(ventas_hoy),
        'variacion': round(variacion, 1),
        'variacion_mes': round(variacion_mes, 1),
        'ventas_max': ventas_max,
        'top_productos': top_productos,
        'margen_promedio': margen_promedio,
        'api_conectada': api_conectada,
        'ventas_grafico': ventas_grafico,
        'ventas_max': ventas_max,
        'periodo': periodo,
        'total_grafico': total_grafico,
        'promedio_grafico': promedio_grafico,
        'dias_con_ventas': dias_con_ventas,
        'mejor_dia': mejor_dia,
        'config': config,
    })

@login_required
def inventario_view(request):
    productos = Producto.objects.filter(usuario=request.user)
    proveedores = Proveedor.objects.all()

    buscar = request.GET.get('buscar', '').strip()
    categoria = request.GET.get('categoria', '').strip()

    if buscar:
        productos = productos.filter(
            Q(nombre__icontains=buscar) |
            Q(codigo__icontains=buscar) |
            Q(categoria__icontains=buscar) |
            Q(descripcion__icontains=buscar)
        )

    if categoria:
        productos = productos.filter(categoria=categoria)

    config, _ = ConfiguracionSistema.objects.get_or_create(id=1)
    limite_stock = config.limite_stock

    stock_bajo = productos.filter(stock__lte=limite_stock).count()

    valor_inventario = productos.aggregate(
        total=Sum(F('precio_venta') * F('stock'))
    )['total'] or 0

    return render(request, 'productos.html', {
        'productos': productos,
        'proveedores': proveedores,
        'stock_bajo': stock_bajo,
        'valor_inventario': valor_inventario,
        'limite_stock': limite_stock,
        'buscar': buscar,
        'categoria_seleccionada': categoria,
        'categorias_producto': Producto._meta.get_field('categoria').choices,
        'config': config,
    })


def logout_view(request):
    storage = get_messages(request)
    for _ in storage:
        pass  

    logout(request)
    return redirect('login')


@login_required
def crear_producto(request):
    config, _ = ConfiguracionSistema.objects.get_or_create(id=1)
    proveedores = Proveedor.objects.all()

    if request.method == 'POST':
        nombre = request.POST.get('nombre')
        descripcion = request.POST.get('descripcion')
        categoria = request.POST.get('categoria')

        tipo_venta = request.POST.get('tipo_venta')

        precio_venta = request.POST.get('precio_venta')
        precio_costo = request.POST.get('precio_costo')

        stock = request.POST.get('stock')

        imagen = request.FILES.get('imagen')


        Producto.objects.create(
            nombre=nombre,
            descripcion=descripcion,
            categoria=categoria,

            tipo_venta=tipo_venta,

            precio_venta=precio_venta,
            precio_costo=precio_costo,

            stock=stock,

            imagen=imagen,
            usuario=request.user
        )

        return redirect('inventario')

    return render(request, 'agregar_producto.html', {
        'proveedores': proveedores,
        'config': config,
    })


@login_required
def editar_producto(request, producto_id):
    producto = get_object_or_404(Producto, id=producto_id, usuario=request.user)

    if request.method == 'POST':
        producto.nombre = request.POST.get('nombre')
        producto.categoria = request.POST.get('categoria')
        producto.descripcion = request.POST.get('descripcion')
        producto.tipo_venta = request.POST.get('tipo_venta')
        producto.precio_venta = request.POST.get('precio_venta')
        producto.precio_costo = request.POST.get('precio_costo')
        producto.stock = request.POST.get('stock')
        
        if request.FILES.get('imagen'):
            producto.imagen = request.FILES.get('imagen')

        producto.save()
        return redirect('inventario')

    return redirect('inventario')


@login_required
def eliminar_producto(request, producto_id):
    producto = get_object_or_404(Producto, id=producto_id, usuario=request.user)

    if request.method == 'POST':
        producto.delete()

    return redirect('inventario')

@login_required
def guardar_config_stock(request):
    if request.method == 'POST':
        limite = request.POST.get('limite_stock')

        if limite and limite.isdigit():
            config, created = configuracionInv.objects.get_or_create(
                usuario=request.user
            )
            config.limite_stock = int(limite)
            config.save()

    return redirect('inventario')

@login_required
def ventas_view(request):
    config, _ = ConfiguracionSistema.objects.get_or_create(id=1)

    productos = Producto.objects.filter(usuario=request.user)

    buscar = request.GET.get('buscar', '').strip()

    if buscar:
        productos = productos.filter(
            Q(nombre__icontains=buscar) |
            Q(codigo__icontains=buscar) |
            Q(categoria__icontains=buscar) |
            Q(descripcion__icontains=buscar)
        )

    carrito = request.session.get('carrito', {})

    venta_actual = []
    subtotal = Decimal('0')

    for producto_id, item in carrito.items():
        producto = get_object_or_404(Producto, id=producto_id, usuario=request.user)

        if isinstance(item, dict) and item.get('tipo') == 'peso':
            item_subtotal = Decimal(item['precio_venta'])
            subtotal += item_subtotal

            venta_actual.append({
                'id': producto.id,
                'nombre': producto.nombre,
                'precio_venta': item_subtotal,
                'cantidad': None,
                'subtotal': int(item_subtotal),
                'tipo': 'peso',
                'imagen': producto.imagen
            })

        else:
            cantidad = int(item)
            item_subtotal = producto.precio_venta * cantidad
            subtotal += item_subtotal

            venta_actual.append({
                'id': producto.id,
                'nombre': producto.nombre,
                'precio_venta': producto.precio_venta,
                'cantidad': cantidad,
                'subtotal': int(item_subtotal),
                'tipo': 'unidad',
                'imagen': producto.imagen,
            })

    iva = int(subtotal * IVA)
    total = int(subtotal + iva)

    return render(request, 'ventas.html', {
        'productos': productos,
        'venta_actual': venta_actual,
        'subtotal': int(subtotal),
        'iva': iva,
        'total': total,
        'buscar': buscar,
        'config': config,
    })


@login_required
def agregar_al_carrito(request, producto_id):
    producto = get_object_or_404(Producto, id=producto_id, usuario=request.user)

    if producto.stock <= 0:
        messages.error(request, f"{producto.nombre} no tiene stock disponible.")
        return redirect('ventas')

    carrito = request.session.get('carrito', {})
    producto_id = str(producto.id)

    # Si el producto ya estaba guardado como venta por peso, lo reiniciamos como unidad
    cantidad_actual = carrito.get(producto_id, 0)

    if isinstance(cantidad_actual, dict):
        cantidad_actual = 0

    cantidad_actual = int(cantidad_actual)

    if Decimal(cantidad_actual + 1) <= producto.stock:
        carrito[producto_id] = cantidad_actual + 1
        messages.success(request, f"{producto.nombre} agregado a la venta.")
    else:
        messages.error(request, f"No puedes agregar más unidades de {producto.nombre} que su stock disponible.")

    request.session['carrito'] = carrito
    request.session.modified = True

    return redirect('ventas')


def quitar_del_carrito(request, producto_id):
    carrito = request.session.get('carrito', {})

    producto_id = str(producto_id)

    if producto_id in carrito:
        del carrito[producto_id]

    request.session['carrito'] = carrito
    request.session.modified = True

    return redirect('ventas')


@login_required
def finalizar_venta(request):
    if request.method != 'POST':
        return redirect('checkout_ventas')

    carrito = request.session.get('carrito', {})

    if not carrito:
        messages.error(request, "No hay productos en la venta actual.")
        return redirect('ventas')

    medio_pago = request.POST.get('medio_pago')

    if not medio_pago:
        messages.error(request, "Debes seleccionar un medio de pago.")
        return redirect('checkout_ventas')

    subtotal = Decimal('0')
    productos_vendidos = []

    for producto_id, item in carrito.items():
        producto = get_object_or_404(Producto, id=producto_id, usuario=request.user)

        # Producto por peso
        if isinstance(item, dict) and item.get('tipo') == 'peso':
            peso = Decimal(item['peso'])
            precio_kg = Decimal(item['precio_kg'])
            total_item = Decimal(item['precio_venta'])

            if peso > producto.stock:
                messages.error(request, f"No hay suficiente stock de {producto.nombre}.")
                return redirect('ventas')

            productos_vendidos.append({
                'producto': producto,
                'cantidad': peso,
                'precio_unitario': precio_kg,
                'tipo': 'peso',
                'peso': peso
            })

            subtotal += total_item

        # Producto normal
        else:
            cantidad = Decimal(item)

            if cantidad > producto.stock:
                messages.error(request, f"No hay suficiente stock de {producto.nombre}.")
                return redirect('ventas')

            total_item = producto.precio_venta * cantidad

            productos_vendidos.append({
                'producto': producto,
                'cantidad': cantidad,
                'precio_unitario': producto.precio_venta,
                'tipo': 'unidad'
            })

            subtotal += total_item

    iva = int(subtotal * IVA)
    total = int(subtotal + iva)

    venta = Venta.objects.create(
        usuario=request.user,
        subtotal=int(subtotal),
        iva=iva,
        total=total,
        medio_pago=medio_pago
    )

    for item in productos_vendidos:
        DetalleVenta.objects.create(
            venta=venta,
            producto=item['producto'],
            cantidad=item['cantidad'],
            precio_unitario=item['precio_unitario']
        )

        if item['tipo'] == 'peso':
            item['producto'].stock -= item['peso']
        else:
            item['producto'].stock -= item['cantidad']

        item['producto'].save()

    request.session['carrito'] = {}
    messages.success(request, "Venta realizada correctamente.")
    return redirect('detalle_venta', venta_id=venta.id)

@login_required
def checkout_ventas(request):
    config, _ = ConfiguracionSistema.objects.get_or_create(id=1)
    carrito = request.session.get('carrito', {})

    if not carrito:
        messages.error(request, "No hay productos en la venta actual.")
        return redirect('ventas')

    venta_actual = []
    subtotal = Decimal('0')

    for producto_id, item in carrito.items():
        producto = get_object_or_404(Producto, id=producto_id, usuario=request.user)

        if isinstance(item, dict) and item.get('tipo') == 'peso':
            item_subtotal = Decimal(item['precio_venta'])
            subtotal += item_subtotal

            venta_actual.append({
                'id': producto.id,
                'nombre': producto.nombre,
                'precio_venta': item_subtotal,
                'cantidad': None,
                'subtotal': int(item_subtotal),
                'tipo': 'peso',
            })

        else:
            cantidad = int(item)
            item_subtotal = producto.precio_venta * cantidad
            subtotal += item_subtotal

            venta_actual.append({
                'id': producto.id,
                'nombre': producto.nombre,
                'precio_venta': producto.precio_venta,
                'cantidad': cantidad,
                'subtotal': int(item_subtotal),
                'tipo': 'unidad',
            })

    iva = int(subtotal * IVA)
    total = int(subtotal + iva)

    return render(request, 'checkout_ventas.html', {
        'venta_actual': venta_actual,
        'subtotal': int(subtotal),
        'iva': iva,
        'total': total,
        'config': config,
    })
    
@login_required
def detalle_venta(request, venta_id):
    config, _ = ConfiguracionSistema.objects.get_or_create(id=1)
    venta = get_object_or_404(Venta, id=venta_id)

    return render(request, 'detalle_venta.html', {
        'venta': venta,
        'config': config,
    })
    
@login_required
def editar_perfil(request):
    usuario = request.user

    if request.method == 'POST':
        nombre = request.POST.get('first_name')
        apellido = request.POST.get('last_name')
        email = request.POST.get('email')

        password_actual = request.POST.get('password_actual')
        nueva_password = request.POST.get('nueva_password')
        confirmar_password = request.POST.get('confirmar_password')

        usuario.first_name = nombre
        usuario.last_name = apellido
        usuario.email = email

        if password_actual or nueva_password or confirmar_password:
            if not usuario.check_password(password_actual):
                messages.error(request, "La contraseña actual es incorrecta.")
                return redirect('editar_perfil')

            if nueva_password != confirmar_password:
                messages.error(request, "Las nuevas contraseñas no coinciden.")
                return redirect('editar_perfil')

            if len(nueva_password) < 8:
                messages.error(request, "La nueva contraseña debe tener al menos 8 caracteres.")
                return redirect('editar_perfil')

            usuario.set_password(nueva_password)
            usuario.save()

            update_session_auth_hash(request, usuario)

            messages.success(request, "Perfil y contraseña actualizados correctamente.")
            return redirect('dashboard')

        usuario.save()
        messages.success(request, "Perfil actualizado correctamente.")
        return redirect('dashboard')

    return render(request, 'editar_perfil.html', {
        'usuario': usuario
    })
    
@login_required
def admin_panel(request):
    if not request.user.is_staff:
        return redirect('dashboard')

    config, created = ConfiguracionSistema.objects.get_or_create(id=1)
    usuarios = User.objects.filter(is_superuser=False).order_by('id')

    if request.method == 'POST':
        if 'guardar_config' in request.POST:
            config.nombre_empresa = request.POST.get('nombre_empresa')
            config.rut_empresa = request.POST.get('rut_empresa')
            config.giro_empresa = request.POST.get('giro_empresa')
            config.direccion_empresa = request.POST.get('direccion_empresa')
            config.comuna_empresa = request.POST.get('comuna_empresa')
            config.ciudad_empresa = request.POST.get('ciudad_empresa')
            config.limite_stock = request.POST.get('limite_stock')
            tema_visual = request.POST.get('tema_visual', 'claro')

            temas_validos = [
                'claro',
                'arena',
                'azul_corporativo',
                'verde_bosque',
                'oscuro',
            ]

            if tema_visual not in temas_validos:
                tema_visual = 'claro'

            config.tema_visual = tema_visual

            colores_principales = {
                'claro': '#2563eb',
                'arena': '#b45309',
                'azul_corporativo': '#38bdf8',
                'verde_bosque': '#22c55e',
                'oscuro': '#6366f1',
            }

            config.tema_visual = tema_visual
            config.color_principal = colores_principales[tema_visual]

            config.save()

            messages.success(request, "Configuración actualizada.")
            return redirect('admin_panel')

        if 'editar_usuario' in request.POST:
            user_id = request.POST.get('user_id')
            usuario = User.objects.get(id=user_id)

            usuario.first_name = request.POST.get('first_name')
            usuario.last_name = request.POST.get('last_name')
            usuario.email = request.POST.get('email')

            usuario.is_staff = True if request.POST.get('is_staff') == 'on' else False
            usuario.is_active = True if request.POST.get('is_active') == 'on' else False

            usuario.save()

            messages.success(request, "Usuario actualizado.")
            return redirect('admin_panel')

    return render(request, 'admin_panel.html', {
        'config': config,
        'usuarios': usuarios
    })
    
@login_required
def gestion_usuarios(request):
    usuarios = User.objects.all().order_by('id')

    return render(request, 'gestion_usuarios.html', {
        'usuarios': usuarios
    })
    
@login_required
def editar_usuario_admin(request, user_id):
    usuario = get_object_or_404(User, id=user_id)

    if request.method == 'POST':
        usuario.first_name = request.POST.get('first_name')
        usuario.last_name = request.POST.get('last_name')
        usuario.email = request.POST.get('email')

        usuario.is_staff = True if request.POST.get('is_staff') == 'on' else False
        usuario.is_active = True if request.POST.get('is_active') == 'on' else False

        usuario.save()
        messages.success(request, "Usuario actualizado correctamente.")
        return redirect('gestion_usuarios')

    return render(request, 'editar_usuario_admin.html', {
        'usuario_edit': usuario
    })
    
@login_required
def actualizar_cantidad_carrito(request, producto_id, accion):
    carrito = request.session.get('carrito', {})
    producto = get_object_or_404(Producto, id=producto_id, usuario=request.user)
    producto_id = str(producto_id)

    if producto_id in carrito:
        if accion == 'sumar':
            if carrito[producto_id] < producto.stock:
                carrito[producto_id] += 1
            else:
                messages.error(request, "No hay más stock disponible.")

        elif accion == 'restar':
            carrito[producto_id] -= 1

            if carrito[producto_id] <= 0:
                del carrito[producto_id]

    request.session['carrito'] = carrito
    return redirect('ventas')

@login_required
def agregar_producto_peso(request, producto_id):
    if request.method != 'POST':
        return redirect('ventas')

    producto = get_object_or_404(Producto, id=producto_id, usuario=request.user)

    precio_kg = Decimal(request.POST.get('precio_kg'))
    peso = Decimal(request.POST.get('peso'))

    total = int(precio_kg * peso)

    carrito = request.session.get('carrito', {})
    producto_id = str(producto.id)

    carrito[producto_id] = {
    'tipo': 'peso',
    'nombre': producto.nombre,
    'peso': str(peso),
    'precio_kg': str(precio_kg),
    'precio_venta': str(total)
}

    request.session['carrito'] = carrito
    return redirect('ventas')

@login_required
def cambiar_cantidad_carrito(request, producto_id):
    if request.method != 'POST':
        return redirect('ventas')

    carrito = request.session.get('carrito', {})
    producto = get_object_or_404(Producto, id=producto_id, usuario=request.user)
    producto_id = str(producto_id)

    nueva_cantidad = request.POST.get('cantidad')

    if not nueva_cantidad or not nueva_cantidad.isdigit():
        messages.error(request, "Cantidad inválida.")
        return redirect('ventas')

    nueva_cantidad = int(nueva_cantidad)

    if nueva_cantidad <= 0:
        if producto_id in carrito:
            del carrito[producto_id]
    elif nueva_cantidad <= producto.stock:
        carrito[producto_id] = nueva_cantidad
    else:
        messages.error(request, f"No hay suficiente stock de {producto.nombre}.")

    request.session['carrito'] = carrito
    return redirect('ventas')




@login_required
def proveedores(request):
    # Definimos las URLs independientes de cada una de las APIs de MockAPI
    api_urls = {
        "Bodega Logística Renca B2B": "https://69f3f2debd2396bf53107ea4.mockapi.io/api/v1/Productos",
        "Comercial Pacífico Sur": "https://6a1a3431bc2f94475491c847.mockapi.io/Productos",
        "Mayorista El Sol": "https://6a1a336abc2f94475491c65c.mockapi.io/Productos",
    }

    datos_api = []
    api_conectada = False  # Cambiará a True si al menos una API responde bien
    
    # Mantenemos tu configuración global del sistema
    config, _ = ConfiguracionSistema.objects.get_or_create(id=1)

    # Consumimos cada API e inyectamos el nombre de la empresa correspondiente
    for nombre_empresa, url_api in api_urls.items():
        try:
            response = requests.get(url_api, timeout=5)

            if response.status_code == 200:
                api_conectada = True
                productos_proveedor = response.json()
                
                # Pegamos la etiqueta del proveedor antes de juntar los productos
                for producto in productos_proveedor:
                    producto["proveedor_nombre"] = nombre_empresa
                
                # Agregamos los productos al listado general
                datos_api += productos_proveedor

        except Exception as e:
            print(f"Error al conectar con la API de {nombre_empresa}:", e)

    return render(request, 'proveedores.html', {
        'proveedores': datos_api,
        'api_conectada': api_conectada,
        'config': config,
    })



@login_required
def recepcion_inventario_view(request):
    if request.method == 'POST':
        try:
            # Leemos el JSON enviado por Fetch desde el carrito en el Frontend
            data = json.loads(request.body)
            productos_comprados = data.get('productos', [])

            for item in productos_comprados:
                # 1. Buscamos o creamos el registro del Proveedor en la base de datos local
                proveedor_obj, _ = Proveedor.objects.get_or_create(nombre=item['proveedor'])

                # 2. Creamos la instancia del producto con el Precio de Venta fijado por el usuario
                nuevo_producto = Producto(
                    nombre=item['nombre'],
                    precio_costo=item['precio_costo'],
                    precio_venta=item['precio_venta'],
                    stock=item['cantidad'],
                    descripcion=f"Compra ingresada desde catálogo. Proveedor: {item['proveedor']}",
                    categoria="otros",  # Puedes cambiarlo por item.get('categoria') si lo añades al carrito
                    usuario=request.user,
                    proveedor=proveedor_obj
                )

                # 3. Descarga asíncrona de la imagen de internet para guardarla localmente
                imagen_url = item.get('imagen')
                if imagen_url and not imagen_url.startswith('http://localhost'):
                    try:
                        respuesta_img = requests.get(imagen_url, timeout=5)
                        if respuesta_img.status_code == 200:
                            # Normalizamos el nombre del archivo JPG
                            nombre_archivo = f"{item['nombre'].replace(' ', '_').lower()}.jpg"
                            # Guardamos el archivo físico en el ImageField sin guardar la fila todavía
                            nuevo_producto.imagen.save(nombre_archivo, ContentFile(respuesta_img.content), save=False)
                    except Exception as e:
                        print(f"Error al descargar imagen para {item['nombre']}: {e}")

                # 4. Guardamos permanentemente el producto en la base de datos local
                nuevo_producto.save()
                print(f"--- PRODUCTO {item['nombre']} GUARDADO EXITOSAMENTE ---")
            
            return JsonResponse({'status': 'success', 'message': 'Productos agregados al inventario correctamente con sus imágenes.'})
        
        except Exception as e:
            return JsonResponse({'status': 'error', 'message': str(e)})

    # Si entran por GET (navegación normal), renderizamos la plantilla de fijación de precios
    return render(request, 'recepcion_inventario.html')

@login_required
def informes_view(request):
    config, _ = ConfiguracionSistema.objects.get_or_create(id=1)

    hoy = timezone.localdate()
    inicio_mes = hoy.replace(day=1)

    mostrar_preview = request.GET.get('preview') == '1'

    tipo_informe = request.GET.get('tipo_informe', 'diario')
    buscar = request.GET.get('buscar', '').strip()
    medio_pago = request.GET.get('medio_pago', '').strip()

    fecha_dia = request.GET.get('fecha_dia', hoy.isoformat())
    fecha_inicio = request.GET.get('fecha_inicio', inicio_mes.isoformat())
    fecha_fin = request.GET.get('fecha_fin', hoy.isoformat())

    if tipo_informe == 'diario':
        fecha_inicio = fecha_dia
        fecha_fin = fecha_dia
        titulo_informe = 'Informe diario'

    elif tipo_informe == 'productos':
        titulo_informe = 'Informe por productos'

    else:
        tipo_informe = 'rango'
        titulo_informe = 'Informe por rango'

    ventas = Venta.objects.filter(
        usuario=request.user,
        fecha__date__gte=fecha_inicio,
        fecha__date__lte=fecha_fin
    ).prefetch_related('detalles__producto').order_by('-fecha')

    if buscar:
        filtro_busqueda = Q(detalles__producto__nombre__icontains=buscar)

        if buscar.isdigit():
            filtro_busqueda = filtro_busqueda | Q(id=int(buscar))

        ventas = ventas.filter(filtro_busqueda).distinct()

    if medio_pago:
        ventas = ventas.filter(medio_pago=medio_pago)

    cantidad_ventas = ventas.count()
    total_mes = ventas.aggregate(total=Sum('total'))['total'] or 0
    subtotal_mes = ventas.aggregate(total=Sum('subtotal'))['total'] or 0
    iva_mes = ventas.aggregate(total=Sum('iva'))['total'] or 0

    ventas_efectivo = ventas.filter(medio_pago='efectivo')
    cantidad_efectivo = ventas_efectivo.count()
    total_efectivo = ventas_efectivo.aggregate(total=Sum('total'))['total'] or 0

    ventas_debito = ventas.filter(medio_pago='debito')
    cantidad_debito = ventas_debito.count()
    total_debito = ventas_debito.aggregate(total=Sum('total'))['total'] or 0

    ventas_credito = ventas.filter(medio_pago='credito')
    cantidad_credito = ventas_credito.count()
    total_credito = ventas_credito.aggregate(total=Sum('total'))['total'] or 0

    ventas_transferencia = ventas.filter(medio_pago='transferencia')
    cantidad_transferencia = ventas_transferencia.count()
    total_transferencia = ventas_transferencia.aggregate(total=Sum('total'))['total'] or 0

    productos_informe = (
        DetalleVenta.objects
        .filter(venta__in=ventas)
        .values('producto__nombre')
        .annotate(
            total_cantidad=Sum('cantidad'),
            total_vendido=Sum(F('cantidad') * F('precio_unitario'))
        )
        .order_by('-total_vendido')
    )

    return render(request, 'informes.html', {
        'ventas': ventas,

        'buscar': buscar,
        'medio_pago': medio_pago,

        'fecha_dia': fecha_dia,
        'fecha_inicio': fecha_inicio,
        'fecha_fin': fecha_fin,

        'tipo_informe': tipo_informe,
        'titulo_informe': titulo_informe,
        'mostrar_preview': mostrar_preview,

        'productos_informe': productos_informe,

        'config': config,
        'hoy': hoy,

        'cantidad_ventas': cantidad_ventas,
        'total_mes': total_mes,
        'subtotal_mes': subtotal_mes,
        'iva_mes': iva_mes,

        'cantidad_efectivo': cantidad_efectivo,
        'total_efectivo': total_efectivo,

        'cantidad_debito': cantidad_debito,
        'total_debito': total_debito,

        'cantidad_credito': cantidad_credito,
        'total_credito': total_credito,

        'cantidad_transferencia': cantidad_transferencia,
        'total_transferencia': total_transferencia,
    })