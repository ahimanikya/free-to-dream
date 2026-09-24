// Timings are milliseconds from the exact audio take, never a separate timer.
export function lyricAt(cues, seconds) {
  const ms = seconds * 1000;
  return cues.find(cue => cue.start <= ms && ms < cue.end)?.text ?? '';
}

export async function attachLyrics(container) {
  const player = container.querySelector('audio');
  const display = container.querySelector('.current-lyric');
  try {
    const response = await fetch(container.dataset.lyricsUrl);
    if (!response.ok) throw new Error('Lyrics unavailable');
    const cues = await response.json();
    const update = () => {
      display.textContent = player.ended ? '' : lyricAt(cues, player.currentTime);
    };
    for (const event of ['timeupdate', 'seeking', 'seeked', 'loadedmetadata', 'ended', 'play']) {
      player.addEventListener(event, update);
    }
    update();
  } catch {
    display.textContent = 'Timed lyrics could not load. You can still play the song or download its SRT.';
  }
}
