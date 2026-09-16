import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import test from "node:test";

const detail = readFileSync(new URL("../src/components/documents/document-detail-workspace.tsx", import.meta.url), "utf8");
const list = readFileSync(new URL("../src/components/documents/documents-workspace.tsx", import.meta.url), "utf8");
const types = readFileSync(new URL("../src/lib/documents/types.ts", import.meta.url), "utf8");

test("document async actions use queued response contracts", () => {
  assert.match(types, /job_id: string/);
  assert.match(types, /status: "queued"/);
  assert.doesNotMatch(types, /chunk_count|embedded_chunks/);
});

test("document views poll only active pipeline states with a finite budget", () => {
  for (const source of [detail, list]) {
    assert.match(source, /isPipelineActive/);
    assert.match(source, /MAX_POLL_ATTEMPTS = 40/);
    assert.match(source, /POLL_INTERVAL_MS = 3000/);
    assert.match(source, /window\.clearTimeout\(timer\)/);
  }
});

test("queued feedback does not claim premature completion", () => {
  for (const source of [detail, list]) {
    assert.match(source, /được xếp hàng/);
    assert.doesNotMatch(source, /Xử lý tài liệu thành công|Lập chỉ mục thành công/);
  }
});
