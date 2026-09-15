import assert from "node:assert/strict";
import test from "node:test";
import { citationKey, selectedCitation, verifiedCitationExcerpt, messageRequest } from "../src/lib/conversations/message-flow.ts";

const a = { citation_index: 1, document_id: "doc-a", chunk_id: "chunk-a", chunk_index: 0, document_name: "A" };
const b = { citation_index: 2, document_id: "doc-b", chunk_id: "chunk-b", chunk_index: 4, document_name: "B" };

test("list, detail, back and switching resolve only the selected citation", () => {
  const citations = [a, b];
  assert.equal(selectedCitation(citations, null), undefined);
  assert.equal(selectedCitation(citations, citationKey(b)), b);
  assert.equal(selectedCitation(citations, null), undefined);
  assert.equal(selectedCitation(citations, citationKey(a)), a);
  assert.deepEqual(citations, [a, b]);
});

test("another answer's citations and replaced chunks cannot satisfy selection", () => {
  assert.equal(selectedCitation([b], citationKey(a)), undefined);
  const replaced = { ...a, chunk_id: "replacement" };
  assert.equal(selectedCitation([replaced], citationKey(a)), undefined);
  assert.equal(selectedCitation([], citationKey(a)), undefined);
});

test("live excerpts require matching UUID; unavailable and empty are distinct", () => {
  assert.equal(verifiedCitationExcerpt([{ id: "replacement", content: "Unrelated text" }], a.chunk_id), null);
  assert.equal(verifiedCitationExcerpt([], a.chunk_id), null);
  assert.equal(verifiedCitationExcerpt([{ id: a.chunk_id, content: " " }], a.chunk_id), "");
  assert.equal(verifiedCitationExcerpt([{ id: a.chunk_id, content: "Evidence\n\nOther paragraph" }], a.chunk_id), "Evidence…");
  assert.equal(Array.from(verifiedCitationExcerpt([{ id: a.chunk_id, content: "ữ".repeat(600) }], a.chunk_id)).length, 280);
});

test("post-answer selection leaves the next question's source scope untouched", () => {
  const scope = ["different-document"];
  const request = messageRequest("Next question", scope);
  selectedCitation([a, b], citationKey(b));
  selectedCitation([a, b], null);
  assert.deepEqual(scope, ["different-document"]);
  assert.deepEqual(request.document_ids, ["different-document"]);
});
