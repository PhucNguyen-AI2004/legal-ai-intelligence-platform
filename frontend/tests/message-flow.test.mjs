import assert from "node:assert/strict";
import test from "node:test";
import { messageRequest, messagePersistence, citationExcerpt } from "../src/lib/conversations/message-flow.ts";

const history = (messages) => ({ id: "conversation", messages });
const user = (id, content) => ({ id, role: "user", content });

test("default scope is omitted and never serialized as an empty array", () => {
  assert.deepEqual(JSON.parse(JSON.stringify(messageRequest("  Question  ", []))), { content: "Question", top_k: 5 });
});

test("scope snapshots cannot change while sending or leak into the next turn", () => {
  const selected = ["document-a", "document-b"];
  const first = messageRequest("Question", selected);
  selected.splice(0, selected.length, "document-c");
  assert.deepEqual(first.document_ids, ["document-a", "document-b"]);
  assert.deepEqual(messageRequest("Follow-up", selected).document_ids, ["document-c"]);
  assert.equal(Object.hasOwn(messageRequest("Next", []), "document_ids"), false);
});

test("an identical earlier question does not establish that a failed send persisted", () => {
  assert.equal(messagePersistence(history([user("old", "Question")]), ["old"], "Question", true), "not-saved");
});

test("a newly persisted user message establishes saved even without an assistant reply", () => {
  assert.equal(messagePersistence(history([user("old", "Question"), user("new", "Question")]), ["old"], "Question", true), "saved");
});

test("network loss with no new user row stays unknown, not safe to resend", () => {
  assert.equal(messagePersistence(history([]), [], "Question", false), "unknown");
  assert.equal(messagePersistence(history([user("new", "Question")]), [], "Question", false), "saved");
});

test("unrelated new messages and assistant text do not count as this submitted question", () => {
  const messages = [user("new", "Other question"), { id: "answer", role: "assistant", content: "Question" }];
  assert.equal(messagePersistence(history(messages), [], "Question", true), "not-saved");
});

test("citation excerpts are bounded regardless of live chunk size", () => {
  assert.equal(citationExcerpt("Short source"), "Short source");
  assert.equal(citationExcerpt("x".repeat(280)), "x".repeat(280));
  assert.equal(citationExcerpt("x".repeat(281)), "x".repeat(279) + "…");
  assert.equal(citationExcerpt("x".repeat(20000)), "x".repeat(279) + "…");
});

test("citation preview stops at the first paragraph rather than later articles", () => {
  const first = "Điều 1. Người sử dụng có quyền truy cập dữ liệu trong phạm vi được cấp quyền.";
  assert.equal(citationExcerpt(`${first}\n\nĐiều 2. Nghĩa vụ.\n\nĐiều 3. Quy định khác.`), `${first}…`);
});

test("citation preview normalizes whitespace and wrapped lines without joining paragraphs", () => {
  assert.equal(citationExcerpt("\n\r\n  Điều 1.\t Người sử dụng\r\n có quyền.\r\n \t\r\nĐiều 2. Khác.\n"), "Điều 1. Người sử dụng có quyền.…");
  assert.equal(citationExcerpt("  Nội dung\n trên\t một   đoạn.  "), "Nội dung trên một đoạn.");
});

test("long first paragraph is capped even when subsequent paragraphs exist", () => {
  const preview = citationExcerpt(`${"a".repeat(1000)}\n\nSecond paragraph`);
  assert.equal(preview, "a".repeat(279) + "…");
});

test("empty or whitespace-only citation source produces no fabricated text", () => {
  for (const source of ["", " \t\n\r\n", "\u00a0\n\n"]) assert.equal(citationExcerpt(source), "");
});

test("Vietnamese accents and Unicode characters survive preview truncation", () => {
  const text = "Người sử dụng có quyền truy cập dữ liệu.";
  assert.equal(citationExcerpt(text.normalize("NFD")), text);
  assert.equal(citationExcerpt("📄".repeat(300)), "📄".repeat(279) + "…");
});
