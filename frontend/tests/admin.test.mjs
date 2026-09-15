import test from 'node:test';
import assert from 'node:assert/strict';
import { isAdmin, adminAccess, adminQuery } from '../src/lib/admin/admin-utils.ts';

test('admin navigation role check fails closed', () => {
  for (const user of [null, undefined, {}, { role: 'user' }, { role: 'ADMIN' }, { role: 'unknown' }]) assert.equal(isAdmin(user), false);
  assert.equal(isAdmin({ role: 'admin' }), true);
});
test('route waits for authoritative identity and denies non-admins', () => {
  assert.equal(adminAccess({ role: 'admin' }, true), 'loading');
  assert.equal(adminAccess(null, false), 'denied');
  assert.equal(adminAccess({ role: 'user' }, false), 'denied');
  assert.equal(adminAccess({ role: 'admin' }, false), 'allowed');
});
test('query uses bounded page size and encodes literal email search', () => {
  const query = new URLSearchParams(adminQuery(20, { email: ' a+b@example.com ', status: '' }));
  assert.equal(query.get('skip'), '20');
  assert.equal(query.get('limit'), '20');
  assert.equal(query.get('email'), 'a+b@example.com');
  assert.equal(query.has('status'), false);
});
test('first-page filters and negative offsets', () => {
  const query = new URLSearchParams(adminQuery(-20, { status: 'failed', embedding_status: 'pending' }));
  assert.equal(query.get('skip'), '0');
  assert.equal(query.get('status'), 'failed');
  assert.equal(query.get('embedding_status'), 'pending');
});
