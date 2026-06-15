import json
import logging
import asyncio
import os
from datetime import datetime, timedelta, timezone
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command, CommandObject
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.context import FSMContext
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.client.default import DefaultBotProperties

logging.basicConfig(level=logging.INFO)

# --- SOZLAMALAR (YANGI GURUH ID INTEGRATSIYA QILINDI) ---
BOT_TOKEN = "8724439262:AAFGNuQQ4IxdqitlcCEtkHLsvyFwSPg_b1c"
CHANNEL_USER = "MADIWAYy" 
GROUP_ID = "-1002130310815"       
NEW_GROUP_ID = "-1004370807037"   # <- Sening yangi guruh ID raqaming 
CHANNEL_ID = "-1002120000000"

ADMIN_ID = 6977836294         
MADIWAY_ADMIN_ID = 8112179116  

bot = Bot(token=BOT_TOKEN, default=DefaultBotProperties(parse_mode="HTML"))
dp = Dispatcher(storage=MemoryStorage())

START_SETTINGS_FILE = "global_start_settings.json"
USERS_DB_FILE = "users_database.json"
YUK_DB_FILE = "yuklar_database.json"

UZB_TZ = timezone(timedelta(hours=5))

AUTO_PAYMENT_MESSAGE = (
    "👋 <b>Salom! MadiWay tizimiga to'lov qilish uchun ma'lumotlar:</b>\n\n"
    "💳 <b>UzCard / VISA Card:</b> <code>4916-9903-5000-8311</code>\n"
    "👤 <b>Ega:</b> MadiWay Admin\n\n"
    "💵 <b>To'lov miqdorlari:</b>\n
    "🔹 1 kunlik — 15 000 so'm\n"
    "🔹 2 kunlik — 20 000 so'm\n"
    "🔹 3 kunlik — 30 000 so'm\n"
    "🔹 1 oylik — 50 000 so'm\n\n"
    "⚠️ To'lovni qilib, chekni shu yerga yuboring.\n"
    "📞 <b>Tekshirish va aloqa (WhatsApp bor):</b> +998 88 325 80 07"
)

TOPICS = {
    "🌍 Europa": 2, "🇩🇪 Germaniya": 14, "🇷🇺 Rossiya": 4, "🇰🇬 Qirg'iziston": 6,
    "🇰🇿 Kazakistan": 8, "🇮🇷 Eron": 10, "🇹🇯 Tojikston": 12, "🇧🇾 Belarusiya": 16,
    "🇬🇪 Gruziya": 18, "📣 Elon berish": 1
}

# --- BAZA FUNKSIYALARI ---
def load_db():
    if os.path.exists(USERS_DB_FILE):
        try:
            with open(USERS_DB_FILE, "r") as f: return json.load(f)
        except: pass
    return {"users": {}, "premium_count": 0}

def save_db(data):
    with open(USERS_DB_FILE, "w") as f: json.dump(data, f, indent=4)

def load_yuk_db():
    if os.path.exists(YUK_DB_FILE):
        try:
            with open(YUK_DB_FILE, "r", encoding="utf-8") as f: return json.load(f)
        except: pass
    return {}

def save_yuk_db(data):
    with open(YUK_DB_FILE, "w", encoding="utf-8") as f: json.dump(data, f, ensure_ascii=False, indent=4)

def register_user(user_id, username, full_name):
    db = load_db()
    uid = str(user_id)
    if uid not in db["users"]:
        db["users"][uid] = {"username": username or "yo'q", "full_name": full_name, "premium_until": None}
        save_db(db)

def check_premium(user_id):
    db = load_db()
    uid = str(user_id)
    if uid in db["users"] and db["users"][uid]["premium_until"]:
        try:
            until_dt = datetime.fromisoformat(db["users"][uid]["premium_until"]).astimezone(UZB_TZ)
            if datetime.now(UZB_TZ) < until_dt: return True
        except: pass
    return False

def load_start_settings():
    if os.path.exists(START_SETTINGS_FILE):
        try:
            with open(START_SETTINGS_FILE, "r", encoding="utf-8") as f: return json.load(f)
        except: pass
    return {"type": "text", "file_id": None, "text": "🏔 MadiWay tizimiga xush kelibsiz!"}

def save_start_settings(data):
    with open(START_SETTINGS_FILE, "w", encoding="utf-8") as f: json.dump(data, f, ensure_ascii=False, indent=4)

