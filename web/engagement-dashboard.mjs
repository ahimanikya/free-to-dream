export function classifyIssue(issue) {
  const labels = (issue.labels || []).map(x => typeof x === 'string' ? x : x.name);
  if (labels.includes('needs-author')) return 'needs-author';
  if (labels.includes('awaiting-contributor')) return 'awaiting-contributor';
  return 'untriaged';
}
export async function loadPublicIssues(repository, request = fetch, maxPages = 5) {
  const match = /^https:\/\/github\.com\/([\w.-]+)\/([\w.-]+)\/?$/.exec(repository);
  if(!match)throw Error('Repository is not configured.');
  const items=[];let truncated=false;
  for(let page=1;page<=maxPages;page++) {
    const response=await request(`https://api.github.com/repos/${match[1]}/${match[2]}/issues?state=open&sort=updated&direction=desc&per_page=100&page=${page}`,{credentials:'omit',headers:{Accept:'application/vnd.github+json'}});
    if(!response.ok)throw Error(response.status===403||response.status===429?'GitHub’s public API limit was reached. Open the inbox on GitHub or try again later.':'Could not load GitHub feedback. Open the inbox directly.');
    const rows=await response.json();if(!Array.isArray(rows))throw Error('Unexpected GitHub response.');
    items.push(...rows.filter(row=>!row.pull_request));
    if(!response.headers.get('link')?.includes('rel="next"'))break;
    if(page===maxPages)truncated=true;
  }
  return {items,truncated};
}
export function setupEngagementDashboard(doc=document) {
  const load=doc.querySelector('#load-feedback');if(!load)return;
  const status=doc.querySelector('#feedback-status'), list=doc.querySelector('#feedback-list'),filter=doc.querySelector('#feedback-filter');
  let snapshot=null;
  function render() {
    list.replaceChildren();
    if(!snapshot)return;
    const visible=snapshot.items.filter(item=>filter.value==='all'||classifyIssue(item)===filter.value);
    for(const issue of visible) {
      const row=doc.createElement('li'),link=doc.createElement('a'),info=doc.createElement('p');
      // API text is untrusted. Only render text and links inside the chosen repo.
      const base=doc.body.dataset.repository.replace(/\/$/,'')+'/issues/';
      link.href=base+Number(issue.number);link.textContent=issue.title;link.target='_blank';link.rel='noopener';
      const author=issue.user?.login||'Unknown contributor';
      info.textContent=`#${issue.number} · ${author} · ${classifyIssue(issue).replaceAll('-',' ')} · ${issue.comments||0} comments`;
      row.append(link,info);list.append(row);
    }
    status.textContent=`${visible.length} matching open issues${snapshot.truncated?' in a partial snapshot; open GitHub for the complete inbox':''}. Refreshed ${new Date().toLocaleTimeString()}.`;
    for(const state of ['needs-author','awaiting-contributor','untriaged']) {
      const output=doc.querySelector('[data-feedback-count="'+state+'"]');
      if(output)output.textContent=String(snapshot.items.filter(item=>classifyIssue(item)===state).length)+(snapshot.truncated?'+':'');
    }
    if(!visible.length){const row=doc.createElement('li');row.textContent='No open feedback matches this view.';list.append(row);}
  }
  filter.addEventListener('change',render);
  load.addEventListener('click',async()=>{
    load.disabled=true;status.textContent='Loading public GitHub issues…';
    try{snapshot=await loadPublicIssues(doc.body.dataset.repository);render();}
    catch(error){status.textContent=error.message;}
    finally{load.disabled=false;}
  });
}
