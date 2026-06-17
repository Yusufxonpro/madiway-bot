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

logging.basicConfig(level=logging.INFO)

# --- SOZLAMALAR VA ID RAQAMLAR ---
BOT_TOKEN = "8724439262:AAFGNuQQ4IxdqitlcCEtkHLsvyFwSPg_b1c"

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

BAD_WORDS = ["sikt", "qo'taq", "am", "bola", "skaman", "jalap", "qanc", "gandon", "tsex", "akkaunt", "otili", "ortilar", "sokin", "krid", "reklama"]

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

# 3 Tilda yukni to'liq ko'rish tugmasi
def get_group_kb(bot_user, msg_id=None):
    buttons = []
    if msg_id and bot_user: 
        buttons.append([types.InlineKeyboardButton(text="🇺🇿 Ko'rish | 🇷🇺 Смотреть | 🇬🇧 View", url=f"https://t.me/{bot_user}?start={msg_id}")])
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
    
    kutish_madiway_guruh_media = State()  
    kutish_yangi_guruh_media = State()    
    
    giving_premium_username = State()
    giving_premium_days = State()
    
    # User yuk tashlash holatlari
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
            "chosen_group": "International Logistik"
        }
        save_db(db)
    
    if command.args:
        yuk_id = command.args
        ydb = load_yuk_db()
        data = ydb.get(yuk_id)
        
        if not data:
            await message.answer("⚠️ Yuk ma'lumotlari topilmadi.")
            return

        # Sotib olish kerakligi haqida ogohlantirish (VIP bo'lmasa)
        if not check_premium(user_id) and user_id not in [ADMIN_ID, MADIWAY_ADMIN_ID]:
            await message.answer("❌ <b>Siz ushbu yuk ma'lumotlarini ko'rish uchun tarif sotib olishingiz kerak!</b>")
            await message.answer(AUTO_PAYMENT_MESSAGE, reply_markup=get_guruh_tanlash_kb())
            return

        # Agar VIP bo'lsa yoki admin bo'lsa ma'lumotni ko'rsatish
        if isinstance(data, dict) and data.get("type") == "navbatli_media":
            text = data.get("text", "")
            media_list = data.get("media_ids", [])
            is_ng = data.get("is_new_group", False)
            full_info = f"{text}\n\n🖼 <b>Jami rasmlar:</b> {len(media_list)} ta"
            await message.answer(get_premium_caption(full_info, "𝗧𝗢'𝗟𝗜𝗤 𝗠𝗔'𝗟𝗨𝗠𝗢𝗧", is_new_group=is_ng))
            for f_id in media_list:
                try: await message.answer_photo(photo=f_id)
                except: pass
            return

        if yuk_id.startswith("c") or isinstance(data, str):
            txt = data if isinstance(data, str) else data.get("text", "")
            await message.answer(get_premium_caption(txt, "𝗧𝗢'𝗟𝗜𝗤 𝗠𝗔'𝗟𝗨𝗠𝗢𝗧"))
            return

        # Foydalanuvchilar media bilan yuk tashlagan bo'lsa, to'liq ko'rinishi
        text = data.get("text", "")
        phone = data.get("phone", "Ko'rsatilmagan")
        owner = data.get("owner", "Noma'lum")
        is_ng = data.get("is_new_group", False)
        media_type = data.get("media_type", "text")
        file_id = data.get("file_id", None)
        
        full_info = f"{text}\n\n☎️ <b>Aloqa uchun telefon:</b> <code>{phone}</code>\n👤 <b>Yuk egasi:</b> {owner}"
        caption = get_premium_caption(full_info, "𝗧𝗢'𝗟𝗜𝗤 𝗠𝗔'𝗟𝗨𝗠𝗢𝗧", is_new_group=is_ng)
        
        if media_type == "photo" and file_id:
            await message.answer_photo(photo=file_id, caption=caption)
        elif media_type == "video" and file_id:
            await message.answer_video(video=file_id, caption=caption)
        elif media_type == "document" and file_id:
            await message.answer_document(document=file_id, caption=caption)
        else:
            await message.answer(caption)
        return

    if user_id in [ADMIN_ID, MADIWAY_ADMIN_ID]:
        kb = types.InlineKeyboardMarkup(inline_keyboard=[
            [types.InlineKeyboardButton(text="⚙️ Start xabari", callback_data="btn_add_start_msg"), types.InlineKeyboardButton(text="🧹 Guruh Tozalash", callback_data="btn_clean_status")],
            [types.InlineKeyboardButton(text="⭐️ Kanalga yuk (Media/Matn)", callback_data="btn_kanal_tashlash"), types.InlineKeyboardButton(text="✨ Bitta Topicga", callback_data="btn_bitta_topic")],
            [types.InlineKeyboardButton(text="💥 Hammasiga (Topic)", callback_data="btn_hamma_topic"), types.InlineKeyboardButton(text="📊 Statistika", callback_data="btn_stats")],
            [types.InlineKeyboardButton(text="📸 MadiWay (Navbatli Rasmlar)", callback_data="btn_madiway_media")],
            [types.InlineKeyboardButton(text="📸 International (Navbatli Rasmlar)", callback_data="btn_yangi_guruh_media")],
            [types.InlineKeyboardButton(text="🔑 VIP Faollashtirish", callback_data="btn_give_vip")]
        ])
        await message.answer("💻 <b>𝗠𝗔𝗗𝗜𝗪𝗔𝗬 | 𝗔𝗗𝗠𝗜𝗡 𝗣𝗔𝗡Ｅ𝗟</b>", reply_markup=kb)
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

