import os
import logging
import random
import re
from typing import Dict, List, Any
from collections import deque
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
import google.genai as genai

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')
GEMINI_API_KEY = os.getenv('GEMINI_API_KEY')

if not TELEGRAM_TOKEN or not GEMINI_API_KEY:
    raise ValueError("Missing TELEGRAM_TOKEN or GEMINI_API_KEY")

genai.configure(api_key=GEMINI_API_KEY)
model = genai.GenerativeModel('gemini-2.0-flash-exp')

KNOWN_USERS = {
    "ronietka": "Верона", "fakwul": "Руслан", "bbbaaaannn": "Косинус",
    "anastasiash8": ["Хуянами", "Анастасия"], "justyayka": "Айк",
    "woolkod": "Милана", "wiixlxxw": "Вика", "Yreotouks": "Лиза",
    "annnetss": "Аня", "gggfter": "Влада", "kl2cdb": "Екатерина",
    "Sashanndra": "Саша", "qwerliiww": "Рита", "ma06_sha": "Маша",
    "vsleuuu": "Вася", "Fakbil": "Долбоеб", "hhjm99": "Андрей",
    "pl1tochkaa": "Алита", "raerinas": "Катя", "astahov67": "Костя",
    "OstapchukT": "Таня", "asadun1808": "Максим"
}

EMOJIS = {
    "ronietka": "👩", "fakwul": "👨", "bbbaaaannn": "📐", "anastasiash8": "😜",
    "justyayka": "🤖", "woolkod": "🌸", "wiixlxxw": "💄", "Yreotouks": "📚",
    "annnetss": "🎀", "gggfter": "👑", "kl2cdb": "📝", "Sashanndra": "🚀",
    "qwerliiww": "🎸", "ma06_sha": "🍎", "vsleuuu": "🛠", "Fakbil": "🤡",
    "hhjm99": "🎮", "pl1tochkaa": "🤖", "raerinas": "😺", "astahov67": "🏗",
    "OstapchukT": "🌹", "asadun1808": "👑"
}

pair_phrases = [
    "Идеальная пара для апокалипсиса!", "Кто бы подумал что эти двое сойдутся?",
    "Любовь с первого удара по башке.", "Партия века!", "Сладкая парочка.",
    "Мне они не нравятся но пускай будут.", "Пара в которой второй будет изменять.",
    "Мур мур любите друг друга.", "Нуу пускай будут эти несчастные.",
    "Вместе как сперматозоид и яйцеклетка - 50/50 что выйдет хуйня.",
    "Любовь зла полюбила и козла.", "Эти двое как ДНК и РНК.",
    "Пара для зомби-апокалипсиса.", "Кто-то будет спать на диване.",
    "Идеально смотрятся в гробу вдвоем.", "Любовь как мутация."
]

insults = [
    "Руслан ты полный хуесос лох ебаный!", "Опять этот лох Руслан выебывается пиздец.",
    "Руслан - лох сука иди нахуй!", "Лоху Руслану привет от мамкиной пизды."
]

chat_histories = {}
OWNER_USERNAMES = ["asadun1808"]

def get_gemini_response(prompt, context=""):
    full_prompt = f"""Ты - Аш саркастичный бот.

Личность:
- КРАТКО (1-2 предложения)
- Саркастичный но не злой  
- Хозяина (@asadun1808) зовешь: Господин/Хозяин/Максим/Шеф/Босс
- Биологические сравнения в 65% ответов
- Матишься если грубят (кроме Хозяина)

Контекст: {context}
Вопрос: {prompt}
Ответ КРАТКО:"""
    
    try:
        response = model.generate_content(full_prompt)
        return response.text.strip()
    except Exception as e:
        logger.error(f"Gemini error: {e}")
        return "Мозги барахлят повтори позже."

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Привет я Аш - саркастичный ИИ. Упоминай 'аш' для болтовни. /help - команды.")

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    help_text = """**Команды:**
/start - приветствие
/pair - случайная пара  
/diagnosis [ник] - диагноз юзера
/boltovnya - резюме чата
/sbor - сбор админов смайликами
/help - это

**Триггеры:** "аш" + вопрос, "лох" = Руслану пиздец, "шип" = пара."""
    await update.message.reply_text(help_text, parse_mode='Markdown')

