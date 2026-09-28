import test from 'node:test';
import assert from 'node:assert/strict';
import {chooseHomeArt} from '../web/home-art.mjs';

test('homepage sections receive distinct artworks without mutating the catalog', () => {
  const works = [{id:'one'}, {id:'two'}, {id:'three'}];
  const before = [...works];
  for (const random of [() => 0, () => .5, () => .99999]) {
    const picked = chooseHomeArt(works, 2, random);
    assert.equal(picked.length, 2);
    assert.equal(new Set(picked.map(work => work.id)).size, 2);
    assert.ok(picked.every(work => works.includes(work)));
  }
  assert.deepEqual(works, before);
});

test('small and empty collections never produce missing artworks', () => {
  assert.deepEqual(chooseHomeArt([], 2), []);
  assert.deepEqual(chooseHomeArt([{id:'only'}], 2), [{id:'only'}]);
});
