import test from 'node:test';
import assert from 'node:assert/strict';
import {slideIndex,slideshowPlaylist,languagePlaybackSource} from '../web/art-slideshow.mjs';
test('Slideshow navigation wraps in either direction and handles an empty collection',()=>{
 assert.equal(slideIndex(0,-1,22),21);assert.equal(slideIndex(21,1,22),0);
 assert.equal(slideIndex(5,1,22),6);assert.equal(slideIndex(0,1,0),0);
});
test('Playlist includes every current language and variation, Odia first, without duplicate formats or archives',()=>{
 const odia={id:'or',language:'odia',url:'odia.mp3'};
 const country={language:'english',url:'country.mp3'};
 const jazz={language:'english',url:'jazz.mp3'};
 const tamil={language:'tamil',url:'tamil.mp3'};
 assert.deepEqual(slideshowPlaylist([country,{language:'telugu',url:'old.mp3',archived:true},odia,jazz,tamil,{...country}, {language:'hindi'}]),[odia,country,jazz,tamil]);
 assert.deepEqual(slideshowPlaylist([]),[]);
});
test('Previous and next songs wrap at either end of the playlist',()=>{
 assert.equal(slideIndex(0,-1,10),9);
 assert.equal(slideIndex(9,1,10),0);
});

test('Language slideshow follows the current variant and transfers the collection playback position',()=>{
 const player=(id,paused,hidden=false)=>({dataset:{recordingId:id},paused,closest:()=>hidden?{}:null});
 const country=player('country',true,true),jazz=player('jazz',true);
 assert.equal(languagePlaybackSource([country,jazz],null).recording,jazz);
 const collection=player('jazz',false);collection.currentTime=71;
 const chosen=languagePlaybackSource([country,jazz],collection);
 assert.equal(chosen.recording,jazz);assert.equal(chosen.playback.currentTime,71);
 assert.equal(languagePlaybackSource([country,jazz],player('odia',false)).recording,jazz);
 assert.equal(languagePlaybackSource([],null),null);
});
