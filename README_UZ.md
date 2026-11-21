# Levelup Mathh — AI Telegram bot

Bu loyiha o'quvchilarning matematika savollariga javob beradigan, **matn va fotosurat** qabul qiladigan Telegram botdir. Botning o'zi bepul ochiq kodli, lekin OpenAI API va hosting xizmati xarajat talab qilishi mumkin.

## Bot imkoniyatlari

- `/start`: SAT Math / Milliy sertifikat / Umumiy matematika yo'nalishlarini tugmalar bilan tanlash
- `/sat`, `/milliy`, `/umumiy`: rejimni o'zgartirish
- O'zbekcha, qadamma-qadam matematika tushuntirishlari
- Inglizcha SAT Math savollari va fotosuratdagi misollarni tahlil qilish
- Oxirgi 6 ta savol-javob juftligining matnini vaqtincha eslab qolish
- `/reset`: vaqtinchalik suhbat xotirasini tozalash
- `/kurslar`, `/privacy`, `/help`
- Har bir foydalanuvchi uchun bir soatlik savollar limiti

## 1. Telegram bot tokenini oling

Telegramdagi rasmiy **@BotFather** botini oching. `/newbot` bilan yangi bot yarating yoki mavjud botingizga yangi token oling. Oldingi token chatga yuborilgan bo'lsa, **BotFather'dan uni bekor qiling**. Haqiqiy tokenni hech qachon GitHub fayliga, commitga yoki chatga joylamang.

## 2. OpenAI API kalitini tayyorlang

OpenAI API hisobingizda kalit yarating: https://platform.openai.com/api-keys

**Eslatma:** ChatGPT Plus obunasi OpenAI API uchun avtomatik kredit bermaydi. API uchun alohida to'lov va limitlar amal qilishi mumkin.

## 3. O'rnatish (Windows)

Python 3.10+ o'rnatilgan kompyuterda:

```bash
python -m pip install -r requirements.txt
```

`.env.example` faylining nusxasini `.env` deb saqlang, unga **haqiqiy** token va API kalitni kiriting:

```dotenv
TELEGRAM_BOT_TOKEN=BotFather_bergan_yangi_token
OPENAI_API_KEY=OpenAI_API_kalitingiz
OPENAI_MODEL=gpt-4.1-mini
QUESTIONS_PER_HOUR=20
```

So'ng ishga tushiring:

```bash
python bot.py
```

Telegramda botingizga `/start` yuboring. Misol: `2x + 7 = 19`.

## 4. Telefonda ishlatish va serverga joylash

iPhone GitHub repository'sini ko'rish va hosting sozlash uchun yetarli. Biroq **GitHub kodi ishlatmaydi** — bot faqat doimiy ishlab turadigan Python jarayoniga joylashtirilganda javob beradi. Bu kod `run_polling` ishlatadi, shu sabab hostingda **background worker / process** kerak (oddiy static website emas).

Hosting panelida source'ni shu GitHub repository'ga ulang, so'ng:

- Build: `pip install -r requirements.txt`
- Start: `python bot.py`
- Environment variables: `TELEGRAM_BOT_TOKEN`, `OPENAI_API_KEY`, ixtiyoriy `OPENAI_MODEL` va `QUESTIONS_PER_HOUR`

Kalitlarni **faqat hostingning maxfiy Environment/Secrets qismiga** kiriting, GitHub kodi ichiga emas. Hostingning rejalari va 24/7 ishlash imkoniyati turlicha; bepul tariflarda uzluksiz ishlash kafolatlanmaydi. Bir bot tokeni bilan ikki parallel polling jarayonini yoqmang.

## 5. Testlar

```bash
python -m unittest discover -s tests -v
```

## Xavfsizlik va maxfiylik

- `.env` fayli `.gitignore` orqali GitHub'dan chiqarilgan.
- Matn va fotosuratlar javob olish uchun OpenAI APIga yuboriladi.
- Suhbat tarixi faqat bot ishlayotgan jarayonning xotirasida saqlanadi. `/reset` orqali o'chirish mumkin.
- OpenAI API so'rovlarida `store=False` qo'llaniladi, lekin bu uchinchi tomon servislarining barcha saqlash siyosatlarini bekor qilmaydi.
- Foydalanuvchilardan parol, pasport, karta yoki boshqa maxfiy ma'lumotlarni so'ramang.
- Bot hozircha ro'yxatga olish, to'lovlar yoki o'quvchilar ma'lumotlar bazasini o'z ichiga olmaydi.

## Rasmiy texnik manbalar

- Telegram Bot API: https://core.telegram.org/bots/api
- Python Telegram Bot: https://docs.python-telegram-bot.org/
- OpenAI API: https://platform.openai.com/docs/