# --- TARIFLAR VA TO'LOV ---
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
    guruh_nomi = user_data.get("tanlangan_guruh", "International Logistik")
    
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
    await callback.message.answer(f"💳 <b>To'lov ma'lumotlari:</b>\nKarta: <code>4916-9903-5000-8311</code>\n\n👇 Pastdagi tugma orqali adminga chekni yuboring!", reply_markup=kb)
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
            db["users"][found_uid] = {"username": "yo'q", "full_name": "Noma'lum", "premium_until": None, "interval_type": "oddiy", "chosen_group": "International Logistik"}
        end_date = datetime.now(UZB_TZ) + timedelta(days=days)
        db["users"][found_uid]["premium_until"] = end_date.isoformat()
        db["users"][found_uid]["interval_type"] = itype
        db["premium_count"] = db.get("premium_count", 0) + 1
        save_db(db)
        
        for gid in [NEW_GROUP_ID, GROUP_ID, MADINA_GROUP_ID]:
            try: await bot.unban_chat_member(chat_id=gid, user_id=int(found_uid), only_if_banned=True)
            except: pass

        formatted = end_date.strftime("%d-%m-%Y %H:%M")
        await callback.message.answer(f"✅ VIP faollashtirildi!")
        
        # FOYDALANUVCHIGA FAQAT INTERNATIONAL LINKINI BERISH (Madiway berilmaydi)
        invite_buttons = [
            [types.InlineKeyboardButton(text="🌍 International Logistik Guruhiga Kirish", url=f"https://t.me/{NEW_GROUP_USER}")],
            [types.InlineKeyboardButton(text="📦 Yuk Tashlashni Boshlash", callback_data="btn_user_send_yuk")]
        ]
        welcome_text = f"🎉 <b>To'lovingiz tasdiqlandi!</b>\n\nSizga yuk tashlash imkoniyati ochildi.\n⏱ VIP muddati: <code>{formatted}</code> gacha."
        try: await bot.send_message(chat_id=int(found_uid), text=welcome_text, reply_markup=types.InlineKeyboardMarkup(inline_keyboard=invite_buttons))
        except: pass
    await state.clear()

# --- REKLAMA FILTRI ---
@dp.message(F.chat.type.in_({"group", "supergroup"}))
async def group_moderator_handler(message: types.Message):
    if message.new_chat_members or message.left_chat_member:
        try: await message.delete()
        except: pass
        return
    user_id = message.from_user.id
    if user_id in [ADMIN_ID, MADIWAY_ADMIN_ID]: return
    if message.chat.id == int(MADINA_GROUP_ID):
        msg_text = message.text or message.caption or ""
        if "http" in msg_text.lower() or "t.me" in msg_text.lower() or "@" in msg_text or any(bad in msg_text.lower() for bad in BAD_WORDS) or message.forward_date:
            try: await message.delete()
            except: pass