def get_premium_caption(main_text, status_label="𝗬𝗨𝗞 𝗘𝗟𝗢𝗡𝗜"):
    now = datetime.now(UZB_TZ)
    sana_soat = now.strftime("📅 %Y-%m-%d  🕒 %I:%M %p") 
    return f"⭐️ <b>𝗠𝗔𝗗𝗜𝗪𝗔𝗬 | {status_label}</b> ⭐️\n───────────────────────\n{main_text}\n───────────────────────\n⏳ Vaqt: {sana_soat}\n📢 Kanal: t.me/{CHANNEL_USER}"

def get_group_kb(bot_user, msg_id=None):
    buttons = []
    if msg_id:
        buttons.append([types.InlineKeyboardButton(text="⭐️ Yukni to'liq ko'rish (VIP)", url=f"https://t.me/{bot_user}?start={msg_id}")])
    buttons.append([types.InlineKeyboardButton(text="📢 Kanalga qo'shilish", url=f"https://t.me/{CHANNEL_USER}")])
    return types.InlineKeyboardMarkup(inline_keyboard=buttons)

class MadiWayStates(StatesGroup):
    kutish_global_start = State()
    kutish_kanal_yuk = State()
    kutish_bitta_topic_yuk = State()
    kutish_hamma_topic_yuk = State()
    kutish_yangi_guruh_yuk = State()
    kutish_yangi_guruh_100_yuk = State()
    giving_premium_username = State()
    giving_premium_days = State()

async def send_all(chat_id, message, caption, kb, t_id=None):
    try:
        if message.photo:
            return await bot.send_photo(chat_id, message.photo[-1].file_id, caption=caption, reply_markup=kb, message_thread_id=t_id)
        elif message.video:
            return await bot.send_video(chat_id, message.video.file_id, caption=caption, reply_markup=kb, message_thread_id=t_id)
        else:
            return await bot.send_message(chat_id, caption, reply_markup=kb, message_thread_id=t_id)
    except Exception as e:
        logging.error(f"Xabar yuborishda xato: {e}")
        return None

# --- DEEPLINK INTEGRATSIYASI ---
@dp.message(Command("start"))
async def start_cmd(message: types.Message, command: CommandObject, state: FSMContext):
    await state.clear()
    user_id = message.from_user.id
    register_user(user_id, message.from_user.username, message.from_user.full_name)
    
    if command.args:
        yuk_id = command.args
        if check_premium(user_id) or user_id in [ADMIN_ID, MADIWAY_ADMIN_ID]:
            yuk_db = load_yuk_db()
            txt = yuk_db.get(yuk_id)
            if txt:
                cap = get_premium_caption(txt, "𝗧𝗢'𝗟𝗜𝗤 𝗠𝗔'𝗟𝗨𝗠𝗢𝗧")
                await message.answer(cap)
                return
            else:
                await message.answer("⚠️ Yuk ma'lumotlari topilmadi yoki eskirgan.")
                return
        else:
            btns = [types.InlineKeyboardButton(text=n, callback_data=f"pay_group_{id}") for n, id in TOPICS.items() if id != 1]
            kb = types.InlineKeyboardMarkup(inline_keyboard=[btns[i:i+2] for i in range(0, len(btns), 2)])
            await message.answer("❌ <b>Ushbu yukni to'liq ko'rish uchun sizda VIP obuna faol emas!</b>\n\n👇 Davom etish uchun tariflardan birini tanlang va faollashtiring:", reply_markup=kb)
            return

    start_data = load_start_settings()
    if user_id in [ADMIN_ID, MADIWAY_ADMIN_ID]:
        kb = types.InlineKeyboardMarkup(inline_keyboard=[
            [types.InlineKeyboardButton(text="⚙️ Start sozlash", callback_data="btn_add_start_msg"),
             types.InlineKeyboardButton(text="📊 Statistika", callback_data="btn_stats")],
            [types.InlineKeyboardButton(text="⭐️ Kanalga yuk", callback_data="btn_kanal_tashlash"),
             types.InlineKeyboardButton(text="✨ Bitta Topicga", callback_data="btn_bitta_topic")],
            [types.InlineKeyboardButton(text="💥 Hammasiga yuborish", callback_data="btn_hamma_topic")],
            [types.InlineKeyboardButton(text="🆕 1Yangi Guruhga xabar", callback_data="btn_yangi_guruh"),
             types.InlineKeyboardButton(text="🚛 Yangi Guruh 100 ta yuk", callback_data="btn_yangi_guruh_100")],
            [types.InlineKeyboardButton(text="🔑 VIP Obuna Aktivlashtirish", callback_data="btn_give_vip")]
        ])
        await message.answer("💻 <b>𝗠𝗔𝗗𝗜𝗪𝗔𝗬 | 𝗔𝗗𝗠𝗜𝗡 𝗣𝗔𝗡𝗘𝗟</b>", reply_markup=kb)
    else:
        kb = types.InlineKeyboardMarkup(inline_keyboard=[
            [types.InlineKeyboardButton(text="📊 Tariflarni va guruhlarni tanlash", callback_data="btn_show_tariffs")],
            [types.InlineKeyboardButton(text="📢 Kanalga o'tish", url=f"https://t.me/{CHANNEL_USER}")]
        ])
        await message.answer(start_data.get("text") or "Tizim faol!", reply_markup=kb)

