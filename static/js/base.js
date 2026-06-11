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
    const sidebar = document.getElementById("sidebar");
    const sidebarOverlay = document.getElementById("sidebarOverlay");

    if (!mobileMenuBtn || !sidebar || !sidebarOverlay) {
        return;
    }

    function abrirMenuMovil() {
        sidebar.classList.remove("-translate-x-full");
        sidebarOverlay.classList.remove("hidden");
    }

    function cerrarMenuMovil() {
        sidebar.classList.add("-translate-x-full");
        sidebarOverlay.classList.add("hidden");
    }

    mobileMenuBtn.addEventListener("click", abrirMenuMovil);
    sidebarOverlay.addEventListener("click", cerrarMenuMovil);

    const linksMenu = sidebar.querySelectorAll("a");

    linksMenu.forEach(function (link) {
        link.addEventListener("click", function () {
            if (window.innerWidth < 768) {
                cerrarMenuMovil();
            }
        });
    });
});