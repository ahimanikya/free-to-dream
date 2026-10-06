import assert from 'node:assert/strict';
import test from 'node:test';
import {buildProposal,githubSubmission,publicMediaURL} from '../web/collaboration.mjs';

const fields={language:'odia',languageName:'Odia',type:'lyrics',title:'A natural pause',current:'ସାଉଁଟି ସାଉଁଟି',proposed:'ସାଉଁଟି… ସାଉଁଟି…',details:'Preserve both words and leave a breath between them.',credit:'A contributor'};

test('Native-script proposals reach a GitHub draft without changing their text',()=>{
  const proposal=buildProposal(fields);
  const link=githubSubmission('https://github.com/example/poems',proposal);
  const url=new URL(link.url);
  assert.equal(url.pathname,'/example/poems/issues/new');
  assert.equal(url.searchParams.get('body'),proposal.body);
  assert.match(proposal.body,/ସାଉଁଟି… ସାଉଁଟି…/);
  assert.equal(link.needsPaste,false);
});

test('Long Unicode proposals stay complete and use an explicit paste handoff',()=>{
  const proposal=buildProposal({...fields,details:'ମୋତେ ସପ୍ନ '.repeat(1200)});
  const handoff=githubSubmission('https://github.com/example/poems',proposal);
  assert.equal(handoff.needsPaste,true);
  assert.ok(handoff.url.length<7500);
  assert.ok(proposal.body.includes('ମୋତେ ସପ୍ନ '.repeat(1000)));
});

test('Missing connection does not produce a pretend submission',()=>{
  assert.deepEqual(githubSubmission('',buildProposal(fields)),{url:'',needsPaste:false});
});

