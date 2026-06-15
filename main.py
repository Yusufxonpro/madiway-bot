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

# --- YANGILANGAN SOZLAMALAR VA ID RAQAMLAR ---
BOT_TOKEN = "8724439262:AAFGNuQQ4IxdqitlcCEtkHLsvyFwSPg_b1c"

CHANNEL_USER = "MADIWAYy"         # MadiWay kanali username
GROUP_USER = "MADIWAYy_Gr"        # Asosiy guruh username
NEW_GROUP_USER = "International_logistik"  # Yangi guruh username

# ID raqamlari (O'zingizniki bilan solishtiring, to'g'ri bo'lsa tegmang)
CHANNEL_ID = "-1003996104316"      
GROUP_ID = "-1003963001370"        
NEW_GROUP_ID = "-1004370807037"    

ADMIN_ID = 6977836294         
MADIWAY_ADMIN_ID = 8112179116  
OWNER_USERNAME = "yusufxonpro1"    

bot = Bot(token=BOT_TOKEN, default=DefaultBotProperties(parse_mode="HTML"))
dp = Dispatcher(storage=MemoryStorage())

START_SETTINGS_FILE = "global_start_settings.json"
USERS_DB_FILE = "users_database.json"
YUK_DB_FILE = "yuklar_database.json"

UZB_TZ = timezone(timedelta(hours=5))
MEDIA_GROUPS_CACHE: Dict[str, List[types.Message]] = {}

# --- TO'LOV XABARI ---
AUTO_PAYMENT_MESSAGE = (
    "👋 <b>Salom! MadiWay guruhlariga qo'shilish uchun to'lov ma'lumotlari:</b>\n\n"
    "💳 <b>UzCard / VISA Card:</b> <code>4916-9903-5000-8311</code>\n"
    "👤 <b>Ega:</b> MadiWay Admin\n\n"
    "💵 <b>Tariflar:</b>\n"
    "🔹 1 kunlik — 15 000 so'm\n"
    "🔹 2 kunlik — 20 000 so'm\n"
    "🔹 3 kunlik — 30 000 so'm\n"
    "🔹 1 oylik — 50 000 so'm\n\n"
    "⚠️ To'lovni amalga oshirib, chekni shu yerga yuboring.\n"
    "📞 <b>Aloqa:</b> +998 88 325 80 07"
)

TOPICS = {
    "🌍 Europa": 2, "🇩🇪 Germaniya": 14, "🇷🇺 Rossiya": 4, "🇰🇬 Qirg'iziston": 6,
    "🇰🇿 Kazakistan": 8, "🇮🇷 Eron": 10, "🇹🇯 Tojikston": 12, "🇧🇾 Belarusiya": 16,
    "🇬🇪 Gruziya": 18, "📣 Elon berish": 1
}

