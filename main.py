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

# Kanallar va guruhlar username va ID lari
CHANNEL_USER = "MADIWAYy"         
GROUP_USER = "MADIWAYy_Gr"        
NEW_GROUP_USER = "International_logistik"  

CHANNEL_ID = "-1003996104316"      
GROUP_ID = "-1003963001370"        # MadiWay Asosiy Guruh ID
NEW_GROUP_ID = "-1004370807037"    # Yangi guruh ID
MADINA_GROUP_ID = "-1001456164408"  # Madina Kilo Kiyimlar Guruh ID

ADMIN_ID = 6977836294         
MADIWAY_ADMIN_ID = 8112179116  
OWNER_USERNAME = "yusufxonpro1"    

bot = Bot(token=BOT_TOKEN, default=DefaultBotProperties(parse_mode="HTML"))
dp = Dispatcher(storage=MemoryStorage())

# Ma'lumotlar bazasi fayllari
USERS_DB_FILE = "users_database.json"
YUK_DB_FILE = "yuklar_database.json"
AUTO_TASKS_FILE = "auto_tasks_database.json"
START_MSG_FILE = "start_message_data.json"  

UZB_TZ = timezone(timedelta(hours=5))
MEDIA_GROUPS_CACHE: Dict[str, List[types.Message]] = {}

# Taqiqlangan so'zlar filtri
BAD_WORDS = ["sikt", "qo'taq", "am", "bola", "skaman", "jalap", "qanc", "gandon", "tsex", "akkaunt", "otili", "ortilar", "sokin", "krid", "reklama"]

# Tarif matni
AUTO_PAYMENT_MESSAGE = (
    "👋 <b>MadiWay tizimida YUK TASHALASH va VIP guruh tariflari:</b>\n\n"
    "💳 <b>UzCard / VISA Card:</b> <code>4916-9903-5000-8311</code>\n"
    "👤 <b>Ega:</b> MadiWay Admin\n\n"
    "💵 <b>Oddiy Kirish va Tashlash tariflari (Har 5-9 soatda qayta tashlanadi):</b>\n"
    "🔹 1 kunlik — 15 000 so'm\n"
    "🔹 2 kunlik — 20 000 so'm\n"
    "🔹 3 kunlik — 30 000 so'm\n"
    "🔹 1 oylik — 50 000 so'm\n\n"
    "⚡️ <b>TEZKOR TARIF (Har 12 minutda avto-qayta tashlash):</b>\n"
    "🚀 1 kunlik (Har 12 daqiqada guruhga yuborish) — 30 000 so'm\n\n"
    "⚠️ To'lovni amalga oshirib, chekni shu yerga yuboring va adminga aloqaga chiqing!\n"
    "📞 <b>Aloqa:</b> +998 88 325 80 07"
)

TOPICS = {
    "🌍 Europa": 2, "🇩🇪 Germaniya": 14, "🇷🇺 Rossiya": 4, "🇰🇬 Qirg'iziston": 6,
    "🇰🇿 Kazakistan": 8, "🇮🇷 Eron": 10, "🇹🇯 Tojikston": 12, "🇧🇾 Belarusiya": 16,
    "🇬🇪 Gruziya": 18, "📣 Elon berish": 1
}

# --- BAZA BILAN ISHLASH ---
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

def load_tasks():
    if os.path.exists(AUTO_TASKS_FILE):
        try: 
            with open(AUTO_TASKS_FILE, "r", encoding="utf-8") as f: return json.load(f)
        except: pass
    return {}

def save_tasks(data):
    with open(AUTO_TASKS_FILE, "w", encoding="utf-8") as f: json.dump(data, f, ensure_ascii=False, indent=4)

def load_start_msg():
    if os.path.exists(START_MSG_FILE):
        try: 
            with open(START_MSG_FILE, "r", encoding="utf-8") as f: return json.load(f)
        except: pass
    return {
        "text": "🏔 <b>MadiWay logistika tizimiga xush kelibsiz!</b>\n\nYuklar haqida ma'lumot olish hamda guruhlarda yuk e'lon qilish uchun quyidagi tugmalardan foydalaning:",
        "type": "text",
        "file_id": None
    }

def check_premium(user_id):
    db = load_db()
    uid = str(user_id)
    if uid in db["users"] and db["users"][uid]["premium_until"]:
        try:
            until_dt = datetime.fromisoformat(db["users"][uid]["premium_until"]).astimezone(UZB_TZ)
            if datetime.now(UZB_TZ) < until_dt: return True
        except: pass
    return False

def get_premium_caption(main_text, status_label="𝗬𝗨𝗞 𝗘𝗟𝗢𝗡𝗜", is_new_group=False):
    now = datetime.now(UZB_TZ)
    sana_soat = now.strftime("📅 %Y-%m-%d  🕒 %I:%M %p") 
    brand = "𝗜𝗡𝗧𝗘𝗥𝗡𝗔𝗧𝗜𝗢𝗡𝗔𝗟 𝗟𝗢𝗚𝗜𝗦𝗧𝗜𝗖" if is_new_group else "𝗠𝗔𝗗𝗜𝗪𝗔𝗬"
    return f"⭐️ <b>{brand} | {status_label}</b> ⭐️\n───────────────────────\n{main_text}\n───────────────────────\n⏳ Vaqt: {sana_soat}\n📢 Kanal: t.me/{CHANNEL_USER}"

