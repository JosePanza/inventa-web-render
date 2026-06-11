function abrirEditor(id, nombre, categoria, descripcion, tipo_venta, precio_venta, precio_costo, stock) {
    const panel = document.getElementById('panel-editar');
    const form = document.getElementById('form-editar');

    if (!panel || !form) {
        return;
    }

    form.action = `/inventario/editar/${id}/`;

    document.getElementById('edit-nombre').value = nombre;
    document.getElementById('edit-categoria').value = categoria;
    document.getElementById('edit-descripcion').value = descripcion;
    document.getElementById('edit-tipo_venta').value = tipo_venta;
    document.getElementById('edit-precio_venta').value = precio_venta;
    document.getElementById('edit-precio_costo').value = precio_costo;
    document.getElementById('edit-stock').value = stock;

    panel.classList.remove('hidden');
    panel.scrollIntoView({ behavior: 'smooth', block: 'start' });
}

function cerrarEditor() {
    const panel = document.getElementById('panel-editar');

    if (panel) {
        panel.classList.add('hidden');
    }
}