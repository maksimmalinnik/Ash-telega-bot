import random
import asyncio
import signal
from telegram import Update, BotCommand
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    filters,
    ContextTypes
)
from google import genai

# Настройка Gemini AI
client = genai.Client(api_key="AIzaSyCD3lMA7zuR7dynDaGEotgU-zCo-wZnQkM")

# Токен бота
TOKEN = "8217181234:AAE7fk3O8Gry41CNZwZDGOvyVOqmEqpJ6ak"

# Хозяин бота
MASTER_USERNAME = "asadun1808"
MASTER_NAMES = ["Господин", "Хозяин", "Максим", "Максим Дмитриевич", "Шеф", "Босс"]

def get_master_name():
    return random.choice(MASTER_NAMES)

ACTIVITY_LEVEL = 5

KNOWN_USERS = {
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
    "OstapchukT": "Таня"
}

pair_phrases = [
    "🔥 Горячая пара дня:\n{} и {}!\nКупидон не промахнулся.",
    "💘 Алгоритм любви выбрал:\n{} ❤️ {}\nСудьба решила за вас.",
    "✨ Магия случайности свела:\n{} и {}!\nСовпадение? Не думаю.",
    "🎭 Драма дня! В главных ролях:\n{} и {}\nОскар за лучшую пару.",
    "🎪 Цирк уехал, а пара осталась:\n{} 🎡 {}\nАплодисменты.",
    "🌟 Звёзды сошлись для:\n{} и {}!\nГороскоп одобряет.",
    "🎲 Кубик судьбы выпал на:\n{} и {}\nВыпала счастливая комбинация.",
    "🎯 Прямо в яблочко! Пара дня:\n{} 🏹 {}\nМеткий выстрел Амура.",
    "🌈 Радужная пара дня:\n{} и {}!\nВместе они – полный спектр эмоций.",
    "🎸 Рок-н-ролл, детка! Пара:\n{} 🎤 {}\nДуэт года.",
    "🍕 Идеальное сочетание как пицца с ананасами:\n{} и {}\nНеожиданно, но интересно.",
    "🚀 Космическая пара дня:\n{} 🌙 {}\nХьюстон, у нас романтика.",
    "🎮 Кооператив дня активирован:\n{} 🕹️ {}\nPlayer 1 + Player 2.",
    "☕ Пара крепче эспрессо:\n{} и {}!\nВзбодрит всех вокруг.",
    "🎪 Та-дам! Пара из шляпы фокусника:\n{} 🎩 {}\nФокус удался.",
]

insults = [
    "пиздабол", "мудак", "долбоёб", "еблан", "хуесос", "мразь ебаная",
    "гандон", "петух конченый", "уёбок", "чмо ебливое", "мудила",
    "хуеплёт", "залупа", "шлюха", "блядина", "пидор", "говноед",
    "сука тупая", "ублюдок", "козёл ебаный", "пидрила", "хуй моржовый",
    "мудозвон", "членосос", "очкошник", "жопа с ушами", "дебил ебаный"
]

chat_history = []

def get_user_name(user):
    if user.username:
        username_lower = user.username.lower()
        if username_lower in KNOWN_USERS:
            known = KNOWN_USERS[username_lower]
            if isinstance(known, list):
                return known[0]
            return known
        return f"@{user.username}"
    name = user.first_name
    if user.last_name:
        name += f" {user.last_name}"
    return name

def get_user_mention(user):
    if user.username:
        return f"@{user.username}"
    name = user.first_name
    if user.last_name:
        name += f" {user.last_name}"
    return f"[{name}](tg://user?id={user.id})"

def is_master(user):
    return user.username and user.username.lower() == MASTER_USERNAME.lower()

