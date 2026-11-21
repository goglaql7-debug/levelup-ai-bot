/**
 * Levelup Mathh AI — serverless Telegram bot.
 * Deploy with Cloudflare Workers; no paid OpenAI API key or always-on VM required.
 * Required secret variables: TELEGRAM_BOT_TOKEN and SETUP_PASSWORD (>= 20 chars).
 * Required AI binding: AI.
 */

const AI_MODEL = "@cf/zai-org/glm-4.7-flash";
const MAX_INPUT = 2400;
const MAX_UPDATE_BYTES = 65536;
const MAX_REPLY_CHARS = 3800;

export function classifyQuestion(input) {
  const text = String(input || "").trim();
  const match = text.match(/^(sat|milliy|ms|umumiy)\s*[:：]\s*/i);
  const prefix = match?.[1]?.toLowerCase();
  const mode = prefix === "sat" ? "SAT Math" :
    prefix === "milliy" || prefix === "ms" ? "Milliy sertifikat" : "Umumiy matematika";
  return { mode, text: match ? text.slice(match[0].length).trim() : text };
}

export function extractAiText(result) {
  const content = result?.choices?.[0]?.message?.content ?? result?.response;
  if (typeof content === "string" && content.trim()) return content.trim();
  if (Array.isArray(content)) {
    const joined = content.map((part) => typeof part?.text === "string" ? part.text : "").join("\n").trim();
    if (joined) return joined;
  }
  return "";
}

export function chunks(text, size = MAX_REPLY_CHARS) {
  const parts = [];
  let rest = String(text).trim();
  while (rest.length > size) {
    let n = rest.lastIndexOf("\n", size);
    if (n < size / 3) n = rest.lastIndexOf(" ", size);
    if (n < size / 3) n = size;
    parts.push(rest.slice(0, n).trim());
    rest = rest.slice(n).trim();
  }
  if (rest) parts.push(rest);
  return parts;
}

async function telegramSecret(setupPassword) {
  const bytes = await crypto.subtle.digest("SHA-256", new TextEncoder().encode(setupPassword + ":telegram"));
  return [...new Uint8Array(bytes)].map((b) => b.toString(16).padStart(2, "0")).join("");
}

function htmlPage() {
  return new Response(`<!doctype html><html lang="uz"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>Levelup Mathh AI — faollashtirish</title>
<style>body{font-family:system-ui,sans-serif;background:#f4f6fb;color:#111827;max-width:540px;margin:65px auto;padding:20px}main{background:white;padding:28px;border:1px solid #e5e7eb;border-radius:18px}h1{font-size:23px}p{line-height:1.55}input,button{box-sizing:border-box;width:100%;padding:14px;border-radius:10px;margin:7px 0;font-size:16px}input{border:1px solid #9ca3af}button{border:0;background:#194dd1;color:white;font-weight:700}small{color:#555}</style></head>
<body><main><h1>Levelup Mathh AI</h1>
<p>Telegram bot webhook'ini faollashtirish uchun Cloudflare'dagi <b>SETUP_PASSWORD</b> maxfiy qiymatini kiriting.</p>
<form action="/setup" method="post">
<label for="password">Maxfiy faollashtirish paroli</label>
<input id="password" name="password" type="password" minlength="20" autocomplete="off" required>
<button type="submit">Telegram botni faollashtirish</button></form>
<p><small>Parol yoki bot tokenini ChatGPT'ga va GitHub'ga yubormang. Parol bu sahifadan xavfsiz HTTPS ulanish orqali yuboriladi.</small></p>
</main></body></html>`, {
    headers: { "content-type": "text/html; charset=utf-8", "cache-control": "no-store" },
  });
}

async function telegram(env, method, payload) {
  const res = await fetch(`https://api.telegram.org/bot${env.TELEGRAM_BOT_TOKEN}/${method}`, {
    method: "POST",
    headers: { "content-type": "application/json" },
    body: JSON.stringify(payload),
  });
  if (!res.ok) throw new Error("telegram_http_" + res.status);
  const data = await res.json();
  if (!data.ok) throw new Error("telegram_api_failed");
  return data;
}

async function sendText(env, chatId, text) {
  for (const piece of chunks(text)) {
    await telegram(env, "sendMessage", {
      chat_id: chatId,
      text: piece,
      disable_web_page_preview: true,
    });
  }
}

