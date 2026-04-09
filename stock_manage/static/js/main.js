// Common UI Logic for Lumiere
document.addEventListener('DOMContentLoaded', () => {
    // Init Lucide Icons
    if (typeof lucide !== 'undefined') {
        lucide.createIcons();
    }

    // Header Scroll Effect
    const header = document.getElementById('main-header');
    if (header) {
        window.addEventListener('scroll', () => {
            if (window.scrollY > 50) {
                header.classList.add('bg-white/95', 'py-2', 'shadow-sm');
                header.classList.remove('h-20');
            } else {
                header.classList.remove('bg-white/95', 'py-2', 'shadow-sm');
                header.classList.add('h-20');
            }
        });
    }

    // Mobile Menu
    const mobileMenuBtn = document.getElementById('mobile-menu-btn');
    const closeMobileMenu = document.getElementById('close-mobile-menu');
    const mobileMenu = document.getElementById('mobile-menu');

    if (mobileMenuBtn && mobileMenu && closeMobileMenu) {
        mobileMenuBtn.addEventListener('click', () => {
            mobileMenu.classList.remove('translate-x-full');
            document.body.style.overflow = 'hidden';
        });

        closeMobileMenu.addEventListener('click', () => {
            mobileMenu.classList.add('translate-x-full');
            document.body.style.overflow = '';
        });
    }

    // Quantity Selector logic (if present)
    const qtyMenus = document.querySelectorAll('.qty-selector');
    qtyMenus.forEach(menu => {
        const minus = menu.querySelector('.minus');
        const plus = menu.querySelector('.plus');
        const input = menu.querySelector('input');

        if (minus && plus && input) {
            minus.addEventListener('click', () => {
                let val = parseInt(input.value);
                if (val > 1) input.value = val - 1;
            });
            plus.addEventListener('click', () => {
                let val = parseInt(input.value);
                input.value = val + 1;
            });
        }
    });
});