# ─── 📦 YANGILANGAN FOYDALANUVCHI (USER) MEDIA BILAN YUK TASHALASH TIZIMI ───
@dp.callback_query(F.data == "btn_user_send_yuk")
async def user_send_yuk_start(callback: types.CallbackQuery, state: FSMContext):
    await callback.answer()
    if not check_premium(callback.from_user.id):
        await callback.message.answer("❌ Sizda VIP obuna faol emas!")
        return
    kb = types.InlineKeyboardMarkup(inline_keyboard=[
        [types.InlineKeyboardButton(text="... MadiWay Asosiy Guruh (Bo'limli)", callback_data="user_target_main")],
        [types.InlineKeyboardButton(text="🌍 International Logistik", callback_data="user_target_new")]
    ])
    await callback.message.answer("🎯 <b>Yukingiz qaysi guruhga joylab borilsin?</b>", reply_markup=kb)
    await state.set_state(MadiWayStates.user_kutish_guruh_tanlash)

@dp.callback_query(MadiWayStates.user_kutish_guruh_tanlash, F.data.startswith("user_target_"))
async def user_guruh_tanladi(callback: types.CallbackQuery, state: FSMContext):
    await callback.answer()
    target = callback.data.split("_")[2]
    await state.update_data(user_target_group=target)
    if target == "main":
        btns = [types.InlineKeyboardButton(text=n, callback_data=f"user_topic_{id}") for n, id in TOPICS.items()]
        kb = types.InlineKeyboardMarkup(inline_keyboard=[btns[i:i+2] for i in range(0, len(btns), 2)])
        await callback.message.answer("📍 <b>MadiWay Guruhidan bo'limni tanlang:</b>", reply_markup=kb)
        await state.set_state(MadiWayStates.user_kutish_topic_tanlash)
    else:
        await callback.message.answer("📥 <b>International Logistik guruhi uchun Yukingizni yuboring:</b>\n<i>(Matn, rasm, video yoki fayl yuborishingiz mumkin)</i>")
        await state.set_state(MadiWayStates.user_kutish_yuk)

@dp.callback_query(MadiWayStates.user_kutish_topic_tanlash, F.data.startswith("user_topic_"))
async def user_topic_tanladi(callback: types.CallbackQuery, state: FSMContext):
    await callback.answer()
    tid = int(callback.data.split("_")[2])
    await state.update_data(user_target_topic=tid)
    await callback.message.answer("📥 <b>Yukingizni yuboring:</b>\n<i>(Matn, rasm, video yoki fayl yuborishingiz mumkin)</i>")
    await state.set_state(MadiWayStates.user_kutish_yuk)

@dp.message(MadiWayStates.user_kutish_yuk)
async def user_get_media_and_text(message: types.Message, state: FSMContext):
    text_check = message.text or message.caption or ""
    user_id = message.from_user.id
    if user_id not in [ADMIN_ID, MADIWAY_ADMIN_ID]:
        if "http" in text_check.lower() or "t.me" in text_check.lower() or "@" in text_check:
            await message.answer("❌ Reklama aniqlandi! Iltimos, havolalarsiz qayta yuboring:")
            return

    media_type = "text"
    file_id = None
    
    if message.photo:
        media_type = "photo"
        file_id = message.photo[-1].file_id
    elif message.video:
        media_type = "video"
        file_id = message.video.file_id
    elif message.document:
        media_type = "document"
        file_id = message.document.file_id

    await state.update_data(
        yuk_text=message.html_text or message.caption or "",
        media_type=media_type,
        file_id=file_id
    )
    await message.answer("☎️ Bog'lanish uchun <b>Telefon Raqamingizni</b> yozing:")
    await state.set_state(MadiWayStates.user_kutish_tel)

