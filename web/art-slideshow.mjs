import {applyArtworkFrame} from './language-art.mjs';

export function slideIndex(index, direction, total) {
  return total > 0 ? ((index + direction) % total + total) % total : 0;
}
export function slideshowPlaylist(items) {
  const seen = new Set();
  return items.filter(item => {
    if (item.archived || !item.url || seen.has(item.url)) return false;
    seen.add(item.url);
    return true;
  }).sort((a,b) => Number(b.language === 'odia') - Number(a.language === 'odia'));
}
export function setupArtSlideshow(doc = document, win = window) {
  const launch = doc.querySelector('#art-slideshow-start');
  const dialog = doc.querySelector('#art-slideshow');
  const cards = [...doc.querySelectorAll('#art-collection .portfolio-card')];
  const languageMode = dialog?.dataset.slideshowMode === 'language';
  if (languageMode) {
    const feature = doc.querySelector('[data-language-art]');
    try {
      const choices = JSON.parse(feature.querySelector('[data-art-choices]').textContent);
      const template = feature.querySelector('.art-frame');
      for (const work of choices) {
        const card = doc.createElement('div');
        const frame = template.cloneNode(true);
        applyArtworkFrame(frame, work);
        card.append(frame);
        cards.push(card);
      }
    } catch { /* Keep the sidebar artwork available if its catalog is missing. */ }
  }
  if (!launch || !dialog || !cards.length || typeof dialog.showModal !== 'function') return;
  const stage = doc.querySelector('#slideshow-stage');
  const audio = doc.querySelector('#slideshow-audio');
  const status = doc.querySelector('#slideshow-status');
  const toggle = doc.querySelector('#slideshow-toggle');
  let running = false;
  let index = 0, timer, revision = 0, session = 0, track = null, playlist = [], trackIndex = 0;
  const failedTracks = new Set();
  let pendingStart = 0;
  audio.loop = languageMode;
  for (const id of ['slideshow-prev', 'slideshow-next']) doc.getElementById(id).hidden = languageMode;
  audio.addEventListener('loadedmetadata', () => {
    if (pendingStart > 0) {
      audio.currentTime = Math.min(pendingStart, Number.isFinite(audio.duration) ? audio.duration : pendingStart);
      pendingStart = 0;
    }
  });
  function updateToggle() {
    const label = running ? 'Pause slideshow' : 'Resume slideshow';
    toggle.setAttribute('aria-label', label);
    toggle.title = label;
    stage.setAttribute('aria-label', running ? 'Artwork: click to pause slideshow' : 'Artwork: click to resume slideshow');
    stage.title = running ? 'Click to pause' : 'Click to resume';
    toggle.querySelector('path').setAttribute('d', running ? 'M6 5h4v14H6zM14 5h4v14h-4z' : 'M7 4 20 12 7 20z');
  }
  const ready = languageMode ? Promise.resolve() : fetch('assets/listening.json').then(response => {
    if (!response.ok) throw Error('Music catalog unavailable');
    return response.json();
  }).then(items => {
    playlist = slideshowPlaylist(items);
    setTrack(0);
  }).catch(() => {});
  function setTrack(next) {
    if (!playlist.length) return;
    trackIndex = slideIndex(next, 0, playlist.length);
    track = playlist[trackIndex];
    audio.dataset.recordingId = track.id;
    audio.dataset.language = track.language;
    audio.src = track.url;
    audio.title = `${track.title} · ${track.language}`;
  }
  async function changeTrack(direction) {
    const request = ++session;
    await ready;
    if (!dialog.open || request !== session || !playlist.length) return;
    setTrack(trackIndex + direction);
    status.textContent = '';
    if (running) playMusic(request);
  }
  function schedule() {
    win.clearTimeout(timer);
    if (dialog.open && running && !doc.hidden)
      timer = win.setTimeout(() => show(index + 1), 8000);
  }
  async function show(next) {
    win.clearTimeout(timer);
    const request = ++revision;
    index = slideIndex(next, 0, cards.length);
    const frame = cards[index].querySelector('.art-frame').cloneNode(true);
    for (const node of frame.querySelectorAll('[id]')) node.removeAttribute('id');
    const img = frame.querySelector('img');
    img.loading = 'eager';
    stage.setAttribute('aria-busy', 'true');
    try { await img.decode(); }
    catch { /* Retain the alt text and continue if an image fails. */ }
    if (request !== revision || !dialog.open) return;
    stage.replaceChildren(frame);
    stage.setAttribute('aria-busy', 'false');
    schedule();
  }
  async function playMusic(request) {
    await ready;
    if (!dialog.open || !running || request !== session) return;
    if (!track) { status.textContent = 'Music is unavailable. The slideshow will continue.'; return; }
    try { await audio.play(); }
    catch {
      if (dialog.open && request === session)
        status.textContent = 'Music could not start. Stop and start the slideshow to try again.';
    }
  }
  function stop() {
    running = false; updateToggle();
    ++session; ++revision; win.clearTimeout(timer);
    audio.pause(); audio.currentTime = 0; pendingStart = 0;
    doc.body.classList.remove('art-slideshow-open');
  }
  launch.hidden = false;
  launch.addEventListener('click', () => {
    if (languageMode) {
      const sources = [...doc.querySelectorAll('.language-sidebar audio[data-recording-id]')];
      const source = sources.find(player => !player.paused)
        || sources.find(player => !player.closest('[hidden]') && !player.closest('details:not([open])'));
      if (!source) return;
      playlist = [{id:source.dataset.recordingId, language:source.dataset.language,
        title:source.getAttribute('aria-label') || 'Current song', url:source.currentSrc || source.src}];
      pendingStart = source.currentTime || 0;
      audio.volume = source.volume;
      audio.muted = source.muted;
      updateVolume();
    }
    for (const player of doc.querySelectorAll('audio,video')) if (player !== audio) player.pause();
    status.textContent = '';
    running = true; updateToggle();
    stage.replaceChildren();
    dialog.showModal();
    doc.body.classList.add('art-slideshow-open');
    failedTracks.clear();
    setTrack(0);
    show(0); playMusic(++session);
  });
  function togglePlayback() {
    running = !running;
    updateToggle();
    ++session;
    if (running) { status.textContent = ''; schedule(); playMusic(session); }
    else { win.clearTimeout(timer); audio.pause(); }
  }
  toggle.addEventListener('click', togglePlayback);
  stage.setAttribute('role', 'button');
  stage.tabIndex = 0;
  stage.addEventListener('click', togglePlayback);
  stage.addEventListener('keydown', event => {
    if ((event.key === 'Enter' || event.key === ' ') && !event.repeat) {
      event.preventDefault();
      togglePlayback();
    }
  });
  const volume = doc.querySelector('#slideshow-volume');
  const mute = doc.querySelector('#slideshow-mute');
  let previousVolume = 1;
  function updateVolume() {
    const silent = audio.muted || audio.volume === 0;
    volume.value = Math.round((audio.muted ? 0 : audio.volume) * 100);
    volume.setAttribute('aria-valuetext', `${volume.value}%`);
    mute.setAttribute('aria-label', silent ? 'Unmute music' : 'Mute music');
    mute.title = silent ? 'Unmute music' : 'Mute music';
    mute.querySelector('.volume-waves').setAttribute('d', silent ? 'm16 9 6 6m0-6-6 6' : 'M16 8a6 6 0 0 1 0 8M19 5a10 10 0 0 1 0 14');
  }
  volume.addEventListener('input', () => {
    audio.volume = Number(volume.value) / 100;
    audio.muted = false;
    if (audio.volume > 0) previousVolume = audio.volume;
    updateVolume();
  });
  mute.addEventListener('click', () => {
    if (audio.muted || audio.volume === 0) {
      audio.muted = false;
      if (audio.volume === 0) audio.volume = previousVolume;
    } else audio.muted = true;
    updateVolume();
  });
  audio.addEventListener('volumechange', updateVolume);
  updateVolume();
  doc.querySelector('#slideshow-art-prev').addEventListener('click', () => show(index - 1));
  doc.querySelector('#slideshow-art-next').addEventListener('click', () => show(index + 1));
  doc.querySelector('#slideshow-prev').addEventListener('click', () => changeTrack(-1));
  doc.querySelector('#slideshow-next').addEventListener('click', () => changeTrack(1));
  audio.addEventListener('ended', () => { if (dialog.open) changeTrack(1); });
  audio.addEventListener('playing', () => failedTracks.clear());
  doc.querySelector('#slideshow-close').addEventListener('click', () => dialog.close());
  dialog.addEventListener('close', () => { stop(); launch.focus({preventScroll:true}); });
  doc.addEventListener('visibilitychange', () => { if (doc.hidden) win.clearTimeout(timer); else schedule(); });
  win.addEventListener('pagehide', stop);
  audio.addEventListener('error', () => {
    if (!dialog.open || !running || !track) return;
    failedTracks.add(track.id || track.url);
    if (failedTracks.size < playlist.length) changeTrack(1);
    else status.textContent = 'Music is unavailable. The slideshow will continue.';
  });
}
