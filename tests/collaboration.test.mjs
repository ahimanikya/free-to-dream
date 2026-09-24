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
