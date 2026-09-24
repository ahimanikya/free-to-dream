// Current takes only: keep the published catalog order, including alternate styles.
export function playlistTracks(items) { return items.filter(item => !item.archived); }
export function adjacentTrack(items, id, direction = 1) {
  const queue = playlistTracks(items), position = queue.findIndex(item => item.id === id);
  return position < 0 ? null : queue[position + direction] || null;
}
export function setupIndexPlayer(doc = document, load = () => fetch('assets/listening.json').then(r => {
  if (!r.ok) throw Error('Could not load recordings');
  return r.json();
})) {
  const panel = doc.querySelector('#index-player');
  if (!panel) return;
  const player = doc.querySelector('#index-audio');
  const version = doc.querySelector('#index-version');
  const link = doc.querySelector('#index-track-link');
  const status = doc.querySelector('#index-play-status');
  const previous = doc.querySelector('#index-previous');
  const next = doc.querySelector('#index-next');
  const auto = doc.querySelector('#index-auto');
  const position = doc.querySelector('#index-position');
  const buttons = [...doc.querySelectorAll('[data-play-recording]')];
  const labels = new Map(buttons.map(b => [b, b.getAttribute('aria-label').replace(/^Play /, '')]));
  let items = [], current = null, request = 0, intent = 0;
  const ready = load().then(data => { items = data; });
  ready.catch(() => {});
  const sync = () => {
    for (const button of buttons) {
      const item = items.find(x => x.id === button.dataset.playRecording);
      const matches = button.classList.contains('card-play') ? item?.language === current?.language : item?.id === current?.id;
      const active = Boolean(current && matches && !player.paused);
      button.setAttribute('aria-pressed', String(active));
      button.setAttribute('aria-label', (active ? 'Pause ' : 'Play ') + labels.get(button));
      button.querySelector('.play-label').textContent = active ? 'Ⅱ Pause' : '▶ Play';
      button.classList.toggle('is-playing', active);
    }
    previous.disabled = !current || !adjacentTrack(items, current.id, -1);
    next.disabled = !current || !adjacentTrack(items, current.id);
  };
  async function start(item) {
    const token = ++request;
    current = item; panel.hidden = false; doc.body.classList.add('has-index-player');
    link.textContent = item.language_name + ' · ' + item.title; link.href = item.page;
    version.replaceChildren();
    for (const take of playlistTracks(items).filter(x => x.language === item.language)) {
      const option = doc.createElement('option'); option.value = take.id; option.textContent = take.title; version.append(option);
    }
    version.value = item.id; version.parentElement.hidden = version.options.length < 2;
    const queue = playlistTracks(items), at = queue.findIndex(x => x.id === item.id);
    position.textContent = at >= 0 ? 'Track ' + (at + 1) + ' of ' + queue.length : 'Earlier version';
    player.src = item.url; status.textContent = ''; sync();
    try { await player.play(); }
    catch { if (token === request) status.textContent = 'Press play to continue listening.'; }
    if (token === request) sync();
  }
  for (const button of buttons) button.addEventListener('click', async () => {
    const turn = ++intent;
    try {
      await ready;
      if (turn !== intent) return;
      const item = items.find(x => x.id === button.dataset.playRecording);
      if (!item) throw Error();
      const same = button.classList.contains('card-play') ? current?.language === item.language : current?.id === item.id;
      if (same) {
        if (player.paused) await player.play(); else player.pause();
        sync(); return;
      }
      await start(item);
    } catch {
      if (turn === intent) {
        panel.hidden = false; doc.body.classList.add('has-index-player');
        status.textContent = 'Could not start playback. Open the language page to listen.';
      }
    }
  });
  const advance = direction => {
    const item = current && adjacentTrack(items, current.id, direction);
    if (item) { ++intent; start(item); }
  };
  previous.addEventListener('click', () => advance(-1));
  next.addEventListener('click', () => advance(1));
  version.addEventListener('change', () => {
    const item = items.find(x => x.id === version.value);
    if (item) { ++intent; start(item); }
  });
  player.addEventListener('ended', () => {
    if (!auto.checked || !current) return;
    if (adjacentTrack(items, current.id)) advance(1);
    else status.textContent = 'You’ve reached the end of this listening journey.';
  });
  doc.querySelector('#index-close').addEventListener('click', () => {
    ++intent; ++request; current = null;
    player.pause(); player.removeAttribute('src'); player.load();
    panel.hidden = true; auto.checked = false; sync(); doc.body.classList.remove('has-index-player');
  });
  for (const event of ['play', 'pause', 'ended']) player.addEventListener(event, sync);
  player.addEventListener('error', () => {
    if (current) status.textContent = 'This recording could not load. Use Next or open its page.';
  });
  sync();
  return {ready};
}
