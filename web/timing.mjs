export function parseTime(value) {
  const input=String(value).trim().replace(',','.');
  if(!/^\d+(?::\d{1,2}){0,2}(?:\.\d{1,3})?$/.test(input))throw Error('Use minutes:seconds.milliseconds, or seconds.');
  const parts=input.split(':').map(Number);
  if(parts.slice(1).some(x=>x>=60))throw Error('Minutes and seconds must be below 60.');
  return Math.round(parts.reduce((sum,part)=>sum*60+part,0)*1000);
}
export function clock(ms) {
  const rounded=Math.round(ms);if(!Number.isFinite(rounded)||rounded<0)throw Error('Invalid time');
  return `${String(Math.floor(rounded/60000)).padStart(2,'0')}:${String(Math.floor(rounded/1000)%60).padStart(2,'0')}.${String(rounded%1000).padStart(3,'0')}`;
}
function srtTime(ms) {return `${String(Math.floor(ms/3600000)).padStart(2,'0')}:${clock(ms%3600000).replace('.',',')}`;}
export function validateCues(cues,duration=Infinity) {
  if(!cues.length)throw Error('Add lyric lines first.');
  cues.forEach((c,i)=>{
    if(!c.text.trim()||c.text.includes('-->')||/[\x00-\x08\x0b-\x1f]/.test(c.text)||/\n\s*\n/.test(c.text))throw Error(`Line ${i+1}: use nonempty plain lyric text.`);
    if(!Number.isInteger(c.start)||!Number.isInteger(c.end)||c.start<0||c.end<=c.start)throw Error(`Line ${i+1}: mark a start and a later end.`);
    if(i&&c.start<cues[i-1].end)throw Error(`Line ${i+1}: timings overlap or run backwards.`);
    if(c.end>duration+50)throw Error(`Line ${i+1}: timing extends beyond this recording.`);
  });return cues;
}
export function serializeSrt(cues,duration=Infinity) {
  validateCues(cues,duration);
  return cues.map((c,i)=>`${i+1}\n${srtTime(c.start)} --> ${srtTime(c.end)}\n${c.text.trim()}`).join('\n\n')+'\n';
}
export function parseSrt(text) {
  const blocks=text.replace(/^\uFEFF/,'').replace(/\r\n?/g,'\n').trim().split(/\n[ \t]*\n/);
  const stamp='(\\d{2,}:[0-5]\\d:[0-5]\\d,\\d{3})';
  const cues=blocks.map((block,i)=>{
    const [id,time,...lines]=block.split('\n');const match=time?.trim().match(new RegExp(`^${stamp} --> ${stamp}$`));
    if(id?.trim()!==String(i+1)||!match||!lines.length)throw Error('Use consecutively numbered SRT cues with HH:MM:SS,mmm timestamps.');
    return {start:parseTime(match[1]),end:parseTime(match[2]),text:lines.join('\n').trim()};
  });return validateCues(cues);
}
export function lyricLines(text) {return text.split(/\r?\n/).map(s=>s.trim()).filter(s=>s&&!/^\[.*\]$/.test(s));}
export function retimeCues(cues,firstSeconds,lastSeconds,duration=Infinity) {
  validateCues(cues);
  if(!Number.isFinite(firstSeconds)||!Number.isFinite(lastSeconds))throw Error('Enter both corrections in seconds.');
  const start=cues[0].start,span=cues.at(-1).start-start;
  if(!span&&firstSeconds!==lastSeconds)throw Error('A single line needs the same correction at both ends.');
  const shift=t=>Math.round(t+firstSeconds*1000+(span?(t-start)/span*(lastSeconds-firstSeconds)*1000:0));
  return validateCues(cues.map(c=>({...c,start:shift(c.start),end:shift(c.end)})),duration);
}
