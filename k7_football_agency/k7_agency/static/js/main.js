// K7 Football Agency — interactividad principal (vanilla JS, sin frameworks)

document.addEventListener("DOMContentLoaded", () => {
  // --- Navbar transparente -> sólido al hacer scroll ---
  const navbar = document.querySelector(".navbar");
  const onScroll = () => {
    if (!navbar) return;
    if (window.scrollY > 40) navbar.classList.add("scrolled");
    else navbar.classList.remove("scrolled");
  };
  window.addEventListener("scroll", onScroll);
  onScroll();

  // --- Menú móvil ---
  const navToggle = document.querySelector(".nav-toggle");
  const navLinks = document.querySelector(".nav-links");
  if (navToggle && navLinks) {
    navToggle.addEventListener("click", () => {
      navLinks.classList.toggle("mobile-open");
      navLinks.style.display = navLinks.classList.contains("mobile-open") ? "flex" : "";
    });
  }

  // --- Partículas animadas del hero ---
  const particlesEl = document.querySelector(".particles");
  if (particlesEl) {
    const count = 26;
    for (let i = 0; i < count; i++) {
      const p = document.createElement("div");
      p.className = "particle";
      p.style.left = Math.random() * 100 + "%";
      p.style.bottom = "-10px";
      p.style.animationDuration = 6 + Math.random() * 10 + "s";
      p.style.animationDelay = Math.random() * 8 + "s";
      p.style.opacity = 0.3 + Math.random() * 0.5;
      particlesEl.appendChild(p);
    }
  }

  // --- Scroll reveal (fade in up) ---
  const revealEls = document.querySelectorAll(".reveal");
  const observer = new IntersectionObserver(
    (entries) => {
      entries.forEach((entry) => {
        if (entry.isIntersecting) {
          entry.target.classList.add("in-view");
          observer.unobserve(entry.target);
        }
      });
    },
    { threshold: 0.15 }
  );
  revealEls.forEach((el) => observer.observe(el));

  // --- Contadores animados (stats) ---
  const counters = document.querySelectorAll("[data-count]");
  const counterObserver = new IntersectionObserver(
    (entries) => {
      entries.forEach((entry) => {
        if (!entry.isIntersecting) return;
        const el = entry.target;
        const target = parseInt(el.getAttribute("data-count"), 10);
        const suffix = el.getAttribute("data-suffix") || "";
        let current = 0;
        const step = Math.max(1, Math.ceil(target / 60));
        const tick = () => {
          current += step;
          if (current >= target) {
            el.textContent = target + suffix;
          } else {
            el.textContent = current + suffix;
            requestAnimationFrame(tick);
          }
        };
        tick();
        counterObserver.unobserve(el);
      });
    },
    { threshold: 0.5 }
  );
  counters.forEach((el) => counterObserver.observe(el));

  // --- Carrusel simple de noticias destacadas ---
  const carousel = document.querySelector("[data-carousel]");
  if (carousel) {
    const track = carousel.querySelector(".carousel-track");
    const slides = Array.from(track.children);
    let index = 0;
    const show = (i) => {
      track.style.transform = `translateX(-${i * 100}%)`;
    };
    setInterval(() => {
      index = (index + 1) % slides.length;
      show(index);
    }, 4500);
  }

  // --- Modales del panel admin (crear/editar) ---
  document.querySelectorAll("[data-open-modal]").forEach((btn) => {
    btn.addEventListener("click", () => {
      const modal = document.querySelector(btn.getAttribute("data-open-modal"));
      if (modal) modal.classList.add("open");
    });
  });
  document.querySelectorAll("[data-close-modal]").forEach((btn) => {
    btn.addEventListener("click", () => {
      btn.closest(".modal-overlay").classList.remove("open");
    });
  });
});
