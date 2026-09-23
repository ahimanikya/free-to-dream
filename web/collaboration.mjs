const kinds = {lyrics:'Lyric suggestion', recording:'Recording submission', feedback:'Listening review', culture:'Musical direction'};

export function buildProposal(fields) {
  const kind = kinds[fields.type];
  if (!kind || !/^[a-z0-9-]+$/.test(fields.language || '')) throw new Error('Choose a language and contribution type.');
  if (!fields.title?.trim() || !fields.details?.trim()) throw new Error('Add a title and explain your contribution.');
  const title = `[${fields.language}] ${kind}: ${fields.title.trim()}`;
  const sections = [
    ['Language', fields.languageName || fields.language],
    ['Contribution', kind],
    ['Dialect or region', fields.dialect],
    ...(fields.type === 'lyrics' ? [['Current wording', fields.current], ['Suggested wording', fields.proposed]] : []),
    ...(fields.type === 'recording' ? [
      ['Recording', fields.recording_link || 'Attach the recording in this GitHub submission box before submitting.'],
      ['Music, voice and production credits', fields.credits],
      ['Permission to share', 'Please describe your permission to submit this recording, including any third-party material. May visitors download and share this recording on social media with these credits? State any limitations.']
    ] : []),
    ['Notes and reason', fields.details],
    ['Preferred contributor credit', fields.credit],
  ];
  const body = sections.filter(([,value])=>value?.trim()).map(([label,value])=>`### ${label}\n${value.trim()}`).join('\n\n');
  return {title, body};
}

export function githubSubmission(repository, proposal) {
  if (!repository) return {url:'', needsPaste:false};
  if (!/^https:\/\/github\.com\/[\w.-]+\/[\w.-]+\/?$/.test(repository)) throw new Error('A valid GitHub repository is required.');
  const base = repository.replace(/\/$/, '')+'/issues/new?';
  const params = new URLSearchParams({title:proposal.title, body:proposal.body});
  const url = base+params;
  if (url.length <= 7500) return {url, needsPaste:false};
  // Long native-script text expands substantially when URL encoded. Preserve
  // the full proposal for explicit copy/paste instead of silently truncating it.
  params.set('body','Paste your complete proposal here. Attach your recording if applicable, then submit.');
  return {url:base+params, needsPaste:true};
}

export function publicMediaURL(value) {
  try {
    const url = new URL(value);
    return url.protocol === 'https:' && !url.username && !url.password;
  } catch {return false;}
}
