import assert from "node:assert/strict";
import { readFileSync } from "node:fs";
import test from "node:test";

const utils = readFileSync(new URL("../src/lib/documents/document-utils.ts", import.meta.url), "utf8");
const detail = readFileSync(new URL("../src/components/documents/document-detail-workspace.tsx", import.meta.url), "utf8");
const list = readFileSync(new URL("../src/components/documents/documents-workspace.tsx", import.meta.url), "utf8");

test("document action failures remain errors and refetch authoritative state", () => {
  assert.match(utils, /error\.status === 409/);
  assert.match(utils, /error\.status >= 500/);
  for (const source of [detail, list]) {
    assert.match(source, /catch \(caught\)[\s\S]*await load\(/);
    assert.match(source, /setError\(message\)/);
    assert.doesNotMatch(source, /catch \(caught\)[\s\S]*setFeedback\([^)]*(?:hoĂ n táº¥t|thĂ nh cĂ´ng)/);
  }
});

test("polling is active-state-only, finite, rerender-safe, and unmount-safe", () => {
  assert.match(utils, /document\.status === "processing" \|\| document\.embedding_status === "indexing"/);
  for (const source of [detail, list]) {
    assert.match(source, /MAX_POLL_ATTEMPTS = 40/);
    assert.match(source, /window\.setTimeout/);
    assert.match(source, /return \(\) => window\.clearTimeout\(timer\)/);
    assert.doesNotMatch(source, /setInterval/);
  }
});
