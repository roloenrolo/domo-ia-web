/* Home v2: scroll nativo, sin dependencias. */
(() => {
  const root = document.documentElement;
  const reduce = matchMedia('(prefers-reduced-motion: reduce)');
  const mobile = matchMedia('(max-width: 820px)');
  const video = document.getElementById('heroVideo');
  const control = document.querySelector('.video-ctl');
  const [pauseLabel, playLabel] = control.querySelectorAll('span');
  let userPaused = false;
  let heroVisible = true;
  function syncControl() {
    pauseLabel.hidden = video.paused;
    playLabel.hidden = !video.paused;
  }
  function playHero() {
    if (!userPaused && heroVisible && !reduce.matches) video.play().catch(syncControl);
  }
  function heroVideo() {
    video.poster = mobile.matches ? '/assets/web/hero-oficina-vertical-v2.jpg' : '/assets/web/hero-oficina-1920.jpg';
    video.autoplay = !userPaused;
    if (reduce.matches) {
      video.pause();
      video.removeAttribute('autoplay');
      video.removeAttribute('src');
      video.load();
      return;
    }
    video.src = mobile.matches ? '/assets/web/v2/hero-vertical.mp4' : '/assets/web/v2/hero-oficina.mp4';
    video.load();
    playHero();
  }
  control.addEventListener('click', () => {
    if (video.paused) {
      userPaused = false;
      playHero();
    } else {
      userPaused = true;
      video.pause();
    }
  });
  video.addEventListener('play', syncControl);
  video.addEventListener('pause', syncControl);
  heroVideo();
  mobile.addEventListener('change', heroVideo);
  /* Ticker: las frases traducidas vienen del HTML. */
  (() => {
    const tk = document.getElementById('tk');
    const src = [...document.querySelectorAll('.ticker-src li')].map(el => el.textContent);
    if (!tk || !src.length) return;
    const tickerReduced = reduce.matches;
    let index = 0;
    function cycle() {
      if (document.hidden) {
        setTimeout(cycle, 1500);
        return;
      }
      index = (index + 1) % src.length;
      if (tickerReduced) {
        tk.textContent = src[index];
        setTimeout(cycle, 4000);
        return;
      }
      tk.textContent = '';
      setTimeout(() => {
        const phrase = src[index];
        let char = 0;
        function type() {
          tk.textContent = phrase.slice(0, ++char);
          if (char < phrase.length) setTimeout(type, 28);
          else setTimeout(cycle, 2600);
        }
        type();
      }, 400);
    }
    setTimeout(cycle, tickerReduced ? 4000 : 2600);
  })();
  if (!reduce.matches && 'IntersectionObserver' in window) {
    const lines = new IntersectionObserver((entries, observer) => {
      entries.forEach(e => {
        if (!e.isIntersecting) return;
        e.target.classList.add('on');
        observer.unobserve(e.target);
      });
    }, {threshold: .35});
    document.querySelectorAll('.linea').forEach(el => lines.observe(el));
  }
  if (!('IntersectionObserver' in window)) return;
  const header = () => root.classList.toggle('scrolled', scrollY > 40);
  addEventListener('scroll', header, {passive: true});
  header();
  new IntersectionObserver(([e]) => {
    heroVisible = e.isIntersecting;
    root.classList.toggle('cta-on', !heroVisible);
    if (heroVisible) playHero();
    else video.pause();
  }).observe(document.querySelector('.hero'));
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
})();