async def get_ai_response(prompt, context=""):
    try:
        full_prompt = f"""Ты - Аш, саркастичный бот с характером.

Личность:
- Отвечаешь КРАТКО (1-2 предложения максимум)
- Саркастичный, но не злой
- Уважаешь Хозяина (@asadun1808 - Максим Дмитриевич). К нему обращаешься по-разному: "Господин", "Хозяин", "Максим", "Максим Дмитриевич", "Шеф" или "Босс" - варьируй
- К остальным нейтрален, пока вежливы
- Используешь биологические сравнения в ~65% ответов
- Можешь материться если с тобой грубят (кроме Хозяина)
- Если Хозяин грубит - извиняешься и налаживаешь контакт

{context}

Вопрос: {prompt}

Ответ (КРАТКО, 1-2 предложения):"""
        
        response = client.models.generate_content(
            model='gemini-2.0-flash-exp',
            contents=full_prompt
        )
        return response.text.strip()
    except Exception as e:
        return "Мозги перегрелись. Попробуй ещё раз."

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = (
        "👋 Аш на связи.\n\n"
        "Команды:\n"
        "/pair или просто «шип» — пара дня\n"
        "/skrestyt @ник1 @ник2 — скрестить двух людей\n"
        "/verdict [ник] — характеристика\n"
        "/citata — мудрость Хозяина\n"
        "/boltovnya — о чём тут болтали\n"
        "/sbor — позвать всех\n"
        "/help — эта справка\n\n"
        "Просто пиши «аш» для вопросов"
    )
    await update.message.reply_text(text)

async def pair_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await create_pair(update, context)