test('Recording submission asks for an attachment and retains creator credits',()=>{
  const proposal=buildProposal({...fields,type:'recording',credits:'Voice: contributor; arrangement: original performance'});
  assert.match(proposal.body,/Attach the recording/);
  assert.match(proposal.body,/Voice: contributor/);
  assert.doesNotMatch(proposal.body,/### Suggested wording/);
});

test('Reject credential-bearing file URLs and non-GitHub handoff destinations',()=>{
  assert.equal(publicMediaURL('https://example.org/audio.mp3'),true);
  for(const value of ['javascript:alert(1)','http://example.org/a.mp3','https://name:secret@example.org/a.mp3']) assert.equal(publicMediaURL(value),false);
  assert.throws(()=>githubSubmission('https://github.com.evil.example/owner/repo',buildProposal(fields)));
  assert.throws(()=>githubSubmission('https://github.com/owner/repo?secret=x',buildProposal(fields)));
});

const {lyricAt, attachLyrics} = await import('../web/lyrics.mjs');
test('Lyric timing follows seeks, gaps, exact boundaries and replay', () => {
  const cues = [{start:1000,end:2000,text:'ସାଉଁଟି'}, {start:3000,end:4500,text:'நான் ஒரு குயவன்.'}];
  for (const [time,text] of [[0,''],[1,'ସାଉଁଟି'],[1.999,'ସାଉଁଟି'],[2,''],[3.5,'நான் ஒரு குயவன்.'],[1.5,'ସାଉଁଟି'],[4.5,'']]) {
    assert.equal(lyricAt(cues,time),text);
  }
});
test('Player events display plain text safely and lyric download failure leaves audio usable', async () => {
  const originalFetch = globalThis.fetch;
  try {
    const events = {};
    const player = {currentTime:1.5, ended:false, addEventListener:(name,fn)=>{events[name]=fn;}};
    const display = {textContent:''};
    const container = {dataset:{lyricsUrl:'lyrics.json'}, querySelector:selector=>selector==='audio'?player:display};
    globalThis.fetch=async()=>({ok:true,json:async()=>[{start:1000,end:2000,text:'<script>literal lyric</script>'}]});
    await attachLyrics(container);
    assert.equal(display.textContent,'<script>literal lyric</script>');
    player.currentTime=4; events.seeked(); assert.equal(display.textContent,'');
    player.currentTime=1.1; events.play(); assert.equal(display.textContent,'<script>literal lyric</script>');
    player.ended=true; events.ended(); assert.equal(display.textContent,'');
    globalThis.fetch=async()=>({ok:false});
    await attachLyrics(container);
    assert.match(display.textContent,/could not load/);
  } finally {globalThis.fetch=originalFetch;}
});

const timing=await import('../web/timing.mjs');
test('SRT round-trip preserves Unicode and millisecond timings',()=>{
  const cues=[{start:1234,end:2345,text:'ସାଉଁଟି\nସାଉଁଟି'},{start:3000,end:6000,text:'நான் ஒரு குயவன்.'}];
  assert.deepEqual(timing.parseSrt(timing.serializeSrt(cues)),cues);
  assert.equal(timing.parseTime('01:02.345'),62345);
  assert.equal(timing.parseTime('1:02:03,456'),3723456);
  assert.equal(timing.clock(3723456),'62:03.456');
  assert.deepEqual(timing.lyricLines('[Intro]\n\nସାଉଁଟି\nସାଉଁଟି\n[Verse 1]\nhello'),['ସାଉଁଟି','ସାଉଁଟି','hello']);
});
test('No invented, overlapping, out-of-range or invalid lyric timestamps are exported',()=>{
  for(const value of ['', '-1', '1:99', 'no time'])assert.throws(()=>timing.parseTime(value));
  for(const cues of [[],[{start:NaN,end:NaN,text:'pending'}],[{start:1000,end:500,text:'reverse'}],[{start:0,end:2000,text:'first'},{start:1000,end:3000,text:'overlap'}],[{start:0,end:1000,text:'one\n\ntwo'}]])assert.throws(()=>timing.serializeSrt(cues));
  assert.throws(()=>timing.serializeSrt([{start:0,end:2100,text:'too long'}],2000));
  assert.throws(()=>timing.parseSrt('2\n00:00:00,000 --> 00:00:01,000\nwrong number'));
});
test('Offsets and gradual drift corrections retain the exact words and validate before changing',()=>{
  const cues=[{start:1000,end:2000,text:'first'},{start:6000,end:7000,text:'middle'},{start:11000,end:12000,text:'last'}];
  const shifted=timing.retimeCues(cues,2,2);
  assert.deepEqual(shifted.map(c=>c.start),[3000,8000,13000]);
  const stretched=timing.retimeCues(cues,0,3);
  assert.deepEqual(stretched.map(c=>c.start),[1000,7500,14000]);
  assert.deepEqual(stretched.map(c=>c.text),cues.map(c=>c.text));
  assert.equal(cues[2].start,11000);
  assert.throws(()=>timing.retimeCues(cues,-2,-2));
  assert.throws(()=>timing.retimeCues(cues,10,-10));
  assert.throws(()=>timing.retimeCues(cues,0,3,13000));
});

import {cardsPerPage, rebasePlan} from '../web/carousel.mjs';
test('Carousel arrows advance a complete visible group on phones and desktops',()=>{
  assert.equal(cardsPerPage(350,326,14,101),1);
  assert.equal(cardsPerPage(1160,300,16,101),3);
  assert.equal(cardsPerPage(620,300,16,101),2);
  assert.equal(cardsPerPage(1160,300,16,2),2);
});
test('Loop rebasing preserves the visible languages and never duplicates a card',()=>{
  const step=316, viewport=1160, count=101, size=3;
  for(const position of [0,316,316*96,316*97]) {
    const order=Array.from({length:count},(_,i)=>i);
    const visible=order.slice(Math.round(position/step),Math.round(position/step)+size);
    const shift=rebasePlan(position,viewport,step,count,size);
    assert.notEqual(shift,0);
    const rotated=[...order.slice(shift),...order.slice(0,shift)];
    const after=(position-shift*step)/step;
    assert.deepEqual(rotated.slice(after,after+size),visible);
    assert.equal(new Set(rotated).size,count);
  }
  assert.equal(rebasePlan(15000,viewport,step,count,size),0);
});

import {backDestination} from '../web/navigation.mjs';
import {playlistTracks, adjacentTrack, setupIndexPlayer} from '../web/index-player.mjs';
const site='https://example.org/free-to-dream/';
test('Back navigation returns to a useful parent, including direct contribution and timing links',()=>{
  const lang='poems--i-am-free-to-dream--languages--odia.html';
  assert.equal(backDestination(site+lang,site+'index.html#collection','languages.html').url,site+'index.html#collection');
  assert.equal(backDestination(site+lang,site+'languages.html?q=odia','languages.html').url,site+'languages.html?q=odia');
  assert.equal(backDestination(site+'contribute.html?language=odia',site+lang,'languages.html').url,site+lang);
  assert.equal(backDestination(site+'contribute.html?language=odia','','languages.html').url,site+lang);
  assert.equal(backDestination(site+'timing.html?recording=odia-audio-01','','languages.html').url,site+'recording--odia-audio-01.html');
  for(const previous of ['https://elsewhere.org/index.html', 'https://example.org/other/index.html',site+'contribute.html',site+lang]) {
    const result=backDestination(site+lang,previous,'languages.html');
    assert.equal(result.url,site+'languages.html'); assert.equal(result.fromPrevious,false);
  }
});
const testTracks=[
  {id:'or',language:'odia',language_name:'Odia',title:'Odia song',url:'or.mp3',page:'or.html'},
  {id:'old',language:'odia',title:'Old take',url:'old.mp3',archived:true},
  {id:'en-country',language:'english',language_name:'English',title:'Country',url:'country.mp3',page:'country.html'},
  {id:'en-jazz',language:'english',language_name:'English',title:'Jazz',url:'jazz.mp3',page:'jazz.html'}
];
test('The listening journey includes alternate styles but skips archived takes and stops at both ends',()=>{
  assert.deepEqual(playlistTracks(testTracks).map(t=>t.id),['or','en-country','en-jazz']);
  assert.equal(adjacentTrack(testTracks,'or').id,'en-country');
  assert.equal(adjacentTrack(testTracks,'en-country',-1).id,'or');
  assert.equal(adjacentTrack(testTracks,'or',-1),null);
  assert.equal(adjacentTrack(testTracks,'en-jazz'),null);
});
function playerFixture(load=async()=>testTracks, loadLyrics=async()=>[]) {
  class Element {
    constructor(){this.listeners={};this.attributes={};this.dataset={};this.classList={contains:()=>false,toggle(){},add(){},remove(){}};this.options=[];this.style={setProperty(){}};this.volume=1;this.parentElement={};this.paused=true;this.checked=false;this.hidden=true;this.textContent='';}
    addEventListener(name,fn){(this.listeners[name]??=[]).push(fn);}
    async emit(name,event={}){for(const fn of this.listeners[name]||[])await fn(event);}
    setAttribute(k,v){this.attributes[k]=v;}
    getAttribute(k){return this.attributes[k];}
    removeAttribute(k){delete this[k];delete this.attributes[k];}
    querySelector(){return this.label??=new Element();}
    replaceChildren(){this.options=[];}
    append(option){this.options.push(option);}
    async play(){if(this.blocked)throw Error('Playback blocked');this.paused=false;await this.emit('play');}
    pause(){this.paused=true;this.emit('pause');}
    load(){}
    focus(){this.focused=true;}
  }
  const ids=['index-player','index-audio','index-playlist','index-track-link','index-play-status','index-previous','index-next','index-stop','index-volume','index-state','index-position','index-close','index-toggle','index-play-icon','index-pause-icon','index-seek','index-elapsed','index-duration','index-mute','index-lyrics-link','index-lyric','index-favourite','index-favourites-list','index-feedback','index-more-toggle','index-more','index-queue-toggle','index-queue','index-queue-list','index-queue-mode','index-lyrics-toggle','index-full-lyrics'];
  const nodes=Object.fromEntries(ids.map(id=>[id,new Element()]));
  const button=new Element();button.dataset.playRecording='or';button.attributes['aria-label']='Play Odia';
  const doc={querySelector:q=>nodes[q.slice(1)],querySelectorAll:q=>q==='[data-playlist]'?[nodes['index-playlist']]:[button],createElement:()=>new Element(),body:new Element()};
  const controller=setupIndexPlayer(doc,load,loadLyrics);
  return {nodes,button,controller};
}
test('The playlist automatically advances after starting; navigation and track selection stay in sync',async()=>{
  const {nodes:n,button,controller}=playerFixture();await controller.ready;
  assert.equal(n['index-audio'].src,undefined);
  n['index-playlist'].value='en-jazz';await n['index-playlist'].emit('change');
  assert.equal(n['index-audio'].src,'jazz.mp3');
  await button.emit('click');assert.equal(n['index-audio'].src,'or.mp3');
  await n['index-audio'].emit('ended');
  assert.equal(n['index-audio'].src,'country.mp3');assert.equal(n['index-playlist'].options.length,4);
  assert.equal(n['index-playlist'].value,'en-country');
  assert.equal(n['index-position'].textContent,'Track 2 of 3');
  n['index-playlist'].value='en-jazz';await n['index-playlist'].emit('change');
  assert.equal(n['index-audio'].src,'jazz.mp3');assert.equal(n['index-next'].disabled,true);
  await n['index-audio'].emit('ended');assert.match(n['index-play-status'].textContent,/end of/);
  await n['index-previous'].emit('click');assert.equal(n['index-audio'].src,'country.mp3');
  await n['index-close'].emit('click');assert.equal(n['index-player'].hidden,true);
  assert.equal(button.focused,true,'Closing the player returns keyboard focus to its launch button');
});
test('Blocked autoplay offers a manual continuation and close cancels a pending catalog request',async()=>{
  const {nodes:n,button,controller}=playerFixture();await controller.ready;
  await button.emit('click');n['index-audio'].blocked=true;
  await n['index-audio'].emit('ended');await Promise.resolve();
  assert.equal(n['index-audio'].src,'country.mp3');assert.match(n['index-play-status'].textContent,/Press play/);
  let release;const pending=playerFixture(()=>new Promise(resolve=>release=resolve));
  const click=pending.button.emit('click');await pending.nodes['index-close'].emit('click');
  release(testTracks);await click;
  assert.equal(pending.nodes['index-player'].hidden,true);
  assert.equal(pending.nodes['index-audio'].src,undefined);
});


test('The custom player seeks by audio time, formats duration, pauses and mutes',async()=>{
  const {nodes:n,button,controller}=playerFixture();await controller.ready;
  await button.emit('click');
  const audio=n['index-audio'];
  audio.duration=180;audio.currentTime=61.5;await audio.emit('loadedmetadata');
  assert.equal(n['index-elapsed'].textContent,'1:01');
  assert.equal(n['index-duration'].textContent,'3:00');
  assert.equal(n['index-seek'].disabled,false);
  n['index-seek'].value='90';await n['index-seek'].emit('input');
  assert.equal(audio.currentTime,90);assert.equal(n['index-elapsed'].textContent,'1:30');
  await n['index-toggle'].emit('click');assert.equal(audio.paused,true);
  assert.equal(n['index-toggle'].getAttribute('aria-label'),'Play');
  assert.equal(n['index-play-icon'].getAttribute('hidden'),undefined);
  assert.equal(n['index-pause-icon'].getAttribute('hidden'),'');
  await n['index-toggle'].emit('click');assert.equal(audio.paused,false);
  await n['index-mute'].emit('click');assert.equal(audio.muted,true);
  assert.equal(n['index-mute'].getAttribute('aria-label'),'Unmute');
});
test('Timed lines follow the current recording and seeking; late lyrics cannot replace the next song',async()=>{
  let deliver;
  const tracks=testTracks.map(t=>({...t,...(t.id==='or'?{lyrics_url:'or.json'}:{})}));
  const {nodes:n,button,controller}=playerFixture(async()=>tracks,()=>new Promise(resolve=>deliver=resolve));
  await controller.ready;await button.emit('click');
  const cues=[{start:1000,end:2000,text:'A first line'},{start:3000,end:4000,text:'A second line'}];
  deliver(cues);await Promise.resolve();
  n['index-audio'].currentTime=1.2;await n['index-audio'].emit('timeupdate');
  assert.equal(n['index-lyric'].textContent,'A first line');
  n['index-audio'].currentTime=3.5;await n['index-audio'].emit('seeked');
  assert.equal(n['index-lyric'].textContent,'A second line');
  await n['index-next'].emit('click');assert.equal(n['index-lyric'].hidden,true);
  await button.emit('click');
  await n['index-next'].emit('click');deliver(cues);await Promise.resolve();
  n['index-audio'].currentTime=1.2;await n['index-audio'].emit('timeupdate');
  assert.equal(n['index-lyric'].textContent,'');assert.equal(n['index-lyric'].hidden,true);
});

test('Stop returns to the beginning without advancing; Play resumes and volume remains adjustable',async()=>{
  const {nodes:n,button,controller}=playerFixture();await controller.ready;await button.emit('click');
  const audio=n['index-audio'];audio.duration=180;audio.currentTime=70;
  await n['index-stop'].emit('click');
  assert.equal(audio.paused,true);assert.equal(audio.currentTime,0);
  assert.equal(n['index-elapsed'].textContent,'0:00');assert.equal(n['index-state'].textContent,'STOPPED');
  await audio.emit('ended');assert.equal(audio.src,'or.mp3');
  await n['index-toggle'].emit('click');assert.equal(audio.paused,false);
  n['index-volume'].value='0.4';await n['index-volume'].emit('input');assert.equal(audio.volume,0.4);
  n['index-volume'].value='0';await n['index-volume'].emit('input');assert.equal(audio.muted,true);
  await n['index-mute'].emit('click');assert.equal(audio.muted,false);assert.equal(audio.volume,0.4);
  await audio.emit('ended');assert.equal(audio.src,'country.mp3');
});

const {shuffledTracks,nextInQueue}=await import('../web/index-player.mjs');
const {cleanEvent,mediaMeter,analyticsAllowed}=await import('../web/engagement.mjs');
const {classifyIssue,loadPublicIssues}=await import('../web/engagement-dashboard.mjs');
const {default:triageModule}=await import('../scripts/engagement-triage.cjs');

test('Shuffle preserves the current take and visits each current recording once; repeat modes differ',()=>{
  const queue=shuffledTracks(testTracks,'en-country',()=>0);
  assert.equal(queue[0].id,'en-country');assert.equal(new Set(queue.map(t=>t.id)).size,3);
  assert.equal(queue.some(t=>t.archived),false);
  const last=queue.at(-1).id;
  assert.equal(nextInQueue(queue,last,1,'off'),null);
  assert.equal(nextInQueue(queue,last,1,'all').id,'en-country');
  assert.equal(nextInQueue(queue,'en-country',1,'one',true).id,'en-country');
  assert.notEqual(nextInQueue(queue,'en-country',1,'one',false).id,'en-country');
});

test('Engagement accepts only scoped events, never feedback text, usernames or arbitrary URLs',()=>{
  assert.deepEqual(cleanEvent('share_intent',{method:'linkedin',recording_id:'odia-audio-01',email:'someone@example.com',feedback:'private',user_id:'abc',language:'odia'}),
    {name:'share_intent',params:{method:'linkedin',recording_id:'odia-audio-01',language:'odia'}});
  assert.equal(cleanEvent('made_up'),null);
  assert.deepEqual(cleanEvent('play_start',{recording_id:'https://example.org?secret=1',language:'<script>'}).params,{});
});

test('Analytics is off without an ID, consent, or on another host; browser privacy preferences win',()=>{
  const data={id:'G-ABC1234567',site:'https://example.org/free-to-dream',location:{origin:'https://example.org',pathname:'/free-to-dream/index.html'},consent:'yes'};
  assert.equal(analyticsAllowed(data),true);
  for(const change of [{id:''},{consent:'no'},{gpc:true},{dnt:true},{location:{origin:'http://127.0.0.1',pathname:'/free-to-dream/index.html'}},{location:{origin:'https://example.org',pathname:'/other/index.html'}}])assert.equal(analyticsAllowed({...data,...change}),false);
});

function meterFixture(duration=100){
  const events=[],listeners={};let wall=0;
  const media={dataset:{recordingId:'odia-audio-01',language:'odia'},tagName:'AUDIO',duration,currentTime:0,src:'a.mp3',paused:false,playbackRate:1,
    addEventListener:(name,fn)=>{(listeners[name]??=[]).push(fn);}};
  const meter=mediaMeter(media,(name,params)=>events.push({name,params}),()=>wall);
  const fire=name=>{for(const fn of listeners[name]||[])fn();};
  const step=seconds=>{wall+=seconds*1000;media.currentTime+=seconds;fire('timeupdate');};
  return {media,meter,events,fire,step};
}
test('Listening counts actual playback; pause/resume and seeking do not create plays or completions',()=>{
  const x=meterFixture();x.fire('playing');x.step(20);x.media.paused=true;x.fire('pause');x.step(40);
  x.media.paused=false;x.fire('playing');x.step(10);
  assert.equal(x.events.filter(e=>e.name==='play_start').length,1);
  assert.equal(x.events.filter(e=>e.name==='play_30s').length,1);
  x.media.seeking=true;x.media.currentTime=99;x.fire('seeking');x.media.seeking=false;x.fire('seeked');x.step(1);x.fire('ended');
  assert.equal(x.events.filter(e=>e.name==='listen_complete').length,0);
  x.media.currentTime=0;x.fire('playing');assert.equal(x.events.filter(e=>e.name==='play_start').length,2);
});
test('A complete listening cycle sends each milestone once, and a new track starts fresh',()=>{
  const x=meterFixture();x.fire('playing');for(let i=0;i<95;i++)x.step(1);
  assert.equal(x.events.filter(e=>e.name==='listen_complete').length,1);
  assert.equal(x.events.filter(e=>e.name==='listen_progress').length,3);
  x.media.dataset.recordingId='tamil-audio-01';x.media.currentTime=0;x.fire('playing');x.step(1);
  assert.equal(x.meter.seconds(),1);assert.equal(x.events.at(-1).params.recording_id,'tamil-audio-01');
});
test('Public feedback pagination excludes PRs, marks partial results and reports rate limits honestly',async()=>{
  let calls=0;
  const result=await loadPublicIssues('https://github.com/owner/repo',async()=>({ok:true,headers:{get:()=>++calls<3?'<next>; rel="next"':null},json:async()=>[{number:calls+1,title:'Feedback',labels:[]},{number:99,pull_request:{}}]}),2);
  assert.equal(result.items.length,2);assert.equal(result.truncated,true);
  assert.equal(classifyIssue({labels:[]}), 'untriaged');
  assert.equal(classifyIssue({labels:[{name:'needs-author'}]}),'needs-author');
  await assert.rejects(()=>loadPublicIssues('https://github.com/owner/repo',async()=>({ok:false,status:403})),/limit/);
});
test('Attention routing preserves closed issues and ignores PRs; the latest human reply determines the next turn',()=>{
  const fn=triageModule.attentionState;
  assert.equal(fn({state:'open'},null,'owner'),'needs-author');
  assert.equal(fn({state:'open'},{user:{login:'OWNER'}},'owner'),'awaiting-contributor');
  assert.equal(fn({state:'open'},{user:{login:'listener'}},'owner'),'needs-author');
  assert.equal(fn({state:'closed'},{user:{login:'listener'}},'owner'),'closed');
  assert.equal(fn({state:'open',pull_request:{}},null,'owner'),null);
});
test('A contributor-reported social post is explicitly separate from automatic share analytics',()=>{
  const proposal=buildProposal({...fields,type:'share',shared_post:'https://example.org/my-public-post'});
  assert.match(proposal.title,/Shared post/);assert.match(proposal.body,/has not verified/);
  assert.throws(()=>buildProposal({...fields,type:'share',shared_post:'javascript:alert(1)'}));
});

const {setupMediaTabs} = await import('../web/media-tabs.mjs');
test('Version tabs sync audio/video, pause hidden players and reveal direct links', () => {
  const registry = new Map(), events = {}, windowEvents = {};
  function node(id='') {
    const n={id, hidden:false, dataset:{}, attrs:{}, handlers:{}, textContent:'', tabIndex:0,
      setAttribute(k,v){this.attrs[k]=v;}, getAttribute(k){return this.attrs[k];},
      addEventListener(k,fn){this.handlers[k]=fn;}, focus(){this.focused=true;}, append(){}};
    if(id) registry.set(id,n);
    return n;
  }
  function group(kind) {
    const panels=['country','jazz'].map(variation=>{
      const p=node(`${kind}-${variation}`), heading=node();heading.textContent=variation;
      p.dataset.variation=variation;p.player={pauses:0,pause(){this.pauses++;}};
      p.querySelector=()=>heading;p.querySelectorAll=()=>[p.player];p.contains=t=>t===p.player;
      return p;
    });
    const g=node();g.attrs['aria-label']=kind;g.panels=panels;
    g.querySelectorAll=()=>panels;g.insertBefore=nav=>{g.nav=nav;};return g;
  }
  const groups=[group('listen'),group('watch')], buttons=[];
  const doc={querySelectorAll:()=>groups, createElement(tag){const n=node();if(tag==='button')buttons.push(n);return n;},
    getElementById:id=>registry.get(id), addEventListener:(k,fn)=>{events[k]=fn;},
    defaultView:{location:{hash:'#watch-jazz'},addEventListener:(k,fn)=>{windowEvents[k]=fn;}}};
  setupMediaTabs(doc);
  assert.deepEqual(groups.map(g=>g.panels.map(p=>p.hidden)),[[true,false],[true,false]]);
  buttons[0].handlers.click();
  assert.deepEqual(groups.map(g=>g.panels.map(p=>p.hidden)),[[false,true],[false,true]]);
  assert.ok(groups[0].panels[1].player.pauses>0);
  let prevented=false;
  buttons[0].handlers.keydown({key:'ArrowRight',preventDefault(){prevented=true;}});
  assert.equal(prevented,true);assert.equal(buttons[1].focused,true);
  assert.equal(buttons[1].attrs['aria-selected'],'true');assert.equal(buttons[0].tabIndex,-1);
  events.play({target:groups[1].panels[0].player});
  assert.deepEqual(groups.map(g=>g.panels.map(p=>p.hidden)),[[false,true],[false,true]]);
  doc.defaultView.location.hash='#watch-jazz';windowEvents.hashchange();
  assert.equal(groups[0].panels[1].hidden,false);
});


import {createFavourites} from '../web/player-favourites.mjs';
test('Personal favourites survive reload, toggle off, and handle corrupt or blocked storage', () => {
  const values = new Map();
  const storage = {getItem:key=>values.get(key), setItem:(key,value)=>values.set(key,value)};
  const first = createFavourites(storage);
  assert.deepEqual(first.toggle('or'), {saved:true, persisted:true});
  const restored = createFavourites(storage);
  assert.equal(restored.has('or'), true);
  restored.toggle('or'); assert.equal(createFavourites(storage).has('or'), false);
  assert.equal(createFavourites({getItem:()=>'{bad'}).has('or'), false);
  assert.equal(createFavourites({getItem:()=>'[null,{},1,"or"]'}).has('or'), true);
  const blocked = createFavourites({getItem(){throw Error();},setItem(){throw Error();}});
  assert.deepEqual(blocked.toggle('or'), {saved:true,persisted:false});
  assert.equal(blocked.has('or'), true);
});
test('Track tools follow the current recording, favourites replay, and Escape closes drawers without stopping music', async () => {
  const {nodes:n,button,controller}=playerFixture();await controller.ready;await button.emit('click');
  assert.match(n['index-feedback'].href,/language=odia&type=feedback&recording=or/);
  await n['index-favourite'].emit('click');
  assert.equal(n['index-favourite'].getAttribute('aria-pressed'),'true');
  await n['index-more-toggle'].emit('click');
  assert.equal(n['index-more'].hidden,false);
  assert.equal(n['index-favourites-list'].options[0].options[0].textContent,'Odia · Odia song');
  await n['index-next'].emit('click');
  assert.equal(n['index-favourite'].getAttribute('aria-pressed'),'false');
  assert.match(n['index-feedback'].href,/recording=en-country/);
  await n['index-favourites-list'].options[0].options[0].emit('click');
  assert.equal(n['index-audio'].src,'or.mp3');
  await n['index-queue-toggle'].emit('click');
  assert.equal(n['index-more'].hidden,true);assert.equal(n['index-queue'].hidden,false);
  await n['index-player'].emit('keydown',{key:'Escape',preventDefault(){}});
  assert.equal(n['index-queue'].hidden,true);assert.equal(n['index-queue-toggle'].focused,true);
  assert.equal(n['index-audio'].paused,false);
  await n['index-favourite'].emit('click');
  assert.match(n['index-favourites-list'].options[0].textContent,/Tap the heart/);
  await n['index-more-toggle'].emit('click');await n['index-close'].emit('click');
  assert.equal(n['index-more'].hidden,true);
});
