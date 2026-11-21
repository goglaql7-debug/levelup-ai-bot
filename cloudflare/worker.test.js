import { test } from "node:test";
import assert from "node:assert/strict";
import { webcrypto } from "node:crypto";
import worker, { classifyQuestion, extractAiText, chunks } from "./worker.js";

globalThis.crypto ??= webcrypto;

test("math prefixes and modes", () => {
  assert.deepEqual(classifyQuestion("SAT: x+3=5"), { mode: "SAT Math", text: "x+3=5" });
  assert.deepEqual(classifyQuestion("MS: x²=9"), { mode: "Milliy sertifikat", text: "x²=9" });
  assert.equal(classifyQuestion("2+2").mode, "Umumiy matematika");
});

test("extract AI answer and split Telegram messages", () => {
  assert.equal(extractAiText({ choices: [{ message: { content: "4" } }] }), "4");
  assert.equal(extractAiText({ response: "6" }), "6");
  assert.equal(extractAiText({ foo: "none" }), "");
  const parts = chunks("X".repeat(8100));
  assert.equal(parts.join(""), "X".repeat(8100));
  assert.ok(parts.every((part) => part.length <= 3800));
});

const env = {
  TELEGRAM_BOT_TOKEN: "FAKE_BOT_TOKEN_TEST_ONLY",
  SETUP_PASSWORD: "fake-demo-password-123456",
  AI: { async run() {
    return { choices: [{ message: { content: "x=6" } }] };
  } }
};

test("GET root is healthy", async () => {
  const res = await worker.fetch(new Request("https://example.workers.dev/"), env, {});
  assert.equal(res.status, 200);
  assert.match(await res.text(), /Levelup Mathh/);
});

test("reject unauthorized Telegram webhooks", async () => {
  const res = await worker.fetch(new Request("https://example.workers.dev/webhook", {
    method: "POST",
    headers: { "x-telegram-bot-api-secret-token": "wrong", "content-type": "application/json" },
    body: JSON.stringify({ message: { text: "/start", chat: { id: 12, type: "private" } } }),
  }), env, { waitUntil() {} });
  assert.equal(res.status, 403);
});

test("activate webhook, then answer Telegram question", async () => {
  const outgoing = [];
  const original = globalThis.fetch;
  globalThis.fetch = async (url, options) => {
    outgoing.push({ url: String(url), payload: JSON.parse(options.body) });
    return Response.json({ ok: true });
  };
  try {
    const form = new URLSearchParams({ password: env.SETUP_PASSWORD });
    const activated = await worker.fetch(new Request("https://example.workers.dev/setup", {
      method: "POST",
      headers: { "content-type": "application/x-www-form-urlencoded" },
      body: form,
    }), env, {});
    assert.equal(activated.status, 200);
    const setup = outgoing.find((item) => item.url.endsWith("/setWebhook"));
    assert.equal(setup?.payload.url, "https://example.workers.dev/webhook");
    assert.ok(setup.payload.secret_token);

    const pending = [];
    const received = await worker.fetch(new Request("https://example.workers.dev/webhook", {
      method: "POST",
      headers: {
        "content-type": "application/json",
        "x-telegram-bot-api-secret-token": setup.payload.secret_token,
      },
      body: JSON.stringify({ message: { text: "SAT: 2x=12", chat: { id: 456, type: "private" } } }),
    }), env, { waitUntil(promise) { pending.push(promise); } });
    assert.equal(received.status, 200);
    await Promise.all(pending);
    const reply = outgoing.find((item) => item.url.endsWith("/sendMessage"));
    assert.equal(reply?.payload.chat_id, 456);
    assert.equal(reply?.payload.text, "x=6");
  } finally {
    globalThis.fetch = original;
  }
});
