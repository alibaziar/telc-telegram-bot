import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup, KeyboardButton
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, MessageHandler, filters, ContextTypes
from telegram.request import HTTPXRequest
import datetime
import pytz
import json
import os
from dotenv import load_dotenv

# بارگذاری تنظیمات
load_dotenv()
BOT_TOKEN = os.getenv('BOT_TOKEN')
TIMEZONE = pytz.timezone(os.getenv('TIMEZONE', 'Asia/Tehran'))

# تنظیم logging
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

# فایل ذخیره داده‌ها
DATA_FILE = 'user_data.json'

# ============ توابع مدیریت داده ============

def load_user_data():
    """بارگذاری اطلاعات کاربران"""
    if os.path.exists(DATA_FILE):
        try:
            with open(DATA_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        except:
            return {}
    return {}

def save_user_data(data):
    """ذخیره اطلاعات کاربران"""
    with open(DATA_FILE, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def init_user(user_id):
    """مقداردهی اولیه کاربر جدید"""
    users = load_user_data()
    user_id_str = str(user_id)
    
    if user_id_str not in users:
        users[user_id_str] = {
            'name': '',
            'current_week': 1,
            'streak': 0,
            'total_days': 0,
            'checklist': {'block1': False, 'block2': False, 'sleep': False},
            'penalty': 0,
            'mock_tests': [],
            'errors': [],
            'skills': {'reading': 6, 'listening': 7, 'writing': 5, 'speaking': 4},
            'last_checklist_date': None,
            'start_date': datetime.datetime.now(TIMEZONE).strftime('%Y-%m-%d'),
            'completed_weeks': []
        }
        save_user_data(users)
    
    return users[user_id_str]

# ============ برنامه 12 هفته‌ای ============

BOOTCAMP_SCHEDULE = {
    1: {
        "focus": "مبانی گرامر و ساختارهای ساده",
        "grammar": ["Present Simple & Continuous", "Past Simple & Continuous", "Question formation"],
        "vocabulary": ["Daily routines", "Family & relationships", "Time expressions"],
        "daily_tasks": [
            "5 جمله با Present Simple بنویس",
            "10 دقیقه تمرین تلفظ با shadowing",
            "یک پاراگراف درباره خانواده‌ات بخوان"
        ]
    },
    2: {
        "focus": "گرامر میانی و توسعه واژگان",
        "grammar": ["Present Perfect", "Future forms", "Modal verbs"],
        "vocabulary": ["Work & professions", "Travel", "Food"],
        "daily_tasks": [
            "یک خبر کوتاه بخوان و خلاصه کن",
            "5 جمله با Present Perfect",
            "تمرین گفتن برنامه‌های هفته آینده"
        ]
    },
    3: {
        "focus": "ساختارهای پیچیده‌تر",
        "grammar": ["Passive voice", "Relative clauses", "Conjunctions"],
        "vocabulary": ["Technology", "Environment", "Health"],
        "daily_tasks": [
            "یک مقاله درباره محیط زیست بخوان",
            "3 جمله Passive بنویس",
            "تمرین دادن نظر با 'Meiner Meinung nach...'"
        ]
    },
    4: {
        "focus": "مهارت‌های نوشتاری",
        "grammar": ["Reported speech", "Conditional sentences", "Infinitive"],
        "vocabulary": ["Education", "Media", "Culture"],
        "daily_tasks": [
            "تمرین نوشتن ایمیل رسمی",
            "خواندن یک فصل از کتاب",
            "تمرین If-clauses"
        ]
    },
    5: {
        "focus": "تقویت Listening",
        "grammar": ["Word order", "Prepositions", "Adjective endings"],
        "vocabulary": ["Shopping", "Housing", "Transport"],
        "daily_tasks": [
            "10 دقیقه Dictation از ویدیو",
            "تمرین توضیح مسیر",
            "نوشتن درباره خانه‌ی ایده‌آل"
        ]
    },
    6: {
        "focus": "Mock Exam اول",
        "grammar": ["Review all structures"],
        "vocabulary": ["All topics review"],
        "daily_tasks": [
            "یک آزمون کامل Reading",
            "تحلیل اشتباهات",
            "تمرین Speaking با ضبط صدا"
        ]
    },
    7: {
        "focus": "استراتژی‌های آزمون",
        "grammar": ["Advanced conjunctions", "Subjunctive II"],
        "vocabulary": ["Politics", "Economy", "Global issues"],
        "daily_tasks": [
            "تمرین خواندن سریع",
            "نوشتن outline برای موضوعات",
            "تمرین جواب به سوالات غیرمنتظره"
        ]
    },
    8: {
        "focus": "تسلط بر Speaking",
        "grammar": ["Idiomatic expressions", "Phrasal verbs"],
        "vocabulary": ["Opinions", "Linking words", "Formal language"],
        "daily_tasks": [
            "تمرین یک موضوع Speaking ۳ دقیقه",
            "ضبط صدای خودت",
            "یادگیری 5 idiom جدید"
        ]
    },
    9: {
        "focus": "Mock Exam دوم",
        "grammar": ["Full review"],
        "vocabulary": ["Exam vocabulary"],
        "daily_tasks": [
            "یک بخش کامل آزمون",
            "تحلیل نقاط ضعف",
            "تمرین تخصصی"
        ]
    },
    10: {
        "focus": "رفع نقاط ضعف",
        "grammar": ["Personal weak points"],
        "vocabulary": ["Gap-filling"],
        "daily_tasks": [
            "2 ساعت روی ضعیف‌ترین مهارت",
            "مرور flashcards",
            "گفتگو با native speaker"
        ]
    },
    11: {
        "focus": "تثبیت و اعتماد به نفس",
        "grammar": ["Light review"],
        "vocabulary": ["Active recall"],
        "daily_tasks": [
            "مرور نکات کلیدی",
            "تمرین آرامش در استرس",
            "شبیه‌سازی روز آزمون"
        ]
    },
    12: {
        "focus": "آماده‌سازی نهایی",
        "grammar": ["Quick review"],
        "vocabulary": ["Final list"],
        "daily_tasks": [
            "استراحت ذهنی",
            "مرور نکات آزمون",
            "آماده‌سازی روحی"
        ]
    }
}

# ============ برنامه روزانه ============

def get_daily_schedule(day_name):
    """برگرداندن برنامه روزانه"""
    schedules = {
        'یکشنبه': """📅 برنامه یکشنبه

🌅 صبح:
06:30 - بیدار شدن
07:00 - صبحانه + فلش‌کارت (15 دقیقه)
08:00 - 📚 بلوک اول: Lesen + Grammatik (1.5 ساعت)
09:30 - کار فروش

🏫 بعدازظهر:
13:30 - کلاس زبان (3 ساعت)
16:30 - باشگاه + پادکست

🌙 شب:
19:00 - 🎧 بلوک دوم: Hören (45 دقیقه)
21:00 - آزاد با دوستان
23:00 - 😴 خواب حتماً!""",

        'دوشنبه': """📅 برنامه دوشنبه

🌅 صبح:
06:30 - بیدار شدن
07:00 - صبحانه + فلش‌کارت
08:00 - ✍️ بلوک اول: Schreiben (1 ساعت)
09:00 - کار فروش

🏫 بعدازظهر:
16:00 - 📝 بلوک دوم: Mock Test یک بخش (1.5 ساعت)
17:30 - باشگاه

🌙 شب:
20:00 - مرور اشتباهات (30 دقیقه)
21:00 - آزاد
23:00 - 😴 خواب""",

        'سه‌شنبه': """📅 برنامه سه‌شنبه

🌅 صبح:
06:30 - بیدار شدن
07:00 - صبحانه + فلش‌کارت
08:00 - 📚 بلوک اول: Lesen + Grammatik (1.5 ساعت)

🏫 بعدازظهر:
12:00 - 🗣️ کلاس مکالمه
13:30 - کلاس زبان (3 ساعت)
16:30 - باشگاه + پادکست

🌙 شب:
19:00 - 🎧 بلوک دوم: Hören (45 دقیقه)
21:00 - آزاد
23:00 - 😴 خواب""",

        'چهارشنبه': """📅 برنامه چهارشنبه

🌅 صبح:
06:30 - بیدار شدن
07:00 - صبحانه + فلش‌کارت
08:00 - ✍️ بلوک اول: Schreiben (1 ساعت)
09:00 - کار فروش

🏫 بعدازظهر:
16:00 - 📝 بلوک دوم: Mock Test یک بخش (1.5 ساعت)
17:30 - باشگاه

🌙 شب:
20:00 - مرور اشتباهات
21:00 - آزاد
23:00 - 😴 خواب""",

        'پنج‌شنبه': """📅 برنامه پنج‌شنبه

🌅 صبح:
06:30 - بیدار شدن
07:00 - صبحانه + فلش‌کارت
08:00 - 📚 بلوک اول: Lesen + Grammatik (1.5 ساعت)

🏫 بعدازظهر:
13:30 - کلاس زبان (3 ساعت)
16:30 - باشگاه + پادکست

🌙 شب:
19:00 - 🎧 بلوک دوم: Hören (45 دقیقه)
21:00 - آزاد
23:00 - 😴 خواب""",

        'جمعه': """📅 برنامه جمعه

🌅 صبح:
آزاد - خانواده/دوستان

📊 بعدازظهر:
15:00 - بازنگری هفتگی (1 ساعت)
16:00 - 📝 Mock Test کامل (2.5 ساعت)

🌙 شب: آزاد""",

        'شنبه': """📅 برنامه شنبه

🌅 صبح:
🎥 ویدیوهای DW یا Easy German (1 ساعت)

🌙 بعدازظهر/شب:
آزاد - پادکست + گردش"""
    }
    
    return schedules.get(day_name, "برنامه‌ای تعریف نشده")

# ============ Handlers ============

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """شروع کار با ربات"""
    user_id = update.effective_user.id
    init_user(user_id)
    
    keyboard = [
        [KeyboardButton("📅 برنامه امروز"), KeyboardButton("✅ چک‌لیست")],
        [KeyboardButton("📊 آمار من"), KeyboardButton("📚 برنامه هفته")],
        [KeyboardButton("📝 Mock Test"), KeyboardButton("❌ دفتر اشتباهات")],
        [KeyboardButton("🎯 تنظیم هفته"), KeyboardButton("💡 راهنما")]
    ]
    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
    
    welcome_text = """🎓 به Boot Camp telc B2 خوش اومدی!

این ربات یه همراه واقعی برای موفقیت توئه، نه فقط یه ربات معمولی! 🔥

چیکارا می‌کنه:
✅ برنامه روزانه دقیق
✅ چک‌لیست تعاملی با Streak
✅ سیستم جریمه (پایبندی = پول!)
✅ مدیریت Mock Test
✅ دفتر اشتباهات شخصی
✅ گزارش پیشرفت هفتگی

🎯 اولین قدم:
اسمت رو بهم بگو تا باهم شروع کنیم!
(مثلاً: علی)"""

    await update.message.reply_text(welcome_text, reply_markup=reply_markup)

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """مدیریت پیام‌های متنی"""
    user_id = update.effective_user.id
    text = update.message.text
    users = load_user_data()
    user_data = users.get(str(user_id), {})
    
    # ثبت نام
    if not user_data.get('name'):
        users[str(user_id)]['name'] = text
        save_user_data(users)
        await update.message.reply_text(
            f"🎉 عالی {text}!\n\n"
            "حالا از منوی پایین استفاده کن.\n"
            "پیشنهاد میدم با '📅 برنامه امروز' شروع کنی! 👇"
        )
        return
    
    # برنامه امروز
    if text == "📅 برنامه امروز":
        now = datetime.datetime.now(TIMEZONE)
        day_name = now.strftime('%A')
        day_mapping = {
            'Saturday': 'شنبه', 'Sunday': 'یکشنبه', 'Monday': 'دوشنبه',
            'Tuesday': 'سه‌شنبه', 'Wednesday': 'چهارشنبه', 
            'Thursday': 'پنج‌شنبه', 'Friday': 'جمعه'
        }
        persian_day = day_mapping[day_name]
        schedule = get_daily_schedule(persian_day)
        
        # اضافه کردن وظایف هفته جاری
        week_data = BOOTCAMP_SCHEDULE.get(user_data.get('current_week', 1))
        tasks_text = "\n\n🎯 وظایف ویژه این هفته:\n"
        for i, task in enumerate(week_data['daily_tasks'], 1):
            tasks_text += f"{i}. {task}\n"
        
        await update.message.reply_text(schedule + tasks_text)
    
    # چک‌لیست
    elif text == "✅ چک‌لیست":
        await show_checklist(update, context)
    
    # آمار
    elif text == "📊 آمار من":
        await show_stats(update, context)
    
    # برنامه هفته
    elif text == "📚 برنامه هفته":
        await show_week_plan(update, context)
    
    # Mock Test
    elif text == "📝 Mock Test":
        await show_mock_test_menu(update, context)
    
    # دفتر اشتباهات
    elif text == "❌ دفتر اشتباهات":
        await show_errors(update, context)
    
    # تنظیم هفته
    elif text == "🎯 تنظیم هفته":
        await set_week_menu(update, context)
    
    # راهنما
    elif text == "💡 راهنما":
        await show_help(update, context)

async def show_checklist(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """نمایش چک‌لیست روزانه"""
    user_id = update.effective_user.id
    users = load_user_data()
    user_data = users[str(user_id)]
    
    today = datetime.datetime.now(TIMEZONE).strftime('%Y-%m-%d')
    
    # ریست چک‌لیست اگه روز جدیده
    if user_data.get('last_checklist_date') != today:
        user_data['checklist'] = {'block1': False, 'block2': False, 'sleep': False}
        user_data['last_checklist_date'] = today
        users[str(user_id)] = user_data
        save_user_data(users)
    
    checklist = user_data['checklist']
    
    block1_icon = "✅" if checklist['block1'] else "⬜"
    block2_icon = "✅" if checklist['block2'] else "⬜"
    sleep_icon = "✅" if checklist['sleep'] else "⬜"
    
    keyboard = [
        [InlineKeyboardButton(f"{block1_icon} بلوک صبح (1.5 ساعت)", callback_data="check_block1")],
        [InlineKeyboardButton(f"{block2_icon} بلوک بعدازظهر (1 ساعت)", callback_data="check_block2")],
        [InlineKeyboardButton(f"{sleep_icon} خواب ساعت 23:00", callback_data="check_sleep")],
        [InlineKeyboardButton("🔄 ریست چک‌لیست", callback_data="reset_checklist")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    completed = sum(checklist.values())
    
    if completed == 3:
        status = "🎉 عالی! روز کامل - Streak ادامه داره!"
        emoji = "🔥"
    elif completed == 2:
        status = "✅ خوبه! ۲ از ۳ - یکی دیگه مونده"
        emoji = "💪"
    elif completed == 1:
        status = "⚠️ یکی رو انجام دادی - ادامه بده!"
        emoji = "😊"
    else:
        status = "❌ هنوز شروع نکردی - بزن بریم!"
        emoji = "🚀"
    
    text = f"""📋 چک‌لیست امروز {emoji}

{status}
🔥 Streak فعلی: {user_data.get('streak', 0)} روز

روی هر گزینه کلیک کن:"""
    
    await update.message.reply_text(text, reply_markup=reply_markup)

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """مدیریت دکمه‌های inline"""
    query = update.callback_query
    await query.answer()
    
    user_id = query.from_user.id
    users = load_user_data()
    user_data = users[str(user_id)]
    
    if query.data.startswith("check_"):
        item = query.data.replace("check_", "")
        user_data['checklist'][item] = not user_data['checklist'][item]
        
        completed = sum(user_data['checklist'].values())
        today = datetime.datetime.now(TIMEZONE).strftime('%Y-%m-%d')
        
        # محاسبه Streak
        if completed == 3 and user_data.get('last_checklist_date') == today:
            if user_data.get('last_streak_update') != today:
                user_data['streak'] += 1
                user_data['total_days'] += 1
                user_data['last_streak_update'] = today
                
                # آپدیت مهارت‌ها
                for skill in user_data['skills']:
                    if user_data['skills'][skill] < 10:
                        user_data['skills'][skill] = min(10, user_data['skills'][skill] + 0.1)
        
        elif completed == 0 and user_data['checklist'] == {'block1': False, 'block2': False, 'sleep': False}:
            user_data['penalty'] += 50000
            user_data['streak'] = 0
        
        users[str(user_id)] = user_data
        save_user_data(users)
        
        # آپدیت پیام
        checklist = user_data['checklist']
        block1_icon = "✅" if checklist['block1'] else "⬜"
        block2_icon = "✅" if checklist['block2'] else "⬜"
        sleep_icon = "✅" if checklist['sleep'] else "⬜"
        
        keyboard = [
            [InlineKeyboardButton(f"{block1_icon} بلوک صبح", callback_data="check_block1")],
            [InlineKeyboardButton(f"{block2_icon} بلوک بعدازظهر", callback_data="check_block2")],
            [InlineKeyboardButton(f"{sleep_icon} خواب ساعت 23:00", callback_data="check_sleep")],
            [InlineKeyboardButton("🔄 ریست", callback_data="reset_checklist")]
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)
        
        completed_now = sum(checklist.values())
        
        if completed_now == 3:
            status = f"🎉 تمام! Streak: {user_data['streak']} روز 🔥"
            emoji = "🏆"
        elif completed_now == 2:
            status = "✅ خوبه! یکی دیگه!"
            emoji = "💪"
        elif completed_now == 1:
            status = "😊 شروع کردی!"
            emoji = "🚀"
        else:
            status = "❌ ریست شد"
            emoji = "⚠️"
        
        text = f"📋 چک‌لیست امروز {emoji}\n\n{status}"
        await query.edit_message_text(text, reply_markup=reply_markup)
    
    elif query.data == "reset_checklist":
        user_data['checklist'] = {'block1': False, 'block2': False, 'sleep': False}
        users[str(user_id)] = user_data
        save_user_data(users)
        await query.edit_message_text("✅ چک‌لیست ریست شد! از منو دوباره باز کن.")

async def show_stats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """نمایش آمار کاربر"""
    user_id = update.effective_user.id
    users = load_user_data()
    user_data = users[str(user_id)]
    
    streak = user_data.get('streak', 0)
    total_days = user_data.get('total_days', 0)
    penalty = user_data.get('penalty', 0)
    current_week = user_data.get('current_week', 1)
    skills = user_data.get('skills', {})
    
    streak_emoji = "🔥" if streak >= 7 else "⭐" if streak >= 3 else "💫"
    
    # محاسبه پیشرفت کلی
    progress_percent = int((current_week / 12) * 100)
    
    # نمایش مهارت‌ها
    skills_text = ""
    for skill_name, skill_level in skills.items():
        stars = "⭐" * int(skill_level)
        skill_persian = {
            'reading': '📚 Reading',
            'listening': '👂 Listening',
            'writing': '✍️ Writing',
            'speaking': '🗣 Speaking'
        }
        skills_text += f"{skill_persian[skill_name]}: {stars} ({skill_level:.1f}/10)\n"
    
    text = f"""📊 آمار {user_data['name']}

{streak_emoji} Streak فعلی: {streak} روز
📅 کل روزهای موفق: {total_days} روز
💰 جریمه تا الان: {penalty:,} تومان
📈 پیشرفت Boot Camp: {progress_percent}% (هفته {current_week}/12)

🎯 سطح مهارت‌ها:
{skills_text}

{"🎉 عالیه! این Streak رو حفظ کن!" if streak >= 7 else "💪 سعی کن Streak بسازی!" if streak < 3 else "✅ داری خوب پیش میری!"}"""
    
    await update.message.reply_text(text)

async def show_week_plan(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """نمایش برنامه هفته جاری"""
    user_id = update.effective_user.id
    users = load_user_data()
    user_data = users[str(user_id)]
    
    current_week = user_data.get('current_week', 1)
    week_data = BOOTCAMP_SCHEDULE.get(current_week)
    
    text = f"""📚 برنامه هفته {current_week}/12

🎯 فوکوس: {week_data['focus']}

📖 گرامر این هفته:
{chr(10).join(f"  • {item}" for item in week_data['grammar'])}

📝 واژگان:
{chr(10).join(f"  • {item}" for item in week_data['vocabulary'])}

✅ وظایف روزانه:
{chr(10).join(f"  {i+1}. {task}" for i, task in enumerate(week_data['daily_tasks']))}

💡 برای دیدن برنامه روزانه: 📅 برنامه امروز"""
    
    await update.message.reply_text(text)

async def show_mock_test_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """منوی Mock Test"""
    keyboard = [
        [InlineKeyboardButton("📝 شروع Mock Test جدید", callback_data="start_mock")],
        [InlineKeyboardButton("📊 نتایج قبلی", callback_data="mock_results")],
        [InlineKeyboardButton("❌ بستن", callback_data="close")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    text = """📝 Mock Test Manager

این بخش به زودی کامل میشه!
الان می‌تونی:
- تاریخ Mock Test رو ثبت کنی
- نتایج رو وارد کنی
- پیشرفت رو ببینی"""
    
    await update.message.reply_text(text, reply_markup=reply_markup)

async def show_errors(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """دفتر اشتباهات"""
    user_id = update.effective_user.id
    users = load_user_data()
    user_data = users[str(user_id)]
    
    errors = user_data.get('errors', [])
    
    if not errors:
        text = """❌ دفتر اشتباهات

هنوز اشتباهی ثبت نشده!

💡 وقتی توی Mock Test یا تمرین اشتباه کردی،
اینجا ثبتش کن تا مرور کنی."""
    else:
        text = "❌ دفتر اشتباهات\n\n"
        for i, error in enumerate(errors[-10:], 1):
            text += f"{i}. {error}\n"
    
    await update.message.reply_text(text)

async def set_week_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """منوی تنظیم هفته"""
    keyboard = []
    for i in range(1, 13):
        keyboard.append([InlineKeyboardButton(f"هفته {i}", callback_data=f"set_week_{i}")])
    
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    text = """🎯 انتخاب هفته

الان کدوم هفته از Boot Camp هستی؟
(این فقط برای نمایش برنامه هفتگیه)"""
    
    await update.message.reply_text(text, reply_markup=reply_markup)

async def show_help(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """راهنما"""
    text = """💡 راهنمای استفاده

📅 برنامه امروز
برنامه دقیق امروز + وظایف هفته جاری

✅ چک‌لیست
۳ کار ساده روزانه:
  • بلوک صبح ۱.۵ ساعت
  • بلوک بعدازظهر ۱ ساعت
  • خواب ساعت ۲۳:۰۰

📊 آمار من
Streak، جریمه، پیشرفت هفتگی

📚 برنامه هفته
گرامر، واژگان و وظایف هفته جاری

🔥 نکات مهم:
• هر روز ۳ تیک = Streak ادامه داره
• اگه همه تیک‌ها رو پاک کنی = جریمه ۵۰ هزار تومان!
• Streak بالاتر = انگیزه بیشتر

موفق باشی! 🚀"""
    
    await update.message.reply_text(text)

# ============ Main ============

def main():
    """اجرای ربات"""
    logger.info("🤖 ربات در حال راه‌اندازی...")
    
    # تنظیمات timeout بالاتر
    request = HTTPXRequest(
        connection_pool_size=8,
        connect_timeout=30.0,
        read_timeout=30.0,
        write_timeout=30.0,
        pool_timeout=30.0
    )
    
    application = (
        Application.builder()
        .token(BOT_TOKEN)
        .request(request)
        .build()
    )
    
    # Handlers
    application.add_handler(CommandHandler("start", start))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    application.add_handler(CallbackQueryHandler(button_handler))
    
    logger.info("✅ ربات آماده است!")
    application.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == '__main__':
    main()
