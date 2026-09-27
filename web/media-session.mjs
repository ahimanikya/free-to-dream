// Optional OS/lock-screen controls; unsupported browsers retain normal playback.
export function setupMediaSession(win, player, controls) {
  const session = win?.navigator?.mediaSession;
  if (!session) return null;
  const handlers = {play:controls.play,pause:controls.pause,previoustrack:controls.previous,nexttrack:controls.next,stop:controls.stop,
    seekbackward:({seekOffset=10})=>{player.currentTime=Math.max(0,player.currentTime-seekOffset);},
    seekforward:({seekOffset=10})=>{if(Number.isFinite(player.duration))player.currentTime=Math.min(player.duration,player.currentTime+seekOffset);},
    seekto:({seekTime})=>{if(Number.isFinite(player.duration)&&Number.isFinite(seekTime))player.currentTime=Math.max(0,Math.min(player.duration,seekTime));}};
  for (const [name,handler] of Object.entries(handlers)) {try{session.setActionHandler(name,handler);}catch{}}
  const sync=()=>{try{session.playbackState=player.paused?'paused':'playing';
    if(Number.isFinite(player.duration)&&player.duration>0)session.setPositionState?.({duration:player.duration,playbackRate:player.playbackRate||1,position:Math.max(0,Math.min(player.duration,player.currentTime||0))});}catch{}};
  for(const name of ['timeupdate','loadedmetadata','seeked'])player.addEventListener(name,sync);
  return {sync,setTrack(track){try{if(win.MediaMetadata)session.metadata=new win.MediaMetadata({title:track.title,artist:'Ahimanikya Satapathy · '+track.language_name,album:'World is One — A Poem Without Borders',artwork:[{src:new URL('media/images/cover.png',win.location.href).href,type:'image/png'}]});}catch{}},
    clear(){try{session.metadata=null;session.playbackState='none';session.setPositionState?.();}catch{}}};
}
