import assert from "node:assert/strict";
import test from "node:test";
import { readFile } from "node:fs/promises";
import { loadReaderPage, citationWindow, READER_PAGE_SIZE } from "../src/lib/documents/source-reader.ts";

const citation = { document_id: "doc", chunk_id: "evidence", chunk_index: 57 };
const document = { id: "doc", title: "Document", file_type: "txt" };
const chunk = { id: "evidence", chunk_index: 57, content: "Full text\n\n" + "x".repeat(3000) };
const page = (items, skip = 55) => ({ document_id: "doc", items, skip, limit: 10, total: 90 });

test("initial window targets a late citation with preceding context and full ordered text", async () => {
  assert.equal(citationWindow(0), 0);
  assert.equal(citationWindow(57), 55);
  const items = [{ id: "before", chunk_index: 55, content: "Before" }, chunk, { id: "after", chunk_index: 58, content: "After" }];
  const calls = [];
  const result = await loadReaderPage(citation, citationWindow(57), {
    document: async id => { calls.push(id); return document; },
    chunks: async (...args) => { calls.push(args); return page(items); },
  });
  assert.equal(result.status, "ready");
  assert.deepEqual(calls, ["doc", ["doc", 55, READER_PAGE_SIZE]]);
  assert.deepEqual(result.page.items, items);
  assert.equal(result.page.items[1].content, chunk.content);
});

test("other pages reverify the exact cited UUID without mixing it into page order", async () => {
  const calls = [];
  const result = await loadReaderPage(citation, 0, {
    document: async () => document,
    chunks: async (_id, skip, limit) => { calls.push([skip, limit]); return skip === 57 ? page([chunk], skip) : page([{ id: "first", chunk_index: 0, content: "First" }], 0); },
  });
  assert.equal(result.status, "ready");
  assert.deepEqual(calls, [[0, 10], [57, 1]]);
  assert.equal(result.page.items.length, 1);
  assert.equal(result.page.items[0].id, "first");
});

test("replacement UUID at the same index is unavailable, never fabricated evidence", async () => {
  const result = await loadReaderPage(citation, 55, { document: async () => document, chunks: async () => page([{ ...chunk, id: "new-version" }]) });
  assert.deepEqual(result, { status: "unavailable" });
});

test("document failures prevent chunk requests and distinguish missing documents", async () => {
  for (const [error, status] of [[new Error("offline"), "document-error"], [{ status: 404 }, "unavailable"]]) {
    const result = await loadReaderPage(citation, 55, { document: async () => { throw error; }, chunks: async () => { assert.fail("Must not fetch chunks"); } });
    assert.deepEqual(result, { status });
  }
});

test("chunk failures and retry use reads only and preserve source selection", async () => {
  let fail = true;
  const scope = ["other-doc"];
  const original = { ...citation };
  const api = { document: async () => document, chunks: async () => { if (fail) throw new Error("offline"); return page([chunk]); } };
  assert.deepEqual(await loadReaderPage(citation, 55, api), { status: "chunks-error" });
  fail = false;
  assert.equal((await loadReaderPage(citation, 55, api)).status, "ready");
  assert.deepEqual(citation, original);
  assert.deepEqual(scope, ["other-doc"]);
});

test("reader waits for document and chunks before publishing ready data", async () => {
  let resolveDocument;
  let resolveChunks;
  const documentPromise = new Promise(resolve => { resolveDocument = resolve; });
  const chunksPromise = new Promise(resolve => { resolveChunks = resolve; });
  let settled = false;
  const loading = loadReaderPage(citation, 55, { document: () => documentPromise, chunks: () => chunksPromise }).then(result => { settled = true; return result; });
  await Promise.resolve();
  assert.equal(settled, false);
  resolveDocument(document);
  await Promise.resolve();
  assert.equal(settled, false);
  resolveChunks(page([chunk]));
  assert.equal((await loading).status, "ready");
});

test("reader has no document-workspace navigation or management controls", async () => {
  const source = await readFile(new URL("../src/components/chat/citation-source.tsx", import.meta.url), "utf8");
  assert.doesNotMatch(source, /href=|next\/link|deleteDocument|processDocument|indexDocument|Xem tài liệu đầy đủ/);
});
