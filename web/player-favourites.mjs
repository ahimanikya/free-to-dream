// A personal listening preference, never a public rating or analytics event.
export function createFavourites(storage) {
  const key = 'world-is-one:favourite-tracks';
  let ids = new Set();
  try {
    const stored = JSON.parse(storage?.getItem(key) || '[]');
    if (Array.isArray(stored)) ids = new Set(stored.filter(id => typeof id === 'string' && /^[a-z0-9-]{1,160}$/.test(id)));
  } catch { /* Private browsing or an old value must not interrupt playback. */ }
  return {
    has: id => ids.has(id),
    toggle(id) {
      if (ids.has(id)) ids.delete(id); else ids.add(id);
      let persisted = false;
      try { if (storage) { storage.setItem(key, JSON.stringify([...ids])); persisted = true; } } catch { /* Keep the session usable. */ }
      return {saved: ids.has(id), persisted};
    }
  };
}