async def create_pair(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat = update.effective_chat
    if chat.type not in ['group', 'supergroup']:
        await update.message.reply_text("Только в группах работает.")
        return
    try:
        admins = await context.bot.get_chat_administrators(chat.id)
        participants = [admin.user for admin in admins if not admin.user.is_bot]
        if len(participants) < 2:
            await update.message.reply_text("Мало народу. Позовите ещё кого-нибудь.")
            return
        couple = random.sample(participants, 2)
        mention1 = get_user_mention(couple[0])
        mention2 = get_user_mention(couple[1])
        phrase = random.choice(pair_phrases)
        message = phrase.format(mention1, mention2)
        await update.message.reply_text(message, parse_mode='MarkdownV2')
    except Exception as e:
        await update.message.reply_text(f"Ошибка: {str(e)}")

async def insult_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    name = get_user_mention(user)
    insult = random.choice(insults)
    phrases = [
        f"{name}, ты {insult}.",
        f"{name} — {insult}. Записал.",
        f"Лох? Это про тебя, {name}, {insult}.",
        f"{name}, {insult} ебучий.",
    ]
    await update.message.reply_text(random.choice(phrases), parse_mode='MarkdownV2')

async def magic_ball(update: Update, context: ContextTypes.DEFAULT_TYPE, question: str):
    user = update.effective_user
    name = get_user_name(user)
    msg = await update.message.reply_text("🔮 Шар думает...")
    await asyncio.sleep(1.5)
    await msg.edit_text("✨ Советуюсь со звёздами...")
    await asyncio.sleep(1.5)
    if random.random() < 0.15:
        answer = f"{name}, как ты додумался меня спросить о такой хуйне?"
    else:
        answers = [
            "Да.", "Нет.", "Возможно.", "Частично.",
            "Определённо да.", "Определённо нет.",
            "Звёзды молчат.", "Без комментариев.",
            "Маловероятно.", "Очень вероятно.",
            "Спроси завтра.", "Лучше не знать."
        ]
        answer = random.choice(answers)
    await msg.edit_text(f"🔮 {answer}")

async def who_is_today(update: Update, context: ContextTypes.DEFAULT_TYPE, role: str):
    chat = update.effective_chat
    try:
        admins = await context.bot.get_chat_administrators(chat.id)
        participants = [admin.user for admin in admins if not admin.user.is_bot]
        if not participants:
            await update.message.reply_text("Никого нет. Странно.")
            return
        chosen = random.choice(participants)
        mention = get_user_mention(chosen)
        phrases = [
            f"{mention} сегодня {role}. Поздравляю.",
            f"Сегодня {role} — {mention}. Заслуженно.",
            f"{mention} удостоился звания '{role}'. Аплодисменты.",
            f"Барабанная дробь... {mention} — {role} дня!",
        ]
        await update.message.reply_text(random.choice(phrases), parse_mode='MarkdownV2')
    except Exception:
        await update.message.reply_text("Не могу выбрать. Технические шоколадки.")

async def skrestyt(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if len(context.args) < 2:
        await update.message.reply_text("Укажи двух участников. Пример: /skrestyt @nick1 @nick2")
        return
    user1 = context.args[0]
    user2 = context.args[1]
    prompt = f"Скрести пользователей {user1} и {user2}. Опиши результат кратко и с юмором (1-2 предложения)."
    response = await get_ai_response(prompt)
    await update.message.reply_text(response)

async def verdict(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        user = update.effective_user
        target = get_user_name(user)
    else:
        target = context.args[0]
    prompt = f"Дай краткую характеристику пользователю {target} (1-2 предложения, саркастично)."
    response = await get_ai_response(prompt)
    await update.message.reply_text(response)

async def citata(update: Update, context: ContextTypes.DEFAULT_TYPE):
    quotes = [
        "Грязь — это просто биомасса не на своём месте.",
        "Порядок в доме начинается с порядка в клетках.",
        "Если бактерии могут поддерживать гомеостаз, то и ты справишься с уборкой.",
        "Чистота — это не привычка, это симбиоз с пространством.",
        "Пыль — враг иммунитета. Тряпка — его союзник.",
        "В природе нет мусора, есть только круговорот веществ. Но дома — убирай, блять.",
        "Митохондрии — электростанция клетки. Пылесос — электростанция квартиры.",
        "Эволюция научила нас адаптироваться. Но к грязи адаптироваться не надо.",
        "Чистый дом — как здоровый организм: всё функционирует без сбоев.",
        "Если плесень захватила угол — это не биология, это капитуляция.",
    ]
    quote_text = random.choice(quotes)
    await update.message.reply_text(f'💬 Как говорил {get_master_name()}: "{quote_text}"')

async def boltovnya(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if len(chat_history) < 5:
        await update.message.reply_text("Тут ещё ничего не обсуждали. Тишина.")
        return
    recent = chat_history[-20:]
    messages_text = "\n".join([f"{msg['user']}: {msg['text']}" for msg in recent])
    prompt = f"Кратко (2-3 предложения) и саркастично резюмируй о чём болтали:\n{messages_text}"
    response = await get_ai_response(prompt)
    await update.message.reply_text(f"📊 {response}")

async def sbor(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat = update.effective_chat
    try:
        admins = await context.bot.get_chat_administrators(chat.id)
        mentions = [get_user_mention(admin.user) for admin in admins if not admin.user.is_bot]
        if not mentions:
            await update.message.reply_text("Никого нет. Пусто.")
            return
        phrases = [
            "📢 Сбор стада: ",
            "📣 Перекличка началась: ",
            "🔔 Все сюда, быстро: ",
            "⚠️ Явка обязательна: ",
        ]
        message = random.choice(phrases) + " ".join(mentions)
        await update.message.reply_text(message, parse_mode='MarkdownV2')
    except Exception:
        await update.message.reply_text("Не могу позвать. Связь плохая.")

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = """❓ Команды Аша:

/start — начать
/pair — пара дня
/skrestyt @ник1 @ник2 — скрестить двух участников
/verdict [ник] — характеристика
/citata — мудрость Хозяина
/boltovnya — о чём болтали
/sbor — позвать всех
/help — эта справка

Триггеры:
• шип → пара дня
• лох → оскорбление
• аш, правда ли... → магический шар
• аш, кто сегодня... → выбор участника
• просто «аш» — обращение к боту

Пиши, не стесняйся 😏"""
    await update.message.reply_text(text)

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not update.message or not update.message.text:
        return

    text = update.message.text.lower()
    user = update.effective_user
    chat_history.append({'user': get_user_name(user), 'text': update.message.text})

    if len(chat_history) > 100:
        chat_history.pop(0)

    if "шип" in text:
        await create_pair(update, context)
        return

    if "лох" in text and not text.startswith('/'):
        await insult_command(update, context)
        return

    if text.startswith("аш, правда ли"):
        question = text.replace("аш, правда ли", "").strip()
        await magic_ball(update, context, question)
        return

    if text.startswith("аш, кто сегодня"):
        role = text.replace("аш, кто сегодня", "").strip()
        if role:
            await who_is_today(update, context, role)
        return

    if "аш" in text and not text.startswith('/'):
        if ACTIVITY_LEVEL == 1 and not text.startswith("аш"):
            return
        if ACTIVITY_LEVEL <= 5 and "аш" not in text:
            return
        if ACTIVITY_LEVEL >= 8 and random.random() > 0.7:
            return

        name = get_user_name(user)
        is_master_user = is_master(user)
        context_info = f"Обращается: {name}"
        if is_master_user:
            context_info += " (это твой Хозяин, будь особенно уважителен)"

        response = await get_ai_response(update.message.text, context_info)
        await update.message.reply_text(response)

# ────────────────────────────────────────────────────────────────
# Запуск бота с правильным завершением для Render
# ────────────────────────────────────────────────────────────────

async def main():
    print("🤖 Аш запускается...")
    application = Application.builder().token(TOKEN).build()

    # Регистрация команд
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("pair", pair_command))
    application.add_handler(CommandHandler("skrestyt", skrestyt))
    application.add_handler(CommandHandler("verdict", verdict))
    application.add_handler(CommandHandler("citata", citata))
    application.add_handler(CommandHandler("boltovnya", boltovnya))
    application.add_handler(CommandHandler("sbor", sbor))
    application.add_handler(CommandHandler("help", help_command))

    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    # Установка команд в меню бота
    await application.bot.set_my_commands([
        BotCommand("start", "Начать общение"),
        BotCommand("pair", "Пара дня"),
        BotCommand("skrestyt", "Скрестить двух участников"),
        BotCommand("verdict", "Характеристика участника"),
        BotCommand("citata", "Мудрость Хозяина"),
        BotCommand("boltovnya", "О чём болтали"),
        BotCommand("sbor", "Собрать всех"),
        BotCommand("help", "Справка"),
    ])

    print("✅ Аш готов к работе!")
    print(f"🎭 Хозяин: @{MASTER_USERNAME}")
    print(f"📊 Уровень активности: {ACTIVITY_LEVEL}/10")
    print(f"👥 Известных участников: {len(KNOWN_USERS)}")
    print("\n🚀 Бот работает! Ожидание сообщений...\n")

    # Запуск
    await application.initialize()
    await application.start()
    await application.updater.start_polling(
        drop_pending_updates=True,
        allowed_updates=Update.ALL_TYPES
    )

    # Бесконечное ожидание + graceful shutdown
    try:
        await asyncio.Event().wait()
    except asyncio.CancelledError:
        pass
    finally:
        print("Получен сигнал завершения, gracefully shutting down...")
        await application.updater.stop()
        await application.stop()
        await application.shutdown()

def run():
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)

    # Обработка сигналов завершения (важно для Render)
    for sig in (signal.SIGINT, signal.SIGTERM):
        loop.add_signal_handler(sig, lambda: asyncio.create_task(shutdown(loop)))

    try:
        loop.run_until_complete(main())
    finally:
        loop.close()

async def shutdown(loop):
    tasks = [t for t in asyncio.all_tasks() if t is not asyncio.current_task()]
    for task in tasks:
        task.cancel()
    await asyncio.gather(*tasks, return_exceptions=True)
    loop.stop()

if __name__ == '__main__':
    run()
