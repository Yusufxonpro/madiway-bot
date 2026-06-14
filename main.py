import json
import logging
import asyncio
import os
from datetime import datetime, timedelta
import pytz
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.context import FSMContext
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.client.default import DefaultBotProperties

logging.basicConfig(level=logging.INFO)

# --- SOZLAMALAR ---
BOT_TOKEN = "8724439262:AAFGNuQQ4IxdqitlcCEtkHLsvyFwSPg_b1c"
CHANNEL_USER = "MADIWAYy" 
GROUP_ID = "-1002130310815"       
NEW_GROUP_ID = "-1002222222222"   
CHANNEL_ID = "-1002120000000"

ADMIN_ID = 6977836294         
MADIWAY_ADMIN_ID = 8112179116  

bot = Bot(token=BOT_TOKEN, default=DefaultBotProperties(parse_mode="HTML"))
dp = Dispatcher(storage=MemoryStorage())

uzb_tz = pytz.timezone('Asia/Tashkent')
START_SETTINGS_FILE = "global_start_settings.json"
USERS_DB_FILE = "users_database.json"

# --- YANGILANGAN TO'LOV MATNI (WHATSAPP BILAN) ---
AUTO_PAYMENT_MESSAGE = (
    "👋 <b>Salom! MadiWay tizimiga to'lov qilish uchun ma'lumotlar:</b>\n\n"
    "💳 <b>UzCard / VISA Card:</b> <code>8600 0000 0000 0000</code>\n"
    "👤 <b>Ega:</b> MadiWay Admin\n\n"
    "💵 <b>To'lov miqdorlari:</b>\n"
    "🔹 1 kunlik — 15 000 so'm\n"
    "🔹 2 kunlik — 20 000 so'm\n"
    "🔹 3 kunlik — 30 000 so'm\n"
    "🔹 1 oylik — 50 000 so'm\n\n"
    "⚠️ To'lovni qilib, chekni shu yerga yuboring.\n"
    "📞 <b>Tekshirish va aloqa (WhatsApp bor):</b> +998 88 325 80 07"
)

# --- BAZANI BOSHQARISH ---
def load_db():
    if os.path.exists(USERS_DB_FILE):
        with open(USERS_DB_FILE, "r") as f:
            return json.load(f)
    return {"users": {}, "premium_count": 0}

def save_db(data):
    with open(USERS_DB_FILE, "w") as f:
        json.dump(data, f, indent=4)

def register_user(user_id, username, full_name):
    db = load_db()
    uid = str(user_id)
    if uid not in db["users"]:
        db["users"][uid] = {
            "username": username or "yo'q",
            "full_name": full_name,
            "premium_until": None
        }
        save_db(db)

def check_premium(user_id):
    db = load_db()
    uid = str(user_id)
    if uid in db["users"] and db["users"][uid]["premium_until"]:
        until_dt = datetime.fromisoformat(db["users"][uid]["premium_until"])
        if datetime.now(uzb_tz) < until_dt.replace(tzinfo=uzb_tz):
            return True
    return False