# --- STATISTIKA VA VIP ---
@dp.callback_query(F.data == "btn_stats")
async def show_stats(callback: types.CallbackQuery):
    await callback.answer()
    db = load_db()
    await callback.message.answer(f"📊 <b>MadiWay Bot Statistikasi:</b>\n\n👤 Umumiy a'zolar: <code>{len(db['users'])}</code> ta\n👑 Premium a'zolar: <code>{db.get('premium_count', 0)}</code> ta")

@dp.callback_query(F.data == "btn_give_vip")
async def start_give_vip(callback: types.CallbackQuery, state: FSMContext):
    await callback.answer()
    await callback.message.answer("🔑 <b>VIP berish uchun Telegram ID yoki @username kiriting:</b>")
    await state.set_state(MadiWayStates.giving_premium_username)

@dp.message(MadiWayStates.giving_premium_username)
async def process_vip_username(message: types.Message, state: FSMContext):
    await state.update_data(target_user=message.text.replace("@", "").strip())
    kb = types.InlineKeyboardMarkup(inline_keyboard=[
        [types.InlineKeyboardButton(text="1 Kunlik", callback_data="set_vip_1"), types.InlineKeyboardButton(text="2 Kunlik", callback_data="set_vip_2")],
        [types.InlineKeyboardButton(text="3 Kunlik", callback_data="set_vip_3"), types.InlineKeyboardButton(text="1 Oylik", callback_data="set_vip_30")]
    ])
    await message.answer("⏱ Muddatni tanlang:", reply_markup=kb)
    await state.set_state(MadiWayStates.giving_premium_days)

@dp.callback_query(MadiWayStates.giving_premium_days, F.data.startswith("set_vip_"))
async def finish_vip_giving(callback: types.CallbackQuery, state: FSMContext):
    await callback.answer()
    days = int(callback.data.split("_")[2])
    data = await state.get_data()
    target = data.get("target_user")
    
    db = load_db()
    found_uid = None
    for uid, uinfo in db["users"].items():
        if uid == target or uinfo["username"].lower() == target.lower():
            found_uid = uid
            break
            
    if found_uid:
        end_date = datetime.now(UZB_TZ) + timedelta(days=days)
        db["users"][found_uid]["premium_until"] = end_date.isoformat()
        db["premium_count"] = db.get("premium_count", 0) + 1
        save_db(db)
        
        formatted = end_date.strftime("%d-%m-%Y %H:%M")
        await callback.message.answer(f"✅ VIP Tasdiqlandi!\n⏱ Muddat: <b>{formatted}</b> gacha.")
        try:
            await bot.send_message(chat_id=int(found_uid), text=f"🎉 <b>Siz muvaffaqiyatli tasdiqlandingiz!</b>\n⏱ VIP obuna muddati: <code>{formatted}</code> gacha faol.")
        except: pass
    else:
        await callback.message.answer("❌ Foydalanuvchi bot bazasidan topilmadi!")
    await state.clear()

