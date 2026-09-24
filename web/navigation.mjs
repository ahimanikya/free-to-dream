const languageFile = /^poems--i-am-free-to-dream--(?:languages--[a-z0-9-]+|original)\.html$/;
const recordingFile = /^recording--[a-z0-9-]+\.html$/;
export function backDestination(currentURL, previousURL, fallback) {
  const current = new URL(currentURL), base = new URL('.', current);
  const page = current.pathname.split('/').pop() || 'index.html';
  try {
    const previous = new URL(previousURL), name = previous.pathname.split('/').pop() || 'index.html';
    const sameSite = previous.origin === base.origin && new URL('.', previous).pathname === base.pathname;
    const collection = ['index.html', 'languages.html'].includes(name);
    const content = languageFile.test(name) || recordingFile.test(name);
    const allowed = page === 'languages.html' ? name === 'index.html'
      : languageFile.test(page) ? collection
      : recordingFile.test(page) ? collection || languageFile.test(name)
      : ['contribute.html', 'timing.html'].includes(page) || page.startsWith('guides--') ? collection || content : false;
    if (sameSite && page !== name && allowed) {
      const label = name === 'index.html' ? '← Home' : name === 'languages.html' ? '← All languages'
        : recordingFile.test(name) ? '← Back to recording' : '← Back to the poem';
      return {url: previous.href, label, fromPrevious: true};
    }
  } catch { /* Direct entry keeps a useful parent link. */ }
  if (page === 'contribute.html') {
    const slug = current.searchParams.get('language');
    if (slug && /^[a-z0-9]+(?:-[a-z0-9]+)*$/.test(slug))
      return {url: new URL('poems--i-am-free-to-dream--languages--' + slug + '.html', base).href, label:'← Back to the poem', fromPrevious:false};
  }
  if (page === 'timing.html') {
    const id = current.searchParams.get('recording');
    if (id && /^[a-z0-9]+(?:-[a-z0-9]+)*$/.test(id))
      return {url:new URL('recording--' + id + '.html', base).href, label:'← Back to recording', fromPrevious:false};
  }
  return {url:new URL(fallback, base).href, label:null, fromPrevious:false};
}
export function setupBackNavigation(doc = document, win = window) {
  const back = doc.querySelector('a.back');
  const key = 'free-to-dream-navigation';
  let previous = doc.referrer;
  try {
    const saved = JSON.parse(win.sessionStorage.getItem(key) || 'null');
    win.sessionStorage.removeItem(key);
    if (saved && saved.to === win.location.href) previous = saved.from;
  } catch { /* Referrer and static links work when storage is unavailable. */ }
  if (back) {
    const target = backDestination(win.location.href, previous, back.href);
    back.href = target.url;
    if (target.label) back.textContent = target.label;
  }
  doc.addEventListener('click', event => {
    const anchor = event.target.closest('a[href]');
    if (!anchor || anchor === back || anchor.target || anchor.hasAttribute('download') || event.defaultPrevented || event.button !== 0 || event.metaKey || event.ctrlKey || event.shiftKey || event.altKey) return;
    const target = new URL(anchor.href, win.location.href);
    if (target.origin !== win.location.origin || !target.pathname.endsWith('.html') || target.pathname === win.location.pathname) return;
    try { win.sessionStorage.setItem(key, JSON.stringify({from:win.location.href,to:target.href})); } catch {}
  });
}
