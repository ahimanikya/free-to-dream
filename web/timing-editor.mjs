import {parseTime,clock,parseSrt,serializeSrt,lyricLines,retimeCues} from './timing.mjs';
import {lyricAt} from './lyrics.mjs';
export async function setupTimingEditor(doc=document) {
  if(!doc.querySelector('#timing-workspace'))return;
  const get=id=>doc.getElementById(id);
  const audio=get('timing-audio'),choice=get('timing-recording'),rows=get('timing-rows'),message=get('timing-status');
  let tracks=[],track=null,cues=[],undo=null,dirty=false,version=0;
  const status=text=>message.textContent=text;
  const duration=()=>Number.isFinite(audio.duration)?Math.round(audio.duration*1000):(track?.duration_seconds?Math.round(track.duration_seconds*1000):Infinity);
  function snapshot() {
    return [...rows.querySelectorAll('.timing-row')].map(row=>{
      const read=key=>{try{return parseTime(row.querySelector(`[data-field="${key}"]`).value);}catch{return NaN;}};
      return {start:read('start'),end:read('end'),text:row.querySelector('[data-field="text"]').value};
    });
  }
  function render() {
    rows.replaceChildren();
    cues.forEach((cue,index)=>{
      const row=doc.createElement('div');row.className='timing-row';row.dataset.index=index;
      const textLabel=doc.createElement('label');textLabel.textContent=`Line ${index+1}`;
      const text=doc.createElement('textarea');text.rows=2;text.dir='auto';text.value=cue.text;text.dataset.field='text';textLabel.append(text);row.append(textLabel);
      for(const field of ['start','end']) {
        const label=doc.createElement('label');label.textContent=field==='start'?'Starts':'Ends';
        const input=doc.createElement('input');input.type='text';input.inputMode='decimal';input.placeholder='00:00.000';input.value=Number.isFinite(cue[field])?clock(cue[field]):'';input.dataset.field=field;input.setAttribute('aria-label',`${field} time for line ${index+1}`);label.append(input);row.append(label);
      }
      const actions=doc.createElement('div');actions.className='timing-row-actions';
      for(const [action,label] of [['start','Start now'],['end','End now'],['preview','Preview line']]) {
        const button=doc.createElement('button');button.type='button';button.dataset.timingAction=action;button.textContent=label;button.setAttribute('aria-label',`${label} ${index+1}`);actions.append(button);
      }
      row.append(actions);rows.append(row);
    });
  }
  function canReplace() {return !dirty||window.confirm('Replace these timing edits? Download the SRT first if you want to keep them.');}
  function replace(next) {cues=next;undo=null;get('timing-undo').disabled=true;dirty=true;render();}
  function select(item) {
    ++version;audio.pause();track=item;audio.src=item.url;audio.load();audio.playbackRate=Number(get('timing-speed').value);
    cues=[];undo=null;dirty=false;render();get('timing-lines').value='';get('timing-undo').disabled=true;
    get('timing-existing').hidden=!item.srt_url;get('timing-draft').disabled=!item.draft;
    get('timing-submit').href=`contribute.html?language=${encodeURIComponent(item.language)}&type=feedback&recording=${encodeURIComponent(item.id)}`;
    status('Start with the exact words sung in this take. Play the recording before marking times.');
    get('timing-live').textContent='Timed lyrics will appear here during preview.';
  }
  rows.addEventListener('input',()=>{dirty=true;});
  rows.addEventListener('click',async event=>{
    const button=event.target.closest('[data-timing-action]');if(!button)return;
    try {
      if(!Number.isFinite(audio.duration))throw Error('Play the recording and wait for it to load first.');
      const row=button.closest('.timing-row'),action=button.dataset.timingAction;
      if(action==='preview') {
        const ms=parseTime(row.querySelector('[data-field="start"]').value);
        if(ms>=duration())throw Error('This line starts beyond the recording.');
        audio.currentTime=ms/1000;await audio.play();
      } else {
        row.querySelector(`[data-field="${action}"]`).value=clock(audio.currentTime*1000);dirty=true;
      }
      status('');
    } catch(error) {status(error.message);}
  });
  for(const event of ['timeupdate','seeking','seeked','ended']) audio.addEventListener(event,()=>{
    get('timing-clock').textContent=clock(audio.currentTime*1000);
    const active=snapshot().filter(c=>Number.isFinite(c.start)&&Number.isFinite(c.end));
    get('timing-live').textContent=audio.ended?'':lyricAt(active,audio.currentTime);
  });
  audio.addEventListener('error',()=>status('The audio could not load. Try its recording page or reload this workspace.'));
  get('timing-speed').addEventListener('change',()=>{audio.playbackRate=Number(get('timing-speed').value);});
  choice.addEventListener('change',()=>{
    if(!canReplace()){choice.value=track.id;return;}
    const item=tracks.find(x=>x.id===choice.value);if(item)select(item);
  });
  get('timing-draft').addEventListener('click',()=>{
    if(!track?.draft)return;
    get('timing-lines').value=lyricLines(track.draft).join('\n');dirty=true;
    status('Check every line and repetition against the audio, then create timing rows.');
  });
  get('timing-create').addEventListener('click',()=>{
    if(cues.length&&!canReplace())return;
    const lines=lyricLines(get('timing-lines').value);
    if(!lines.length){status('Paste the sung lyrics first.');return;}
    replace(lines.map(text=>({text,start:NaN,end:NaN})));
    status('Play the audio, then use Start now and End now for each line. You can also edit the time fields.');
  });
  async function importText(read) {
    if(!canReplace())return;
    const token=version;
    try {
      const next=parseSrt(await read());
      serializeSrt(next,duration());
      if(token!==version)return;
      replace(next);status('Imported. Listen through this exact recording to confirm every cue.');
    } catch(error){if(token===version)status(error.message);}
  }
  get('timing-import').addEventListener('change',event=>{const file=event.target.files[0];if(file)importText(()=>file.text());event.target.value='';});
  get('timing-existing').addEventListener('click',()=>{
    const url=track?.srt_url;if(!url)return;
    importText(async()=>{const r=await fetch(url);if(!r.ok)throw Error('The SRT could not load.');return r.text();});
  });
  get('timing-shift').addEventListener('click',()=>{
    try {
      const previous=snapshot();
      const next=retimeCues(previous,Number(get('timing-first-shift').value),Number(get('timing-last-shift').value),duration());
      undo=previous;cues=next;dirty=true;render();get('timing-undo').disabled=false;
      status('Correction applied. Preview the start, middle and ending, then check every line.');
    }catch(error){status(error.message);}
  });
  get('timing-undo').addEventListener('click',()=>{if(!undo)return;cues=undo;undo=null;dirty=true;render();get('timing-undo').disabled=true;status('Correction undone.');});
  get('timing-export').addEventListener('click',()=>{
    try {
      if(!track)throw Error('Choose a recording first.');
      const content=serializeSrt(snapshot(),duration());
      const url=URL.createObjectURL(new Blob([content],{type:'text/plain;charset=utf-8'}));
      const link=doc.createElement('a');link.href=url;link.download=track.id+'.srt';link.click();setTimeout(()=>URL.revokeObjectURL(url),10000);
      dirty=false;status(`Downloaded ${track.id}.srt. Submit it with this recording ID after listening review.`);
    }catch(error){status(error.message);}
  });
  window.addEventListener('beforeunload',event=>{if(dirty){event.preventDefault();event.returnValue='';}});
  try {
    const r=await fetch('assets/listening.json');if(!r.ok)throw Error();tracks=await r.json();
    choice.replaceChildren();
    for(const item of tracks){const option=doc.createElement('option');option.value=item.id;option.textContent=item.title+(item.archived?' · earlier take':'');choice.append(option);}
    const requested=new URLSearchParams(location.search).get('recording');
    const initial=tracks.find(x=>x.id===requested)||tracks[0];
    if(!initial){choice.disabled=true;status('No audio recordings are available yet.');return;}
    choice.value=initial.id;select(initial);
  } catch {status('The recording list could not load. Reload this page to try again.');choice.disabled=true;}
}
