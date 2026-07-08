// app.js — Landing page behaviors: mobile menu, smooth scroll, sticky nav,
// active link highlighting, FAQ accordion, scroll reveal animations, theme toggle.
(function(){
  'use strict';

  const nav = document.querySelector('.nav');
  const navToggle = document.querySelector('.nav-toggle');
  const menu = document.getElementById('primary-menu');
  const navLinks = Array.from(document.querySelectorAll('.nav-list a'));
  const sections = Array.from(document.querySelectorAll('main [id]'));
  const detailsEls = Array.from(document.querySelectorAll('details'));
  const revealSelector = ['.feature-card', '.ai-card', '.steps li', '.hero-preview', '.feature-grid li'].join(',');

  /* Utility */
  const isMobile = ()=> window.matchMedia('(max-width:700px)').matches;

  /* Mobile menu */
  function closeMenu(){
    if(menu){
      menu.classList.remove('open');
      menu.style.display = '';
    }
    if(navToggle) navToggle.setAttribute('aria-expanded','false');
  }

  if(navToggle && menu){
    navToggle.addEventListener('click', ()=>{
      const opened = menu.classList.toggle('open');
      navToggle.setAttribute('aria-expanded', String(opened));
      menu.style.display = opened ? 'flex' : '';
    });

    // close when clicking a link on mobile
    menu.addEventListener('click', (e)=>{
      if(e.target.tagName === 'A' && isMobile()) closeMenu();
    });

    // close when clicking outside
    document.addEventListener('click', (e)=>{
      if(!menu.contains(e.target) && !navToggle.contains(e.target) && menu.classList.contains('open')){
        closeMenu();
      }
    });

    // ensure menu resets on resize
    window.addEventListener('resize', ()=>{
      if(window.innerWidth > 700) closeMenu();
    });
  }

  /* Smooth scrolling for in-page links */
  navLinks.concat(Array.from(document.querySelectorAll('a[href^="#"]'))).forEach(a=>{
    a.addEventListener('click', (e)=>{
      const href = a.getAttribute('href');
      if(!href || !href.startsWith('#')) return;
      const target = document.querySelector(href);
      if(!target) return;
      e.preventDefault();
      const navHeight = nav ? nav.offsetHeight : 0;
      const rect = target.getBoundingClientRect();
      const top = window.scrollY + rect.top - navHeight - 12;
      window.scrollTo({top, behavior:'smooth'});
      // close mobile menu after navigation
      if(isMobile()) closeMenu();
    });
  });

  /* Sticky nav effect */
  function onScrollNav(){
    if(!nav) return;
    if(window.scrollY > 12) nav.classList.add('scrolled'); else nav.classList.remove('scrolled');
  }
  onScrollNav();
  window.addEventListener('scroll', onScrollNav, {passive:true});

  /* Active nav highlighting using IntersectionObserver */
  if(sections.length && navLinks.length){
    const idToLink = Object.fromEntries(navLinks.map(a=>[a.getAttribute('href')?.replace('#',''), a]));
    const observer = new IntersectionObserver((entries)=>{
      entries.forEach(entry=>{
        const id = entry.target.id;
        const link = idToLink[id];
        if(!link) return;
        if(entry.isIntersecting){
          navLinks.forEach(l=>l.classList.remove('active'));
          link.classList.add('active');
        }
      });
    },{root:null,rootMargin:'-30% 0px -40% 0px',threshold:0.15});
    sections.forEach(s=>observer.observe(s));
  }

  /* FAQ accordion: ensure one open at a time and keyboard support */
  if(detailsEls.length){
    detailsEls.forEach(d=>{
      const summary = d.querySelector('summary');
      if(summary){
        summary.addEventListener('click', (e)=>{
          // if closing, let it; if opening, close others
          const willOpen = !d.open;
          if(willOpen){
            detailsEls.forEach(other=>{ if(other !== d) other.open = false; });
          }
        });

        summary.addEventListener('keydown', (ev)=>{
          if(ev.key === 'Enter' || ev.key === ' '){ ev.preventDefault(); summary.click(); }
        });
      }
    });
  }

  /* Scroll reveal animations */
  const revealTargets = Array.from(document.querySelectorAll(revealSelector));
  if(revealTargets.length){
    const revealObserver = new IntersectionObserver((entries, obs)=>{
      entries.forEach(entry=>{
        if(entry.isIntersecting){
          const el = entry.target;
          el.classList.add('fade-in');
          obs.unobserve(el);
        }
      });
    },{threshold:0.12});
    revealTargets.forEach(t=>revealObserver.observe(t));
  }

  /* Theme toggle: create control and persist preference */
  const THEME_KEY = 'aiqr_theme';
  const darkVars = {
    '--bg':'#0F172A', '--card-bg':'rgba(255,255,255,0.03)', '--glass-border':'rgba(255,255,255,0.06)',
    '--text':'#E6EEF8','--muted':'#9FB3C8','--shadow-1':'0 6px 18px rgba(2,6,23,0.6)','--shadow-2':'0 10px 30px rgba(2,6,23,0.7)'
  };
  const lightVars = {
    '--bg':'#F8FAFC','--card-bg':'rgba(255,255,255,0.12)','--glass-border':'rgba(255,255,255,0.25)',
    '--text':'#0f172a','--muted':'#475569','--shadow-1':'0 6px 18px rgba(15,23,42,0.08)','--shadow-2':'0 10px 30px rgba(15,23,42,0.12)'
  };

  function applyVars(vars){
    const root = document.documentElement;
    Object.entries(vars).forEach(([k,v])=>root.style.setProperty(k,v));
  }

  function setTheme(t){
    if(t === 'dark') applyVars(darkVars);
    else if(t === 'light') applyVars(lightVars);
    else { // system
      const prefersDark = window.matchMedia('(prefers-color-scheme: dark)').matches;
      applyVars(prefersDark ? darkVars : lightVars);
    }
    try{ if(t) localStorage.setItem(THEME_KEY, t); else localStorage.removeItem(THEME_KEY); }catch(e){}
  }

  // Create toggle button in nav (if not present)
  (function createThemeToggle(){
    const saved = (()=>{ try{return localStorage.getItem(THEME_KEY);}catch(e){return null;} })();
    setTheme(saved || 'system');

    const toggle = document.createElement('button');
    toggle.className = 'btn btn-ghost theme-toggle';
    toggle.type = 'button';
    toggle.setAttribute('aria-label','Toggle theme');
    toggle.textContent = saved === 'dark' ? '🌙' : saved === 'light' ? '☀️' : '🌓';

    toggle.addEventListener('click', ()=>{
      const current = localStorage.getItem(THEME_KEY) || 'system';
      const next = current === 'dark' ? 'light' : current === 'light' ? 'system' : 'dark';
      setTheme(next);
      toggle.textContent = next === 'dark' ? '🌙' : next === 'light' ? '☀️' : '🌓';
    });

    const navInner = document.querySelector('.nav-inner');
    if(navInner){
      // place before CTAs
      const cta = navInner.querySelector('.nav-ctas');
      if(cta) navInner.insertBefore(toggle, cta);
      else navInner.appendChild(toggle);
    } else document.body.appendChild(toggle);
  })();

  /* Footer year update */
  const yearEl = document.getElementById('year');
  if(yearEl) yearEl.textContent = new Date().getFullYear();

})();
