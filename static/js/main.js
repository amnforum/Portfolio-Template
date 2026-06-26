/* ============================================================
   Open Portfolio
   ============================================================ */

function initPortfolio() {

  // --- Loading Screen ---------------------------------------
  const loadingScreen = document.getElementById('loading-screen');
  if (loadingScreen) {
    if (sessionStorage.getItem('portfolio_loaded')) {
      loadingScreen.classList.add('hidden', 'no-transition');
      requestAnimationFrame(checkReveal);
    } else {
      setTimeout(function () {
        loadingScreen.classList.add('hidden');
        sessionStorage.setItem('portfolio_loaded', 'true');
        setTimeout(checkReveal, 100);
      }, 800);
    }
  } else {
    requestAnimationFrame(checkReveal);
  }

  // --- Scroll Progress Bar ----------------------------------
  const progressBar = document.getElementById('scroll-progress');
  const navbar = document.getElementById('navbar');
  const heroBg = document.querySelector('.hero-bg');
  function updateProgress() {
    const scrollTop = window.scrollY;
    const docHeight = document.documentElement.scrollHeight - window.innerHeight;
    const progress = docHeight > 0 ? (scrollTop / docHeight) * 100 : 0;
    if (progressBar) progressBar.style.width = progress + '%';
  }

  // --- Navbar Scroll Behavior -------------------------------
  function updateNavbar() {
    if (!navbar) return;
    if (window.scrollY > 60) {
      navbar.classList.add('scrolled');
    } else {
      navbar.classList.remove('scrolled');
    }
  }
  function updateHeroParallax() {
    if (!heroBg) return;
    heroBg.style.transform = 'scale(1.05) translateY(' + (window.scrollY * 0.3) + 'px)';
  }

  let scrollTicking = false;
  function handleScroll() {
    if (scrollTicking) return;
    scrollTicking = true;
    requestAnimationFrame(function () {
      updateProgress();
      updateNavbar();
      updateHeroParallax();
      scrollTicking = false;
    });
  }

  window.addEventListener('scroll', handleScroll, { passive: true });
  handleScroll();

  // --- Active Nav Link (Intersection Observer) -------------
  const sections = document.querySelectorAll('section[id]');
  const navLinks = document.querySelectorAll('.nav-link[href^="#"]');

  const sectionObserver = new IntersectionObserver(function (entries) {
    entries.forEach(function (entry) {
      if (entry.isIntersecting) {
        const id = entry.target.getAttribute('id');
        navLinks.forEach(function (link) {
          link.classList.remove('active');
          if (link.getAttribute('href') === '#' + id) {
            link.classList.add('active');
          }
        });
      }
    });
  }, { threshold: 0.4 });

  sections.forEach(function (s) { sectionObserver.observe(s); });

  // --- Smooth Scroll for anchor links ----------------------
  document.querySelectorAll('a[href^="#"], a[href^="/#"]').forEach(function (anchor) {
    anchor.addEventListener('click', function (e) {
      let href = this.getAttribute('href');
      // If starts with /, strip it for the selector check
      let targetId = href.startsWith('/') ? href.substring(1) : href;
      
      const target = document.querySelector(targetId);
      if (target) {
        e.preventDefault();
        target.scrollIntoView({ behavior: 'smooth', block: 'start' });
        
        // Close legacy mobile menu
        if (typeof closeMobileMenu === 'function') closeMobileMenu();
        
        // Close base.html mobile menu
        const mobileMenu = document.getElementById('nav-mobile-menu');
        const mobileToggle = document.getElementById('nav-mobile-toggle');
        if (mobileMenu && !mobileMenu.classList.contains('hidden')) {
          mobileMenu.classList.add('hidden');
          if (mobileToggle) {
            mobileToggle.innerHTML = '<i class="fas fa-bars"></i>';
            mobileToggle.setAttribute('aria-expanded', 'false');
          }
        }
      }
    });
  });

  // --- Mobile Menu ------------------------------------------
  const menuBtn = document.getElementById('menu-btn');
  const closeBtn = document.getElementById('menu-close');
  const mobileMenu = document.getElementById('mobile-menu');

  function openMobileMenu() {
    if (mobileMenu) mobileMenu.classList.add('open');
    document.body.style.overflow = 'hidden';
  }
  function closeMobileMenu() {
    if (mobileMenu) mobileMenu.classList.remove('open');
    document.body.style.overflow = '';
  }

  if (menuBtn) menuBtn.addEventListener('click', openMobileMenu);
  if (closeBtn) closeBtn.addEventListener('click', closeMobileMenu);

  // --- Parallax Hero ----------------------------------------

  // --- Scroll Reveal ----------------------------------------
  const reveals = document.querySelectorAll('.reveal');

  const revealObserver = new IntersectionObserver(function (entries) {
    entries.forEach(function (entry, i) {
      if (entry.isIntersecting) {
        const delay = entry.target.dataset.delay || 0;
        setTimeout(function () {
          entry.target.classList.add('visible');
        }, parseInt(delay));
        revealObserver.unobserve(entry.target);
      }
    });
  }, { threshold: 0.1, rootMargin: '0px 0px -40px 0px' });

  reveals.forEach(function (el) { revealObserver.observe(el); });

  function checkReveal() {
    reveals.forEach(function (el) {
      const rect = el.getBoundingClientRect();
      if (rect.top < window.innerHeight) {
        el.classList.add('visible');
      }
    });
  }

  // --- Skill Bar Animation ----------------------------------
  const skillBars = document.querySelectorAll('.skill-bar-fill');

  const skillObserver = new IntersectionObserver(function (entries) {
    entries.forEach(function (entry) {
      if (entry.isIntersecting) {
        const target = entry.target.dataset.width;
        entry.target.style.width = target + '%';
        skillObserver.unobserve(entry.target);
      }
    });
  }, { threshold: 0.2 });

  skillBars.forEach(function (bar) { skillObserver.observe(bar); });

  // --- Project Category Filter ------------------------------
  const filterBtns = document.querySelectorAll('.filter-btn');
  const projectCards = document.querySelectorAll('.project-item');

  filterBtns.forEach(function (btn) {
    btn.addEventListener('click', function () {
      filterBtns.forEach(function (b) { b.classList.remove('active'); });
      this.classList.add('active');
      const cat = this.dataset.category;

      projectCards.forEach(function (card) {
        if (cat === 'all' || card.dataset.category === cat) {
          card.style.display = '';
          setTimeout(function () { card.style.opacity = '1'; card.style.transform = ''; }, 50);
        } else {
          card.style.opacity = '0';
          card.style.transform = 'scale(0.95)';
          setTimeout(function () { card.style.display = 'none'; }, 300);
        }
      });
    });
  });

  // --- Contact Form UX -------------------------------------
  const contactForm = document.getElementById('contact-form');
  if (contactForm) {
    const submitBtn = contactForm.querySelector('#submit-btn');
    contactForm.addEventListener('submit', function () {
      if (submitBtn) {
        submitBtn.textContent = 'SENDING...';
        submitBtn.disabled = true;
      }
    });
  }

  // --- Typed Effect on Hero ---------------------------------
  const typedEl = document.getElementById('typed-text');
  if (typedEl) {
    const words = typedEl.dataset.words ? typedEl.dataset.words.split('|') : [];
    let wordIdx = 0;
    let charIdx = 0;
    let deleting = false;

    function typeLoop() {
      const current = words[wordIdx] || '';
      if (!deleting) {
        typedEl.textContent = current.slice(0, charIdx + 1);
        charIdx++;
        if (charIdx === current.length) {
          deleting = true;
          setTimeout(typeLoop, 2000);
        } else {
          setTimeout(typeLoop, 80);
        }
      } else {
        typedEl.textContent = current.slice(0, charIdx - 1);
        charIdx--;
        if (charIdx === 0) {
          deleting = false;
          wordIdx = (wordIdx + 1) % words.length;
          setTimeout(typeLoop, 400);
        } else {
          setTimeout(typeLoop, 50);
        }
      }
    }
    if (words.length > 0) typeLoop();
  }

  // --- Message auto-hide ------------------------------------
  const msgs = document.querySelectorAll('.auto-hide-msg');
  msgs.forEach(function (msg) {
    setTimeout(function () {
      msg.style.opacity = '0';
      msg.style.transform = 'translateY(-10px)';
      setTimeout(function () { msg.remove(); }, 400);
    }, 5000);
  });
  // --- Hidden Admin Shortcut --------------------------------
}

if (document.readyState === 'loading') {
  document.addEventListener('DOMContentLoaded', initPortfolio);
} else {
  initPortfolio();
}
