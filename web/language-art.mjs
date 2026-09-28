// Apply the same framed print treatment in the sidebar and slideshow.
export function applyArtworkFrame(frame, work) {
  const image = frame.querySelector('img');
  frame.className = `art-frame frame-${work.frame} mat-${work.mat} frame-${work.variant} refined-frame`;
  frame.style.setProperty('--art-ratio', work.width / work.height);
  const crop = frame.querySelector('.screen-art-crop');
  crop.className = `screen-art-crop screen-art-${work.id}`;
  crop.style.setProperty('--crop-ratio', work.width / (work.height * work.art_bottom));
  crop.style.setProperty('--source-ratio', work.width / work.height);
  frame.querySelector('[data-print-title]').textContent = work.title;
  frame.querySelector('[data-print-caption]').textContent = work.caption;
  image.width = work.width;
  image.height = work.height;
  image.alt = `${work.title}, refined print of artwork by Ahimanikya Satapathy`;
  image.src = work.image;
}

// Select once per page load. Reading and listening never trigger a change.
export function setupLanguageArt(doc = document) {
  const feature = doc.querySelector('[data-language-art]');
  if (!feature) return;
  let choices;
  try {
    choices = JSON.parse(feature.querySelector('[data-art-choices]').textContent);
  } catch {
    return; // The server-rendered artwork remains useful without enhancement.
  }
  if (!Array.isArray(choices) || !choices.length) return;
  const work = choices[Math.floor(Math.random() * choices.length)];
  const frame = feature.querySelector('[data-art-frame]');
  const link = feature.querySelector('[data-art-link]');
  applyArtworkFrame(frame, work);
  link.href = work.page;
  link.setAttribute('aria-label', `Read about ${work.title} in the Art Journal`);
  feature.querySelector('#language-art-title').textContent = work.title;
}
