import {attachLyrics} from './lyrics.mjs';
import {buildProposal, githubSubmission, publicMediaURL} from './collaboration.mjs';

const search = document.querySelector('#search');
const filter = document.querySelector('#filter');
const cards = [...document.querySelectorAll('.language-card')];
function update() {
  const query = search.value.normalize('NFKC').toLocaleLowerCase().trim();
  let count = 0;
  for (const card of cards) {
    const match = card.dataset.search.normalize('NFKC').toLocaleLowerCase().includes(query);
    const status = filter.value === 'all' || (filter.value === 'listen' ? card.dataset.listen === 'true' : card.dataset.status === filter.value);
    card.hidden = !(match && status);
    if (!card.hidden) count++;
  }
  document.querySelector('#result-count').textContent = `${count} ${count === 1 ? 'language' : 'languages'}`;
  document.querySelector('#no-results').hidden = count > 0;
}
if (search && filter) {
  search.addEventListener('input', update);
  filter.addEventListener('change', update);
}
// Keep competing recordings from playing over one another.
document.addEventListener('play', event => {
  for (const player of document.querySelectorAll('audio, video')) {
    if (player !== event.target) player.pause();
  }
}, true);

const form = document.querySelector('#contribution-form');
if (form) {
  const language = document.querySelector('#contribution-language');
  const type = document.querySelector('#contribution-type');
  const params = new URLSearchParams(location.search);
  for (const [control,key] of [[language,'language'],[type,'type']]) {
    if ([...control.options].some(x=>x.value === params.get(key))) control.value=params.get(key);
  }
  const recordingId = params.get('recording');
  if (recordingId && /^[a-z0-9-]+$/.test(recordingId)) document.querySelector('#contribution-details').value=`Recording: ${recordingId}\nTimestamp(s): \n\n`;
  function showFields() {
    for (const [id,visible] of [['recording-fields',type.value==='recording'],['lyric-fields',type.value==='lyrics']]) {
      const panel=document.getElementById(id);
      panel.hidden=!visible;
      for (const field of panel.querySelectorAll('input,textarea')) field.disabled=!visible;
    }
    document.querySelector('#recording-credits').required=type.value==='recording';
    document.querySelector('#proposed-phrase').required=type.value==='lyrics';
  }
  showFields();
  type.addEventListener('change',showFields);
  const status=document.querySelector('#contribution-status');
  const proposalText=document.querySelector('#proposal-text');
  let currentProposal=null;
  // Invalidate the prepared handoff if the author changes their proposal.
  form.addEventListener('input',event=>{
    if (event.target.closest('#proposal-preview')) return;
    document.querySelector('#proposal-preview').hidden=true;
    document.querySelector('#recording-link').setCustomValidity('');
    event.target.setCustomValidity?.('');
    status.textContent='';
    currentProposal=null;
  });
  form.addEventListener('submit',event=>{
    event.preventDefault();
    const fields=Object.fromEntries(new FormData(form));
    for (const id of ['contribution-title','contribution-details']) {
      const input=document.getElementById(id);
      if (!input.value.trim()) {input.setCustomValidity('Please enter some text.');form.reportValidity();return;}
    }
    if (fields.recording_link && !publicMediaURL(fields.recording_link)) {
      document.querySelector('#recording-link').setCustomValidity('Use a public HTTPS link without a username or password.');
      form.reportValidity(); return;
    }
    fields.languageName=language.selectedOptions[0].textContent;
    currentProposal=buildProposal(fields);
    proposalText.value=`# ${currentProposal.title}\n\n${currentProposal.body}`;
    const handoff=githubSubmission(document.body.dataset.repository,currentProposal);
    const next=document.querySelector('#github-submit');
    next.hidden=!handoff.url;
    if (handoff.url) next.href=handoff.url; else next.removeAttribute('href');
    document.querySelector('#proposal-handoff').textContent=handoff.needsPaste
      ? 'This proposal is too long to place in a link. Copy the full proposal, continue on GitHub, and paste it into the submission box. No text has been shortened.'
      : handoff.url ? 'GitHub opens with these details filled in. Add any recording attachment there, then choose Submit new issue. Nothing has been submitted yet.'
      : 'The project owner needs to connect the GitHub repository before online submissions can open. You can copy or save your proposal now.';
    document.querySelector('#proposal-preview').hidden=false;
    status.textContent='Proposal prepared. Nothing has been submitted or uploaded.';
    document.querySelector('#proposal-preview').scrollIntoView({block:'start',behavior:'smooth'});
  });
  document.querySelector('#copy-proposal').addEventListener('click',async()=>{
    try {await navigator.clipboard.writeText(proposalText.value); status.textContent='Proposal copied. Paste it into GitHub when needed.';}
    catch {proposalText.focus();proposalText.select();status.textContent='Select and copy the proposal text below.';}
  });
  document.querySelector('#save-proposal').addEventListener('click',()=>{
    if (!currentProposal) return;
    const blob=new Blob([proposalText.value+'\n'],{type:'text/markdown;charset=utf-8'});
    const url=URL.createObjectURL(blob);
    const link=document.createElement('a');link.href=url;link.download=`${language.value}-proposal.md`;link.click();
    setTimeout(()=>URL.revokeObjectURL(url),1000);
    status.textContent='Proposal downloaded. It has not been submitted.';
  });
}

