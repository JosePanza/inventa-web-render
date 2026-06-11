function abrirModalPeso(productoId, nombreProducto, precioVenta) {
    const nombre = document.getElementById('nombreProductoPeso');
    const form = document.getElementById('formPeso');
    const precioKg = document.getElementById('precioKg');
    const modal = document.getElementById('modalPeso');

    if (!nombre || !form || !precioKg || !modal) {
        return;
    }

    nombre.textContent = nombreProducto;
    form.action = `/ventas/agregar-peso/${productoId}/`;
    precioKg.value = precioVenta;
    modal.classList.remove('hidden');

    calcularTotalPeso();
}

function cerrarModalPeso() {
    const modal = document.getElementById('modalPeso');

    if (modal) {
        modal.classList.add('hidden');
    }
}

function calcularTotalPeso() {
    const precioInput = document.getElementById('precioKg');
    const pesoInput = document.getElementById('pesoKg');
    const totalSpan = document.getElementById('totalPeso');

    if (!precioInput || !pesoInput || !totalSpan) {
        return;
    }

    const precio = parseFloat(precioInput.value) || 0;
    const peso = parseFloat(pesoInput.value) || 0;
    const total = Math.round(precio * peso);

    totalSpan.textContent = total;
}

document.addEventListener('DOMContentLoaded', function () {
    const precioKg = document.getElementById('precioKg');
    const pesoKg = document.getElementById('pesoKg');

    if (precioKg) {
        precioKg.addEventListener('input', calcularTotalPeso);
    }

    if (pesoKg) {
        pesoKg.addEventListener('input', calcularTotalPeso);
    }
});