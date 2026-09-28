// Choose once per visit, excluding the fixed homepage artwork. No timers or storage.
export function chooseHomeArt(choices, count, random = Math.random) {
  const pool = [...choices];
  const selected = [];
  while (pool.length && selected.length < count) {
    selected.push(pool.splice(Math.floor(random() * pool.length), 1)[0]);
  }
  return selected;
}

export function setupHomeArt(doc = document) {
  const figures = [...doc.querySelectorAll('[data-home-art]:not([data-home-art-fixed])')];
  if (!figures.length) return;
  let choices;
  try { choices = JSON.parse(doc.querySelector('[data-home-art-choices]').textContent); }
  catch { return; } // Keep the linked, server-rendered fallback.
  if (!Array.isArray(choices) || !choices.length) return;
  const fixed = new Set([...doc.querySelectorAll('[data-home-art-fixed]')].map(figure => figure.getAttribute('data-home-art-fixed')));
  chooseHomeArt(choices.filter(work => !fixed.has(work.id)), figures.length).forEach((work, index) => {
    const figure = figures[index];
    const image = figure.querySelector('[data-home-art-image]');
    const frame = figure.querySelector('[data-home-art-frame]');
    frame.className = `art-frame frame-${work.frame} mat-${work.mat} frame-${work.variant} refined-frame`;
    frame.style.setProperty('--art-ratio', work.width / work.height);
    const crop = figure.querySelector('.screen-art-crop');
    crop.className = `screen-art-crop screen-art-${work.id}`;
    crop.style.setProperty('--crop-ratio', work.width / (work.height * work.art_bottom));
    crop.style.setProperty('--source-ratio', work.width / work.height);
    figure.querySelector('[data-print-title]').textContent = work.title;
    figure.querySelector('[data-print-caption]').textContent = work.caption;
    image.width = work.width;
    image.height = work.height;
    image.alt = `${work.title}, refined print of artwork by Ahimanikya Satapathy`;
    image.src = work.image;
    for (const link of figure.querySelectorAll('[data-home-art-link]')) {
      link.href = work.page;
      link.setAttribute('aria-label', `Read about ${work.title} in the Art Journal`);
    }
  });
}