LINKS_INFO = (
    "🔗 <b>MadiWay tizimidagi rasmiy guruh va kanallar:</b>\n\n"
    "1️⃣ <b>MadiWay Kanali:</b>\n<code>t.me/MADIWAYy</code>\n\n"
    "2️⃣ <b>MadiWay Asosiy Guruh (Yuklar bo'limi):</b>\n<code>t.me/MADIWAYy_Gr</code>\n\n"
    "3️⃣ <b>MadiWay Yangi Guruh:</b>\n<code>t.me/International_logistik</code>\n\n"
    "⚠️ <i>Ushbu havolalardan (link) birini ko'chirib (copy qilib) botga yuboring!</i>"
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
    return f"⭐️ <b><b>𝗠𝗔𝗗𝗜𝗪𝗔𝗬 | {status_label}</b></b> ⭐️\n───────────────────────\n{main_text}\n───────────────────────\n⏳ Vaqt: {sana_soat}\n📢 Kanal: t.me/{CHANNEL_USER}"

def get_group_kb(bot_user, msg_id=None):
    buttons = []
    if msg_id:
        buttons.append([types.InlineKeyboardButton(text="⭐️ Yukni to'liq ko'rish", url=f"https://t.me/{bot_user}?start={msg_id}")])
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
    kutish_yangi_guruh_media_yuk = State()
    giving_premium_username = State()
    giving_premium_days = State()
    kutish_guruh_linki = State()

# --- START BUYRUG'I VA DEEPLINK ---
@dp.message(Command("start"))
async def start_cmd(message: types.Message, command: CommandObject, state: FSMContext):
    await state.clear()
    user_id = message.from_user.id
    register_user(user_id, message.from_user.username, message.from_user.full_name)
    
    if command.args:
        yuk_id = command.args
        yuk_db = load_yuk_db()
        txt = yuk_db.get(yuk_id)
        
        # 1. KANALIDAN KELGAN YUKLAR ("c" bilan boshlanadi) -> MUTLOQ BEPUL KO'RADI
        if yuk_id.startswith("c"):
            if txt:
                await message.answer(get_premium_caption(txt, "𝗧𝗢'𝗟𝗜𝗤 𝗠𝗔'𝗟𝗨𝗠𝗢𝗧"))
            else:
                await message.answer("⚠️ Yuk ma'lumotlari topilmadi yoki o'chirilgan.")
            return

        # 2. GURUXLARDAN KELGAN YUKLAR ("g", "b", "h" bilan boshlanadi) -> PULLIK TEKSHIRUV
        if check_premium(user_id) or user_id in [ADMIN_ID, MADIWAY_ADMIN_ID]:
            if txt:
                await message.answer(get_premium_caption(txt, "𝗧𝗢'𝗟𝗜𝗤 𝗠𝗔'𝗟𝗨𝗠𝗢𝗧"))
            else:
                await message.answer("⚠️ Yuk ma'lumotlari topilmadi.")
            return
        else:
            # Agar foydalanuvchi VIP bo'lmasa, qaysi guruhdan kelganini aniqlab tarif ko'rsatamiz
            if yuk_id.startswith("g"):
                guruh_nomi = "MadiWay Yangi Guruh (International Logistik)"
            else:
                guruh_nomi = "MadiWay Asosiy Guruh (Yuklar bo'limi)"
                
            await state.set_state(MadiWayStates.kutish_guruh_linki)
            await state.update_data(tanlangan_guruh=guruh_nomi)
            
            await message.answer(
                f"❌ <b>Ushbu guruhdagi yukni to'liq ko'rish uchun sizda VIP obuna faol emas!</b>\n\n"
                f"✅ <b>Guruh aniqlandi:</b> {guruh_nomi}\n\n"
                f"👇 Davom etish uchun quyidagi muddatlardan birini tanlang va faollashtiring:", 
                reply_markup=get_tariff_keyboard()
            )
            return

    # Admin Panel
    if user_id in [ADMIN_ID, MADIWAY_ADMIN_ID]:
        kb = types.InlineKeyboardMarkup(inline_keyboard=[
            [types.InlineKeyboardButton(text="⚙️ Start xabarini sozlash", callback_data="btn_add_start_msg"),
             types.InlineKeyboardButton(text="📊 Statistika", callback_data="btn_stats")],
            [types.InlineKeyboardButton(text="⭐️ Kanalga yuk (BEPUL)", callback_data="btn_kanal_tashlash"),
             types.InlineKeyboardButton(text="✨ Bitta Topicga (PULLIK)", callback_data="btn_bitta_topic")],
            [types.InlineKeyboardButton(text="💥 Hammasiga yuborish (PULLIK)", callback_data="btn_hamma_topic")],
            [types.InlineKeyboardButton(text="🆕 Yangi Guruhga xabar (PULLIK)", callback_data="btn_yangi_guruh")],
            [types.InlineKeyboardButton(text="🚛 Yangi Guruh 100 ta yuk", callback_data="btn_yangi_guruh_100")],
            [types.InlineKeyboardButton(text="📸 Yangi Guruh (10 ta rasm)", callback_data="btn_yangi_guruh_media")],
            [types.InlineKeyboardButton(text="🔑 VIP Obuna Aktivlashtirish", callback_data="btn_give_vip")]
        ])
        await message.answer("💻 <b>𝗠𝗔𝗗𝗜𝗪𝗔𝗬 | 𝗔𝗗𝗠𝗜𝗡 𝗣𝗔𝗡𝗘𝗟</b>", reply_markup=kb)
    else:
        kb = types.InlineKeyboardMarkup(inline_keyboard=[
            [types.InlineKeyboardButton(text="💰 Guruhga qo'shilish / Tariflar", callback_data="btn_show_tariffs")],
            [types.InlineKeyboardButton(text="📢 MadiWay Kanaliga o'tish", url=f"https://t.me/{CHANNEL_USER}")]
        ])
        await message.answer("🏔 <b>MadiWay logistika tizimiga xush kelibsiz!</b>\n\nYuklar haqida ma'lumot olish hamda pullik guruhlarga qo'shilish uchun tugmalardan foydalaning:", reply_markup=kb)

# --- TARIFLAR VA HAVOLA TEKSHIRUV ---
@dp.callback_query(F.data == "btn_show_tariffs")
async def show_tariffs_menu(callback: types.CallbackQuery, state: FSMContext):
    await callback.answer()
    await callback.message.answer(LINKS_INFO)
    await state.set_state(MadiWayStates.kutish_guruh_linki)

@dp.message(MadiWayStates.kutish_guruh_linki)
async def process_group_link(message: types.Message, state: FSMContext):
    link_text = message.text.lower() if message.text else ""
    
    if "madiwayy_gr" in link_text or "madiwayy_group" in link_text:
        guruh_nomi = "MadiWay Asosiy Guruh (Yuklar)"
    elif "international_logistik" in link_text:
        guruh_nomi = "MadiWay Yangi Guruh (International)"
    elif "madiwayy" in link_text:
        # Agar adashib kanal linkini tashlasa ogohlantiramiz
        await message.answer("📢 MadiWay kanali mutloq bepul! Iltimos pullik guruhlardan birini linkini yuboring.")
        return
    else:
        guruh_nomi = "Siz tanlagan guruh"

    await state.update_data(tanlangan_guruh=guruh_nomi)
    await message.answer(f"✅ <b>Guruh tasdiqlandi:</b> {guruh_nomi}\n\n⏱ Ushbu guruhga kirish muddatini tanlang:", reply_markup=get_tariff_keyboard())

@dp.callback_query(MadiWayStates.kutish_guruh_linki, F.data.startswith('track_'))
async def track_and_redirect(callback: types.CallbackQuery, state: FSMContext):
    await callback.answer()
    parts = callback.data.split("_")
    kun = parts[1]
    user_data = await state.get_data()
    guruh_nomi = user_data.get("tanlangan_guruh", "Noma'lum guruh")
    user = callback.from_user
    
    alert = (
        f"🔔 <b>YANGI TO'LOV SO'ROVI:</b>\n\n"
        f"👤 Foydalanuvchi: {user.full_name}\n"
        f"🆔 ID: <code>{user.id}</code>\n"
        f"🌐 Username: @{user.username if user.username else 'yoq'}\n"
        f"📦 Guruh: <b>{guruh_nomi}</b>\n"
        f"🛒 Tarif: {parts[1]} {parts[2]}\n"
        f"➔ Foydalanuvchi hozir @{OWNER_USERNAME} ga o'tmoqda."
    )
    for adm in [MADIWAY_ADMIN_ID, ADMIN_ID]:
        try: await bot.send_message(chat_id=adm, text=alert)
        except: pass
        
    kb = types.InlineKeyboardMarkup(inline_keyboard=[[types.InlineKeyboardButton(text="🚀 Adminga chek yuborish", url=f"https://t.me/{OWNER_USERNAME}")]])
    await callback.message.answer(
        f"💳 <b>To'lov ma'lumotlari:</b>\nKartaga nusxa oling: <code>4916-9903-5000-8311</code>\n\n"
        f"Tanlangan muddat: <b>{kun} kun/oy</b>\n\n"
        f"👇 Pastdagi tugma orqali adminga o'ting va to'lov chekingizni yuboring. Administrator sizni guruhga qo'shadi!", 
        reply_markup=kb
    )
    await state.clear()

# --- ADMIN TUGLMALARI ---
@dp.callback_query(F.data.startswith('btn_'))
async def admin_buttons(callback: types.CallbackQuery, state: FSMContext):
    await callback.answer()
    if callback.data == "btn_add_start_msg":
        await callback.message.answer("⚙️ Yangi start xabarni yuboring:")
        await state.set_state(MadiWayStates.kutish_global_start)
    elif callback.data == "btn_kanal_tashlash":
        await callback.message.answer("📥 Kanal yukini yuboring (BEPUL KO'RILADI):")
        await state.set_state(MadiWayStates.kutish_kanal_yuk)
    elif callback.data == "btn_hamma_topic":
        await callback.message.answer("💥 Barcha topiklarga yuboriladigan yukni kiriting:")
        await state.set_state(MadiWayStates.kutish_hamma_topic_yuk)
    elif callback.data == "btn_yangi_guruh":
        await callback.message.answer("📥 Yangi guruhga oddiy xabarni kiriting:")
        await state.set_state(MadiWayStates.kutish_yangi_guruh_yuk)
    elif callback.data == "btn_yangi_guruh_100":
        await callback.message.answer("🚛 Yangi guruhga ketma-ket yuk xabarini yuboring:")
        await state.set_state(MadiWayStates.kutish_yangi_guruh_100_yuk)
    elif callback.data == "btn_yangi_guruh_media":
        await callback.message.answer("📸 Yangi guruh uchun 10 tagacha rasm/videoni bitta albom qilib (caption yozib) yuboring:")
        await state.set_state(MadiWayStates.kutish_yangi_guruh_media_yuk)
    elif callback.data == "btn_bitta_topic":
        btns = [types.InlineKeyboardButton(text=n, callback_data=f"select_topic_{id}") for n, id in TOPICS.items()]
        kb = types.InlineKeyboardMarkup(inline_keyboard=[btns[i:i+2] for i in range(0, len(btns), 2)])
        await callback.message.answer("📍 Bo'limni tanlang:", reply_markup=kb)

# --- 10 TAGACHA RASM (MEDIA GROUP) QABUL QILISH FUNKSIYASI ---
@dp.message(MadiWayStates.kutish_yangi_guruh_media_yuk, F.media_group_id)
async def handle_yangi_guruh_media_group(message: types.Message, state: FSMContext):
    mg_id = message.media_group_id
    if mg_id not in MEDIA_GROUPS_CACHE:
        MEDIA_GROUPS_CACHE[mg_id] = []
        asyncio.create_task(process_media_group_delayed(mg_id, state, message.message_id, message.from_user.id))
    MEDIA_GROUPS_CACHE[mg_id].append(message)

# Rasmlarni xatosiz bitta albom qilib yuborish qismi
async def process_media_group_delayed(mg_id: str, state: FSMContext, original_msg_id: int, user_id: int):
    await asyncio.sleep(1.5)  # Telegram hamma rasmni uzatib olishi uchun vaqt
    messages = MEDIA_GROUPS_CACHE.get(mg_id, [])
    if not messages: return
    
    caption_text = ""
    for msg in messages:
        if msg.caption:
            caption_text = msg.caption
            break
            
    m_id = f"g{original_msg_id}"
    ydb = load_yuk_db(); ydb[m_id] = caption_text; save_yuk_db(ydb)
    bot_info = await bot.get_me()
    
    short_txt = caption_text[:150] + "..." if len(caption_text) > 150 else caption_text
    cap = get_premium_caption(short_txt, "𝗫𝗔𝗩𝗙𝗦𝗜𝗭 𝗠𝗘𝗗𝗜𝗔 𝗬𝗨𝗞")
    
    # Albom yig'ish (MediaGroupBuilder orqali fayllarni joylash)
    media_group = MediaGroupBuilder()
    is_first = True
    for msg in messages:
        # Birinchi rasmga matnni (caption) biriktiramiz, qolganlariga shart emas
        current_cap = cap if is_first else None
        if msg.photo:
            media_group.add_photo(media=msg.photo[-1].file_id, caption=current_cap)
            is_first = False
        elif msg.video:
            media_group.add_video(media=msg.video.file_id, caption=current_cap)
            is_first = False
            
    try:
        # Albomni yuboramiz
        await bot.send_media_group(chat_id=NEW_GROUP_ID, media=media_group.build())
        # To'liq ko'rish tugmasini albom ostidan alohida xabar qilib chiqaramiz
        await bot.send_message(
            chat_id=NEW_GROUP_ID, 
            text="👆 <b>Yuqoridagi media yukning to'liq ma'lumotlarini ko'rish:</b>", 
            reply_markup=get_group_kb(bot_info.username, m_id)
        )
        await bot.send_message(chat_id=user_id, text="✅ Albom va VIP ko'rish tugmasi yangi guruhga muvaffaqiyatli ketdi!")
    except Exception as e:
        logging.error(f"Albom yuborishda xato: {e}")
        await bot.send_message(chat_id=user_id, text="❌ Albomni yuborishda xatolik yuz berdi. Bot guruhda adminligini tekshiring.")
        
    if mg_id in MEDIA_GROUPS_CACHE: del MEDIA_GROUPS_CACHE[mg_id]
    await state.clear()

# --- 100 TA YUK YUBORISHDA LIMIT MUAMMOSINI DAVOLASH ---
@dp.message(MadiWayStates.kutish_yangi_guruh_100_yuk)
async def yangi_guruh_100_yuk(message: types.Message, state: FSMContext):
    txt = message.html_text or message.caption or ""
    m_id = f"g{message.message_id}"
    ydb = load_yuk_db(); ydb[m_id] = txt; save_yuk_db(ydb)
    
    bot_info = await bot.get_me()
    short_txt = txt[:150] + "..." if len(txt) > 150 else txt
    cap = get_premium_caption(short_txt, "𝗫𝗔𝗩𝗙𝗦𝗜𝗭 𝗬𝗨𝗞")
    
    # 100 ta ketma-ket yuborilganda flood xato bermasligi uchun biroz kutish qo'shildi
    await asyncio.sleep(0.4) 
    res = await send_all(NEW_GROUP_ID, message, cap, get_group_kb(bot_info.username, m_id))
    if res:
        await message.answer("✅ Yuk yangi guruhga yuborildi!")
    else:
        await message.answer("❌ Xatolik yuz berdi.")
    await state.clear()

# --- QOLGAN STANDART OPERATSIYALAR ---
@dp.message(MadiWayStates.kutish_kanal_yuk)
async def chan_yuk(message: types.Message, state: FSMContext):
    txt = message.html_text or message.caption or ""
    m_id = f"c{message.message_id}"  # Kanal yuklari 'c' bilan saqlanadi
    ydb = load_yuk_db(); ydb[m_id] = txt; save_yuk_db(ydb)
    bot_info = await bot.get_me()
    cap = get_premium_caption(txt[:150] + "...")
    await send_all(CHANNEL_ID, message, cap, get_group_kb(bot_info.username, m_id))
    await message.answer("✅ Kanalga muvaffaqiyatli yuborildi! (Bu xabarni foydalanuvchilar mutloq bepul ko'rishadi)")
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
        await asyncio.sleep(0.4)  # Limit oldini olish uchun
    await message.answer("✅ Barcha topiklarga pullik rejimda ketdi!")
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
    await message.answer("✅ Topikka pullik rejimda yuborildi!")
    await state.clear()

@dp.message(MadiWayStates.kutish_yangi_guruh_yuk)
async def yangi_guruh_yuk(message: types.Message, state: FSMContext):
    txt = message.html_text or message.caption or ""
    cap = get_premium_caption(txt, "YANGI GURUH ELONI")
    await send_all(NEW_GROUP_ID, message, cap, get_group_kb(None))
    await message.answer("✅ Oddiy xabar yangi guruhga ketdi!")
    await state.clear()

async def send_all(chat_id, message, caption, kb, t_id=None):
    try:
        if message.photo: return await bot.send_photo(chat_id, message.photo[-1].file_id, caption=caption, reply_markup=kb, message_thread_id=t_id)
        elif message.video: return await bot.send_video(chat_id, message.video.file_id, caption=caption, reply_markup=kb, message_thread_id=t_id)
        else: return await bot.send_message(chat_id, caption, reply_markup=kb, message_thread_id=t_id)
    except Exception as e:
        logging.error(f"Xabar yuborishda xato: {e}")
        return None

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
