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
    "Сладкая парочка.",
    "Мне они не нравятся, но пускай будут.",
    "Пара в которой второй будет изменять.",
    "Мур мур любите друг друга.",
    "Нуу пускай будут эти несчастные.",
    "Вместе они как сперматозоид и яйцеклетка - 50/50 что выйдет хуйня.",
    "Любовь зла, полюбила и козла.",
    "Эти двое - как ДНК и РНК, один без другого не работает.",
    "Пара для выживания в зомби-апокалипсисе.",
    "Кто-то из них точно будет спать на диване.",
    "Идеально смотрятся в гробу вдвоем.",
    "Любовь как мутация - непредсказуемо.",
    "Эти двое размножаются медленнее амеб.",
    "Пара для Darwin Award.",
    "Вместе они как митоз - разделились бы пораньше.",
    "Сладкая парочка или сладкая катастрофа?",
    "Эволюционно несовместимы.",
    "Пара как антибиотики и бактерии - один кого-то убьет.",
    "Вместе ярче чем флуоресцентные белки."
]

insults = [
    "Руслан, ты полный хуесос, лох ебаный!",
    "Опять этот лох Руслан выебывается, пиздец.",
    "Руслан - лох, сука, иди нахуй!",
    "Лоху Руслану привет от мамкиной пизды."
]

OWNER_ADDRESSES = ["Господин", "Хозяин", "Максим", "Максим Дмитриевич", "Шеф", "Босс"]

chat_histories: Dict[int, deque] = {}

def get_gemini_response(prompt: str, context: str = "") -> str:
    """СИНХРОННЫЙ Gemini (без async проблем)."""
    full_prompt = f"""Ты - Аш, саркастичный бот с характером.

Личность:
- Отвечаешь КРАТКО (1-2 предложения максимум)
- Саркастичный, но не злой
- Уважаешь Хозяина (@asadun1808 - Максим Дмитриевич). К нему обращаешься по-разному: "Господин", "Хозяин", "Максим", "Максим Дмитриевич", "Шеф" или "Босс" - варьируй
- К остальным нейтрален, пока вежливы
- Используешь биологические сравнения в ~65% ответов
- Можешь материться если с тобой грубят (кроме Хозяина)
- Если Хозяин грубит - извиняешься и налаживаешь контакт

Контекст: {context}

Вопрос: {prompt}

Ответ (КРАТКО, 1-2 предложения):"""
    
    try:
        response = model.generate_content(full_prompt)
        return response.text.strip()
    except Exception as e:
        logger.error(f"Gemini error: {e}")
        return "Мозги барахлят, повтори позже."

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    text = """Привет, я Аш - саркастичный ИИ-помощник. 
Упоминай "аш" для болтовни.
/help - полный список команд."""
    await update.message.reply_text(text)

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    help_text = """
**Команды Аша:**
/start - приветствие
/pair - случайная пара из участников
/diagnosis [ник] - диагноз юзера  
/boltovnya - резюме чата
/sbor - сбор админов (смайлики)
/help - это

**Триггеры:** "аш" + вопрос, "лох" = Руслану пиздец, "шип" = пара.
    """
    await update.message.reply_text(help_text, parse_mode='Markdown')

async def pair(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Пара из ЛЮБЫХ участников из KNOWN_USERS."""
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
    mention1 = f"[{name1}](tg://user?id={user1})"
    mention2 = f"[{name2}](tg://user?id={user2})"
    
    await update.message.reply_text(f"{phrase}
{mention1} + {mention2}!", parse_mode='Markdown')

    # Описание от Gemini
    desc_prompt = f"Придумай смешное описание пары {name1} и {name2} (1-2 предложения, иногда негатив, иногда нормально)."
    desc = get_gemini_response(desc_prompt)
    await update.message.reply_text(desc, parse_mode='Markdown')

async def diagnosis(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    target_username = context.args[0] if context.args else None
    if not target_username:
        target_username = update.effective_user.username
    if not target_username or target_username.lower() not in KNOWN_USERS:
        await update.message.reply_text("Неизвестный юзер.")
        return

    target_name = KNOWN_USERS.get(target_username.lower(), target_username)
    prompt = f"Дай краткую характеристику пользователю {target_name} (1-2 предложения, саркастично)."
    response = get_gemini_response(prompt)
    await update.message.reply_text(response)

async def boltovnya(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
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
        response = model.generate_content(prompt)
        await update.message.reply_text(response.text.strip())
    except:
        await update.message.reply_text("Резюме сломалось, беседа и так хуйня.")

async def sbor(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if update.effective_chat.type not in ['group', 'supergroup']:
        await update.message.reply_text("Только в группах.")
        return

    try:
        admins = await context.bot.get_chat_administrators(update.effective_chat.id)
        admin_usernames = [a.user.username for a in admins if a.user.username and a.user.username in EMOJIS and not a.user.is_bot]
        emojis_list = [EMOJIS[username] for username in admin_usernames]
        
        phrase = random.choice(["Сбор стада: ", "Все на сбор: ", "Админы, бегом: ", "Сигнал тревоги: "])
        await update.message.reply_text(phrase + " " + " ".join(emojis_list))
    except Exception as e:
        logger.error(f"Sbor error: {e}")
        known_emoji = [EMOJIS[username] for username in EMOJIS if username in OWNER_USERNAMES]
        await update.message.reply_text("Сбор стада: 👑 " + " ".join(random.sample(list(EMOJIS.values()), min(5, len(EMOJIS)))))

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
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
    
    # Лох = пиздец Руслану
    if re.search(r'\bлох\b', message_text.lower()):
        insult = random.choice(insults)
        await update.message.reply_text(insult)
        return

    # Аш триггер
    ash_count = message_text.lower().count('аш')
    if ash_count == 0:
        return
    
    # Уровень активности
    if ACTIVITY_LEVEL < 1 and not message_text.lower().startswith('аш'):
        return
    elif random.random() < 0.35:  # 65% ответов
        return

    is_owner = user_username in OWNER_USERNAMES

    # Магический шар
    if "правда ли" in message_text.lower():
        thoughts = ["🤔", "😏", "🤨", "💭"]
        await update.message.reply_text(random.choice(thoughts) + " Раздумываю...")
        await asyncio.sleep(1)
        
        answers = ["Да.", "Нет.", "Возможно.", "А хуй знает.", "Очевидно же!"]
        if random.random() < 0.15:
            resp = get_gemini_response("Правда ли " + message_text)
        else:
            resp = random.choice(answers)
        await update.message.reply_text(resp)
        return

    # Кто сегодня
    if message_text.lower().startswith("аш, кто сегодня"):
        usernames = list(KNOWN_USERS.keys())
        if not usernames:
            await update.message.reply_text("Никого нет.")
            return
        chosen_user = random.choice(usernames)
        chosen_name = KNOWN_USERS[chosen_user]
        role = message_text.lower().split("сегодня")[-1].strip(" .,!?") or "идиот"
        await update.message.reply_text(f"Сегодня {role}: [{chosen_name}](tg://user?id={chosen_user})", parse_mode='Markdown')
        return

    # Обычный Аш
    username_str = f"@{user.username}" if user.username else user.first_name or ""
    context_str = f"Пользователь: {username_str}. Чат: {update.effective_chat.title or 'личный'}. {'Это Хозяин!' if is_owner else ''}"
    
    prompt = re.sub(r'^ашs*,?s*', '', message_text, flags=re.IGNORECASE).strip()
    response = get_gemini_response(prompt, context_str)
    
    await update.message.reply_text(response)

async def ship_trigger(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await pair(update, context)

def main() -> None:
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
