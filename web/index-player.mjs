import {setupMediaSession} from './media-session.mjs';
import {lyricAt} from './lyrics.mjs';
// Current takes only: keep the published catalog order, including alternate styles.
export function playlistTracks(items) { return items.filter(item => !item.archived); }
export function adjacentTrack(items, id, direction = 1) {
  const queue = playlistTracks(items), position = queue.findIndex(item => item.id === id);
  return position < 0 ? null : queue[position + direction] || null;
}
export function shuffledTracks(items, currentId, random = Math.random) {
  const tracks = playlistTracks(items), current = tracks.find(t => t.id === currentId);
  const rest = tracks.filter(t => t !== current);
  for (let i = rest.length - 1; i > 0; i--) {
    const j = Math.floor(random() * (i + 1)); [rest[i], rest[j]] = [rest[j], rest[i]];
  }
  return current ? [current, ...rest] : rest;
}
export function nextInQueue(queue, id, direction = 1, repeat = 'off', automatic = false) {
  const index = queue.findIndex(t => t.id === id);
  if (index < 0) return null;
  if (automatic && repeat === 'one') return queue[index];
  const next = queue[index + direction];
  return next || (repeat === 'all' ? queue[(index + direction + queue.length) % queue.length] : null);
}
export function playbackTime(seconds) {
  if (!Number.isFinite(seconds) || seconds < 0) return '0:00';
  return Math.floor(seconds / 60) + ':' + String(Math.floor(seconds % 60)).padStart(2, '0');
}
export function setupIndexPlayer(doc = document, load = () => fetch('assets/listening.json', {cache: 'no-cache'}).then(r => {
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
  const shuffle = doc.querySelector('#index-shuffle'), repeat = doc.querySelector('#index-repeat');
  const queueToggle = doc.querySelector('#index-queue-toggle'), queuePanel = doc.querySelector('#index-queue');
  const queueList = doc.querySelector('#index-queue-list'), queueMode = doc.querySelector('#index-queue-mode');
  const lyricsToggle = doc.querySelector('#index-lyrics-toggle'), fullLyrics = doc.querySelector('#index-full-lyrics');
  const lyricsText = doc.querySelector('#index-lyrics-text'), lyricsNote = doc.querySelector('#index-lyrics-note');
  const share = doc.querySelector('#index-share');
  let order = [], shuffleOn = false, repeatMode = 'off', launchButton = null;
  const nextTrack = (direction = 1, automatic = false) => current && nextInQueue(order, current.id, direction, repeatMode, automatic);
  const buttons = [...doc.querySelectorAll('[data-play-recording]')];
  const labels = new Map(buttons.map(b => [b, b.getAttribute('aria-label').replace(/^Play /, '')]));
  let items = [], cues = [], current = null, request = 0, intent = 0, continuePlayback = false, stopped = false, lastVolume = 1;
  const ready = load().then(data => {
    items = data; order = playlistTracks(items);
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
    const at = order.findIndex(item => item.id === current?.id);
    position.textContent = at >= 0 ? 'Track ' + (at + 1) + ' of ' + order.length : current ? 'Earlier version' : '';
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
    previous.disabled = !current;
    next.disabled = !current || !nextTrack();
    mediaSession?.sync();
  };
  function renderQueue() {
    if (!queueList) return;
    queueList.replaceChildren();
    const at = current ? order.findIndex(t => t.id === current.id) : -1;
    let upcoming = order.slice(at + 1);
    if (repeatMode === 'all' && at >= 0) upcoming = [...upcoming, ...order.slice(0, at + 1)];
    if (repeatMode === 'one' && current) upcoming = [current];
    queueMode.textContent = repeatMode === 'one' ? 'Repeating this track' : shuffleOn ? 'Shuffled · a new path through the collection' : 'In collection order';
    for (const take of upcoming) {
      const row = doc.createElement('li'), button = doc.createElement('button');
      button.type = 'button'; button.textContent = take.language_name + ' · ' + take.title;
      button.addEventListener('click', () => { ++intent; start(take); });
      row.append(button); queueList.append(row);
    }
    if (!upcoming.length) { const row = doc.createElement('li'); row.textContent = 'End of the queue. Turn on Repeat all to keep listening.'; queueList.append(row); }
  }
  function toggleDrawer(which) {
    const show = which.hidden;
    if (queuePanel) queuePanel.hidden = true;
    if (fullLyrics) fullLyrics.hidden = true;
    which.hidden = !show;
    queueToggle?.setAttribute('aria-expanded', String(!queuePanel.hidden));
    lyricsToggle?.setAttribute('aria-expanded', String(!fullLyrics.hidden));
  }
  queueToggle?.addEventListener('click', () => {renderQueue(); toggleDrawer(queuePanel);});
  lyricsToggle?.addEventListener('click', () => toggleDrawer(fullLyrics));
  shuffle?.addEventListener('click', () => {
    shuffleOn = !shuffleOn; order = shuffleOn ? shuffledTracks(items, current?.id) : playlistTracks(items);
    shuffle.setAttribute('aria-pressed',String(shuffleOn)); shuffle.setAttribute('aria-label','Shuffle '+(shuffleOn?'on':'off'));
    renderQueue(); sync();
  });
  repeat?.addEventListener('click', () => {
    repeatMode = ['off','all','one'][(['off','all','one'].indexOf(repeatMode)+1)%3];
    repeat.setAttribute('aria-pressed', String(repeatMode !== 'off')); repeat.setAttribute('aria-label','Repeat '+repeatMode); repeat.title='Repeat '+repeatMode;
    const one = doc.querySelector('#index-repeat-one'); if (one) one.hidden = repeatMode !== 'one';
    renderQueue(); sync();
  });
  share?.addEventListener('click', async () => {
    if (!current || !doc.body.dataset.siteUrl) return;
    const url = new URL(current.page, doc.body.dataset.siteUrl.replace(/\/$/,'')+'/').href;
    const nav = doc.defaultView?.navigator;
    doc.dispatchEvent?.(new CustomEvent('collection-engagement',{detail:{name:'share_intent',params:{recording_id:current.id,language:current.language,method:nav?.share?'native':'copy_link'}}}));
    try {
      if (nav?.share) await nav.share({title:current.title, text:'I Am Free to Dream · '+current.language_name, url});
      else { await nav.clipboard.writeText(url); status.textContent='Track link copied.'; }
    } catch (error) { if(error.name!=='AbortError') status.textContent='Open Details to copy or share this track’s link.'; }
  });
  async function start(item) {
    const token = ++request;
    current = item; continuePlayback = true; stopped = false; panel.hidden = false; doc.body.classList.add('has-index-player');
    link.href = item.page;
    lyricsLink.href = item.lyric_page || 'poems--i-am-free-to-dream--languages--' + item.language + '.html#poem-text';
    lyricsLink.textContent = 'Read lyrics';
    cues = []; lyric.textContent = ''; lyric.hidden = true;
    for (const picker of pickers) picker.value = item.id;
    player.dataset.playbackToken = String(token); player.dataset.recordingId = item.id; player.dataset.language = item.language;
    player.src = item.url; status.textContent = '';
    if (lyricsText) lyricsText.textContent = (item.draft || '').replace(/^\s*\[[^\]\n]+\]\s*$/gm,'').trim();
    if (lyricsNote) lyricsNote.textContent = item.draft ? 'Draft lyrics · wording may differ slightly from this recording.' : 'Lyrics aren’t available yet. You can still read the poem.';
    renderQueue(); mediaSession?.setTrack(item);
    seek.style.setProperty('--progress', '0%');
    seek.value = '0'; seek.max = '0'; seek.disabled = true;
    elapsed.textContent = '0:00'; duration.textContent = playbackTime(item.duration_seconds || 0);
    sync(); prepareLyrics(item, token);
    try { await player.play(); }
    catch { if (token === request && continuePlayback) status.textContent = 'Press play to continue listening.'; }
    if (token === request) sync();
  }
  for (const button of buttons) button.addEventListener('click', async () => {
    launchButton = button;
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
    const item = nextTrack(direction);
    if (item) { ++intent; start(item); }
  };
  toggle.addEventListener('click', async () => {
    if (!current) return;
    const token = request;
    if (!player.paused) { continuePlayback = false; player.pause(); }
    else {
      continuePlayback = true; stopped = false;
      try { await player.play(); if (token === request) status.textContent = ''; }
      catch { if (token === request && continuePlayback) status.textContent = 'Could not play this track. Try Next or open Details.'; }
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
  previous.addEventListener('click', () => { if(player.currentTime > 3) {player.currentTime=0;updateTimeline();} else advance(-1); });
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
    const upcoming = nextTrack(1, true);
    if (upcoming) { ++intent; start(upcoming); }
    else { continuePlayback = false; status.textContent = 'You’ve reached the end of this listening journey.'; }
  });
  doc.querySelector('#index-close').addEventListener('click', () => {
    ++intent; ++request; continuePlayback = false; stopped = false; current = null; cues = []; lyric.textContent = ''; lyric.hidden = true;
    player.pause(); player.removeAttribute('src'); player.load();
    mediaSession?.clear();
    panel.hidden = true; for (const picker of pickers) picker.value = ''; sync(); doc.body.classList.remove('has-index-player');
    launchButton?.focus?.();
  });
  for (const event of ['play', 'pause', 'ended']) player.addEventListener(event, sync);
  player.addEventListener('error', () => {
    if (current) status.textContent = 'This recording could not load. Use Next or open its page.';
  });
  const mediaSession = setupMediaSession(doc.defaultView, player, {play:()=>{if(player.paused)toggle.click();}, pause:()=>{continuePlayback=false;player.pause();}, previous:()=>advance(-1), next:()=>advance(1), stop:()=>stop.click()});
  doc.addEventListener?.('keydown', event => {
    if (panel.hidden || !current || event.altKey || event.ctrlKey || event.metaKey || event.target?.closest?.('input,textarea,select,button,a,[contenteditable]')) return;
    if (event.code === 'Space') { event.preventDefault(); toggle.click(); }
    if (event.key?.toLowerCase() === 'm') mute.click();
  });
  sync();
  return {ready};
}