@dp.message(MadiWayStates.user_kutish_tel)
async def user_finish_yuk(message: types.Message, state: FSMContext):
    sdata = await state.get_data()
    yuk_text = sdata.get("yuk_text")
    media_type = sdata.get("media_type")
    file_id = sdata.get("file_id")
    t_group = sdata.get("user_target_group")
    t_topic = sdata.get("user_target_topic", None)
    phone = message.text
    user_id = message.from_user.id
    
    db = load_db()
    itype = db["users"].get(str(user_id), {}).get("interval_type", "oddiy")
    is_ng = (t_group == "new")
    m_id = f"u{message.message_id}"
    
    ydb = load_yuk_db()
    ydb[m_id] = {
        "text": yuk_text, 
        "phone": phone, 
        "owner": message.from_user.full_name, 
        "user_id": user_id, 
        "is_new_group": is_ng,
        "media_type": media_type,
        "file_id": file_id
    }
    save_yuk_db(ydb)
    
    tasks = load_tasks()
    tasks[str(user_id)] = {"yuk_id": m_id, "target_group": t_group, "target_topic": t_topic, "interval": 12 if itype == "tezkor" else 300, "last_sent": datetime.now(UZB_TZ).isoformat()}
    save_tasks(tasks)
    
    await message.answer("✅ <b>Yukingiz avto-post tizimiga joylandi.</b>")
    bot_info = await bot.get_me()
    cap = get_premium_caption(yuk_text[:150] + "...", "AVTO YUK", is_new_group=is_ng)
    chat = NEW_GROUP_ID if is_ng else GROUP_ID
    
    # Guruhga birinchi xabarni chiqarish (Matnli yoki Mediali qilib)
    kb = get_group_kb(bot_info.username, m_id)
    await send_all_universal(chat, media_type, file_id, cap, kb, t_topic)
    await state.clear()


# --- ADMIN FUNKSIYALARI ---
@dp.callback_query(F.data.startswith('btn_'))
async def admin_buttons(callback: types.CallbackQuery, state: FSMContext):
    await callback.answer()
    if callback.data == "btn_clean_status":
        await callback.message.answer(f"🧹 Guruh tozalandi.")
    elif callback.data == "btn_add_start_msg":
        await callback.message.answer("⚙️ Yangi start xabari uchun Rasm, Video yoki Matn yuboring:")
        await state.set_state(MadiWayStates.kutish_global_start)
    elif callback.data == "btn_kanal_tashlash":
        await callback.message.answer("📥 Kanal yukini yuboring (Matn, Rasm yoki Video):")
        await state.set_state(MadiWayStates.kutish_kanal_yuk)
    elif callback.data == "btn_hamma_topic":
        await callback.message.answer("💥 Barcha topiklarga yuboriladigan yukni kiriting:")
        await state.set_state(MadiWayStates.kutish_hamma_topic_yuk)
    elif callback.data == "btn_madiway_media":
        await callback.message.answer("📸 <b>MADIWAY</b> (Albom) yuboring:")
        await state.set_state(MadiWayStates.kutish_madiway_guruh_media)
    elif callback.data == "btn_yangi_guruh_media":
        await callback.message.answer("📸 <b>INTERNATIONAL</b> (Albom) yuboring:")
        await state.set_state(MadiWayStates.kutish_yangi_guruh_media)
    elif callback.data == "btn_bitta_topic":
        btns = [types.InlineKeyboardButton(text=n, callback_data=f"select_topic_{id}") for n, id in TOPICS.items()]
        kb = types.InlineKeyboardMarkup(inline_keyboard=[btns[i:i+2] for i in range(0, len(btns), 2)])
        await callback.message.answer("📍 Bo'limni tanlang:", reply_markup=kb)
    elif callback.data == "btn_give_vip":
        await callback.message.answer("🔑 VIP berish uchun Telegram ID yozing:")
        await state.set_state(MadiWayStates.giving_premium_username)
    elif callback.data == "btn_stats":
        db = load_db()
        await callback.message.answer(f"📊 A'zolar: {len(db['users'])}\nVIP: {db.get('premium_count', 0)}")

