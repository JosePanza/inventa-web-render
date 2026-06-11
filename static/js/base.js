function toggleUserMenu() {
    const menu = document.getElementById('userMenu');

    if (menu) {
        menu.classList.toggle('hidden');
    }
}

document.addEventListener('click', function(e) {
    const menu = document.getElementById('userMenu');
    const container = document.getElementById('userMenuContainer');

    if (menu && container && !container.contains(e.target)) {
        menu.classList.add('hidden');
    }
});

// =============================
// MENÚ LATERAL RESPONSIVE
// =============================
document.addEventListener("DOMContentLoaded", function () {
    const mobileMenuBtn = document.getElementById("mobileMenuBtn");
    const sidebarOverlay = document.getElementById("sidebarOverlay");
    const sidebar = document.getElementById("sidebar");

    if (!mobileMenuBtn || !sidebarOverlay || !sidebar) {
        return;
    }

    function abrirMenuMovil() {
        document.body.classList.add("sidebar-open");
    }

    function cerrarMenuMovil() {
        document.body.classList.remove("sidebar-open");
    }

    mobileMenuBtn.addEventListener("click", function () {
        if (document.body.classList.contains("sidebar-open")) {
            cerrarMenuMovil();
        } else {
            abrirMenuMovil();
        }
    });

    sidebarOverlay.addEventListener("click", cerrarMenuMovil);

    const linksMenu = sidebar.querySelectorAll("a");

    linksMenu.forEach(function (link) {
        link.addEventListener("click", function () {
            if (window.innerWidth <= 768) {
                cerrarMenuMovil();
            }
        });
    });
});