# --- TARIFLAR ---
@dp.callback_query(F.data == "btn_show_tariffs")
async def show_tariffs_menu(callback: types.CallbackQuery):
    await callback.answer()
    btns = [types.InlineKeyboardButton(text=n, callback_data=f"pay_group_{id}") for n, id in TOPICS.items() if id != 1]
    kb = types.InlineKeyboardMarkup(inline_keyboard=[btns[i:i+2] for i in range(0, len(btns), 2)])
    await callback.message.answer("❓ Qaysi yuk guruhiga kirish uchun to'lov qilmoqchisiz?", reply_markup=kb)

@dp.callback_query(F.data.startswith('pay_group_'))
async def select_days_tariff(callback: types.CallbackQuery):
    await callback.answer()
    group_id = callback.data.split('_')[2]
    kb = types.InlineKeyboardMarkup(inline_keyboard=[
        [types.InlineKeyboardButton(text="💰 1 Kun (15 000)", callback_data=f"track_1_g{group_id}")],
        [types.InlineKeyboardButton(text="💰 2 Kun (20 000)", callback_data=f"track_2_g{group_id}")],
        [types.InlineKeyboardButton(text="💰 3 Kun (30 000)", callback_data=f"track_3_g{group_id}")],
        [types.InlineKeyboardButton(text="👑 1 Oy (50 000)", callback_data=f"track_30_g{group_id}")]
    ])
    await callback.message.answer("⏱ Obuna muddatini tanlang:", reply_markup=kb)

@dp.callback_query(F.data.startswith('track_'))
async def track_and_redirect(callback: types.CallbackQuery):
    await callback.answer()
    parts = callback.data.split("_")
    days, g_id = parts[1], parts[2]
    user = callback.from_user
    alert = f"🔔 <b>KUZATISH:</b>\n👤 Foydalanuvchi: {user.full_name}\n🆔 ID: <code>{user.id}</code>\n🛒 Tarif: {days} kunlik (Guruh: {g_id})\n➔ Adminga o'tmoqda."
    for adm in [MADIWAY_ADMIN_ID, ADMIN_ID]:
        try: await bot.send_message(chat_id=adm, text=alert)
        except: pass
    kb = types.InlineKeyboardMarkup(inline_keyboard=[[types.InlineKeyboardButton(text="🚀 Adminga o'tish (Chek yuborish)", url="https://t.me/madiways")]])
    await callback.message.answer("To'lov chekini yuborish uchun adminga o'tishingiz mumkin:", reply_markup=kb)

# --- ADMIN PANEL CALL BACKS ---
@dp.callback_query(F.data.startswith('btn_'))
async def admin_buttons(callback: types.CallbackQuery, state: FSMContext):
    await callback.answer()
    if callback.data == "btn_add_start_msg":
        await callback.message.answer("⚙️ Yangi start xabarni yuboring:")
        await state.set_state(MadiWayStates.kutish_global_start)
    elif callback.data == "btn_kanal_tashlash":
        await callback.message.answer("📥 Kanal yukini yuboring:")
        await state.set_state(MadiWayStates.kutish_kanal_yuk)
    elif callback.data == "btn_hamma_topic":
        await callback.message.answer("💥 Hammasiga yuboring:")
        await state.set_state(MadiWayStates.kutish_hamma_topic_yuk)
    elif callback.data == "btn_yangi_guruh":
        await callback.message.answer("📥 Yangi guruhga oddiy xabarni kiriting:")
        await state.set_state(MadiWayStates.kutish_yangi_guruh_yuk)
    elif callback.data == "btn_yangi_guruh_100":
        await callback.message.answer("🚛 Yangi guruh uchun yuk ma'lumotini kiriting:")
        await state.set_state(MadiWayStates.kutish_yangi_guruh_100_yuk)
    elif callback.data == "btn_bitta_topic":
        btns = [types.InlineKeyboardButton(text=n, callback_data=f"select_topic_{id}") for n, id in TOPICS.items()]
        kb = types.InlineKeyboardMarkup(inline_keyboard=[btns[i:i+2] for i in range(0, len(btns), 2)])
        await callback.message.answer("📍 Bo'limni tanlang:", reply_markup=kb)

@dp.callback_query(F.data.startswith('select_topic_'))
async def topic_sel(callback: types.CallbackQuery, state: FSMContext):
    await state.update_data(target_topic_id=callback.data.split('_')[2])
    await callback.message.answer("📥 Yukni yuboring:")
    await state.set_state(MadiWayStates.kutish_bitta_topic_yuk)

