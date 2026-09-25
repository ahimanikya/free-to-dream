import {lyricAt} from './lyrics.mjs';
// Current takes only: keep the published catalog order, including alternate styles.
export function playlistTracks(items) { return items.filter(item => !item.archived); }
export function adjacentTrack(items, id, direction = 1) {
  const queue = playlistTracks(items), position = queue.findIndex(item => item.id === id);
  return position < 0 ? null : queue[position + direction] || null;
}
export function playbackTime(seconds) {
  if (!Number.isFinite(seconds) || seconds < 0) return '0:00';
  return Math.floor(seconds / 60) + ':' + String(Math.floor(seconds % 60)).padStart(2, '0');
}
export function setupIndexPlayer(doc = document, load = () => fetch('assets/listening.json').then(r => {
  if (!r.ok) throw Error('Could not load recordings');
  return r.json();
}), loadLyrics = url => fetch(url).then(response => {
  if (!response.ok) throw Error('Lyrics unavailable');
  return response.json();
})) {
  const panel = doc.querySelector('#index-player');
  if (!panel) return;
  const player = doc.querySelector('#index-audio');
  const pickers = [...doc.querySelectorAll('[data-playlist]')];
  const link = doc.querySelector('#index-track-link');
  const status = doc.querySelector('#index-play-status');
  const toggle = doc.querySelector('#index-toggle');
  const playIcon = doc.querySelector('#index-play-icon');
  const pauseIcon = doc.querySelector('#index-pause-icon');
  const seek = doc.querySelector('#index-seek');
  const elapsed = doc.querySelector('#index-elapsed');
  const duration = doc.querySelector('#index-duration');
  const mute = doc.querySelector('#index-mute');
  const lyricsLink = doc.querySelector('#index-lyrics-link');
  const lyric = doc.querySelector('#index-lyric');
  const previous = doc.querySelector('#index-previous');
  const next = doc.querySelector('#index-next');
  const stop = doc.querySelector('#index-stop');
  const volume = doc.querySelector('#index-volume');
  const state = doc.querySelector('#index-state');
  const position = doc.querySelector('#index-position');
  const buttons = [...doc.querySelectorAll('[data-play-recording]')];
  const labels = new Map(buttons.map(b => [b, b.getAttribute('aria-label').replace(/^Play /, '')]));
  let items = [], cues = [], current = null, request = 0, intent = 0, continuePlayback = false, stopped = false, lastVolume = 1;
  const ready = load().then(data => {
    items = data;
    for (const picker of pickers) {
      picker.replaceChildren();
      const placeholder = doc.createElement('option');
      placeholder.value = ''; placeholder.disabled = true; placeholder.textContent = 'Choose a track…'; picker.append(placeholder);
      for (const take of playlistTracks(items)) {
        const option = doc.createElement('option'); option.value = take.id;
        const title = take.language === 'english' ? take.title.replace(/^I Am Free to Dream\s*[-–—]\s*/, '') : take.title;
        option.textContent = take.language_name + ' · ' + title;
        picker.append(option);
      }
      picker.value = '';
    }
  });
  ready.catch(() => {});
  function updateTimeline() {
    const length = Number.isFinite(player.duration) && player.duration > 0 ? player.duration : 0;
    const time = Number.isFinite(player.currentTime) ? player.currentTime : 0;
    elapsed.textContent = playbackTime(time);
    duration.textContent = playbackTime(length || current?.duration_seconds || 0);
    seek.disabled = !length;
    seek.max = String(length);
    seek.value = String(Math.min(time, length));
    seek.style.setProperty('--progress', (length ? Math.min(time / length, 1) * 100 : 0) + '%');
    seek.setAttribute('aria-valuetext', playbackTime(time) + ' of ' + duration.textContent);
    lyric.textContent = player.ended ? '' : lyricAt(cues, time);
    lyric.hidden = !cues.length;
  }
  async function prepareLyrics(item, token) {
    if (!item.lyrics_url) return;
    try {
      const loaded = await loadLyrics(item.lyrics_url);
      if (token !== request) return;
      if (!Array.isArray(loaded) || !loaded.every(c => Number.isFinite(c.start) && Number.isFinite(c.end) && c.end > c.start && typeof c.text === 'string')) return;
      cues = loaded; updateTimeline();
    } catch { /* The song and Read lyrics link remain available. */ }
  }
  const sync = () => {
    const playing = Boolean(current && !player.paused && !player.ended);
    toggle.disabled = stop.disabled = !current;
    panel.classList.toggle('is-playing', playing);
    state.textContent = !current ? 'READY' : stopped ? 'STOPPED' : playing ? 'PLAYING' : player.ended ? 'FINISHED' : 'PAUSED';
    toggle.setAttribute('aria-label', playing ? 'Pause' : 'Play');
    toggle.setAttribute('title', playing ? 'Pause' : 'Play');
    if (playing) { playIcon.setAttribute('hidden', ''); pauseIcon.removeAttribute('hidden'); }
    else { playIcon.removeAttribute('hidden'); pauseIcon.setAttribute('hidden', ''); }
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
    current = item; continuePlayback = true; stopped = false; panel.hidden = false; doc.body.classList.add('has-index-player');
    link.href = item.page;
    lyricsLink.href = item.lyric_page || 'poems--i-am-free-to-dream--languages--' + item.language + '.html#poem-text';
    lyricsLink.textContent = 'Read lyrics';
    cues = []; lyric.textContent = ''; lyric.hidden = true;
    for (const picker of pickers) picker.value = item.id;
    const queue = playlistTracks(items), at = queue.findIndex(x => x.id === item.id);
    position.textContent = at >= 0 ? 'Track ' + (at + 1) + ' of ' + queue.length : 'Earlier version';
    player.src = item.url; status.textContent = '';
    seek.style.setProperty('--progress', '0%');
    seek.value = '0'; seek.max = '0'; seek.disabled = true;
    elapsed.textContent = '0:00'; duration.textContent = playbackTime(item.duration_seconds || 0);
    sync(); prepareLyrics(item, token);
    try { await player.play(); }
    catch { if (token === request && continuePlayback) status.textContent = 'Press play to continue listening.'; }
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
        if (player.paused) { continuePlayback = true; stopped = false; await player.play(); } else { continuePlayback = false; player.pause(); }
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
  toggle.addEventListener('click', async () => {
    if (!current) return;
    const token = request;
    if (!player.paused) { continuePlayback = false; player.pause(); }
    else {
      continuePlayback = true; stopped = false;
      try { await player.play(); if (token === request) status.textContent = ''; }
      catch { if (token === request && continuePlayback) status.textContent = 'Could not play this track. Try Next or open Track details.'; }
    }
    sync();
  });
  stop.addEventListener('click', () => {
    ++intent; continuePlayback = false; stopped = true;
    player.pause();
    if (current) player.currentTime = 0;
    status.textContent = '';
    updateTimeline(); sync();
  });
  seek.addEventListener('input', () => {
    const value = Number(seek.value);
    if (Number.isFinite(player.duration) && player.duration > 0 && Number.isFinite(value)) {
      player.currentTime = Math.max(0, Math.min(value, player.duration));
      updateTimeline();
    }
  });
  function syncMute() {
    if (player.volume > 0) lastVolume = player.volume;
    mute.setAttribute('aria-label', player.muted ? 'Unmute' : 'Mute');
    mute.setAttribute('title', player.muted ? 'Unmute' : 'Mute');
    mute.setAttribute('aria-pressed', String(Boolean(player.muted)));
    mute.classList.toggle('is-muted', Boolean(player.muted));
    volume.value = String(player.muted ? 0 : player.volume);
    volume.style.setProperty('--progress', (player.muted ? 0 : player.volume * 100) + '%');
  }
  volume.addEventListener('input', () => {
    const value = Number(volume.value);
    if (!Number.isFinite(value)) return;
    player.volume = Math.max(0, Math.min(1, value)); player.muted = player.volume === 0;
    syncMute();
  });
  mute.addEventListener('click', () => {
    if (player.muted || player.volume === 0) {
      player.muted = false;
      if (player.volume === 0) player.volume = lastVolume;
    } else player.muted = true;
    syncMute();
  });
  player.addEventListener('volumechange', syncMute);
  for (const event of ['timeupdate','loadedmetadata','durationchange','seeking','seeked','ended']) player.addEventListener(event, updateTimeline);
  previous.addEventListener('click', () => advance(-1));
  next.addEventListener('click', () => advance(1));
  for (const picker of pickers) picker.addEventListener('change', () => {
    const item = playlistTracks(items).find(x => x.id === picker.value);
    if (item) {
      ++intent; start(item);
      if (picker !== doc.querySelector('#index-playlist')) doc.querySelector('#index-playlist').focus?.({preventScroll:true});
    }
  });
  player.addEventListener('ended', () => {
    if (!continuePlayback || !current) return;
    if (adjacentTrack(items, current.id)) advance(1);
    else { continuePlayback = false; status.textContent = 'You’ve reached the end of this listening journey.'; }
  });
  doc.querySelector('#index-close').addEventListener('click', () => {
    ++intent; ++request; continuePlayback = false; stopped = false; current = null; cues = []; lyric.textContent = ''; lyric.hidden = true;
    player.pause(); player.removeAttribute('src'); player.load();
    panel.hidden = true; for (const picker of pickers) picker.value = ''; sync(); doc.body.classList.remove('has-index-player');
  });
  for (const event of ['play', 'pause', 'ended']) player.addEventListener(event, sync);
  player.addEventListener('error', () => {
    if (current) status.textContent = 'This recording could not load. Use Next or open its page.';
  });
  sync();
  return {ready};
}
