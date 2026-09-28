// Progressive enhancement: without JavaScript, every version stays available.
export function setupMediaTabs(doc = document) {
  const groups = [];
  for (const group of doc.querySelectorAll('.media-group')) {
    const panels = [...group.querySelectorAll(':scope > .recording-variation')];
    if (panels.length < 2) continue;
    const nav = doc.createElement('div');
    nav.className = 'media-tabs';
    nav.setAttribute('role', 'tablist');
    nav.setAttribute('aria-label', `${group.getAttribute('aria-label')} versions`);
    const buttons = panels.map(panel => {
      const button = doc.createElement('button');
      button.type = 'button';
      button.id = `${panel.id}-tab`;
      button.textContent = panel.querySelector('h3').textContent;
      button.setAttribute('role', 'tab');
      button.setAttribute('aria-controls', panel.id);
      panel.setAttribute('role', 'tabpanel');
      panel.setAttribute('aria-labelledby', button.id);
      panel.tabIndex = 0;
      panel.querySelector('h3').hidden = true;
      nav.append(button);
      return button;
    });
    const activate = index => {
      panels.forEach((panel, i) => {
        panel.hidden = i !== index;
        buttons[i].setAttribute('aria-selected', String(i === index));
        buttons[i].tabIndex = i === index ? 0 : -1;
        if (i !== index) panel.querySelectorAll('audio, video').forEach(player => player.pause());
      });
    };
    const select = index => {
      activate(index);
      const variation = panels[index].dataset.variation;
      for (const other of groups) {
        if (other.panels === panels) continue;
        const matching = other.panels.findIndex(panel => panel.dataset.variation === variation);
        if (matching >= 0) other.activate(matching);
      }
    };
    buttons.forEach((button, index) => {
      button.addEventListener('click', () => select(index));
      button.addEventListener('keydown', event => {
        let next;
        if (event.key === 'ArrowRight') next = (index + 1) % buttons.length;
        if (event.key === 'ArrowLeft') next = (index - 1 + buttons.length) % buttons.length;
        if (event.key === 'Home') next = 0;
        if (event.key === 'End') next = buttons.length - 1;
        if (next === undefined) return;
        event.preventDefault();
        select(next);
        buttons[next].focus();
      });
    });
    group.insertBefore(nav, panels[0]);
    groups.push({panels, activate, select});
    activate(0);
  }
  // A playlist selection or a deep link should reveal its version too.
  const reveal = target => {
    for (const group of groups) {
      const index = group.panels.findIndex(panel => panel === target || panel.contains(target));
      if (index >= 0) group.select(index);
    }
  };
  doc.addEventListener('play', event => reveal(event.target), true);
  const followHash = () => {
    let id;
    try { id = decodeURIComponent(doc.defaultView.location.hash.slice(1)); } catch { return; }
    const target = doc.getElementById(id);
    if (target) reveal(target);
  };
  doc.defaultView.addEventListener('hashchange', followHash);
  followHash();
}
