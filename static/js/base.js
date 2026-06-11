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