def load_start_settings():
    if os.path.exists(START_SETTINGS_FILE):
        with open(START_SETTINGS_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {"type": "text", "file_id": None, "text": "🏔 MadiWay tizimiga xush kelibsiz!"}

def save_start_settings(data):
    with open(START_SETTINGS_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=4)

def get_premium_caption(main_text, status_label="𝗬𝗨𝗞 𝗘𝗟𝗢𝗡𝗜"):
    now = datetime.now(uzb_tz)
    sana_soat = now.strftime("📅 %Y-%m-%d  🕒 %I:%M %p") 
    return f"⭐️ <b>𝗠𝗔𝗗𝗜𝗪𝗔𝗬 | {status_label}</b> ⭐️\n───────────────────────\n{main_text}\n───────────────────────\n⏳ Vaqt: {sana_soat}\n📢 Kanal: t.me/{CHANNEL_USER}"

def get_channel_kb(msg_id=None):
    buttons = []
    if msg_id:
        buttons.append([types.InlineKeyboardButton(text="⭐️ Yukni to'liq ko'rish (VIP)", callback_data=f"show_full_{msg_id}")])
    buttons.append([types.InlineKeyboardButton(text="📢 Kanalga qo'shilish", url=f"https://t.me/{CHANNEL_USER}")])
    return types.InlineKeyboardMarkup(inline_keyboard=buttons)

YUK_OMBORI = {}

class MadiWayStates(StatesGroup):
    kutish_global_start = State()
    kutish_kanal_yuk = State()
    kutish_bitta_topic_yuk = State()
    kutish_hamma_topic_yuk = State()
    kutish_yangi_guruh_yuk = State()
    giving_premium_username = State()
    giving_premium_days = State()

TOPICS = {
    "🌍 Europa": 2, "🇩🇪 Germaniya": 14, "🇷🇺 Rossiya": 4, "🇰🇬 Qirg'iziston": 6,
    "🇰🇿 Kazakistan": 8, "🇮🇷 Eron": 10, "🇹🇯 Tojikston": 12, "🇧🇾 Belarusiya": 16,
    "🇬🇪 Gruziya": 18, "📣 Elon berish": 1
}

# --- HANDLERS ---
@dp.message(Command("start"))
async def start_cmd(message: types.Message, state: FSMContext):
    await state.clear()
    user_id = message.from_user.id
    register_user(user_id, message.from_user.username, message.from_user.full_name)
    start_data = load_start_settings()
    
    if user_id in [ADMIN_ID, MADIWAY_ADMIN_ID]:
        kb = types.InlineKeyboardMarkup(inline_keyboard=[
            [types.InlineKeyboardButton(text="⚙️ Start sozlash", callback_data="btn_add_start_msg"),
             types.InlineKeyboardButton(text="📊 Statistika", callback_data="btn_stats")],
            [types.InlineKeyboardButton(text="⭐️ Kanalga yuk", callback_data="btn_kanal_tashlash"),
             types.InlineKeyboardButton(text="✨ Bitta Topicga", callback_data="btn_bitta_topic")],
            [types.InlineKeyboardButton(text="💥 Hammasiga yuborish", callback_data="btn_hamma_topic")],
            [types.InlineKeyboardButton(text="🆕 Yangi Guruhga xabar", callback_data="btn_yangi_guruh")],
            [types.InlineKeyboardButton(text="🔑 VIP Obuna Aktivlashtirish", callback_data="btn_give_vip")]
        ])
        await message.answer("💻 <b><b>𝗠𝗔𝗗𝗜𝗪𝗔𝗬 | 𝗔𝗗𝗠𝗜𝗡 𝗣𝗔𝗡𝗘𝗟</b></b>", reply_markup=kb)
    else:
        kb = types.InlineKeyboardMarkup(inline_keyboard=[
            [types.InlineKeyboardButton(text="📊 Tariflarni va guruhlarni tanlash", callback_data="btn_show_tariffs")],
            [types.InlineKeyboardButton(text="📢 Kanalga o'tish", url=f"https://t.me/{CHANNEL_USER}")]
        ])
        t = start_data.get("text") or "Tizim faol!"
        await message.answer(t, reply_markup=kb)

@dp.callback_query(F.data == "btn_stats")
async def show_stats(callback: types.CallbackQuery):
    await callback.answer()
    db = load_db()
    total_users = len(db["users"])
    vip_users = db.get("premium_count", 0)
    await callback.message.answer(f"📊 <b>MadiWay Bot Statistikasi:</b>\n\n👤 Umumiy a'zolar: <code>{total_users}</code> ta\n👑 Premium sotib olganlar: <code>{vip_users}</code> ta")

@dp.callback_query(F.data == "btn_give_vip")
async def start_give_vip(callback: types.CallbackQuery, state: FSMContext):
    await callback.answer()
    await callback.message.answer("🔑 <b>VIP berish kerak bo'lgan foydalanuvchining Telegram ID raqamini yoki @username ini yuboring:</b>")
    await state.set_state(MadiWayStates.giving_premium_username)

@dp.message(MadiWayStates.giving_premium_username)
async def process_vip_username(message: types.Message, state: FSMContext):
    target = message.text.replace("@", "").strip()
    await state.update_data(target_user=target)
    
    kb = types.InlineKeyboardMarkup(inline_keyboard=[
        [types.InlineKeyboardButton(text="1 Kunlik", callback_data="set_vip_1"),
         types.InlineKeyboardButton(text="2 Kunlik", callback_data="set_vip_2")],
        [types.InlineKeyboardButton(text="3 Kunlik", callback_data="set_vip_3"),
         types.InlineKeyboardButton(text="1 Oylik", callback_data="set_vip_30")]
    ])
    await message.answer("⏱ Muddatni tanlang:", reply_markup=kb)
    await state.set_state(MadiWayStates.giving_premium_days)

# 👑 ADMIN RUXSAT BERGANDA ISHLAYDIGAN VA MUDDATNI ANIQ KO'RSATUVCHI QISM
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
        end_date = datetime.now(uzb_tz) + timedelta(days=days)
        db["users"][found_uid]["premium_until"] = end_date.isoformat()
        db["premium_count"] = db.get("premium_count", 0) + 1
        save_db(db)
        
        # Sanani chiroyli formatlash (Kun-Oy-Yil Soat:Minut ko'rinishida)
        formatted_expiry = end_date.strftime("%d-%m-%Y %H:%M")
        
        await callback.message.answer(f"✅ Muvaffaqiyatli tasdiqlandi!\n👤 Foydalanuvchi obunasi: <b>{formatted_expiry}</b> gacha faol.")
        
        # Foydalanuvchiga boradigan maxsus tasdiq xabari
        try:
            user_alert = (
                f"🎉 <b>Siz muvaffaqiyatli tasdiqlandingiz!</b>\n\n"
                f"🚀 Endi MadiWay platformasidan to'liq foydalanishingiz va barcha yuklarni ko'rishingiz mumkin.\n"
                f"⏱ <b>Sizning VIP obuna muddatingiz:</b> <code>{formatted_expiry}</code> gacha amal qiladi.\n\n"
                f"Omadli va xavfsiz yo'llar tilaymiz! 🚛"
            )
            await bot.send_message(chat_id=int(found_uid), text=user_alert)
        except: pass
    else:
        await callback.message.answer("❌ Foydalanuvchi bot bazasidan topilmadi. U avval botga start bergan bo'lishi kerak!")
    await state.clear()

# --- TARIFLAR VA KUZATISH TIZIMI ---
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
    days = parts[1]
    g_id = parts[2]
    
    user = callback.from_user
    username_text = f"@{user.username}" if user.username else "Username yo'q"
    
    alert_text = (
        f"🔔 <b>KUZATISH:</b>\n"
        f"👤 Foydalanuvchi: {user.full_name} ({username_text})\n"
        f"🆔 ID: <code>{user.id}</code>\n"
        f"🛒 Tanlangan tarif: <b>{days} kunlik</b> (Guruh: {g_id})\n"
        f"➔ Hozir adminga to'lov uchun o'tmoqda."
    )
    try: await bot.send_message(chat_id=MADIWAY_ADMIN_ID, text=alert_text)
    except: pass
    try: await bot.send_message(chat_id=ADMIN_ID, text=alert_text)
    except: pass
    
    kb = types.InlineKeyboardMarkup(inline_keyboard=[
        [types.InlineKeyboardButton(text="🚀 Adminga o'tish (To'lov chekini yuborish)", url="https://t.me/madiways")]
    ])
    await callback.message.answer("To'lov tafsilotlarini olish va chekni yuborish uchun quyidagi tugma orqali adminga o'tishingiz mumkin:", reply_markup=kb)

# --- YUKNI TO'LIQ KO'RISH TEKSHIRUVI ---
@dp.callback_query(F.data.startswith('show_full_'))
async def show_full_yuk(callback: types.CallbackQuery):
    await callback.answer()
    user_id = callback.from_user.id
    
    if check_premium(user_id) or user_id in [ADMIN_ID, MADIWAY_ADMIN_ID]:
        msg_id = callback.data.replace("show_full_", "")
        txt = YUK_OMBORI.get(msg_id, "⚠️ Ma'lumot topilmadi yoki keshdan o'chgan.")
        cap = get_premium_caption(txt, "𝗧𝗢'𝗟𝗜𝗤 𝗠𝗔'𝗟𝗨𝗠𝗢𝗧")
        try: await callback.message.edit_caption(caption=cap, reply_markup=get_channel_kb())
        except: await callback.message.answer(cap)
    else:
        kb = types.InlineKeyboardMarkup(inline_keyboard=[
            [types.InlineKeyboardButton(text="💰 To'lov qilish (VIP obuna)", callback_data="btn_show_tariffs")]
        ])
        await callback.message.answer("❌ <b>Ushbu yukni to'liq ko'rish uchun VIP obunangiz faol bo'lishi kerak!</b>\nIltimos, avval obuna sotib oling.", reply_markup=kb)

# --- ADMIN PANEL FUNKSIYALARI ---
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
        await callback.message.answer("📥 Yangi guruhga xabarni kiriting:")
        await state.set_state(MadiWayStates.kutish_yangi_guruh_yuk)
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
    txt = message.html_text or message.caption or ""
    cfg = {"type": "text", "file_id": None, "text": txt}
    if message.photo: cfg.update({"type": "photo", "file_id": message.photo[-1].file_id})
    elif message.video: cfg.update({"type": "video", "file_id": message.video.file_id})
    save_start_settings(cfg)
    await message.answer("✅ Start xabari saqlandi!")
    await state.clear()

async def send_all(chat_id, message, caption, kb, t_id=None):
    if message.photo: await bot.send_photo(chat_id, message.photo[-1].file_id, caption=caption, reply_markup=kb, message_thread_id=t_id)
    elif message.video: await bot.send_video(chat_id, message.video.file_id, caption=caption, reply_markup=kb, message_thread_id=t_id)
    else: await bot.send_message(chat_id, caption, reply_markup=kb, message_thread_id=t_id)

@dp.message(MadiWayStates.kutish_kanal_yuk)
async def chan_yuk(message: types.Message, state: FSMContext):
    txt = message.html_text or message.caption or ""
    m_id = f"c_{message.message_id}"
    YUK_OMBORI[m_id] = txt
    cap = get_premium_caption(txt[:150] + "...")
    await send_all(CHANNEL_ID, message, cap, get_channel_kb(m_id))
    await message.answer("✅ Kanalga ketdi!")
    await state.clear()

@dp.message(MadiWayStates.kutish_hamma_topic_yuk)
async def all_yuk(message: types.Message, state: FSMContext):
    cap = get_premium_caption(message.html_text or message.caption or "")
    for n, tid in TOPICS.items():
        try: await send_all(GROUP_ID, message, cap, get_channel_kb(), tid); await asyncio.sleep(0.3)
        except: continue
    await message.answer("✅ Hammasiga yuborildi!")
    await state.clear()

@dp.message(MadiWayStates.kutish_yangi_guruh_yuk)
async def yangi_guruh_yuk(message: types.Message, state: FSMContext):
    cap = get_premium_caption(message.html_text or message.caption or "", "YANGI GURUH ELONI")
    try:
        await send_all(NEW_GROUP_ID, message, cap, get_channel_kb())
        await message.answer("✅ Xabar yangi guruhga yuborildi!")
    except Exception as e:
        await message.answer(f"❌ Xato: {e}")
    await state.clear()

# --- ADMINDAN CHIQISHDA AVTO JAVOB ---
@dp.message()
async def auto_reply_handler(message: types.Message):
    if message.chat.type == "private" and message.from_user.id not in [ADMIN_ID, MADIWAY_ADMIN_ID]:
        await message.answer(AUTO_PAYMENT_MESSAGE)

async def main():
    await dp.start_polling(bot)

if __name__ == '__main__':
    asyncio.run(main())
