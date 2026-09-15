import assert from "node:assert/strict";
import test from "node:test";
import { readFile } from "node:fs/promises";
import ts from "typescript";
import { canStartSubmission, isClientAbort, messageRequest } from "../src/lib/conversations/message-flow.ts";

const asModule = (source) => `data:text/javascript;base64,${Buffer.from(source).toString("base64")}`;
const source = await readFile(new URL("../src/components/conversations/use-conversation-messages.ts", import.meta.url), "utf8");
let instance = 0;

// Exercise the real hook callbacks with a minimal state/ref host, not a browser
// simulation. React rendering, focus and effect timing require owner acceptance.
async function harness() {
  const unique = instance++;
  const reactUrl = asModule(`// ${unique}
    export const states = [];
    export const useCallback = fn => fn;
    export const useRef = value => ({ current: value });
    export function useState(value) {
      const index = states.push(value) - 1;
      return [value, next => states[index] = typeof next === 'function' ? next(states[index]) : next];
    }
  `);
  const apiUrl = asModule(`// ${unique}
    export class ApiError extends Error { constructor(status) { super('API'); this.status = status; } }
    export const api = { send: async () => ({}), read: async () => ({ id: 'c', messages: [] }), calls: [] };
    export function sendMessage(id, body, signal) { api.calls.push({ id, body, signal }); return api.send(id, body, signal); }
    export function getConversation(id) { return api.read(id); }
  `);
  const helperUrl = new URL("../src/lib/conversations/message-flow.ts", import.meta.url).href;
  const compiled = ts.transpileModule(source, { compilerOptions: { module: ts.ModuleKind.ESNext, target: ts.ScriptTarget.ES2022 } }).outputText
    .replaceAll('"react"', JSON.stringify(reactUrl))
    .replaceAll('"@/lib/api/client"', JSON.stringify(apiUrl))
    .replaceAll('"@/lib/conversations/conversation-api"', JSON.stringify(apiUrl))
    .replaceAll('"@/lib/conversations/message-flow"', JSON.stringify(helperUrl));
  const { states } = await import(reactUrl);
  const { api, ApiError } = await import(apiUrl);
  const { useConversationMessages: mountCallbacks } = await import(asModule(compiled));
  const hook = mountCallbacks(() => {});
  return { hook, api, ApiError, history: () => states[0].c, submission: () => states[1].c, draft: () => states[2].c };
}

const question = messageRequest("Question", ["a"]);
const empty = { id: "c", messages: [] };
const saved = { id: "c", messages: [{ id: "u", role: "user", content: "Question" }] };
const deferred = () => { let resolve; const promise = new Promise(r => { resolve = r; }); return { promise, resolve }; };

test("abort classification and phase guard distinguish transport from server outcomes", () => {
  assert.equal(isClientAbort(new DOMException("Stopped", "AbortError")), true);
  assert.equal(isClientAbort(new Error("Network failure")), false);
  for (const phase of ["queued", "sending", "stopping", "reconciling"]) assert.equal(canStartSubmission(phase), false);
  assert.equal(canStartSubmission("settled"), true);
  assert.equal(canStartSubmission(), true);
});

test("normal send reconciles authoritative history and sends the source snapshot", async () => {
  const h = await harness();
  await h.hook.loadHistory("c");
  h.api.read = async () => saved;
  assert.equal(await h.hook.submitMessage("c", question), true);
  assert.deepEqual(h.history(), saved);
  assert.equal(h.submission().phase, "settled");
  assert.deepEqual(h.api.calls[0].body.document_ids, ["a"]);
});

test("queued first send is claimed once, including repeated Strict Mode callbacks", async () => {
  const h = await harness();
  const post = deferred();
  h.api.send = () => post.promise;
  h.hook.queueMessage(empty, question);
  const first = h.hook.submitMessage("c");
  assert.equal(await h.hook.submitMessage("c"), false);
  assert.equal(await h.hook.submitMessage("c", question), false);
  post.resolve({});
  await first;
  assert.equal(h.api.calls.length, 1);
  assert.equal(h.api.calls[0].id, "c");
});

for (const [name, history, persistence] of [["saved user", saved, "saved"], ["unknown persistence", empty, "unknown"]]) {
  test(`first-message Stop preserves ${name}, editable copy and never resends`, async () => {
    const h = await harness();
    const read = deferred();
    h.api.send = (_id, _body, signal) => new Promise((_resolve, reject) => signal.addEventListener("abort", () => reject(new DOMException("Stopped", "AbortError"))));
    h.api.read = () => read.promise;
    h.hook.queueMessage(empty, question);
    const first = h.hook.submitMessage("c");
    h.hook.stopMessage("c");
    assert.equal(h.submission().phase, "stopping");
    assert.equal(h.api.calls[0].signal.aborted, true);
    assert.equal(h.draft(), "Question");
    h.hook.editDraftCopy("c", "Edited question");
    await Promise.resolve();
    assert.equal(h.submission().phase, "reconciling");
    assert.equal(await h.hook.submitMessage("c", question), false);
    assert.equal(h.submission().postError, null);
    assert.equal(h.submission().acknowledged, false);
    read.resolve(history);
    await first;
    assert.deepEqual(h.history(), history);
    assert.equal(h.submission().persistence, persistence);
    assert.equal(h.draft(), "Edited question");
    assert.equal(h.api.calls.length, 1);
    assert.equal(h.submission().acknowledged, true);
    assert.equal(h.submission().postError, null);
    h.api.send = async () => ({});
    await h.hook.submitMessage("c", messageRequest(h.draft(), []));
    assert.equal(h.api.calls.length, 2);
    assert.equal(h.api.calls[1].id, "c");
    assert.equal(h.api.calls[1].body.content, "Edited question");
    assert.equal(Object.hasOwn(h.api.calls[1].body, "document_ids"), false);
  });
}

test("failed reconciliation blocks sends and preserves edits through GET-only recovery", async () => {
  const h = await harness();
  const post = deferred();
  h.hook.queueMessage(empty, question);
  h.api.send = () => post.promise;
  h.api.read = async () => { throw new Error("offline"); };
  const first = h.hook.submitMessage("c");
  h.hook.stopMessage("c");
  h.hook.editDraftCopy("c", "Keep edit");
  post.resolve({}); // Abort can race with an already resolving response.
  await first;
  assert.equal(h.submission().syncError, true);
  assert.equal(h.submission().acknowledged, false);
  assert.equal(await h.hook.submitMessage("c", question), false);
  h.api.read = async () => saved;
  await h.hook.loadHistory("c");
  assert.equal(h.submission().syncError, false);
  assert.equal(h.submission().interruption, "client-stop");
  assert.equal(h.draft(), "Keep edit");
  assert.equal(h.api.calls.length, 1);
  assert.equal(h.submission().acknowledged, true);
  h.api.send = async () => ({});
  assert.equal(await h.hook.submitMessage("c", messageRequest(h.draft(), [])), true);
  assert.equal(h.api.calls.length, 2);
  assert.equal(h.api.calls[1].body.content, "Keep edit");
});

test("ordinary provider failure still reconciles saved questions without automatic draft restore", async () => {
  const h = await harness();
  h.hook.queueMessage(empty, question);
  h.api.send = async () => { throw new h.ApiError(503); };
  h.api.read = async () => saved;
  await h.hook.submitMessage("c");
  assert.equal(h.submission().persistence, "saved");
  assert.equal(h.draft(), undefined);
  assert.equal(h.api.calls.length, 1);
});
