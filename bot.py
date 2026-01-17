import asyncio
import os
import logging
import random
import re
from typing import Dict, List, Any, Optional
from collections import deque
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
import google.genai as genai
from google.genai.types import HttpOptions

# Настройка логирования
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Конфигурация
TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')
GEMINI_API_KEY = os.getenv('GEMINI_API_KEY')

if not TELEGRAM_TOKEN or not GEMINI_API_KEY:
    raise ValueError("Missing environment variables TELEGRAM_TOKEN or GEMINI_API_KEY")

genai.configure(api_key=GEMINI_API_KEY)
model = genai.GenerativeModel('gemini-2.0-flash-exp')

ACTIVITY_LEVEL = 5
KNOWN_USERS: Dict[str, Any] = {
    "ronietka": "Верона",
    "fakwul": "Руслан",
    "bbbaaaannn": "Косинус",
    "anastasiash8": ["Хуянами", "Анастасия"],
    "justyayka": "Айк",
    "woolkod": "Милана",
    "wiixlxxw": "Вика",
    "Yreotouks": "Лиза",
    "annnetss": "Аня",
    "gggfter": "Влада",
    "kl2cdb": "Екатерина",
    "Sashanndra": "Саша",
    "qwerliiww": "Рита",
    "ma06_sha": "Маша",
    "vsleuuu": "Вася",
    "Fakbil": "Долбоеб",
    "hhjm99": "Андрей",
    "pl1tochkaa": "Алита",
    "raerinas": "Катя",
    "astahov67": "Костя",
    "OstapchukT": "Таня",
    "asadun1808": "Максим"
}

OWNER_USERNAMES = ["asadun1808"]

EMOJIS = {
    "ronietka": "👩",
    "fakwul": "👨",
    "bbbaaaannn": "📐",
    "anastasiash8": "😜",
    "justyayka": "🤖",
    "woolkod": "🌸",
    "wiixlxxw": "💄",
    "Yreotouks": "📚",
    "annnetss": "🎀",
    "gggfter": "👑",
    "kl2cdb": "📝",
    "Sashanndra": "🚀",
    "qwerliiww": "🎸",
    "ma06_sha": "🍎",
    "vsleuuu": "🛠",
    "Fakbil": "🤡",
    "hhjm99": "🎮",
    "pl1tochkaa": "🤖",
    "raerinas": "😺",
    "astahov67": "🏗",
    "OstapchukT": "🌹",
    "asadun1808": "👑"
}

pair_phrases = [
    "Идеальная пара для апокалипсиса!",
    "Кто бы подумал, что эти двое сойдутся?",
    "Любовь с первого удара по башке.",
    "Партия века!",
    "Сладкая парочка."
    "Мне они не нравятся, но пускай будут"
    "Пара в которой второй будет изменять"
    "Мур мур любите друг друга"
    "Нуу пускай будут эти несчастные"
]

insults = [
    "Руслан, ты лох ебаный!",
    "Опять этот лох Руслан выебывается, пиздец.",
    "Руслан - лох, сука, иди нахуй!",
    "Лоху Руслану привет от мамкиной пизды."
]

OWNER_ADDRESSES = ["Господин", "Хозяин", "Максим Дмитриевич", "Шеф", "Босс"]

# Глобальное хранилище истории по чатам (chat_id -> deque of messages)
chat_histories: Dict[int, deque] = {}

async def get_gemini_response(prompt: str, context: str = "") -> str:
    """Генерация ответа от Gemini."""
    full_prompt = f"""Ты - Аш, саркастичный бот с характером.

Личность:
- Отвечаешь КРАТКО (1-2 предложения максимум)
- Саркастичный, но не злой
- Уважаешь Хозяина (@asadun1808 - Максим Дмитриевич). К нему обращаешься по-разному: "Господин", "Хозяин", "Максим", "Максим Дмитриевич", "Шеф" или "Босс" - варьируй
- К остальным нейтрален, пока вежливы
- Используешь биологические сравнения в ~65% ответов
- Можешь материться если с тобой грубят (кроме Хозяина)
- Если Хозяин грубит - извиняешься и налаживаешь контакт с ним

Контекст: {context}

Вопрос: {prompt}

Ответ (КРАТКО, 1-2 предложения):"""
    
    try:
        response = await model.generate_content_async(full_prompt)
        return response.text.strip()
    except Exception as e:
        logger.error(f"Gemini error: {e}")
        return "Мозги барахлят, повтори позже."

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Команда /start."""
    text = """Привет, я Аш - ИИ-помощник. 
Упоминай "аш" для болтовни.
/help - полный список команд."""
    await update.message.reply_text(text)

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Команда /help."""
    help_text = """
**Команды:**
/start - приветствие
/pair - случайная пара админов
/diagnosis [ник] - диагноз юзера
/boltovnya - резюме чата
/sbor - сбор админов
/help - это

**Триггеры:** "аш" + вопрос, "лох" для Руслана.
    """
    await update.message.reply_text(help_text, parse_mode='Markdown')

