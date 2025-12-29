import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup, KeyboardButton
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, MessageHandler, filters, ContextTypes
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

def load_user_data():
    """بارگذاری اطلاعات کاربران"""
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
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
            'streak': 0,
            'total_days': 0,
            'checklist': {'block1': False, 'block2': False, 'sleep': False},
            'penalty': 0,
            'mock_tests': [],
            'errors': [],
            'partner_id': None,
            'last_checklist_date': None,
            'start_date': datetime.datetime.now(TIMEZONE).strftime('%Y-%m-%d')
        }
        save_user_data(users)
    
    return users[user_id_str]

def get_daily_schedule(day_name):
    """برگرداندن برنامه روزانه بر اساس روز"""
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
    
    return schedules.get(day_name, "برنامه‌ای برای این روز تعریف نشده")

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """شروع کار با ربات"""
    user_id = update.effective_user.id
    init_user(user_id)
    
    keyboard = [
        [KeyboardButton("📅 برنامه امروز"), KeyboardButton("✅ چک‌لیست")],
        [KeyboardButton("📊 آمار من"), KeyboardButton("📝 Mock Test")],
        [KeyboardButton("❌ دفتر اشتباهات"), KeyboardButton("⚙️ تنظیمات")]
    ]
    reply_markup = ReplyKeyboardMarkup(keyboard, resize_keyboard=True)
    
    welcome_text = """🎯 به ربات Boot Camp آلمانی خوش اومدی!

این ربات تو رو تا آزمون telc B2 همراهی می‌کنه.

امکانات:
✅ یادآوری خودکار برنامه
✅ چک‌لیست روزانه
✅ سیستم Streak و امتیاز
✅ مدیریت Mock Test
✅ دفتر اشتباهات
✅ گزارش پیشرفت

دستور اول: یک اسم برای خودت انتخاب کن
فقط بهم بگو اسمت چیه؟ (مثل: علی)"""

    await update.message.reply_text(welcome_text, reply_markup=reply_markup)

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """مدیریت پیام‌های متنی"""
    user_id = update.effective_user.id
    text = update.message.text
    users = load_user_data()
    user_data = users.get(str(user_id), {})
    
    if not user_data.get('name'):
        users[str(user_id)]['name'] = text
        save_user_data(users)
        await update.message.reply_text(f"عالیه {text}! حالا از منوی پایین استفاده کن 👇")
        return
    
    if text == "📅 برنامه امروز":
        now = datetime.datetime.now(TIMEZONE)
        day_name = now.strftime('%A')
        day_mapping = {
            'Saturday': 'شنبه',
            'Sunday': 'یکشنبه',
            'Monday': 'دوشنبه',
            'Tuesday': 'سه‌شنبه',
            'Wednesday': 'چهارشنبه',
            'Thursday': 'پنج‌شنبه',
            'Friday': 'جمعه'
        }
        persian_day = day_mapping[day_name]
        schedule = get_daily_schedule(persian_day)
        await update.message.reply_text(schedule)
    
    elif text == "✅ چک‌لیست":
        await show_checklist(update, context)
    
    elif text == "📊 آمار من":
        await show_stats(update, context)
    
    elif text == "📝 Mock Test":
        await update.message.reply_text("📝 قابلیت Mock Test به زودی اضافه میشه!")
    
    elif text == "❌ دفتر اشتباهات":
        await show_errors(update, context)
    
    elif text == "⚙️ تنظیمات":
        await update.message.reply_text("⚙️ قابلیت تنظیمات به زودی اضافه میشه!")

async def show_checklist(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """نمایش چک‌لیست روزانه"""
    user_id = update.effective_user.id
    users = load_user_data()
    user_data = users[str(user_id)]
    
    today = datetime.datetime.now(TIMEZONE).strftime('%Y-%m-%d')
    
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
    status = ""
    if completed == 3:
        status = "🎉 روز موفق! همه کارها انجام شد"
    elif completed == 2:
        status = "✅ روز موفق! ۲ از ۳"
    elif completed == 1:
        status = "⚠️ روز قابل قبول - ۱ از ۳"
    else:
        status = "❌ هنوز کاری انجام نشده"
    
    text = f"""📋 چک‌لیست امروز

{status}

روی هر گزینه کلیک کن تا تیک بخوره:"""
    
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
        
        if completed == 3 and user_data.get('last_checklist_date') == today:
            user_data['streak'] += 1
            user_data['total_days'] += 1
        
        elif completed == 0:
            user_data['penalty'] += 50000
            user_data['streak'] = 0
        
        users[str(user_id)] = user_data
        save_user_data(users)
        
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
            status = "🎉 عالی! همه کارها انجام شد\n⭐ Streak: " + str(user_data['streak'])
        elif completed_now == 2:
            status = "✅ خوبه! ۲ از ۳"
        elif completed_now == 1:
            status = "⚠️ قابل قبول - ۱ از ۳"
        else:
            status = "❌ هنوز کاری انجام نشده"
        
        text = f"📋 چک‌لیست امروز\n\n{status}"
        await query.edit_message_text(text, reply_markup=reply_markup)
    
    elif query.data == "reset_checklist":
        user_data['checklist'] = {'block1': False, 'block2': False, 'sleep': False}
        users[str(user_id)] = user_data
        save_user_data(users)
        await query.edit_message_text("✅ چک‌لیست ریست شد!")

async def show_stats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """نمایش آمار کاربر"""
    user_id = update.effective_user.id
    users = load_user_data()
    user_data = users[str(user_id)]
    
    streak = user_data.get('streak', 0)
    total_days = user_data.get('total_days', 0)
    penalty = user_data.get('penalty', 0)
    
    streak_emoji = "🔥" if streak >= 7 else "⭐"
    
    text = f"""📊 آمار {user_data['name']}

{streak_emoji} Streak فعلی: {streak} روز
📅 کل روزهای موفق: {total_days} روز
💰 جریمه تا الان: {penalty:,} تومان

{"🎉 عالیه! به همین روال ادامه بده!" if streak >= 7 else "💪 سعی کن Streak خودت رو بالا ببری!"}"""
    
    await update.message.reply_text(text)

async def show_errors(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """نمایش دفتر اشتباهات"""
    await update.message.reply_text("❌ دفتر اشتباهات خالیه!\n\nاین قابلیت به زودی کامل میشه.")

def main():
    """اجرای ربات"""
    print("🤖 ربات در حال راه‌اندازی...")
    
    application = Application.builder().token(BOT_TOKEN).build()
    
    application.add_handler(CommandHandler("start", start))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    application.add_handler(CallbackQueryHandler(button_handler))
    
    print("✅ ربات آماده است!")
    application.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == '__main__':
    main()
