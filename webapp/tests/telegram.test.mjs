import test from "node:test";
import assert from "node:assert/strict";
import { canSendToBot } from "../telegram.js";

const sendData = () => {};

test("keyboard-button launch with empty initData can send to bot", () => {
  assert.equal(canSendToBot({ initData: "", platform: "android", sendData }), true);
  assert.equal(canSendToBot({ platform: "android", sendData }), true);
});

test("inline-button launch with full initData cannot send to bot", () => {
  const initData = "query_id=AAEAAAE&user=%7B%22id%22%3A123%7D&hash=0123456789abcdef";
  assert.equal(canSendToBot({ initData, platform: "android", sendData }), false);
});

test("page opened outside Telegram cannot send to bot", () => {
  assert.equal(canSendToBot({ initData: "", platform: "unknown", sendData }), false);
  assert.equal(canSendToBot(undefined), false);
});

test("missing sendData cannot send to bot", () => {
  assert.equal(canSendToBot({ platform: "ios" }), false);
});