@dp.message(MadiWayStates.kutish_global_start)
async def save_start(message: types.Message, state: FSMContext):
    save_start_settings({"text": message.html_text or message.caption or ""})
    await message.answer("✅ Start xabari saqlandi!")
    await state.clear()

@dp.message(MadiWayStates.kutish_kanal_yuk)
async def chan_yuk(message: types.Message, state: FSMContext):
    txt = message.html_text or message.caption or ""
    m_id = f"c{message.message_id}"
    ydb = load_yuk_db(); ydb[m_id] = txt; save_yuk_db(ydb)
    
    bot_info = await bot.get_me()
    cap = get_premium_caption(txt[:150] + "...")
    res = await send_all(CHANNEL_ID, message, cap, get_group_kb(bot_info.username, m_id))
    await message.answer("✅ Kanalga yuborildi!" if res else "❌ Kanal ID xato.")
    await state.clear()

# ⚡️ YANGI GURUHGA 100 TA YUK (SOZLANMALAR TO'LIQ ISHLAYDI)
@dp.message(MadiWayStates.kutish_yangi_guruh_100_yuk)
async def yangi_guruh_100_yuk(message: types.Message, state: FSMContext):
    txt = message.html_text or message.caption or ""
    m_id = f"g{message.message_id}"
    ydb = load_yuk_db(); ydb[m_id] = txt; save_yuk_db(ydb)
    
    bot_info = await bot.get_me()
    short_txt = txt[:150] + "..." if len(txt) > 150 else txt
    cap = get_premium_caption(short_txt, "𝗫𝗔𝗩𝗙𝗦𝗜𝗭 𝗬𝗨𝗞")
    
    res = await send_all(NEW_GROUP_ID, message, cap, get_group_kb(bot_info.username, m_id))
    if res:
        await message.answer("✅ Yangi guruhga tugmalar bilan ketdi!")
    else:
        await message.answer(f"❌ Guruhga yuborib bo'lmadi! Bot guruhda (`{NEW_GROUP_ID}`) admin ekanligini qayta tekshiring.")
    await state.clear()

@dp.message(MadiWayStates.kutish_hamma_topic_yuk)
async def all_yuk(message: types.Message, state: FSMContext):
    txt = message.html_text or message.caption or ""
    m_id = f"h{message.message_id}"
    ydb = load_yuk_db(); ydb[m_id] = txt; save_yuk_db(ydb)
    
    bot_info = await bot.get_me()
    cap = get_premium_caption(txt[:150] + "...")
    for n, tid in TOPICS.items():
        await send_all(GROUP_ID, message, cap, get_group_kb(bot_info.username, m_id), tid)
        await asyncio.sleep(0.3)
    await message.answer("✅ Barcha topiklarga ketdi!")
    await state.clear()

@dp.message(MadiWayStates.kutish_bitta_topic_yuk)
async def bitta_topic_yuk(message: types.Message, state: FSMContext):
    data = await state.get_data()
    tid = int(data.get("target_topic_id", 1))
    txt = message.html_text or message.caption or ""
    m_id = f"b{message.message_id}"
    ydb = load_yuk_db(); ydb[m_id] = txt; save_yuk_db(ydb)
    
    bot_info = await bot.get_me()
    cap = get_premium_caption(txt[:150] + "...")
    await send_all(GROUP_ID, message, cap, get_group_kb(bot_info.username, m_id), tid)
    await message.answer("✅ Topikka yuborildi!")
    await state.clear()

@dp.message(MadiWayStates.kutish_yangi_guruh_yuk)
async def yangi_guruh_yuk(message: types.Message, state: FSMContext):
    txt = message.html_text or message.caption or ""
    cap = get_premium_caption(txt, "YANGI GURUH ELONI")
    res = await send_all(NEW_GROUP_ID, message, cap, get_group_kb(None))
    await message.answer("✅ Oddiy xabar guruhga ketdi!" if res else "❌ Yuborishda xato yuz berdi.")
    await state.clear()

# --- AVTO JAVOB TIZIMI ---
@dp.message()
async def auto_reply_handler(message: types.Message):
    if message.chat.type == "private" and message.from_user.id not in [ADMIN_ID, MADIWAY_ADMIN_ID]:
        await message.answer(AUTO_PAYMENT_MESSAGE)

async def main():
    await dp.start_polling(bot)

if __name__ == '__main__':
    asyncio.run(main())
