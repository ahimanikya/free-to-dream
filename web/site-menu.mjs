export function setupSiteMenu(doc = document) {
  const header = doc.querySelector('.site-header');
  const button = header?.querySelector('.menu-toggle');
  const nav = header?.querySelector('.site-navigation');
  if (!button || !nav) return;
  const setOpen = open => button.setAttribute('aria-expanded', String(open));
  button.hidden = false;
  header.classList.add('has-menu');
  button.addEventListener('click', () => setOpen(button.getAttribute('aria-expanded') !== 'true'));
  header.addEventListener('keydown', event => {
    if (event.key === 'Escape' && button.getAttribute('aria-expanded') === 'true') {
      setOpen(false);
      button.focus();
    }
  });
  nav.addEventListener('click', event => {
    if (event.target.closest('a')) setOpen(false);
  });
  doc.addEventListener('click', event => {
    if (!header.contains(event.target)) setOpen(false);
  });
}