# --- KANALGA MULTIMEDIA YUKLASH ---
@dp.message(MadiWayStates.kutish_kanal_yuk)
async def chan_yuk(message: types.Message, state: FSMContext):
    txt = message.html_text or message.caption or ""
    m_id = f"c{message.message_id}"
    
    media_type = "text"
    file_id = None
    if message.photo: media_type = "photo"; file_id = message.photo[-1].file_id
    elif message.video: media_type = "video"; file_id = message.video.file_id
    elif message.document: media_type = "document"; file_id = message.document.file_id

    ydb = load_yuk_db()
    ydb[m_id] = {"text": txt, "media_type": media_type, "file_id": file_id}
    save_yuk_db(ydb)
    
    bot_info = await bot.get_me()
    await send_all_universal(CHANNEL_ID, media_type, file_id, get_premium_caption(txt), get_group_kb(bot_info.username, m_id))
    await message.answer("✅ Kanalga muvaffaqiyatli yuklandi.")
    await state.clear()


# ─── 📸 1. MADIWAY NAVBATLI RASMLAR (ADMIN) ───
@dp.message(MadiWayStates.kutish_madiway_guruh_media, F.media_group_id)
async def handle_madiway_media_group(message: types.Message, state: FSMContext):
    mg_id = message.media_group_id
    if mg_id not in MEDIA_GROUPS_CACHE:
        MEDIA_GROUPS_CACHE[mg_id] = []
        asyncio.create_task(process_madiway_media_delayed(mg_id, state, message.message_id))
    MEDIA_GROUPS_CACHE[mg_id].append(message)

async def process_madiway_media_delayed(mg_id: str, state: FSMContext, original_msg_id: int):
    await asyncio.sleep(1.5)
    messages = MEDIA_GROUPS_CACHE.get(mg_id, [])
    if not messages: return
    caption_text = next((msg.caption for msg in messages if msg.caption), "")
    media_ids = [msg.photo[-1].file_id for msg in messages if msg.photo]
    
    m_id = f"m_navbat_{original_msg_id}"
    ydb = load_yuk_db()
    ydb[m_id] = {"type": "navbatli_media", "text": caption_text, "media_ids": media_ids, "current_index": 0, "is_new_group": False}
    save_yuk_db(ydb)
    
    bot_info = await bot.get_me()
    try:
        await bot.send_photo(chat_id=GROUP_ID, photo=media_ids[0], caption=get_premium_caption(caption_text, "𝗠𝗔𝗗𝗜𝗪𝗔𝗬 𝗬𝗨𝗞"), reply_markup=get_group_kb(bot_info.username, m_id), message_thread_id=1)
        tasks = load_tasks()
        tasks[f"admin_{m_id}"] = {"yuk_id": m_id, "target_group": "main", "target_topic": 1, "interval": 12, "last_sent": datetime.now(UZB_TZ).isoformat()}
        save_tasks(tasks)
    except: pass
    if mg_id in MEDIA_GROUPS_CACHE: del MEDIA_GROUPS_CACHE[mg_id]
    await state.clear()

# ─── 📸 2. INTERNATIONAL NAVBATLI RASMLAR (ADMIN) ───
@dp.message(MadiWayStates.kutish_yangi_guruh_media, F.media_group_id)
async def handle_yangi_media_group(message: types.Message, state: FSMContext):
    mg_id = message.media_group_id
    if mg_id not in MEDIA_GROUPS_CACHE:
        MEDIA_GROUPS_CACHE[mg_id] = []
        asyncio.create_task(process_yangi_media_delayed(mg_id, state, message.message_id))
    MEDIA_GROUPS_CACHE[mg_id].append(message)

