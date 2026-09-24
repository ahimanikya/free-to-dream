export async function setupIndexPlayer(doc = document) {
  const panel = doc.querySelector('#index-player');
  if (!panel) return;
  const player = doc.querySelector('#index-audio');
  const version = doc.querySelector('#index-version');
  const link = doc.querySelector('#index-track-link');
  const status = doc.querySelector('#index-play-status');
  const buttons = [...doc.querySelectorAll('[data-play-recording]')];
  const labels=new Map(buttons.map(b=>[b,b.getAttribute('aria-label').replace(/^Play /,'')]));
  let items = [], current = null, request = 0;
  const ready = fetch('assets/listening.json').then(r=>{if(!r.ok)throw Error();return r.json();}).then(data=>items=data);
  ready.catch(()=>{});
  const sync = () => {
    for (const button of buttons) {
      const active = items.find(x=>x.id===button.dataset.playRecording)?.language===current?.language && !player.paused;
      button.setAttribute('aria-pressed',String(Boolean(active)));
      button.setAttribute('aria-label',(active?'Pause ':'Play ')+labels.get(button));
      button.querySelector('.play-label').textContent=active?'Ⅱ Pause':'▶ Play';
      button.classList.toggle('is-playing',Boolean(active));
    }
  };
  async function start(item) {
    current = item; panel.hidden=false; doc.body.classList.add('has-index-player');
    link.textContent=item.title; link.href=item.page;
    player.src=item.url; status.textContent='';
    const token=++request;
    try { await player.play(); }
    catch {if(token===request)status.textContent='Press play below to listen. If playback fails, open the recording page.';}
    sync();
  }
  for (const button of buttons) button.addEventListener('click',async()=>{
    try {
      await ready;
      const item=items.find(x=>x.id===button.dataset.playRecording);
      if(!item)throw Error();
      if(current?.language===item.language) {
        if(player.paused) {await player.play();} else {player.pause();}
        sync();return;
      }
      version.replaceChildren();
      for(const take of items.filter(x=>x.language===item.language&&!x.archived)) {
        const option=doc.createElement('option');option.value=take.id;option.textContent=take.title;version.append(option);
      }
      version.value=item.id;version.parentElement.hidden=version.options.length<2;
      await start(item);
    } catch {panel.hidden=false;doc.body.classList.add('has-index-player');status.textContent='Could not start playback. Open the language page to listen.';}
  });
  version.addEventListener('change',()=>{const item=items.find(x=>x.id===version.value);if(item)start(item);});
  doc.querySelector('#index-close').addEventListener('click',()=>{
    ++request;player.pause();player.removeAttribute('src');player.load();panel.hidden=true;current=null;sync();doc.body.classList.remove('has-index-player');
  });
  for(const event of ['play','pause','ended'])player.addEventListener(event,sync);
  player.addEventListener('error',()=>{if(current)status.textContent='This recording could not load. Open its page for download options.';});
}