for (const panel of document.querySelectorAll('.sharing')) {
  const result=panel.querySelector('.share-result');
  const data=panel.dataset;
  let preparedFile=null, preparedURL=null;
  panel.addEventListener('click',async event=>{
    const button=event.target.closest('button[data-action]');
    if (!button || button.disabled) return;
    try {
      if (button.dataset.action==='copy-link' || button.dataset.action==='copy-caption') {
        const text=button.dataset.action==='copy-link' ? data.shareUrl : data.caption+(data.shareUrl?'\n'+data.shareUrl:'');
        if (!text) return;
        try {await navigator.clipboard.writeText(text);result.textContent=button.dataset.action==='copy-link'?'Link copied.':'Caption and credits copied.';}
        catch {result.textContent=`Copy this text: ${text}`;}
      } else if (button.dataset.action==='share-link') {
        if (!data.shareUrl) return;
        if (navigator.share) await navigator.share({title:data.shareTitle,text:data.caption,url:data.shareUrl});
        else {await navigator.clipboard.writeText(data.shareUrl);result.textContent='Link copied. Paste it into your social post or message.';}
      } else if (button.dataset.action==='prepare-file') {
        button.disabled=true;result.textContent='Preparing the media file…';
        // File fetches need host CORS permission. No credentials are sent.
        const response=await fetch(data.mediaUrl,{credentials:'omit'});
        if (!response.ok) throw new Error('The media host did not return the file.');
        const limit=150*1024*1024;
        if (Number(response.headers.get('Content-Length'))>limit) {
          await response.body?.cancel();throw new Error('This file is large. Use Download / open and share it from your device.');
        }
        const reader=response.body?.getReader();
        if (!reader) throw new Error('This browser cannot prepare the file. Use Download / open instead.');
        let size=0;const chunks=[];
        while (true) {
          const chunk=await reader.read();if (chunk.done) break;
          size+=chunk.value.byteLength;
          if (size>limit) {await reader.cancel();throw new Error('This file is large. Use Download / open and share it from your device.');}
          chunks.push(chunk.value);
        }
        const type=response.headers.get('Content-Type')?.split(';')[0];
        if (type==='text/html') throw new Error('The link returned a web page instead of a media file.');
        const blob=new Blob(chunks,{type:type?.startsWith(data.mediaKind+'/')?type:data.mime});
        preparedFile=new File([blob],data.fileName,{type:blob.type});
        if (preparedURL) URL.revokeObjectURL(preparedURL);
        preparedURL=URL.createObjectURL(preparedFile);
        const save=panel.querySelector('.prepared-download');save.href=preparedURL;save.download=data.fileName;save.hidden=false;
        const native=Boolean(navigator.share && navigator.canShare?.({files:[preparedFile]}));
        panel.querySelector('[data-action="share-file"]').hidden=!native;
        result.textContent=native?'File ready. Choose Share file to pick an app, or save it to your device.':'File ready. Save it, then attach it in your social app. This browser does not support sharing files directly.';
        button.textContent='Prepare file again';button.disabled=false;
      } else if (button.dataset.action==='share-file' && preparedFile) {
        await navigator.share({files:[preparedFile],title:data.shareTitle,text:data.caption});
      }
    } catch (error) {
      button.disabled=false;
      if (error.name==='AbortError') {result.textContent='Sharing cancelled.';return;}
      result.textContent=button.dataset.action==='prepare-file'
        ? `${error instanceof TypeError?'The media host or browser blocked file preparation.':error.message} Use Download / open, then attach the file in your social app.`
        : 'Sharing is unavailable in this browser. Use Copy link or download the file instead.';
    }
  });
  window.addEventListener('pagehide',()=>{if(preparedURL)URL.revokeObjectURL(preparedURL);});
}

for (const container of document.querySelectorAll('[data-lyrics-url]')) attachLyrics(container);

if (document.querySelector('#index-player')) import('./index-player.mjs').then(({setupIndexPlayer})=>setupIndexPlayer());
if (document.querySelector('#timing-workspace')) import('./timing-editor.mjs').then(({setupTimingEditor})=>setupTimingEditor());

// The featured shelf remains scrollable without JavaScript; buttons add mouse access.
const featuredShelf = document.querySelector('#featured-cards');
if (featuredShelf) {
  const previous = document.querySelector('#cards-previous');
  const next = document.querySelector('#cards-next');
  document.querySelector('.card-scroll-controls').hidden = false;
  const updateShelf = () => {
    previous.disabled = featuredShelf.scrollLeft <= 2;
    next.disabled = featuredShelf.scrollLeft + featuredShelf.clientWidth >= featuredShelf.scrollWidth - 2;
  };
  const moveShelf = direction => {
    const card = featuredShelf.querySelector('.language-card');
    if (!card) return;
    const distance = card.getBoundingClientRect().width + (parseFloat(getComputedStyle(featuredShelf).columnGap) || 0);
    featuredShelf.scrollBy({left: direction * distance, behavior: matchMedia('(prefers-reduced-motion: reduce)').matches ? 'auto' : 'smooth'});
  };
  previous.addEventListener('click', () => moveShelf(-1));
  next.addEventListener('click', () => moveShelf(1));
  featuredShelf.addEventListener('scroll', updateShelf, {passive:true});
  window.addEventListener('resize', updateShelf);
  updateShelf();
}

const copyLyricsPrompt = document.querySelector('#copy-lyrics-prompt');
if (copyLyricsPrompt) copyLyricsPrompt.addEventListener('click', async () => {
  const lyrics = document.querySelector('#lyrics-prompt-text');
  const status = document.querySelector('#lyrics-copy-status');
  try {
    await navigator.clipboard.writeText(lyrics.value);
    status.textContent = 'Lyrics prompt copied, including song sections.';
  } catch {
    lyrics.focus();
    lyrics.select();
    status.textContent = 'The lyrics are selected. Copy them using your browser’s copy command.';
  }
});