def get_group_kb(bot_user, msg_id=None):
    buttons = []
    if msg_id and bot_user: 
        buttons.append([types.InlineKeyboardButton(text="⭐️ Yukni to'liq ko'rish", url=f"https://t.me/{bot_user}?start={msg_id}")])
    return types.InlineKeyboardMarkup(inline_keyboard=buttons)

def get_tariff_keyboard():
    return types.InlineKeyboardMarkup(inline_keyboard=[
        [types.InlineKeyboardButton(text="💰 1 Kun (15 000)", callback_data="track_1_kun")],
        [types.InlineKeyboardButton(text="💰 2 Kun (20 000)", callback_data="track_2_kun")],
        [types.InlineKeyboardButton(text="💰 3 Kun (30 000)", callback_data="track_3_kun")],
        [types.InlineKeyboardButton(text="👑 1 Oy (50 000)", callback_data="track_30_kun")]
    ])

def get_guruh_tanlash_kb():
    return types.InlineKeyboardMarkup(inline_keyboard=[
        [types.InlineKeyboardButton(text="🚛 MadiWay Asosiy Guruh", callback_data="buy_guruh_main")],
        [types.InlineKeyboardButton(text="🌍 International Logistik", callback_data="buy_guruh_new")]
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
    user_kutish_guruh_tanlash = State()
    user_kutish_topic_tanlash = State()
    user_kutish_yuk = State()       
    user_kutish_tel = State()       
    admin_quick_vip_days = State()

# --- START BUYRUG'I ---
@dp.message(Command("start"), F.chat.type == "private")
async def start_cmd(message: types.Message, command: CommandObject, state: FSMContext):
    await state.clear()
    user_id = message.from_user.id
    
    db = load_db()
    uid = str(user_id)
    if uid not in db["users"]:
        db["users"][uid] = {
            "username": message.from_user.username or "yo'q", 
            "full_name": message.from_user.full_name, 
            "premium_until": None, 
            "interval_type": "oddiy", 
            "chosen_group": "MadiWay Asosiy Guruh"
        }
        save_db(db)
    
    if command.args:
        yuk_id = command.args
        ydb = load_yuk_db()
        data = ydb.get(yuk_id)
        if yuk_id.startswith("c"):
            if data:
                txt = data if isinstance(data, str) else data.get("text", "")
                await message.answer(get_premium_caption(txt, "𝗧𝗢'𝗟𝗜𝗤 𝗠𝗔'𝗟𝗨𝗠𝗢𝗧"))
            else: 
                await message.answer("⚠️ Yuk ma'lumotlari topilmadi.")
            return

        if check_premium(user_id) or user_id in [ADMIN_ID, MADIWAY_ADMIN_ID]:
            if data:
                if isinstance(data, str): 
                    await message.answer(get_premium_caption(data, "𝗧𝗢'𝗟𝗜𝗤 𝗠𝗔'𝗟𝗨𝗠𝗢𝗧"))
                else:
                    text = data.get("text", "")
                    phone = data.get("phone", "Ko'rsatilmagan")
                    owner = data.get("owner", "Noma'lum")
                    is_ng = data.get("is_new_group", False)
                    full_info = f"{text}\n\n☎️ <b>Aloqa uchun telefon:</b> <code>{phone}</code>\n👤 <b>Yuk egasi:</b> {owner}"
                    await message.answer(get_premium_caption(full_info, "𝗧𝗢'𝗟𝗜𝗤 𝗠𝗔'𝗟𝗨𝗠𝗢𝗧 VA RAQAM", is_new_group=is_ng))
            else: 
                await message.answer("⚠️ Yuk topilmadi.")
            return
        else:
            await message.answer(AUTO_PAYMENT_MESSAGE, reply_markup=get_guruh_tanlash_kb())
            return

    if user_id in [ADMIN_ID, MADIWAY_ADMIN_ID]:
        kb = types.InlineKeyboardMarkup(inline_keyboard=[
            [types.InlineKeyboardButton(text="⚙️ Start xabari (Media)", callback_data="btn_add_start_msg"), types.InlineKeyboardButton(text="🧹 Reklama Tozalash", callback_data="btn_clean_status")],
            [types.InlineKeyboardButton(text="⭐️ Kanalga yuk (BEPUL)", callback_data="btn_kanal_tashlash"), types.InlineKeyboardButton(text="✨ Bitta Topicga", callback_data="btn_bitta_topic")],
            [types.InlineKeyboardButton(text="💥 Hammasiga yuborish", callback_data="btn_hamma_topic"), types.InlineKeyboardButton(text="📊 Statistika", callback_data="btn_stats")],
            [types.InlineKeyboardButton(text="🆕 Yangi Guruh xabar", callback_data="btn_yangi_guruh"), types.InlineKeyboardButton(text="🚛 Yangi Guruh 100 ta yuk", callback_data="btn_yangi_guruh_100")],
            [types.InlineKeyboardButton(text="📸 Yangi Guruh (10 rasm)", callback_data="btn_yangi_guruh_media"), types.InlineKeyboardButton(text="🔑 VIP Faollashtirish", callback_data="btn_give_vip")]
        ])
        await message.answer("💻 <b>𝗠𝗔𝗗𝗜𝗪𝗔𝗬 | 𝗔𝗗𝗠𝗜𝗡 𝗣𝗔𝗡𝗘𝗟</b>", reply_markup=kb)
    else:
        start_data = load_start_msg()
        buttons = [[types.InlineKeyboardButton(text="💰 Guruhga qo'shilish / Tariflar", callback_data="btn_show_tariffs")]]
        if check_premium(user_id): 
            buttons.append([types.InlineKeyboardButton(text="📦 Yuk Tashlash (Avto-Post)", callback_data="btn_user_send_yuk")])
        kb = types.InlineKeyboardMarkup(inline_keyboard=buttons)
        
        if start_data["type"] == "photo": 
            await message.answer_photo(photo=start_data["file_id"], caption=start_data["text"], reply_markup=kb)
        elif start_data["type"] == "video": 
            await message.answer_video(video=start_data["file_id"], caption=start_data["text"], reply_markup=kb)
        else: 
            await message.answer(text=start_data["text"], reply_markup=kb)

# --- TARIFLAR MENYUSI VA TASDIQLASH ---
@dp.callback_query(F.data == "btn_show_tariffs")
async def show_tariffs_menu(callback: types.CallbackQuery):
    await callback.answer()
    await callback.message.answer(AUTO_PAYMENT_MESSAGE, reply_markup=get_guruh_tanlash_kb())

@dp.callback_query(F.data.startswith("buy_guruh_"))
async def process_buy_guruh(callback: types.CallbackQuery, state: FSMContext):
    await callback.answer()
    g_type = callback.data.split("_")[2]
    guruh_nomi = "MadiWay Asosiy Guruh" if g_type == "main" else "International Logistik"
    await state.update_data(tanlangan_guruh=guruh_nomi)
    await callback.message.answer(f"📦 <b>Guruh:</b> {guruh_nomi}\n⏱ Kerakli tarif muddatini tanlang:", reply_markup=get_tariff_keyboard())

@dp.callback_query(F.data.startswith('track_'))
async def track_and_redirect(callback: types.CallbackQuery, state: FSMContext):
    await callback.answer()
    parts = callback.data.split("_")
    user_data = await state.get_data()
    guruh_nomi = user_data.get("tanlangan_guruh", "MadiWay Asosiy Guruh")
    
    db = load_db()
    uid = str(callback.from_user.id)
    if uid in db["users"]:
        db["users"][uid]["chosen_group"] = guruh_nomi
        save_db(db)
        
    alert = (
        f"🔔 <b>YANGI TO'LOV SO'ROVI:</b>\n\n"
        f"👤 Foydalanuvchi: {callback.from_user.full_name}\n"
        f"🆔 ID: <code>{callback.from_user.id}</code>\n"
        f"📦 Guruh: {guruh_nomi}\n"
        f"🛒 Tarif: {parts[1]} {parts[2]}"
    )
    admin_kb = types.InlineKeyboardMarkup(inline_keyboard=[[types.InlineKeyboardButton(text="✅ To'lovni tasdiqlash", callback_data=f"adm_approve_{callback.from_user.id}")]])
    for adm in [MADIWAY_ADMIN_ID, ADMIN_ID]:
        try: await bot.send_message(chat_id=adm, text=alert, reply_markup=admin_kb)
        except: pass
        
    kb = types.InlineKeyboardMarkup(inline_keyboard=[[types.InlineKeyboardButton(text="🚀 Adminga chek yuborish", url=f"https://t.me/{OWNER_USERNAME}")]])
    await callback.message.answer(f"💳 <b>To'lov ma'lumotlari:</b>\nKarta: <code>4916-9903-5000-8311</code>\n\n👇 Pastdagi tugma orqali adminga chekni yuboring, admin to'lovni tasdiqlashi bilan tizim sizni faollashtiradi!", reply_markup=kb)
    await state.clear()

@dp.callback_query(F.data.startswith("adm_approve_"))
async def admin_quick_approve(callback: types.CallbackQuery, state: FSMContext):
    await callback.answer()
    target_uid = callback.data.split("_")[2]
    await state.update_data(quick_target_uid=target_uid)
    kb = types.InlineKeyboardMarkup(inline_keyboard=[
        [types.InlineKeyboardButton(text="🗓 1 Kun (Oddiy - 5 soat)", callback_data="qset_1_oddiy")],
        [types.InlineKeyboardButton(text="🗓 1 Oy (Oddiy - 5 soat)", callback_data="qset_30_oddiy")],
        [types.InlineKeyboardButton(text="🚀 1 Kun (⚡️ Tezkor - 12 minut)", callback_data="qset_1_tezkor")]
    ])
    await callback.message.answer(f"👤 ID: <code>{target_uid}</code> bo'lgan foydalanuvchiga VIP muddatini bering:", reply_markup=kb)
    await state.set_state(MadiWayStates.admin_quick_vip_days)

@dp.callback_query(MadiWayStates.admin_quick_vip_days, F.data.startswith("qset_"))
async def admin_finalize_quick_vip(callback: types.CallbackQuery, state: FSMContext):
    await callback.answer()
    parts = callback.data.split("_")
    days, itype = int(parts[1]), parts[2]
    sdata = await state.get_data()
    found_uid = sdata.get("quick_target_uid")
    
    if found_uid:
        db = load_db()
        if found_uid not in db["users"]: 
            db["users"][found_uid] = {"username": "yo'q", "full_name": "Noma'lum", "premium_until": None, "interval_type": "oddiy", "chosen_group": "MadiWay Asosiy Guruh"}
        end_date = datetime.now(UZB_TZ) + timedelta(days=days)
        db["users"][found_uid]["premium_until"] = end_date.isoformat()
        db["users"][found_uid]["interval_type"] = itype
        db["premium_count"] = db.get("premium_count", 0) + 1
        guruh_nomi = db["users"][found_uid].get("chosen_group", "MadiWay Asosiy Guruh")
        save_db(db)
        
        for gid in [NEW_GROUP_ID, GROUP_ID, MADINA_GROUP_ID]:
            try: await bot.unban_chat_member(chat_id=gid, user_id=int(found_uid), only_if_banned=True)
            except: pass

        formatted = end_date.strftime("%d-%m-%Y %H:%M")
        await callback.message.answer(f"✅ VIP muvaffaqiyatli faollashtirildi!\nMuddat: {formatted} gacha.")
        
        invite_buttons = []
        welcome_text = f"🎉 <b>Administrator to'lovingizni qabul qildi va tasdiqladi!</b>\n\nSizga yuk tashlash imkoniyati ochildi.\n⏱ VIP muddati: <code>{formatted}</code> gacha belgilandi.\n\n"
        
        if guruh_nomi == "International Logistik":
            invite_buttons.append([types.InlineKeyboardButton(text="🌍 International Logistik Guruhiga Kirish", url=f"https://t.me/{NEW_GROUP_USER}")])
        else:
            try:
                invite_link_obj = await bot.create_chat_invite_link(chat_id=GROUP_ID, member_limit=1, name="VIP Special Single Link")
                invite_buttons.append([types.InlineKeyboardButton(text="Cg== MadiWay Asosiy Guruhga Kirish (1 marta)", url=invite_link_obj.invite_link)])
                invite_buttons.append([types.InlineKeyboardButton(text="✅ Guruhga kirdim (Tugmani o'chirish)", callback_data="delete_join_msg")])
            except: 
                invite_buttons.append([types.InlineKeyboardButton(text="Cg== MadiWay Asosiy Guruh", url=f"https://t.me/{GROUP_USER}")])
        
        invite_buttons.append([types.InlineKeyboardButton(text="📦 Yuk Tashlashni Boshlash", callback_data="btn_user_send_yuk")])
        try: await bot.send_message(chat_id=int(found_uid), text=welcome_text, reply_markup=types.InlineKeyboardMarkup(inline_keyboard=invite_buttons))
        except: pass
    await state.clear()

@dp.callback_query(F.data == "delete_join_msg")
async def delete_join_message_handler(callback: types.CallbackQuery):
    try: await callback.message.delete()
    except: pass

# --- GURUH XABARLARINI NAZORAT QILISH (REKLAMA/SOKINISH TOZALAGICH) ---
@dp.message(F.chat.type.in_({"group", "supergroup"}))
async def group_moderator_handler(message: types.Message):
    if message.new_chat_members or message.left_chat_member:
        try: await message.delete()
        except: pass
        return

    chat_id_str = str(message.chat.id)
    user_id = message.from_user.id

    if user_id in [ADMIN_ID, MADIWAY_ADMIN_ID]:
        return

    if chat_id_str == MADINA_GROUP_ID:
        msg_text = message.text or message.caption or ""
        has_link = "http" in msg_text.lower() or "t.me" in msg_text.lower() or "@" in msg_text
        has_bad_word = any(bad in msg_text.lower() for bad in BAD_WORDS)
        
        if has_link or has_bad_word:
            try: await message.delete()
            except: pass

# --- FOYDALANUVCHI YUK YUBORISH TIZIMI ---
@dp.callback_query(F.data == "btn_user_send_yuk")
async def user_send_yuk_start(callback: types.CallbackQuery, state: FSMContext):
    await callback.answer()
    if not check_premium(callback.from_user.id):
        await callback.message.answer("❌ Sizda VIP aktiv emas!")
        return
    kb = types.InlineKeyboardMarkup(inline_keyboard=[
        [types.InlineKeyboardButton(text="Asosiy Guruh (MadiWay Yuklar)", callback_data="user_target_main")],
        [types.InlineKeyboardButton(text="Yangi Guruh (International)", callback_data="user_target_new")]
    ])
    await callback.message.answer("🎯 <b>Yukingiz qaysi guruhga avtomatik va vaqtli joylab turilsin?</b>", reply_markup=kb)
    await state.set_state(MadiWayStates.user_kutish_guruh_tanlash)

@dp.callback_query(MadiWayStates.user_kutish_guruh_tanlash, F.data.startswith("user_target_"))
async def user_guruh_tanladi(callback: types.CallbackQuery, state: FSMContext):
    await callback.answer()
    target = callback.data.split("_")[2]
    await state.update_data(user_target_group=target)
    if target == "main":
        btns = [types.InlineKeyboardButton(text=n, callback_data=f"user_topic_{id}") for n, id in TOPICS.items()]
        kb = types.InlineKeyboardMarkup(inline_keyboard=[btns[i:i+2] for i in range(0, len(btns), 2)])
        await callback.message.answer("📍 <b>MadiWay Asosiy guruhidan kerakli bo'limni tanlang:</b>", reply_markup=kb)
        await state.set_state(MadiWayStates.user_kutish_topic_tanlash)
    else:
        await callback.message.answer("📥 <b>Yangi guruhga yuboriladigan yuk matnini kiriting:</b>\n⚠️ Reklama, havolalar taqiqlanadi!")
        await state.set_state(MadiWayStates.user_kutish_yuk)

@dp.callback_query(MadiWayStates.user_kutish_topic_tanlash, F.data.startswith("user_topic_"))
async def user_topic_tanladi(callback: types.CallbackQuery, state: FSMContext):
    await callback.answer()
    tid = int(callback.data.split("_")[2])
    await state.update_data(user_target_topic=tid)
    await callback.message.answer("📥 <b>Tanlangan bo'lim uchun yuk matnini kiriting:</b>\n⚠️ Reklama taqiqlanadi!")
    await state.set_state(MadiWayStates.user_kutish_yuk)

@dp.message(MadiWayStates.user_kutish_yuk)
async def user_get_text(message: types.Message, state: FSMContext):
    text_check = message.text or message.caption or ""
    user_id = message.from_user.id
    if user_id not in [ADMIN_ID, MADIWAY_ADMIN_ID]:
        if "http" in text_check.lower() or "t.me" in text_check.lower() or "@" in text_check:
            await message.answer("❌ <b>Tizim xavfsizligi!</b> Reklama aniqlandi. Toza matn yuboring:")
            return
    await state.update_data(yuk_text=message.html_text)
    await message.answer("☎️ Bog'lanish uchun <b>Telefon Raqamingizni</b> yuboring:")
    await state.set_state(MadiWayStates.user_kutish_tel)

@dp.message(MadiWayStates.user_kutish_tel)
async def user_finish_yuk(message: types.Message, state: FSMContext):
    sdata = await state.get_data()
    yuk_text = sdata.get("yuk_text")
    t_group = sdata.get("user_target_group")
    t_topic = sdata.get("user_target_topic", None)
    phone = message.text
    user_id = message.from_user.id
    
    db = load_db()
    itype = db["users"].get(str(user_id), {}).get("interval_type", "oddiy")
    is_ng = (t_group == "new")
    m_id = f"u{message.message_id}"
    ydb = load_yuk_db()
    ydb[m_id] = {"text": yuk_text, "phone": phone, "owner": message.from_user.full_name, "user_id": user_id, "is_new_group": is_ng}
    save_yuk_db(ydb)
    
    tasks = load_tasks()
    tasks[str(user_id)] = {"yuk_id": m_id, "target_group": t_group, "target_topic": t_topic, "interval": 12 if itype == "tezkor" else 300, "last_sent": datetime.now(UZB_TZ).isoformat()}
    save_tasks(tasks)
    
    await message.answer("✅ <b>Tasdiqlandi! Yukingiz avto-postga joylandi.</b>")
    bot_info = await bot.get_me()
    cap = get_premium_caption(yuk_text[:150] + "...", "AVTO YUK", is_new_group=is_ng)
    chat = NEW_GROUP_ID if is_ng else GROUP_ID
    await bot.send_message(chat_id=chat, text=cap, reply_markup=get_group_kb(bot_info.username, m_id), message_thread_id=t_topic)
    await state.clear()

# --- ADMIN PANEL BOSHQARUVI ---
@dp.callback_query(F.data.startswith('btn_'))
async def admin_buttons(callback: types.CallbackQuery, state: FSMContext):
    await callback.answer()
    if callback.data == "btn_clean_status":
        await callback.message.answer(f"🧹 <b>Madina Kilo Kiyimlar Guruh Nazorati:</b>\n\n"
                                      f"ID: <code>{MADINA_GROUP_ID}</code>\n"
                                      f"⚡️ Kirdi-Chiqdi xabarlari: <b>Avtomat o'chiriladi</b>\n"
                                      f"🚫 Reklama va havolalar: <b>Taqiqlangan (O'chiriladi)</b>\n"
                                      f"🤬 So'kinish va haqoratlar: <b>Tozalanadi</b>\n"
                                      f"👑 Adminlar: <b>Cheklovsiz</b>")
    elif callback.data == "btn_add_start_msg":
        await callback.message.answer("⚙️ Yangi start xabari uchun Rasm, Video yoki oddiy Matn yuboring:")
        await state.set_state(MadiWayStates.kutish_global_start)
    elif callback.data == "btn_kanal_tashlash":
        await callback.message.answer("📥 Kanal yukini yuboring:")
        await state.set_state(MadiWayStates.kutish_kanal_yuk)
    elif callback.data == "btn_hamma_topic":
        await callback.message.answer("💥 Barcha topiklarga yuboriladigan yukni kiriting:")
        await state.set_state(MadiWayStates.kutish_hamma_topic_yuk)
    elif callback.data == "btn_yangi_guruh":
        await callback.message.answer("📥 Yangi guruhga xabarni kiriting:")
        await state.set_state(MadiWayStates.kutish_yangi_guruh_yuk)
    elif callback.data == "btn_yangi_guruh_100":
        await callback.message.answer("🚛 Yangi guruhga 100 ta yuk xabarini yuboring:")
        await state.set_state(MadiWayStates.kutish_yangi_guruh_100_yuk)
    elif callback.data == "btn_yangi_guruh_media":
        await callback.message.answer("📸 Yangi guruh uchun albomni yuboring:")
        await state.set_state(MadiWayStates.kutish_yangi_guruh_media_yuk)
    elif callback.data == "btn_bitta_topic":
        btns = [types.InlineKeyboardButton(text=n, callback_data=f"select_topic_{id}") for n, id in TOPICS.items()]
        kb = types.InlineKeyboardMarkup(inline_keyboard=[btns[i:i+2] for i in range(0, len(btns), 2)])
        await callback.message.answer("📍 Bo'limni tanlang:", reply_markup=kb)
    elif callback.data == "btn_give_vip":
        await callback.message.answer("🔑 VIP berish uchun Telegram ID yozing:")
        await state.set_state(MadiWayStates.giving_premium_username)
    elif callback.data == "btn_stats":
        db = load_db()
        await callback.message.answer(f"📊 <b>Statistika:</b>\n👤 A'zolar: {len(db['users'])}\n👑 VIP: {db.get('premium_count', 0)}")

# --- MANUAL VIP BERISH MUDDATI ---
@dp.message(MadiWayStates.giving_premium_username)
async def admin_vip_user(message: types.Message, state: FSMContext):
    await state.update_data(target_user=message.text.replace("@", "").strip())
    kb = types.InlineKeyboardMarkup(inline_keyboard=[
        [types.InlineKeyboardButton(text="🗓 1 Kun (Oddiy - 5 soat)", callback_data="set_user_vip_1_oddiy")],
        [types.InlineKeyboardButton(text="🗓 1 Oy (Oddiy - 5 soat)", callback_data="set_user_vip_30_oddiy")],
        [types.InlineKeyboardButton(text="🚀 1 Kun (⚡️ Tezkor - 12 minut)", callback_data="set_user_vip_1_tezkor")]
    ])
    await message.answer("⏱ Turi va muddatini tanlang:", reply_markup=kb)
    await state.set_state(MadiWayStates.giving_premium_days)

@dp.callback_query(MadiWayStates.giving_premium_days, F.data.startswith("set_user_vip_"))
async def admin_finalize_vip(callback: types.CallbackQuery, state: FSMContext):
    await callback.answer()
    parts = callback.data.split("_")
    days, itype = int(parts[3]), parts[4]
    data = await state.get_data()
    target = data.get("target_user")
    db = load_db()
    found_uid = None
    
    for uid, info in db["users"].items():
        if uid == target or info["username"].lower() == target.lower():
            found_uid = uid
            break
            
    if found_uid:
        end_date = datetime.now(UZB_TZ) + timedelta(days=days)
        db["users"][found_uid]["premium_until"] = end_date.isoformat()
        db["users"][found_uid]["interval_type"] = itype
        db["premium_count"] = db.get("premium_count", 0) + 1
        save_db(db)
        
        for gid in [NEW_GROUP_ID, GROUP_ID, MADINA_GROUP_ID]:
            try: await bot.unban_chat_member(chat_id=gid, user_id=int(found_uid), only_if_banned=True)
            except: pass
        await callback.message.answer(f"✅ VIP berildi!")
    await state.clear()

# --- ADMIN MATN/ALBOM AMALLARI ---
@dp.message(MadiWayStates.kutish_global_start)
async def save_start(message: types.Message, state: FSMContext):
    start_data = {"text": message.html_text or message.caption or "", "type": "text", "file_id": None}
    if message.photo: 
        start_data["type"] = "photo"
        start_data["file_id"] = message.photo[-1].file_id
    elif message.video: 
        start_data["type"] = "video"
        start_data["file_id"] = message.video.file_id
    with open(START_MSG_FILE, "w", encoding="utf-8") as f: json.dump(start_data, f, ensure_ascii=False, indent=4)
    await message.answer("✅ Start saqlandi.")
    await state.clear()

@dp.message(MadiWayStates.kutish_yangi_guruh_100_yuk)
async def yangi_guruh_100_yuk(message: types.Message, state: FSMContext):
    txt = message.html_text or message.caption or ""
    m_id = f"g{message.message_id}"
    ydb = load_yuk_db()
    ydb[m_id] = {"text": txt, "phone": "Admin", "owner": "Admin", "is_new_group": True}
    save_yuk_db(ydb)
    bot_info = await bot.get_me()
    cap = get_premium_caption(txt[:150] + "...", "YUKLAR", is_new_group=True)
    await asyncio.sleep(0.4)
    await send_all(NEW_GROUP_ID, message, cap, get_group_kb(bot_info.username, m_id))
    await message.answer("✅ 100 ta yuk guruhga ketdi!")
    await state.clear()

@dp.message(MadiWayStates.kutish_yangi_guruh_media_yuk, F.media_group_id)
async def handle_media_group(message: types.Message, state: FSMContext):
    mg_id = message.media_group_id
    if mg_id not in MEDIA_GROUPS_CACHE:
        MEDIA_GROUPS_CACHE[mg_id] = []
        asyncio.create_task(process_media_group_delayed(mg_id, state, message.message_id, message.from_user.id))
    MEDIA_GROUPS_CACHE[mg_id].append(message)

async def process_media_group_delayed(mg_id: str, state: FSMContext, original_msg_id: int, user_id: int):
    await asyncio.sleep(1.5)
    messages = MEDIA_GROUPS_CACHE.get(mg_id, [])
    if not messages: return
    caption_text = next((msg.caption for msg in messages if msg.caption), "")
    m_id = f"g{original_msg_id}"
    ydb = load_yuk_db()
    ydb[m_id] = {"text": caption_text, "phone": "MadiWay", "owner": "Admin", "is_new_group": True}
    save_yuk_db(ydb)
    bot_info = await bot.get_me()
    cap = get_premium_caption(caption_text[:150] + "...", "𝗫𝗔𝗩𝗙𝗦𝗜𝗭 𝗠𝗘𝗗𝗜𝗔", is_new_group=True)
    media_group = MediaGroupBuilder()
    is_first = True
    for msg in messages:
        current_cap = cap if is_first else None
        if msg.photo: 
            media_group.add_photo(media=msg.photo[-1].file_id, caption=current_cap)
            is_first = False
        elif msg.video: 
            media_group.add_video(media=msg.video.file_id, caption=current_cap)
            is_first = False
    try:
        await bot.send_media_group(chat_id=NEW_GROUP_ID, media=media_group.build())
        await bot.send_message(chat_id=NEW_GROUP_ID, text="▲ <b>Ma'lumotlar:</b>", reply_markup=get_group_kb(bot_info.username, m_id))
    except: pass
    if mg_id in MEDIA_GROUPS_CACHE: del MEDIA_GROUPS_CACHE[mg_id]
    await state.clear()

@dp.message(MadiWayStates.kutish_kanal_yuk)
async def chan_yuk(message: types.Message, state: FSMContext):
    txt = message.html_text or message.caption or ""
    m_id = f"c{message.message_id}"
    ydb = load_yuk_db()
    ydb[m_id] = txt
    save_yuk_db(ydb)
    bot_info = await bot.get_me()
    await send_all(CHANNEL_ID, message, get_premium_caption(txt), get_group_kb(bot_info.username, m_id))
    await message.answer("✅ Kanalga ketdi.")
    await state.clear()

@dp.message(MadiWayStates.kutish_hamma_topic_yuk)
async def all_yuk(message: types.Message, state: FSMContext):
    txt = message.html_text or message.caption or ""
    m_id = f"h{message.message_id}"
    ydb = load_yuk_db()
    ydb[m_id] = {"text": txt, "phone": "Admin", "owner": "Admin", "is_new_group": False}
    save_yuk_db(ydb)
    bot_info = await bot.get_me()
    for n, tid in TOPICS.items():
        await send_all(GROUP_ID, message, get_premium_caption(txt[:150] + "..."), get_group_kb(bot_info.username, m_id), tid)
        await asyncio.sleep(0.4)
    await message.answer("✅ Hammasiga ketdi.")
    await state.clear()

@dp.callback_query(F.data.startswith('select_topic_'))
async def topic_sel(callback: types.CallbackQuery, state: FSMContext):
    await state.update_data(target_topic_id=callback.data.split('_')[2])
    await callback.message.answer("📥 Yukni kiriting:")
    await state.set_state(MadiWayStates.kutish_bitta_topic_yuk)

@dp.message(MadiWayStates.kutish_bitta_topic_yuk)
async def bitta_topic_yuk(message: types.Message, state: FSMContext):
    tid = int((await state.get_data()).get("target_topic_id", 1))
    txt = message.html_text or message.caption or ""
    m_id = f"b{message.message_id}"
    ydb = load_yuk_db()
    ydb[m_id] = {"text": txt, "phone": "Admin", "owner": "Admin", "is_new_group": False}
    save_yuk_db(ydb)
    bot_info = await bot.get_me()
    await send_all(GROUP_ID, message, get_premium_caption(txt[:150] + "..."), get_group_kb(bot_info.username, m_id), tid)
    await message.answer("✅ Ketdi.")
    await state.clear()

@dp.message(MadiWayStates.kutish_yangi_guruh_yuk)
async def yangi_guruh_yuk(message: types.Message, state: FSMContext):
    txt = message.html_text or message.caption or ""
    await send_all(NEW_GROUP_ID, message, get_premium_caption(txt, "INFO", is_new_group=True), get_group_kb(None))
    await message.answer("✅ Yuborildi.")
    await state.clear()

async def send_all(chat_id, message, caption, kb, t_id=None):
    try:
        if message.photo: 
            return await bot.send_photo(chat_id, message.photo[-1].file_id, caption=caption, reply_markup=kb, message_thread_id=t_id)
        elif message.video: 
            return await bot.send_video(chat_id, message.video.file_id, caption=caption, reply_markup=kb, message_thread_id=t_id)
        else: 
            return await bot.send_message(chat_id, caption, reply_markup=kb, message_thread_id=t_id)
    except: return None

# --- SHAXSIY CHAT AVTO-JAVOB ---
@dp.message(F.chat.type == "private")
async def auto_reply_handler(message: types.Message):
    if message.from_user.id not in [ADMIN_ID, MADIWAY_ADMIN_ID]:
        await message.answer(AUTO_PAYMENT_MESSAGE, reply_markup=get_guruh_tanlash_kb())

# --- 🔄 MULTI-GURUH CRON TIZIMI (XAVFSIZ TOZALASH) ---
async def auto_cron_job():
    while True:
        try:
            now = datetime.now(UZB_TZ)
            db = load_db()
            tasks = load_tasks()
            db_changed = False
            tasks_changed = False

            # 1. VIP muddati tugaganlarni tozalash va haydash
            for uid, info in list(db["users"].items()):
                if info.get("premium_until"):
                    try:
                        until_dt = datetime.fromisoformat(info["premium_until"]).astimezone(UZB_TZ)
                    except: continue
                    
                    if now > until_dt:
                        for gid in [NEW_GROUP_ID, GROUP_ID, MADINA_GROUP_ID]:
                            try:
                                await bot.ban_chat_member(chat_id=gid, user_id=int(uid))
                                await bot.unban_chat_member(chat_id=gid, user_id=int(uid))
                            except: pass
                        
                        db["users"][uid]["premium_until"] = None
                        db["users"][uid]["interval_type"] = "oddiy"
                        db_changed = True
                        
                        if uid in tasks:
                            del tasks[uid]
                            tasks_changed = True
                        
                        try:
                            await bot.send_message(
                                chat_id=int(uid), 
                                text="⚠️ <b>VIP obunangiz muddati tugadi!</b>\nTizim sizni guruhlardan va avto-postdan avtomatik ravishda o'chirdi. Obunani yangilash uchun adminga murojaat qiling."
                            )
                        except: pass

            if db_changed: save_db(db)
            if tasks_changed: save_tasks(tasks)

            # 2. Avto Re-Post tizimi
            ydb = load_yuk_db()
            bot_info = await bot.get_me()
            
            for uid, task in list(tasks.items()):
                if not check_premium(int(uid)):
                    if uid in tasks:
                        del tasks[uid]
                        save_tasks(tasks)
                    continue
                
                try:
                    last_sent = datetime.fromisoformat(task["last_sent"]).astimezone(UZB_TZ)
                except: last_sent = now
                
                diff_minutes = (now - last_sent).total_seconds() / 60
                
                if diff_minutes >= task["interval"]:
                    yuk_data = ydb.get(task["yuk_id"])
                    if yuk_data:
                        is_ng = yuk_data.get("is_new_group", False)
                        cap = get_premium_caption(yuk_data["text"][:150] + "...", "🔂 AVTO RE-POST", is_new_group=is_ng)
                        kb = get_group_kb(bot_info.username, task["yuk_id"])
                        chat = NEW_GROUP_ID if is_ng else GROUP_ID
                        tid = task.get("target_topic", None)
                        try:
                            await bot.send_message(chat_id=chat, text=cap, reply_markup=kb, message_thread_id=tid)
                            tasks[uid]["last_sent"] = now.isoformat()
                            save_tasks(tasks)
                        except: pass
                            
        except Exception as ex: logging.error(f"Cron error: {ex}")
        await asyncio.sleep(30)

async def main():
    asyncio.create_task(auto_cron_job())
    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)

if __name__ == '__main__':
    asyncio.run(main())
