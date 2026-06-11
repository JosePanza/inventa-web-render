function abrirDetalleVenta(id) {
    const modal = document.getElementById(id);

    if (modal) {
        modal.classList.remove('hidden');
    }
}

function cerrarDetalleVenta(id) {
    const modal = document.getElementById(id);

    if (modal) {
        modal.classList.add('hidden');
    }
}

function abrirModalInforme() {
    const modal = document.getElementById('modal-informe');

    if (modal) {
        modal.classList.remove('hidden');
        cambiarTipoInforme();
    }
}

function cerrarModalInforme() {
    const modal = document.getElementById('modal-informe');

    if (modal) {
        modal.classList.add('hidden');
    }
}

function cambiarTipoInforme() {
    const tipo = document.getElementById('tipo-informe');
    const campoDia = document.getElementById('campo-dia');
    const campoRango = document.getElementById('campo-rango');

    if (!tipo || !campoDia || !campoRango) {
        return;
    }

    if (tipo.value === 'diario') {
        campoDia.classList.remove('hidden');
        campoRango.classList.add('hidden');
    } else {
        campoDia.classList.add('hidden');
        campoRango.classList.remove('hidden');
    }
}

document.addEventListener('DOMContentLoaded', function () {
    cambiarTipoInforme();

    const vistaPrevia = document.getElementById('vista-previa-informe');

    if (vistaPrevia) {
        setTimeout(function () {
            vistaPrevia.scrollIntoView({
                behavior: 'smooth',
                block: 'start'
            });
        }, 200);
    }
});