async def process_yangi_media_delayed(mg_id: str, state: FSMContext, original_msg_id: int):
    await asyncio.sleep(1.5)
    messages = MEDIA_GROUPS_CACHE.get(mg_id, [])
    if not messages: return
    caption_text = next((msg.caption for msg in messages if msg.caption), "")
    media_ids = [msg.photo[-1].file_id for msg in messages if msg.photo]
    
    m_id = f"y_navbat_{original_msg_id}"
    ydb = load_yuk_db()
    ydb[m_id] = {"type": "navbatli_media", "text": caption_text, "media_ids": media_ids, "current_index": 0, "is_new_group": True}
    save_yuk_db(ydb)
    
    bot_info = await bot.get_me()
    try:
        await bot.send_photo(chat_id=NEW_GROUP_ID, photo=media_ids[0], caption=get_premium_caption(caption_text, "𝗜𝗡𝗧𝗘𝗥𝗡𝗔𝗧𝗜𝗢𝗡𝗔𝗟 𝗬𝗨𝗞", is_new_group=True), reply_markup=get_group_kb(bot_info.username, m_id))
        tasks = load_tasks()
        tasks[f"admin_{m_id}"] = {"yuk_id": m_id, "target_group": "new", "target_topic": None, "interval": 12, "last_sent": datetime.now(UZB_TZ).isoformat()}
        save_tasks(tasks)
    except: pass
    if mg_id in MEDIA_GROUPS_CACHE: del MEDIA_GROUPS_CACHE[mg_id]
    await state.clear()


# --- UNIVERSAL ALL-MEDIA SEND UTILITY ---
async def send_all_universal(chat_id, media_type, file_id, caption, kb, t_id=None):
    try:
        if media_type == "photo" and file_id:
            return await bot.send_photo(chat_id, file_id, caption=caption, reply_markup=kb, message_thread_id=t_id)
        elif media_type == "video" and file_id:
            return await bot.send_video(chat_id, file_id, caption=caption, reply_markup=kb, message_thread_id=t_id)
        elif media_type == "document" and file_id:
            return await bot.send_document(chat_id, file_id, caption=caption, reply_markup=kb, message_thread_id=t_id)
        else:
            return await bot.send_message(chat_id, caption, reply_markup=kb, message_thread_id=t_id)
    except Exception as e:
        logging.error(f"Universal send error: {e}")
        return None

# --- TOPIC & OTHER LEGACY FLOWS ---
@dp.message(MadiWayStates.kutish_hamma_topic_yuk)
async def all_yuk(message: types.Message, state: FSMContext):
    txt = message.html_text or message.caption or ""
    m_id = f"h{message.message_id}"
    ydb = load_yuk_db()
    ydb[m_id] = {"text": txt, "phone": "Admin", "owner": "Admin", "is_new_group": False}
    save_yuk_db(ydb)
    bot_info = await bot.get_me()
    for n, tid in TOPICS.items():
        await bot.send_message(chat_id=GROUP_ID, text=get_premium_caption(txt[:150] + "..."), reply_markup=get_group_kb(bot_info.username, m_id), message_thread_id=tid)
        await asyncio.sleep(0.3)
    await message.answer("✅ Mavjud bo'limlarga ketdi.")
    await state.clear()

@dp.callback_query(F.data.startswith('select_topic_'))
async def topic_sel(callback: types.CallbackQuery, state: FSMContext):
    await state.update_data(target_topic_id=callback.data.split('_')[2])
    await callback.message.answer("📥 Yuk matnini kiriting:")
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
    await bot.send_message(chat_id=GROUP_ID, text=get_premium_caption(txt[:150] + "..."), reply_markup=get_group_kb(bot_info.username, m_id), message_thread_id=tid)
    await message.answer("✅ Ketdi.")
    await state.clear()

