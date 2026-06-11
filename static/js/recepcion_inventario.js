let carritoRecepcion = JSON.parse(sessionStorage.getItem('carrito_proveedores')) || [];

document.addEventListener("DOMContentLoaded", () => {
    if (carritoRecepcion.length === 0) {
        alert("No hay productos pendientes de recepción. Redirigiendo...");
        window.location.href = "/proveedores/";
        return;
    }

    renderizarTabla();
});

function renderizarTabla() {
    const tbody = document.getElementById('tabla-recepcion');

    if (!tbody) {
        return;
    }

    let html = "";

    carritoRecepcion.forEach((item, index) => {
        html += `
            <tr class="hover:bg-gray-50 transition-colors">
                <td class="p-4 font-bold text-slate-800">${item.nombre}</td>
                <td class="p-4 text-sm text-gray-600">🏢 ${item.proveedor}</td>
                <td class="p-4 text-sm font-bold text-slate-700">${item.cantidad} un.</td>
                <td class="p-4 text-sm font-bold text-gray-500">$${item.precio.toLocaleString('es-CL')}</td>
                <td class="p-4">
                    <div class="relative w-32">
                        <span class="absolute left-3 top-2.5 text-gray-400 font-bold">$</span>
                        <input 
                            type="number" 
                            id="venta-${index}" 
                            min="${item.precio}" 
                            placeholder="Ej: ${item.precio + 500}" 
                            class="w-full bg-blue-50 border border-blue-200 text-blue-900 font-bold rounded-lg pl-8 pr-3 py-2 outline-none focus:ring-2 focus:ring-blue-500">
                    </div>
                </td>
            </tr>
        `;
    });

    tbody.innerHTML = html;
}

function guardarInventarioFinal() {
    let productosFinales = [];
    let hayError = false;

    carritoRecepcion.forEach((item, index) => {
        const inputVenta = document.getElementById(`venta-${index}`);

        if (!inputVenta || !inputVenta.value || parseInt(inputVenta.value) <= 0) {
            hayError = true;
            return;
        }

        productosFinales.push({
            nombre: item.nombre,
            proveedor: item.proveedor,
            cantidad: item.cantidad,
            precio_costo: item.precio,
            precio_venta: parseInt(inputVenta.value),
            sku: item.sku,
            imagen: item.imagen
        });
    });

    if (hayError) {
        alert("Por favor, asigna un Precio de Venta válido a todos los productos antes de continuar.");
        return;
    }

    const csrfInput = document.getElementById('csrf-token');
    const csrfToken = csrfInput ? csrfInput.value : '';

    fetch('/recepcion-inventario/', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': csrfToken
        },
        body: JSON.stringify({
            productos: productosFinales
        })
    })
    .then(response => response.json())
    .then(data => {
        if (data.status === 'success') {
            alert("✅ " + data.message);
            sessionStorage.removeItem('carrito_proveedores');
            window.location.href = "/inventario/";
        } else {
            alert("❌ Ocurrió un error: " + data.message);
        }
    })
    .catch(error => {
        console.error('Error:', error);
        alert("Error al conectar con el servidor.");
    });
}