export function cardsPerPage(viewport, cardWidth, gap, total) {
  return Math.max(1, Math.min(total, Math.floor((viewport + gap) / (cardWidth + gap))));
}

// Rotate only off-screen nodes, so each language and its play button exist once.
export function rebasePlan(position, viewport, step, total, pageSize) {
  const buffer = Math.min(Math.max(2, pageSize * 2), Math.floor(total / 3));
  if (!buffer) return 0;
  if (position < buffer * step / 2) return -buffer;
  if (position + viewport > (total - buffer / 2) * step) return buffer;
  return 0;
}

export function setupLanguageCarousel(doc = document) {
  const shelf = doc.querySelector('#featured-cards');
  if (!shelf) return;
  const previous = doc.querySelector('#cards-previous');
  const next = doc.querySelector('#cards-next');
  const status = doc.querySelector('#carousel-status');
  const total = shelf.children.length;
  if (!total) return;
  doc.querySelector('.card-scroll-controls').hidden = false;
  let timer, moving = false, rebasing = false, dragging = false;
  const metrics = () => {
    const width = shelf.firstElementChild.getBoundingClientRect().width;
    const gap = parseFloat(getComputedStyle(shelf).columnGap) || 0;
    return {step: width + gap, size: cardsPerPage(shelf.clientWidth, width, gap, total)};
  };
  function rotate(shift, step) {
    if (!shift) return;
    const nodes = [...shelf.children];
    const moved = shift > 0 ? nodes.slice(0, shift) : nodes.slice(shift);
    if (moved.some(node => node.contains(doc.activeElement))) return;
    const position = shelf.scrollLeft;
    rebasing = true;
    shelf.style.scrollSnapType = 'none';
    if (shift > 0) shelf.append(...moved); else shelf.prepend(...moved);
    shelf.scrollLeft = position - shift * step;
    requestAnimationFrame(() => {
      shelf.style.scrollSnapType = '';
      rebasing = false;
    });
  }
  function settle() {
    if (dragging || rebasing) return;
    moving = false;
    const {step, size} = metrics();
    rotate(rebasePlan(shelf.scrollLeft, shelf.clientWidth, step, total, size), step);
    const start = Math.round(shelf.scrollLeft / step);
    const names = [...shelf.children].slice(start, start + size).map(node => node.querySelector('h3').textContent);
    status.textContent = 'Showing ' + names.join(', ') + '.';
  }
  function schedule() {
    if (rebasing) return;
    clearTimeout(timer);
    timer = setTimeout(settle, 160);
  }
  function move(direction) {
    if (moving) return;
    const {step, size} = metrics();
    if (total <= size) return;
    moving = true;
    shelf.scrollBy({left: direction * size * step, behavior: matchMedia('(prefers-reduced-motion: reduce)').matches ? 'auto' : 'smooth'});
    schedule();
  }
  previous.addEventListener('click', () => move(-1));
  next.addEventListener('click', () => move(1));
  shelf.addEventListener('keydown', event => {
    if (event.target !== shelf || !['ArrowLeft','ArrowRight'].includes(event.key)) return;
    event.preventDefault();
    move(event.key === 'ArrowLeft' ? -1 : 1);
  });
  shelf.addEventListener('scroll', schedule, {passive:true});
  shelf.addEventListener('pointerdown', () => {dragging = true;}, {passive:true});
  for (const event of ['pointerup','pointercancel']) window.addEventListener(event, () => {dragging = false; schedule();}, {passive:true});
  window.addEventListener('resize', schedule);
  const {step, size} = metrics();
  const buffer = Math.min(Math.max(2, size * 2), Math.floor(total / 3));
  previous.disabled = next.disabled = total <= size;
  rotate(-buffer, step);
}