# --- MANUAL VIP MUDDATI ---
@dp.message(MadiWayStates.giving_premium_username)
async def admin_vip_user(message: types.Message, state: FSMContext):
    await state.update_data(target_user=message.text.replace("@", "").strip())
    kb = types.InlineKeyboardMarkup(inline_keyboard=[
        [types.InlineKeyboardButton(text="🗓 1 Kun (Oddiy)", callback_data="set_user_vip_1_oddiy")],
        [types.InlineKeyboardButton(text="🗓 1 Oy (Oddiy)", callback_data="set_user_vip_30_oddiy")],
        [types.InlineKeyboardButton(text="🚀 1 Kun (⚡️ Tezkor)", callback_data="set_user_vip_1_tezkor")]
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
        await callback.message.answer(f"✅ VIP berildi!")
    await state.clear()

@dp.message(MadiWayStates.kutish_global_start)
async def save_start(message: types.Message, state: FSMContext):
    start_data = {"text": message.html_text or message.caption or "", "type": "text", "file_id": None}
    if message.photo: start_data["type"] = "photo"; start_data["file_id"] = message.photo[-1].file_id
    elif message.video: start_data["type"] = "video"; start_data["file_id"] = message.video.file_id
    with open(START_MSG_FILE, "w", encoding="utf-8") as f: json.dump(start_data, f, ensure_ascii=False, indent=4)
    await message.answer("✅ Start saqlandi.")
    await state.clear()

@dp.message(F.chat.type == "private")
async def auto_reply_handler(message: types.Message):
    if message.from_user.id not in [ADMIN_ID, MADIWAY_ADMIN_ID]:
        await message.answer(AUTO_PAYMENT_MESSAGE, reply_markup=get_guruh_tanlash_kb())


# ─── 🔄 AUTOMATION CRON JOB (RE-POST & EXPIRED USERS) ───
async def auto_cron_job():
    while True:
        try:
            now = datetime.now(UZB_TZ)
            db = load_db()
            tasks = load_tasks()
            ydb = load_yuk_db()
            bot_info = await bot.get_me()
            
            tasks_changed = False
            db_changed = False

            for uid, info in list(db["users"].items()):
                if info.get("premium_until"):
                    try: until_dt = datetime.fromisoformat(info["premium_until"]).astimezone(UZB_TZ)
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
                        if uid in tasks: del tasks[uid]; tasks_changed = True
                        try: await bot.send_message(chat_id=int(uid), text="⚠️ VIP muddati yakunlandi.")
                        except: pass

            if db_changed: save_db(db)

            for task_id, task in list(tasks.items()):
                if not task_id.startswith("admin_") and not check_premium(int(task_id)):
                    if task_id in tasks: del tasks[task_id]; tasks_changed = True
                    continue
                
                try: last_sent = datetime.fromisoformat(task["last_sent"]).astimezone(UZB_TZ)
                except: last_sent = now
                
                diff_minutes = (now - last_sent).total_seconds() / 60
                
                if diff_minutes >= task["interval"]:
                    yuk_data = ydb.get(task["yuk_id"])
                    if not yuk_data: continue
                    
                    is_ng = yuk_data.get("is_new_group", False) if isinstance(yuk_data, dict) else False
                    chat = NEW_GROUP_ID if is_ng else GROUP_ID
                    tid = task.get("target_topic", None)
                    kb = get_group_kb(bot_info.username, task["yuk_id"])

                    # A. ADMIN NAVBATLI RASMLARI
                    if isinstance(yuk_data, dict) and yuk_data.get("type") == "navbatli_media":
                        media_ids = yuk_data.get("media_ids", [])
                        current_idx = yuk_data.get("current_index", 0)
                        if media_ids:
                            try:
                                await bot.send_photo(chat_id=chat, photo=media_ids[current_idx], caption=get_premium_caption(yuk_data["text"], "🔄 RE-POST", is_new_group=is_ng), reply_markup=kb, message_thread_id=tid)
                                ydb[task["yuk_id"]]["current_index"] = (current_idx + 1) % len(media_ids)
                                save_yuk_db(ydb)
                                tasks[task_id]["last_sent"] = now.isoformat()
                                tasks_changed = True
                            except: pass

                    # B. USER MULTIMEDIA AVTO RE-POSTLARI
                    elif isinstance(yuk_data, dict):
                        cap = get_premium_caption(yuk_data["text"][:150] + "...", "🔂 AVTO RE-POST", is_new_group=is_ng)
                        m_type = yuk_data.get("media_type", "text")
                        f_id = yuk_data.get("file_id", None)
                        try:
                            await send_all_universal(chat, m_type, f_id, cap, kb, tid)
                            tasks[task_id]["last_sent"] = now.isoformat()
                            tasks_changed = True
                        except: pass

            if tasks_changed: save_tasks(tasks)
        except Exception as ex: logging.error(f"Cron error: {ex}")
        await asyncio.sleep(30)

async def main():
    asyncio.create_task(auto_cron_job())
    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)

if __name__ == '__main__':
    asyncio.run(main())
