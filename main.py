import json
import logging
import asyncio
import os
from datetime import datetime, timedelta, timezone
from typing import List, Dict
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command, CommandObject
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.context import FSMContext
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.client.default import DefaultBotProperties
from aiogram.utils.media_group import MediaGroupBuilder

logging.basicConfig(level=logging.INFO)

# --- SOZLAMALAR VA ID RAQAMLAR ---
BOT_TOKEN = "8724439262:AAFGNuQQ4IxdqitlcCEtkHLsvyFwSPg_b1c"
CHANNEL_USER = "MADIWAYy"  

GROUP_ID = "-1003963001370"        # Asosiy guruh (Topiclar bor guruh)
NEW_GROUP_ID = "-1004370807037"    # Yangi guruh
CHANNEL_ID = "-1003996104316"      # MadiWay kanali

ADMIN_ID = 6977836294         
MADIWAY_ADMIN_ID = 8112179116  
OWNER_USERNAME = "yusufxonpro1"    # Sening shaxsiy profiling

bot = Bot(token=BOT_TOKEN, default=DefaultBotProperties(parse_mode="HTML"))
dp = Dispatcher(storage=MemoryStorage())

START_SETTINGS_FILE = "global_start_settings.json"
USERS_DB_FILE = "users_database.json"
YUK_DB_FILE = "yuklar_database.json"

UZB_TZ = timezone(timedelta(hours=5))

# Albomlarni (Media Group) vaqtincha xotirada saqlash uchun kesh
MEDIA_GROUPS_CACHE: Dict[str, List[types.Message]] = {}