async function processUpdate(update, env) {
  const message = update?.message;
  if (!message || message.chat?.type !== "private" || !Number.isSafeInteger(message.chat?.id)) return;
  const chatId = message.chat.id;
  const rawText = typeof message.text === "string" ? message.text.trim() : "";

  if (!rawText && (message.photo || message.document)) {
    await sendText(env, chatId, "Bu bepul versiya hozircha faqat matnli savollarni tushunadi. Iltimos, rasmdagi misolni matn qilib yozing.");
    return;
  }
  if (!rawText) return;

  const command = rawText.split(/\s/)[0].split("@")[0].toLowerCase();
  if (command === "/start" || command === "/help") {
    await sendText(env, chatId,
      "Levelup Mathh AI botiga xush kelibsiz!\n\n" +
      "Matematika masalasini yuboring, men uni qadamma-qadam tushuntiraman.\n\n" +
      "Yo'nalish uchun savolingizni quyidagicha boshlang:\n" +
      "SAT: 2x + 7 = 19\n" +
      "MS: x² - 5x + 6 = 0\n" +
      "Yoki oddiy savol yozing.\n\n" +
      "/kurslar — yo'nalishlar\n/privacy — maxfiylik\n/help — yordam");
    return;
  }
  if (command === "/kurslar") {
    await sendText(env, chatId,
      "Levelup Mathh: Digital SAT Math va Milliy sertifikat matematikasiga tayyorgarlik.\n" +
      "SAT savoli oldiga SAT:, milliy sertifikat savoli oldiga MS: yozing.\n" +
      "Kurs narxi va qabul jadvalini administrator tasdiqlashi kerak.");
    return;
  }
  if (command === "/privacy") {
    await sendText(env, chatId,
      "Savollaringiz javob berish uchun Cloudflare Workers AI xizmatida qayta ishlanadi. " +
      "Ushbu bepul versiya doimiy suhbat xotirasini saqlamaydi. " +
      "Parol, karta ma'lumoti va boshqa maxfiy ma'lumotlarni yubormang.");
    return;
  }
  if (command.startsWith("/")) {
    await sendText(env, chatId, "Noma'lum buyruq. Yordam uchun /help ni yuboring.");
    return;
  }
  if (rawText.length > MAX_INPUT) {
    await sendText(env, chatId, "Savol uzunligi 2400 belgidan oshmasin. Qisqaroq qilib yuboring.");
    return;
  }
  const question = classifyQuestion(rawText);
  if (!question.text) {
    await sendText(env, chatId, "Savolni ham yozing. Masalan: SAT: 2x+7=19");
    return;
  }

  try {
    const answer = await env.AI.run(AI_MODEL, {
      messages: [
        {
          role: "system",
          content: "Siz Levelup Mathh uchun o'zbekcha matematika yordamchisisiz. " +
            "O'quvchining savolini oddiy, aniq, bosqichma-bosqich yeching; zarur formulalar va tekshiruvni ko'rsating. " +
            "Savol yo'nalishi: " + question.mode + ". " +
            "Savol inglizcha bo'lsa, atamalarni o'zbekchaga tushuntiring. " +
            "Notanish ma'lumotlarni to'qimang. Faqat yakuniy javobni va yechim izohini yozing."
        },
        { role: "user", content: question.text }
      ],
      max_completion_tokens: 900,
      reasoning_effort: "low",
      chat_template_kwargs: { enable_thinking: false },
    });
    const answerText = extractAiText(answer);
    await sendText(env, chatId, answerText || "AI javob qaytarmadi. Savolni boshqacha yozib ko'ring.");
  } catch (err) {
    console.error("ai_reply_failed", err instanceof Error ? err.name : "unknown");
    try { await sendText(env, chatId, "AI xizmati vaqtincha ishlamayapti yoki bepul limit tugagan. Keyinroq qayta urinib ko'ring."); }
    catch { /* Telegram also unavailable. */ }
  }
}

export default {
  async fetch(request, env, ctx) {
    const path = new URL(request.url).pathname;
    if (request.method === "GET" && path === "/") {
      return new Response("Levelup Mathh AI server ishga tushgan. Faollashtirish: /setup", {
        headers: { "content-type": "text/plain; charset=utf-8" },
      });
    }
    if (request.method === "GET" && path === "/setup") return htmlPage();

    if (request.method === "POST" && path === "/setup") {
      if (!env.TELEGRAM_BOT_TOKEN || !env.SETUP_PASSWORD || env.SETUP_PASSWORD.length < 20)
        return new Response("Cloudflare'da TELEGRAM_BOT_TOKEN va uzun SETUP_PASSWORD sozlanmagan.", { status: 503 });
      const form = await request.formData().catch(() => null);
      const password = form?.get("password");
      if (typeof password !== "string" || password !== env.SETUP_PASSWORD)
        return new Response("Faollashtirish paroli noto'g'ri.", { status: 403 });
      try {
        const secret = await telegramSecret(env.SETUP_PASSWORD);
        const hookUrl = new URL("/webhook", request.url).href;
        await telegram(env, "setWebhook", {
          url: hookUrl,
          secret_token: secret,
          allowed_updates: ["message"],
        });
        return new Response("Bot webhook'i faollashtirildi! Endi Telegram'da botingizga /start yuboring.", {
          headers: { "content-type": "text/plain; charset=utf-8", "cache-control": "no-store" },
        });
      } catch {
        return new Response("Telegram webhook'ini o'rnatib bo'lmadi. Tokenni tekshiring.", { status: 502 });
      }
    }

    if (request.method === "POST" && path === "/webhook") {
      if (!env.TELEGRAM_BOT_TOKEN || !env.SETUP_PASSWORD || env.SETUP_PASSWORD.length < 20 || !env.AI)
        return new Response("Worker noto'g'ri sozlangan.", { status: 503 });
      const received = request.headers.get("x-telegram-bot-api-secret-token") || "";
      const expected = await telegramSecret(env.SETUP_PASSWORD);
      if (received !== expected) return new Response("Forbidden", { status: 403 });
      const length = Number(request.headers.get("content-length") || "0");
      if (length > MAX_UPDATE_BYTES) return new Response("Too large", { status: 413 });
      let update;
      try {
        const raw = await request.text();
        if (raw.length > MAX_UPDATE_BYTES) return new Response("Too large", { status: 413 });
        update = JSON.parse(raw);
      } catch {
        return new Response("Bad JSON", { status: 400 });
      }
      ctx.waitUntil(processUpdate(update, env).catch(() => console.error("update_failed")));
      return new Response("OK", { status: 200 });
    }
    return new Response("Not found", { status: 404 });
  },
};