async def pair(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_chat.type not in ['group', 'supergroup']:
        await update.message.reply_text("Только в группах.")
        return

    usernames = list(KNOWN_USERS.keys())
    if len(usernames) < 2:
        await update.message.reply_text("Мало народу.")
        return

    user1, user2 = random.sample(usernames, 2)
    name1 = KNOWN_USERS[user1]
    name2 = KNOWN_USERS[user2]
    phrase = random.choice(pair_phrases)
    
    # ✅ БЕЗ f-строк - обычные строки
    text = phrase + "
[" + name1 + "](tg://user?id=" + user1 + ") + [" + name2 + "](tg://user?id=" + user2 + ")!"
    await update.message.reply_text(text, parse_mode='Markdown')

    desc_prompt = "Придумай смешное описание пары " + name1 + " и " + name2 + " (1-2 предложения)."
    desc = get_gemini_response(desc_prompt)
    await update.message.reply_text(desc, parse_mode='Markdown')

async def diagnosis(update: Update, context: ContextTypes.DEFAULT_TYPE):
    target_username = context.args[0] if context.args else update.effective_user.username
    if not target_username or target_username.lower() not in KNOWN_USERS:
        await update.message.reply_text("Неизвестный юзер.")
        return

    target_name = KNOWN_USERS[target_username.lower()]
    prompt = "Дай краткую характеристику пользователю " + str(target_name) + " (1-2 предложения саркастично)."
    response = get_gemini_response(prompt)
    await update.message.reply_text(response)

async def boltovnya(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    history = chat_histories.get(chat_id, deque(maxlen=100))
    
    if len(history) < 5:
        await update.message.reply_text("Тишина в эфире мертвецы.")
        return

    recent = list(history)[-50:]
    messages_text = "
".join([f"{msg.get('user', 'Anon')}: {msg['text']}" for msg in recent])
    prompt = "Кратко (2-3 предложения) саркастично резюмируй последние 50 сообщений: " + messages_text
    
    try:
        response = model.generate_content(prompt)
        await update.message.reply_text(response.text.strip())
    except:
        await update.message.reply_text("Резюме сломалось беседа и так хуйня.")

async def sbor(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_chat.type not in ['group', 'supergroup']:
        await update.message.reply_text("Только в группах.")
        return

    try:
        admins = await context.bot.get_chat_administrators(update.effective_chat.id)
        admin_usernames = [a.user.username for a in admins if a.user.username and a.user.username in EMOJIS and not a.user.is_bot]
        emojis_list = [EMOJIS[username] for username in admin_usernames]
        phrase = random.choice(["Сбор стада: ", "Все на сбор: ", "Админы бегом: "])
        await update.message.reply_text(phrase + " " + " ".join(emojis_list))
    except:
        await update.message.reply_text("Сбор стада: 👑 👨 📐 😜 🤖 🌸 💄 📚 🎀 👑")

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    message_text = update.message.text or ""
    chat_id = update.effective_chat.id
    user = update.effective_user
    
    if chat_id not in chat_histories:
        chat_histories[chat_id] = deque(maxlen=100)
    chat_histories[chat_id].append({'user': user.username or user.first_name or 'Anon', 'text': message_text})

    user_username = user.username.lower() if user.username else None
    
    if re.search(r'\bлох\b', message_text.lower()):
        insult = random.choice(insults)
        await update.message.reply_text(insult)
        return

    ash_count = message_text.lower().count('аш')
    if ash_count == 0:
        return

    if random.random() < 0.35:
        return

    is_owner = user_username in OWNER_USERNAMES

    if "правда ли" in message_text.lower():
        await update.message.reply_text(random.choice(["🤔", "😏", "🤨", "💭"]) + " Раздумываю...")
        await asyncio.sleep(1)
        if random.random() < 0.15:
            resp = get_gemini_response("Правда ли " + message_text)
        else:
            resp = random.choice(["Да.", "Нет.", "Возможно.", "А хуй знает.", "Очевидно же!"])
        await update.message.reply_text(resp)
        return

    if message_text.lower().startswith("аш, кто сегодня"):
        usernames = list(KNOWN_USERS.keys())
        chosen_user = random.choice(usernames)
        chosen_name = KNOWN_USERS[chosen_user]
        role = message_text.lower().split("сегодня")[-1].strip(" .,!?") or "идиот"
        text = "Сегодня " + role + ": [" + chosen_name + "](tg://user?id=" + chosen_user + ")"
        await update.message.reply_text(text, parse_mode='Markdown')
        return

    username_str = f"@{user.username}" if user.username else user.first_name or ""
    context_str = "Пользователь: " + username_str + ". Чат: " + (update.effective_chat.title or 'личный')
    if is_owner:
        context_str += ". Это Хозяин!"
    
    prompt = re.sub(r'^ашs*,?s*', '', message_text, flags=re.IGNORECASE).strip()
    response = get_gemini_response(prompt, context_str)
    await update.message.reply_text(response)

async def ship_trigger(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await pair(update, context)

def main():
    application = Application.builder().token(TELEGRAM_TOKEN).build()

    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("pair", pair))
    application.add_handler(CommandHandler("diagnosis", diagnosis))
    application.add_handler(CommandHandler("boltovnya", boltovnya))
    application.add_handler(CommandHandler("sbor", sbor))
    application.add_handler(MessageHandler(filters.Regex(r'шип', re.IGNORECASE), ship_trigger))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    logger.info("🚀 Аш запущен!")
    application.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == '__main__':
    main()