# --- TO'LOV XABARI ---
AUTO_PAYMENT_MESSAGE = (
    "👋 <b>Salom! MadiWay tizimiga to'lov qilish uchun ma'lumotlar:</b>\n\n"
    "💳 <b>UzCard / VISA Card:</b> <code>4916-9903-5000-8311</code>\n"
    "👤 <b>Ega:</b> MadiWay Admin\n\n"
    "💵 <b>To'lov miqdorlari:</b>\n"
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

LINKS_INFO = (
    "🔗 <b>MadiWay tizimidagi mavjud guruhlar va kanallar:</b>\n\n"
    "1️⃣ <b>MadiWay Kanali:</b>\n<code>t.me/MADIWAYy</code>\n\n"
    "2️⃣ <b>MadiWay Asosiy Guruh (Yuklar bo'limi):</b>\n<code>t.me/MadiWay_Group</code>\n\n"
    "3️⃣ <b>MadiWay Yangi Guruh:</b>\n<code>t.me/MadiWay_NewGroup</code>\n\n"
    "⚠️ <i>Tepada yozilgan linklardan birining ustiga bosib, nusxa oling (copy qiling) va quyida botga yuboring!</i>"
)

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

def get_tariff_keyboard():
    return types.InlineKeyboardMarkup(inline_keyboard=[
        [types.InlineKeyboardButton(text="💰 1 Kun (15 000)", callback_data="track_1_kun")],
        [types.InlineKeyboardButton(text="💰 2 Kun (20 000)", callback_data="track_2_kun")],
        [types.InlineKeyboardButton(text="💰 3 Kun (30 000)", callback_data="track_3_kun")],
        [types.InlineKeyboardButton(text="👑 1 Oy (50 000)", callback_data="track_30_kun")]
    ])

class MadiWayStates(StatesGroup):
    kutish_global_start = State()
    kutish_kanal_yuk = State()
    kutish_bitta_topic_yuk = State()
    kutish_hamma_topic_yuk = State()
    kutish_yangi_guruh_yuk = State()
    kutish_yangi_guruh_100_yuk = State()
    kutish_yangi_guruh_media_yuk = State()  # YANGI TUGMA UCHUN HOLAT
    giving_premium_username = State()
    giving_premium_days = State()
    kutish_guruh_linki = State()

# --- START BUYRUG'I VA AVTOMATIK DEEPLINK ---
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
            if yuk_id.startswith("g"):
                guruh_nomi = "MadiWay Yangi Guruh"
                await state.set_state(MadiWayStates.kutish_guruh_linki)
                await state.update_data(tanlangan_guruh=guruh_nomi)
                
                await message.answer(
                    f"❌ <b>Ushbu yukni to'liq ko'rish uchun sizda VIP obuna faol emas!</b>\n\n"
                    f"✅ <b>Guruh aniqlandi:</b> {guruh_nomi}\n\n"
                    f"👇 Davom etish uchun guruh tariflaridan birini tanlang va faollashtiring:", 
                    reply_markup=get_tariff_keyboard()
                )
                return
            else:
                await message.answer("❌ <b>Ushbu yukni to'liq ko'rish uchun sizda VIP obuna faol emas!</b>\n\n" + LINKS_INFO)
                await state.set_state(MadiWayStates.kutish_guruh_linki)
                return

    if user_id in [ADMIN_ID, MADIWAY_ADMIN_ID]:
        kb = types.InlineKeyboardMarkup(inline_keyboard=[
            [types.InlineKeyboardButton(text="⚙️ Start sozlash", callback_data="btn_add_start_msg"),
             types.InlineKeyboardButton(text="📊 Statistika", callback_data="btn_stats")],
            [types.InlineKeyboardButton(text="⭐️ Kanalga yuk", callback_data="btn_kanal_tashlash"),
             types.InlineKeyboardButton(text="✨ Bitta Topicga", callback_data="btn_bitta_topic")],
            [types.InlineKeyboardButton(text="💥 Hammasiga yuborish", callback_data="btn_hamma_topic")],
            [types.InlineKeyboardButton(text="🆕 Yangi Guruhga xabar", callback_data="btn_yangi_guruh"),
             types.InlineKeyboardButton(text="🚛 Yangi Guruh 100 ta yuk", callback_data="btn_yangi_guruh_100")],
            [types.InlineKeyboardButton(text="📸 Yangi Guruh (10 ta rasm)", callback_data="btn_yangi_guruh_media")], # YANGI TUGMA
            [types.InlineKeyboardButton(text="🔑 VIP Obuna Aktivlashtirish", callback_data="btn_give_vip")]
        ])
        await message.answer("💻 <b>𝗠𝗔𝗗𝗜𝗪𝗔𝗬 | 𝗔𝗗𝗠𝗜𝗡 𝗣𝗔𝗡𝗘𝗟</b>", reply_markup=kb)
    else:
        kb = types.InlineKeyboardMarkup(inline_keyboard=[
            [types.InlineKeyboardButton(text="💰 Guruh sotib olish / To'lov", callback_data="btn_show_tariffs")],
            [types.InlineKeyboardButton(text="📢 MadiWay Kanaliga o'tish", url=f"https://t.me/{CHANNEL_USER}")]
        ])
        clean_text = "🏔 <b>MadiWay logistika tizimiga xush kelibsiz!</b>\n\nYuklar haqida to'liq ma'lumot olish va guruhlarga qo'shilish uchun quyidagi tugmalardan foydalaning:"
        await message.answer(clean_text, reply_markup=kb)

# --- TARIFLAR TIZIMI ---
@dp.callback_query(F.data == "btn_show_tariffs")
async def show_tariffs_menu(callback: types.CallbackQuery, state: FSMContext):
    await callback.answer()
    await callback.message.answer(LINKS_INFO)
    await state.set_state(MadiWayStates.kutish_guruh_linki)

@dp.message(MadiWayStates.kutish_guruh_linki)
async def process_group_link(message: types.Message, state: FSMContext):
    link_text = message.text.lower() if message.text else ""
    if "madiwayy" in link_text: guruh_nomi = "MadiWay Kanali"
    elif "madiway_group" in link_text: guruh_nomi = "MadiWay Asosiy Guruh (Yuklar)"
    elif "madiway_newgroup" in link_text: guruh_nomi = "MadiWay Yangi Guruh"
    else: guruh_nomi = "Siz tanlagan guruh"

    await state.update_data(tanlangan_guruh=guruh_nomi)
    await message.answer(f"✅ <b>Guruh aniqlandi:</b> {guruh_nomi}\n\n⏱ Endi ushbu guruh uchun obuna muddatini tanlang:", reply_markup=get_tariff_keyboard())

@dp.callback_query(MadiWayStates.kutish_guruh_linki, F.data.startswith('track_'))
async def track_and_redirect(callback: types.CallbackQuery, state: FSMContext):
    await callback.answer()
    parts = callback.data.split("_")
    kun = parts[1]
    user_data = await state.get_data()
    guruh_nomi = user_data.get("tanlangan_guruh", "Noma'lum guruh")
    user = callback.from_user
    
    alert = (
        f"🔔 <b>YANGI TO'LOV SO'ROVI (KUZATISH):</b>\n\n"
        f"👤 Foydalanuvchi: {user.full_name}\n"
        f"🆔 ID: <code>{user.id}</code>\n"
        f"🌐 Username: @{user.username if user.username else 'yoq'}\n"
        f"📦 Guruh: <b>{guruh_nomi}</b>\n"
        f"🛒 Tarif: {kun} kunlik\n"
        f"➔ Foydalanuvchi hozir @{OWNER_USERNAME} ga o'tmoqda."
    )
    for adm in [MADIWAY_ADMIN_ID, ADMIN_ID]:
        try: await bot.send_message(chat_id=adm, text=alert)
        except: pass
        
    kb = types.InlineKeyboardMarkup(inline_keyboard=[[types.InlineKeyboardButton(text="🚀 Adminga chek yuborish", url=f"https://t.me/{OWNER_USERNAME}")]])
    await callback.message.answer(
        f"💳 <b>To'lov ma'lumotlari:</b>\nNusxa oling: <code>4916-9903-5000-8311</code>\n\nTanlangan muddat: <b>{kun} kun</b>\n\n👇 Pastdagi tugma orqali adminga o'ting va chekni yuboring!", 
        reply_markup=kb
    )
    await state.clear()

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
        await callback.message.answer("🚛 Yangi guruh uchun oddiy yuk matnini kiriting:")
        await state.set_state(MadiWayStates.kutish_yangi_guruh_100_yuk)
    elif callback.data == "btn_yangi_guruh_media":
        await callback.message.answer("📸 Yangi guruh uchun albom shaklida yukni yuboring (10 tagacha rasm/video):")
        await state.set_state(MadiWayStates.kutish_yangi_guruh_media_yuk)
    elif callback.data == "btn_bitta_topic":
        btns = [types.InlineKeyboardButton(text=n, callback_data=f"select_topic_{id}") for n, id in TOPICS.items()]
        kb = types.InlineKeyboardMarkup(inline_keyboard=[btns[i:i+2] for i in range(0, len(btns), 2)])
        await callback.message.answer("📍 Bo'limni tanlang:", reply_markup=kb)

# --- 10 TAGACHA MEDIA/ALBOM BILAN YUKNI USHLASH VA JAMLASH FUNKSIYASI ---
@dp.message(MadiWayStates.kutish_yangi_guruh_media_yuk, F.media_group_id)
async def handle_yangi_guruh_media_group(message: types.Message, state: FSMContext):
    mg_id = message.media_group_id
    if mg_id not in MEDIA_GROUPS_CACHE:
        MEDIA_GROUPS_CACHE[mg_id] = []
        # Albomning barcha parchalari kelishi uchun 1 soniya kutamiz
        asyncio.create_task(process_media_group_delayed(mg_id, state, message.message_id))
    
    MEDIA_GROUPS_CACHE[mg_id].append(message)

async def process_media_group_delayed(mg_id: str, state: FSMContext, original_msg_id: int):
    await asyncio.sleep(1.0) # Rasmlar yuklanishini kutish vaqti
    messages = MEDIA_GROUPS_CACHE.get(mg_id, [])
    if not messages:
        return
    
    # Kelgan barcha parchalardan sarlavha (caption) ni qidirib topamiz
    caption_text = ""
    for msg in messages:
        if msg.caption:
            caption_text = msg.caption
            break
    
    # Ma'lumotlar bazasiga to'liq matnni saqlaymiz
    m_id = f"g{original_msg_id}"
    ydb = load_yuk_db()
    ydb[m_id] = caption_text
    save_yuk_db(ydb)
    
    bot_info = await bot.get_me()
    short_txt = caption_text[:150] + "..." if len(caption_text) > 150 else caption_text
    cap = get_premium_caption(short_txt, "𝗫𝗔𝗩𝗙𝗦𝗜𝗭 𝗠𝗘𝗗𝗜𝗔 𝗬𝗨𝗞")
    
    # MediaGroup builder yaratamiz va rasmlarni bitta guruhga yig'amiz
    media_group = MediaGroupBuilder(caption=cap)
    for msg in messages:
        if msg.photo:
            media_group.add_photo(media=msg.photo[-1].file_id)
        elif msg.video:
            media_group.add_video(media=msg.video.file_id)
            
    try:
        # 1. Guruhga albomni o'zini ketma-ketlikda chiroyli yuboramiz
        await bot.send_media_group(chat_id=NEW_GROUP_ID, media=media_group.build())
        # 2. Albom ketidan srazu VIP tugmasini alohida xabar qilib chiqaramiz (albom ichiga inline tugma qo'yib bo'lmaydi)
        await bot.send_message(
            chat_id=NEW_GROUP_ID, 
            text="👆 <b>Yuqoridagi yukning to'liq ma'lumotlarini ko'rish:</b>", 
            reply_markup=get_group_kb(bot_info.username, m_id)
        )
        await bot.send_message(chat_id=messages[0].from_user.id, text="✅ Albom va VIP tugmasi yangi guruhga bitta navbatda muvaffaqiyatli ketdi!")
    except Exception as e:
        logging.error(f"Media guruh yuborishda xato: {e}")
        await bot.send_message(chat_id=messages[0].from_user.id, text="❌ Albomni yangi guruhga yuborishda xatolik yuz berdi.")
        
    # Keshni tozalaymiz va holatni yopamiz
    if mg_id in MEDIA_GROUPS_CACHE:
        del MEDIA_GROUPS_CACHE[mg_id]
    await state.clear()

# --- QOLGAN ESKI FUNKSIYALAR TEGILMADI ---
@dp.callback_query(F.data.startswith('select_topic_'))
async def topic_sel(callback: types.CallbackQuery, state: FSMContext):
    await state.update_data(target_topic_id=callback.data.split('_')[2])
    await callback.message.answer("📥 Yukni yuboring:")
    await state.set_state(MadiWayStates.kutish_bitta_topic_yuk)

@dp.message(MadiWayStates.kutish_global_start)
async def save_start(message: types.Message, state: FSMContext):
    with open(START_SETTINGS_FILE, "w", encoding="utf-8") as f:
        json.dump({"text": message.html_text or message.caption or ""}, f, ensure_ascii=False, indent=4)
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
    await message.answer("✅ Kanalga muvaffaqiyatli yuborildi!" if res else "❌ Xato yuz berdi.")
    await state.clear()

@dp.message(MadiWayStates.kutish_yangi_guruh_100_yuk)
async def yangi_guruh_100_yuk(message: types.Message, state: FSMContext):
    txt = message.html_text or message.caption or ""
    m_id = f"g{message.message_id}"
    ydb = load_yuk_db(); ydb[m_id] = txt; save_yuk_db(ydb)
    bot_info = await bot.get_me()
    short_txt = txt[:150] + "..." if len(txt) > 150 else txt
    cap = get_premium_caption(short_txt, "𝗫𝗔𝗩𝗙𝗦𝗜𝗭 𝗬𝗨𝗞")
    res = await send_all(NEW_GROUP_ID, message, cap, get_group_kb(bot_info.username, m_id))
    await message.answer("✅ Yangi guruhga yuk yuborildi!" if res else "❌ Xato yuz berdi.")
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
    res = await send_all(GROUP_ID, message, cap, get_group_kb(bot_info.username, m_id), tid)
    await message.answer("✅ Topikka yuborildi!" if res else "❌ Xato yuz berdi.")
    await state.clear()

@dp.message(MadiWayStates.kutish_yangi_guruh_yuk)
async def yangi_guruh_yuk(message: types.Message, state: FSMContext):
    txt = message.html_text or message.caption or ""
    cap = get_premium_caption(txt, "YANGI GURUH ELONI")
    res = await send_all(NEW_GROUP_ID, message, cap, get_group_kb(None))
    await message.answer("✅ Oddiy xabar yangi guruhga ketdi!" if res else "❌ Yuborishda xato yuz berdi.")
    await state.clear()

async def send_all(chat_id, message, caption, kb, t_id=None):
    try:
        if message.photo: return await bot.send_photo(chat_id, message.photo[-1].file_id, caption=caption, reply_markup=kb, message_thread_id=t_id)
        elif message.video: return await bot.send_video(chat_id, message.video.file_id, caption=caption, reply_markup=kb, message_thread_id=t_id)
        else: return await bot.send_message(chat_id, caption, reply_markup=kb, message_thread_id=t_id)
    except Exception as e:
        logging.error(f"Xabar yuborishda xato: {e}")
        return None

# --- STATISTIKA VA VIP TIZIMI ---
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
        try: await bot.send_message(chat_id=int(found_uid), text=f"🎉 <b>Siz muvaffaqiyatli tasdiqlandingiz!</b>\n⏱ VIP obuna muddati: <code>{formatted}</code> gacha faol.")
        except: pass
    else:
        await callback.message.answer("❌ Foydalanuvchi bot bazasidan topilmadi!")
    await state.clear()

@dp.message()
async def auto_reply_handler(message: types.Message):
    if message.chat.type == "private" and message.from_user.id not in [ADMIN_ID, MADIWAY_ADMIN_ID]:
        await message.answer(AUTO_PAYMENT_MESSAGE)

async def main():
    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)

if __name__ == '__main__':
    asyncio.run(main())
