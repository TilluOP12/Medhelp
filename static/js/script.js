// Add dynamic features with JavaScript if necessary
// For example, a sticky navbar on scroll, animations, etc.

window.addEventListener('scroll', function () {
    const navbar = document.querySelector('.navbar');
    navbar.classList.toggle('sticky', window.scrollY > 0);
});
