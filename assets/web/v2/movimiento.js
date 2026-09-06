/* Home v2: scroll nativo, sin dependencias. */
(() => {
  const root = document.documentElement;
  const reduce = matchMedia('(prefers-reduced-motion: reduce)');
  const mobile = matchMedia('(max-width: 820px)');
  const video = document.getElementById('heroVideo');
  function heroVideo() {
    video.poster = mobile.matches ? '/assets/web/hero-oficina-vertical-v2.jpg' : '/assets/web/hero-oficina-1920.jpg';
    if (reduce.matches) {
      video.pause();
      video.removeAttribute('autoplay');
      video.removeAttribute('src');
      video.load();
      return;
    }
    video.autoplay = true;
    video.src = mobile.matches ? '/assets/web/v2/hero-vertical.mp4' : '/assets/web/v2/hero-oficina.mp4';
    video.load();
    video.play().catch(() => {});
  }
  heroVideo();
  mobile.addEventListener('change', heroVideo);
  if (!('IntersectionObserver' in window)) return;
  const header = () => root.classList.toggle('scrolled', scrollY > 40);
  addEventListener('scroll', header, {passive: true});
  header();
  new IntersectionObserver(([e]) => root.classList.toggle('cta-on', !e.isIntersecting)).observe(document.querySelector('.hero'));
  if (reduce.matches) return;
  root.classList.add('motion');
  reduce.addEventListener('change', () => { root.classList.toggle('motion', !reduce.matches); heroVideo(); });
  document.querySelectorAll('[data-words]').forEach(el => {
    const words = el.textContent.split(/(\s+)/);
    el.replaceChildren(...words.map((word, i) => {
      if (!word.trim()) return document.createTextNode(word);
      const span = document.createElement('span');
      span.className = 'word';
      span.style.setProperty('--i', Math.floor(i / 2));
      span.textContent = word;
      return span;
    }));
  });
  const ribbon = document.querySelector('.marquee-track');
  // La frase se repite hasta cubrir la ventana: funciona igual en es, en e it.
  const base = ribbon.firstElementChild;
  const frase = base.textContent.trim();
  let veces = 1;
  while (base.getBoundingClientRect().width < innerWidth * 1.15 && veces < 40) {
    veces += 1;
    base.textContent = Array(veces).fill(frase).join('  ·  ');
  }
  const copy = document.createElement('p');
  copy.className = 'mono marquee-copy';
  copy.setAttribute('aria-hidden', 'true');
  // El duplicado visual usa el texto ya traducido; no duplica innerText ni la lectura accesible.
  copy.dataset.text = ribbon.firstElementChild.textContent;
  ribbon.append(copy);

  /* IO: entradas únicas y fallback temporal (sin motor externo). */
  const native = CSS.supports('animation-timeline: view()');
  root.classList.toggle('native-motion', native);
  const reveal = new IntersectionObserver(entries => {
    entries.forEach(e => {
      if (!e.isIntersecting) return;
      const el = e.target;
      el.classList.remove('waiting');
      el.classList.add('in');
      // Cierra la entrada aunque el visitante detenga el scroll a mitad del elemento.
      // Un solo plazo independiente; ninguna transición encadena otra.
      if (native) setTimeout(() => el.classList.add('settled'), 900);
      reveal.unobserve(el);
    });
  }, {threshold: 0.01});
  document.querySelectorAll('[data-enter]').forEach(el => {
    el.classList.add('waiting');
    reveal.observe(el);
  });
  const final = document.querySelector('.final');
  new IntersectionObserver((entries, obs) => {
    if (!entries[0].isIntersecting) return;
    final.classList.add('in');
    final.querySelector('[data-words]').classList.add('in');
    obs.disconnect();
  }, {threshold: 0.1}).observe(final);
  const count = document.querySelector('[data-count]');
  new IntersectionObserver((entries, obs) => {
    if (!entries[0].isIntersecting) return;
    obs.disconnect();
    const start = performance.now();
    function tick(now) {
      const p = Math.min(1, (now - start) / 900);
      count.textContent = Math.round(9 * p);
      if (p < 1) requestAnimationFrame(tick);
    }
    requestAnimationFrame(tick);
  }).observe(count);

  const fronts = document.getElementById('frentes');
  const number = fronts.querySelector('.front-counter');
  // Un observador común decide el frente visible sin escuchar la rueda.
  const frontObserver = new IntersectionObserver(entries => {
    for (const e of entries) if (e.isIntersecting) {
      if (fronts.dataset.activa === e.target.dataset.front) continue;
      fronts.dataset.activa = e.target.dataset.front;
      number.dataset.number = '0' + fronts.dataset.activa;
      number.classList.remove('wipe');
      void number.offsetWidth;
      number.classList.add('wipe');
    }
  }, {rootMargin: '-25% 0px -40% 0px'});
  fronts.querySelectorAll('.front-row').forEach(el => frontObserver.observe(el));

  const team = document.getElementById('equipo');
  const track = team.querySelector('.team-track');
  const progress = team.querySelector('.team-progress');
  const desktop = matchMedia('(min-width: 1024px) and (min-height: 820px)');
  const nativeGallery = CSS.supports('animation-timeline: scroll(root block)') && CSS.supports('animation-range: 0px 1px');
  let start = 0, distance = 1, travel = 0, watching = false, queued = false;
  function frame() {
    queued = false;
    if (!root.classList.contains('gallery') || nativeGallery) return;
    const p = Math.max(0, Math.min(1, (scrollY - start) / distance));
    track.style.transform = `translateX(${-travel * p}px)`;
    progress.style.transform = `scaleX(${p})`;
  }
  function measure() {
    root.classList.toggle('gallery', desktop.matches);
    root.classList.toggle('native-gallery', desktop.matches && nativeGallery);
    track.style.transform = '';
    progress.style.transform = '';
    if (!desktop.matches) return;
    // Si las viñetas no caben completas, conserva la cuadrícula legible.
    const room = team.querySelector('.team-window').clientHeight;
    const fits = [...team.querySelectorAll('.worker')].every(el => el.scrollHeight <= room + 2);
    if (!fits) {
      root.classList.remove('gallery', 'native-gallery');
      return;
    }
    start = team.getBoundingClientRect().top + scrollY - 72;
    distance = team.offsetHeight - (innerHeight - 72);
    travel = track.scrollWidth - team.querySelector('.team-window').clientWidth;
    team.style.setProperty('--travel', travel + 'px');
    team.style.setProperty('--scroll-start', start + 'px');
    team.style.setProperty('--scroll-end', start + distance + 'px');
    frame();
  }
  new IntersectionObserver(([e]) => { watching = e.isIntersecting; frame(); }).observe(team);
  addEventListener('scroll', () => {
    if (watching && !nativeGallery && !queued) {
      queued = true;
      requestAnimationFrame(frame);
    }
  }, {passive: true});
  addEventListener('resize', measure, {passive: true});
  measure();
  document.fonts.ready.then(measure);
  const method = document.querySelector('.video-frame');
  const film = method.querySelector('video');
  method.querySelector('button').addEventListener('click', () => film.play().catch(() => {}));
  film.addEventListener('play', () => method.classList.add('playing'));
})();
