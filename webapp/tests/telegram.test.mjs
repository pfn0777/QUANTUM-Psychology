import test from "node:test";
import assert from "node:assert/strict";
import { canSendToBot } from "../telegram.js";

const sendData = () => {};

test("keyboard-button launch with empty initData can send to bot", () => {
  assert.equal(canSendToBot({ initData: "", platform: "android", sendData }), true);
});

test("page opened outside Telegram cannot send to bot", () => {
  assert.equal(canSendToBot({ initData: "", platform: "unknown", sendData }), false);
  assert.equal(canSendToBot(undefined), false);
});

test("missing sendData cannot send to bot", () => {
  assert.equal(canSendToBot({ platform: "ios" }), false);
});
