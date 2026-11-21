# iPhone orqali BEPUL Levelup Mathh AI botini ishga tushirish

Bu yo'l uchun noutbuk, Render, pullik hosting yoki OpenAI API kaliti **kerak emas**.

**Texnologiya:** Cloudflare Workers (Telegram webhook) + Cloudflare Workers AI (bepul limitdagi `@cf/zai-org/glm-4.7-flash`) + GitHub Git integration.

## Nimalar ishlaydi?

- O'zbek tilida matematik savollarga AI javob.
- SAT Math savollari: `SAT: 2x+7=19`
- Milliy sertifikat savollari: `MS: x^2-5x+6=0`
- Oddiy savollar va `/start`, `/help`, `/kurslar`, `/privacy`.
- Telefon va kompyuter o'chiq bo'lsa ham, Telegram webhook orqali ishlaydi (bepul limit va xizmat mavjudligi doirasida).
- GitHub'ga yangi kod yozilsa, Cloudflare avtomatik deploy qila oladi.

**Cheklovlar:** Bu *Cloudflare uchun bepul versiya* hozircha faqat **matnli** savollarni qo'llab-quvvatlaydi; rasmli yechim va oldingi suhbat xotirasi qo'shilmagan. Asl Python versiya alohida turibdi. Cloudflare'dagi AI javob sifatini jonli sinash kerak.

## 1-qadam. Cloudflare akkauntingizga kiring

1. iPhone'dagi Safari'da https://dash.cloudflare.com/ oching.
2. Hisobingiz bo'lmasa, foydalanish shartlarini ko'rib chiqib ro'yxatdan o'ting; **Workers Free** rejimini tanlang. Pullik reja va karta talab qiladigan variantni tanlamang.
3. **Workers & Pages** ga kiring.
4. **Create application** ni bosing, **Import a repository** yoki **GitHub** variantini tanlang (interfeys nomi o'zgarishi mumkin).
5. GitHub'ga ruxsat bering va `goglaql7-debug/levelup-ai-bot` repository'sini tanlang.

## 2-qadam. Worker deploy

Konfiguratsiya fayli repository ildizida tayyor: `wrangler.jsonc`.

- Worker nomi: `levelup-mathh-ai-free` (**aniq shu nomni** tanlang)
- Root directory: repo root `/`
- Build command: `npm install` (agar so'ralsa)
- Deploy command: `npx wrangler deploy` (agar so'ralsa)
- Plan: **Free**.

**Save and Deploy** ni bosing. Worker manzili quyidagiga o'xshash bo'ladi:
`https://levelup-mathh-ai-free.SIZNING_SUBDOMAIN.workers.dev`

Agar Cloudflare deploymentdan keyin `AI` binding topilmadi desa, Worker'ning **Settings → Bindings** bo'limidan **Workers AI** qo'shing va nomini aynan `AI` qo'ying. Odatda `wrangler.jsonc` buni avtomatik yaratadi.

## 3-qadam. Maxfiy qiymatlarni Cloudflare ichida saqlang

Cloudflare dashboard → **Workers & Pages → levelup-mathh-ai-free → Settings → Variables and Secrets**.

**Add variable / secret**:

1. Name: `TELEGRAM_BOT_TOKEN`, Type: **Secret**, Value: @BotFather bergan **yangi** Telegram token.
2. Name: `SETUP_PASSWORD`, Type: **Secret**, Value: o'zingiz yaratgan **kamida 20 belgili, tasodifiy** parol.

Saqlang va kerak bo'lsa **Deploy** tugmasi bilan yangi sozlamalarni chiqarib qo'ying.

**Muhim:** Token va parolni GitHub kodi ichiga yoki ChatGPT chatiga yubormang. Avval chatga yuborilgan eski Telegram tokenini BotFather orqali bekor qilib, yangisini oling. `SETUP_PASSWORD` ni Apple Passwords yoki ishonchli parol menejerida saqlang.

## 4-qadam. Telefon orqali Telegram webhook'ini yoqing

Brauzerda Worker manzilingizning oxiriga `/setup` qo'shing:

`https://levelup-mathh-ai-free.SIZNING_SUBDOMAIN.workers.dev/setup`

Sahifada `SETUP_PASSWORD` ni kiriting va **Telegram botni faollashtirish** tugmasini bosing.

**“Bot webhook'i faollashtirildi!”** degan xabar chiqishi kerak.

Keyin Telegram'ga kiring, o'z botingizga `/start` va `SAT: 2x+7=19` yuboring.

## 5-qadam. Keyinchalik ChatGPT orqali yangilash

GitHub'ni ChatGPT bilan oldin ulab qo'ygansiz. Men `goglaql7-debug/levelup-ai-bot` repository'sidagi kodlarni sizning topshirig'ingiz asosida yangilay olaman. Cloudflare Git integration o'rnatilgach, GitHub `main` branch'dagi o'zgarishlar Worker'ga **avtomatik deploy** bo'ladi.

Bu **Cloudflare hisobini ChatGPT'ga to'g'ridan-to'g'ri ulash emas**. Cloudflare panelidagi sirlar, to'lov va xizmat sozlamalari sizning nazoratingizda qoladi.

## Narx va cheklovlar

2026-yil noyabr holatiga ko'ra:
- Workers Free: kuniga 100,000 HTTP so'rov chegarasi.
- Workers AI: kuniga 10,000 neuron bepul.
- Limit tugasa, tegishli operatsiyalar keyingi hisob davrigacha xato qaytarishi mumkin.
- Bepul resurslar kafolatli cheksiz xizmat emas; AI sifatiga va tezligiga ham model imkoniyatlari ta'sir qiladi.
- Bot qo'shimcha pullik xizmatga ulanmaguncha OpenAI API uchun to'lov qilinmaydi.

Rasmiy hujjatlar:
- https://developers.cloudflare.com/workers/ci-cd/builds/
- https://developers.cloudflare.com/workers/platform/limits/
- https://developers.cloudflare.com/workers-ai/platform/pricing/
- https://developers.cloudflare.com/workers-ai/models/glm-4.7-flash/
