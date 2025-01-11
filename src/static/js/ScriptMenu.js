document.addEventListener('DOMContentLoaded', function () {
    console.log('Página cargada con layout actualizado.');

    // Evento para resaltar el botón de logout al pasar el mouse
    const logoutButton = document.querySelector('.btn-success');
    logoutButton.addEventListener('mouseenter', () => {
        logoutButton.style.boxShadow = '0 4px 12px rgba(0, 0, 0, 0.3)';
    });
    logoutButton.addEventListener('mouseleave', () => {
        logoutButton.style.boxShadow = 'none';
    });

    // Animación de hover en los enlaces del navbar lateral
    const navLinks = document.querySelectorAll('.nav-link');
    navLinks.forEach(link => {
        link.addEventListener('mouseenter', () => {
            link.style.boxShadow = '0 4px 12px rgba(0, 0, 0, 0.3)';
            link.style.transform = 'translateY(-2px)';
        });
        link.addEventListener('mouseleave', () => {
            link.style.boxShadow = 'none';
            link.style.transform = 'none';
        });
    });
});