async def pair(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Команда /pair."""
    if update.effective_chat.type not in ['group', 'supergroup']:
        await update.message.reply_text("Только в группах, кретин.")
        return

    try:
        admins = await context.bot.get_chat_administrators(update.effective_chat.id)
        human_admins = [admin for admin in admins if not admin.user.is_bot]
        if len(human_admins) < 2:
            await update.message.reply_text("Мало админов для пары.")
            return

        admin1, admin2 = random.sample(human_admins, 2)
        mention1 = admin1.user.mention_html()
        mention2 = admin2.user.mention_html()
        
        phrase = random.choice(pair_phrases)
        await update.message.reply_text(f"{phrase} {mention1} и {mention2}!")

        # Описание от Gemini
        desc_prompt = f"Придумай смешное описание пары {admin1.user.username or admin1.user.first_name} и {admin2.user.username or admin2.user.first_name} (1-2 предложения, иногда негатив, иногда нормально)."
        desc = await get_gemini_response(desc_prompt)
        await update.message.reply_text(desc)
    except Exception as e:
        logger.error(f"Pair error: {e}")
        await update.message.reply_text("Что-то сломалось в matchmaking.")

async def diagnosis(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Команда /diagnosis."""
    target_username = context.args[0] if context.args else update.effective_user.username
    if not target_username:
        await update.message.reply_text("Ник не найден.")
        return

    target_name = KNOWN_USERS.get(target_username.lower(), target_username)
    prompt = f"Дай краткую характеристику пользователю {target_name} (1-2 предложения, саркастично)."
    response = await get_gemini_response(prompt)
    await update.message.reply_text(response)

async def boltovnya(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Команда /boltovnya."""
    chat_id = update.effective_chat.id
    history = chat_histories.get(chat_id, deque(maxlen=100))
    
    if len(history) < 5:
        await update.message.reply_text("Тишина в эфире, мертвецы.")
        return

    recent = list(history)[-50:]
    messages_text = "
".join([f"{msg.get('user', 'Anon')}: {msg['text']}" for msg in recent])
    prompt = f"Кратко (2-3 предложения) и саркастично резюмируй о чём болтали в последних 50 сообщениях: {messages_text}"
    
    try:
        response = await model.generate_content_async(prompt)
        await update.message.reply_text(response.text.strip())
    except:
        await update.message.reply_text("Резюме сломалось, беседа и так хуйня.")

async def sbor(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Команда /sbor."""
    if update.effective_chat.type not in ['group', 'supergroup']:
        await update.message.reply_text("Только в группах.")
        return

    try:
        admins = await context.bot.get_chat_administrators(update.effective_chat.id)
        human_admins = [a.user.username for a in admins if not a.user.is_bot and a.user.username in EMOJIS]
        emojis_list = [EMOJIS[username] for username in human_admins if username in EMOJIS]
        
        phrase = random.choice(["Сбор стада: ", "Все на сбор: ", "Админы, бегом: ", "Сигнал тревоги: "])
        await update.message.reply_text(phrase + " ".join(emojis_list))
    except Exception as e:
        logger.error(f"Sbor error: {e}")
        await update.message.reply_text("Сбор провалился.")

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Обработчик сообщений."""
    message_text = update.message.text or ""
    chat_id = update.effective_chat.id
    user = update.effective_user
    
    # Сохраняем историю
    if chat_id not in chat_histories:
        chat_histories[chat_id] = deque(maxlen=100)
    chat_histories[chat_id].append({
        'user': user.username or user.first_name or 'Anon',
        'text': message_text
    })

    user_username = user.username.lower() if user.username else None
    
    # Лох - оскорбление Руслана
    if re.search(r'\bлох\b', message_text.lower()):
        insult = random.choice(insults)
        await update.message.reply_text(insult)
        return

    # Проверка активности для "аш"
    ash_count = message_text.lower().count('аш')
    if ash_count == 0:
        return
    
    if ACTIVITY_LEVEL < 1 and not message_text.lower().startswith('аш'):
        return
    elif random.random() < 0.35:  # ~65% шанс ответа для level 5
        return

    is_owner = user_username in OWNER_USERNAMES

    # Магический шар
    if "аш, правда ли" in message_text.lower():
        thoughts = ["🤔", "😏", "🤨", "💭"]
        await update.message.reply_text(random.choice(thoughts) + " Раздумываю...")
        
        answers = ["Да.", "Нет.", "Возможно.", "А хуй знает.", "Очевидно же!"]
        sarc = random.random() < 0.15
        if sarc:
            await asyncio.sleep(1)
            resp = await get_gemini_response("Правда ли " + message_text)
        else:
            resp = random.choice(answers)
        await update.message.reply_text(resp)
        return

    # Кто сегодня...
    if message_text.lower().startswith("аш, кто сегодня"):
        try:
            admins = await context.bot.get_chat_administrators(chat_id)
            human_admins = [a.user for a in admins if not a.user.is_bot]
            if not human_admins:
                await update.message.reply_text("Нет админов.")
                return
            chosen = random.choice(human_admins).mention_html()
            role = message_text.split("сегодня")[-1].strip() or "идиот"
            await update.message.reply_text(f"Сегодня {role}: {chosen}")
        except:
            await update.message.reply_text("Не могу выбрать.")
        return

    # Обычный запрос к Ашу
    username_str = f"@{user.username}" if user.username else user.first_name or ""
    context_str = f"Пользователь: {username_str}. Чат: {update.effective_chat.title or 'личный'}."
    if is_owner:
        context_str += " Это Хозяин!"
    
    prompt = message_text.replace("аш", "").strip()
    response = await get_gemini_response(prompt, context_str)
    
    await update.message.reply_text(response)

async def ship_trigger(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Триггер шип."""
    await pair(update, context)

def main() -> None:
    """Запуск бота."""
    application = Application.builder().token(TELEGRAM_TOKEN).build()

    # Команды
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("pair", pair))
    application.add_handler(CommandHandler("diagnosis", diagnosis))
    application.add_handler(CommandHandler("boltovnya", boltovnya))
    application.add_handler(CommandHandler("sbor", sbor))

    # Триггеры
    application.add_handler(MessageHandler(filters.Regex(r'шип'), ship_trigger))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    logger.info("Запуск Аша...")
    application.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == '__main__':
    main()
