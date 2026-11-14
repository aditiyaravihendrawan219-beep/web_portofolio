const scrollup = document.querySelector
(".scroll-up");

window.onscroll = () => {
    if (window.scrollY> 250){
        scrollup.classList.add("scroll-active")
    } else {
        scrollup.classList.remove("scroll-active")
    }
};

const themeToggleBtn = document.getElementById('theme-toggle');

// Cek status dark mode saat halaman dimuat
if (localStorage.getItem('theme') === 'dark') {
    document.body.classList.add('dark-mode');
    if (themeToggleBtn) {
        themeToggleBtn.innerHTML = '<i class="fa-solid fa-sun"></i>';
    }
}

// Fungsi saat tombol diklik
if (themeToggleBtn) {
    themeToggleBtn.addEventListener('click', function () {
        document.body.classList.toggle('dark-mode');
        
        if (document.body.classList.contains('dark-mode')) {
            localStorage.setItem('theme', 'dark');
            themeToggleBtn.innerHTML = '<i class="fa-solid fa-sun"></i>';
        } else {
            localStorage.setItem('theme', 'light');
            themeToggleBtn.innerHTML = '<i class="fa-solid fa-moon"></i>';
        }
    });
}

