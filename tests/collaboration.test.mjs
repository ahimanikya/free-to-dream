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
