// No user text is executed; issue/comment metadata only selects attention labels.
function attentionState(issue, latestComment, maintainer) {
  if(issue.pull_request)return null;
  if(issue.state!=='open')return 'closed';
  return latestComment?.user?.login?.toLowerCase()===maintainer.toLowerCase()?'awaiting-contributor':'needs-author';
}
async function triage({github,context,maintainer}) {
  const {owner,repo}=context.repo;
  const issue_number=context.payload.issue?.number;
  if(!issue_number||context.payload.issue.pull_request||context.payload.sender?.type==='Bot')return;
  const {data:issue}=await github.rest.issues.get({owner,repo,issue_number});
  const comments=issue.comments?await github.paginate(github.rest.issues.listComments,{owner,repo,issue_number,per_page:100}):[];
  const latest=comments.filter(c=>c.user?.type!=='Bot').at(-1);
  const state=attentionState(issue,latest,maintainer);
  const labels=[{name:'needs-author',color:'B7793E',description:'A contribution or reply needs the project author’s attention.'},
    {name:'awaiting-contributor',color:'6C8C75',description:'The author has replied; waiting for the next contribution or follow-up.'}];
  for(const label of labels){
    try{await github.rest.issues.createLabel({owner,repo,...label});}catch(error){if(error.status!==422)throw error;}
    const exists=issue.labels.some(x=>x.name===label.name);
    if(label.name===state&&!exists)await github.rest.issues.addLabels({owner,repo,issue_number,labels:[label.name]});
    if(label.name!==state&&exists)try{await github.rest.issues.removeLabel({owner,repo,issue_number,name:label.name});}catch(error){if(error.status!==404)throw error;}
  }
}
module.exports={attentionState,triage};
