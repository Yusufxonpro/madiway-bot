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

# MP3 Taglar bilan ishlash uchun
from mutagen.mp3 import MP3
from mutagen.id3 import ID3, TPE1, TALB, APIC

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
MUSIC_CHANNEL_ID = "-1004442364818" # Yangi Musiqa kanali ID

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

# Doimiy Musiqa Muqovasi (Shu fayl nomli rasmni bot papkasiga tashlab qo'ying)
MUSIC_COVER_IMAGE = "music_cover.jpg" 

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

def get_group_kb(bot_user, msg_id=None):
    buttons = []
    if msg_id and bot_user: 
        buttons.append([types.InlineKeyboardButton(text="🇺🇿 Ko'rish | 🇷🇺 Смотреть | 🇬🇧 View", url=f"https://t.me/{bot_user}?start={msg_id}")])
    return types.InlineKeyboardMarkup(inline_keyboard=buttons)

def get_guruh_tanlash_kb():
    return types.InlineKeyboardMarkup(inline_keyboard=[
        [types.InlineKeyboardButton(text="🚛 MadiWay Asosiy Guruh", callback_data="buy_guruh_main")],
        [types.InlineKeyboardButton(text="🌍 International Logistik", callback_data="buy_guruh_new")]
    ])

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
    
    # Universal Admin Yuk Tashlash xolatlari
    kutish_adm_madiway_all = State()
    kutish_adm_inter_all = State()
    kutish_music_upload = State() # Musiqa yuklash holati

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

        if not check_premium(user_id) and user_id not in [ADMIN_ID, MADIWAY_ADMIN_ID]:
            await message.answer("❌ <b>Siz ushbu yuk ma'lumotlarini ko'rish uchun tarif sotib olishingiz kerak!</b>")
            await message.answer(AUTO_PAYMENT_MESSAGE, reply_markup=get_guruh_tanlash_kb())
            return

        # Yagona va universal media/albom tekshiruvi
        txt = data.get("text", "")
        is_ng = data.get("is_new_group", False)
        phone = data.get("phone", "Ko'rsatilmagan")
        owner = data.get("owner", "Noma'lum")
        
        # Telefon va Egasi haqida ma'lumot (agar user yuklagan bo'lsa)
        if "phone" in data and data["phone"] != "Admin":
            full_info = f"{txt}\n\n☎️ <b>Aloqa uchun telefon:</b> <code>{phone}</code>\n👤 <b>Yuk egasi:</b> {owner}"
        else:
            full_info = txt

        caption = get_premium_caption(full_info, "𝗧𝗢'𝗟𝗜𝗤 𝗠𝗔'𝗟𝗨𝗠𝗢𝗧", is_new_group=is_ng)
        media_list = data.get("media_list", [])

        if media_list:
            if len(media_list) == 1:
                await send_single_media_direct(message.chat.id, media_list[0]["type"], media_list[0]["file_id"], caption)
            else:
                # Albom holatida to'liq matn bilan birga yuborish
                album_items = []
                for idx, media in enumerate(media_list):
                    if idx == 0:
                        album_items.append(types.InputMediaPhoto(media=media["file_id"], caption=caption) if media["type"] == "photo" else types.InputMediaVideo(media=media["file_id"], caption=caption))
                    else:
                        album_items.append(types.InputMediaPhoto(media=media["file_id"]) if media["type"] == "photo" else types.InputMediaVideo(media=media["file_id"]))
                try: await message.answer_media_group(media=album_items)
                except: pass
        else:
            await message.answer(caption)
        return

    if user_id in [ADMIN_ID, MADIWAY_ADMIN_ID]:
        kb = types.InlineKeyboardMarkup(inline_keyboard=[
            [types.InlineKeyboardButton(text="⚙️ Start xabari", callback_data="btn_add_start_msg"), types.InlineKeyboardButton(text="🧹 Guruh Tozalash", callback_data="btn_clean_status")],
            [types.InlineKeyboardButton(text="⭐️ Kanalga yuk", callback_data="btn_kanal_tashlash"), types.InlineKeyboardButton(text="📊 Statistika", callback_data="btn_stats")],
            [types.InlineKeyboardButton(text="🚛 MadiWayga yuklash", callback_data="btn_adm_madiway"), types.InlineKeyboardButton(text="🌍 Internationalga yuklash", callback_data="btn_adm_inter")],
            [types.InlineKeyboardButton(text="🎵 Musiqa Kanalga (Avto MP3)", callback_data="btn_adm_music")],
            [types.InlineKeyboardButton(text="✨ Bitta Topicga", callback_data="btn_bitta_topic"), types.InlineKeyboardButton(text="💥 Hammasiga (Topic)", callback_data="btn_hamma_topic")],
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

# --- TARIFLAR VA TASDIQLASH (O'zgarishsiz qoldi) ---
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
        
        invite_buttons = [
            [types.InlineKeyboardButton(text="🌍 International Logistik Guruhiga Kirish", url=f"https://t.me/{NEW_GROUP_USER}")],
            [types.InlineKeyboardButton(text="📦 Yuk Tashlashni Boshlash", callback_data="btn_user_send_yuk")]
        ]
        welcome_text = f"🎉 <b>To'lovingiz tasdiqlandi!</b>\n\nSizga yuk tashlash imkoniyati ochildi.\n⏱ VIP muddati: <code>{formatted}</code> gacha."
        try: await bot.send_message(chat_id=int(found_uid), text=welcome_text, reply_markup=types.InlineKeyboardMarkup(inline_keyboard=invite_buttons))
        except: pass
    await state.clear()


# --- 🛠 UNIVERSAL ALBOM VA MULTIMEDIA QABUL QILUVCHI TIZIM ---
async def collect_media_group_data(messages: List[types.Message]) -> dict:
    """Albom yoki bitta mediani yaxlit formatga keltiruvchi yordamchi funksiya"""
    caption_text = next((msg.html_text for msg in messages if msg.html_text), "")
    if not caption_text:
        caption_text = next((msg.caption for msg in messages if msg.caption), "")
        
    media_list = []
    for msg in messages:
        if msg.photo:
            media_list.append({"type": "photo", "file_id": msg.photo[-1].file_id})
        elif msg.video:
            media_list.append({"type": "video", "file_id": msg.video.file_id})
        elif msg.document:
            media_list.append({"type": "document", "file_id": msg.document.file_id})
            
    return {"text": caption_text, "media_list": media_list}

async def send_universal_media_package(chat_id, media_data, caption, kb, t_id=None):
    """Bitta rasm yoki butun boshli albomni guruhga benuqson repost qiluvchi funksiya"""
    media_list = media_data.get("media_list", [])
    if not media_list:
        return await bot.send_message(chat_id, caption, reply_markup=kb, message_thread_id=t_id)
        
    if len(media_list) == 1:
        return await send_single_media_direct(chat_id, media_list[0]["type"], media_list[0]["file_id"], caption, kb, t_id)
        
    # Albom (Media Group) jo'natish
    album_items = []
    for idx, media in enumerate(media_list):
        if idx == 0:
            if media["type"] == "photo":
                album_items.append(types.InputMediaPhoto(media=media["file_id"], caption=caption))
            else:
                album_items.append(types.InputMediaVideo(media=media["file_id"], caption=caption))
        else:
            if media["type"] == "photo":
                album_items.append(types.InputMediaPhoto(media=media["file_id"]))
            else:
                album_items.append(types.InputMediaVideo(media=media["file_id"]))
                
    msgs = await bot.send_media_group(chat_id, media=album_items, message_thread_id=t_id)
    # Inline tugmani albomning eng oxirgi xabariga tirkab qo'yamiz
    if msgs and kb:
        try: await bot.edit_message_reply_markup(chat_id=chat_id, message_id=msgs[-1].message_id, reply_markup=kb)
        except: pass
    return msgs

async def send_single_media_direct(chat_id, m_type, file_id, caption, kb=None, t_id=None):
    if m_type == "photo":
        return await bot.send_photo(chat_id, file_id, caption=caption, reply_markup=kb, message_thread_id=t_id)
    elif m_type == "video":
        return await bot.send_video(chat_id, file_id, caption=caption, reply_markup=kb, message_thread_id=t_id)
    elif m_type == "document":
        return await bot.send_document(chat_id, file_id, caption=caption, reply_markup=kb, message_thread_id=t_id)


# --- ADMIN BOSHQARUV PANEL TUGLARI ---
@dp.callback_query(F.data.startswith('btn_'))
async def admin_buttons(callback: types.CallbackQuery, state: FSMContext):
    await callback.answer()
    if callback.data == "btn_clean_status":
        await callback.message.answer(f"🧹 Guruh tozalandi.")
    elif callback.data == "btn_add_start_msg":
        await callback.message.answer("⚙️ Yangi start xabari uchun Rasm, Video yoki Matn yuboring:")
        await state.set_state(MadiWayStates.kutish_global_start)
    elif callback.data == "btn_kanal_tashlash":
        await callback.message.answer("📥 Kanal yukini yuboring (Xohlasangiz albom yoki bitta fayl):")
        await state.set_state(MadiWayStates.kutish_kanal_yuk)
        
    # ─── 🚛 ADMIN: MADIWAY GURUHIGA YUK (ALBOM/SINGLE/TEXT) Tashlash ───
    elif callback.data == "btn_adm_madiway":
        btns = [types.InlineKeyboardButton(text=n, callback_data=f"adm_mw_topic_{id}") for n, id in TOPICS.items()]
        kb = types.InlineKeyboardMarkup(inline_keyboard=[btns[i:i+2] for i in range(0, len(btns), 2)])
        await callback.message.answer("📍 MadiWay Guruhidan yuk joylanadigan bo'limni tanlang:", reply_markup=kb)
        
    # ─── 🌍 ADMIN: INTERNATIONAL GURUHIGA YUK Tashlash ───
    elif callback.data == "btn_adm_inter":
        await callback.message.answer("📥 <b>International logistik</b> guruhi uchun yukingizni yuboring (Matn, Rasm, Albom yoki Video):")
        await state.set_state(MadiWayStates.kutish_adm_inter_all)

    # ─── 🎵 ADMIN: MUSIQA KANALIGA AVTO MP3 TAYYORLAB JOYLASh ───
    elif callback.data == "btn_adm_music":
        await callback.message.answer("🎵 <b>Musiqa kanaliga yuklash uchun MP3 (Audio) yoki MP4 (Video) fayl yuboring:</b>\n<i>(Bot uni avtomat o'zgartirib taglarini to'g'rilaydi)</i>")
        await state.set_state(MadiWayStates.kutish_music_upload)

    elif callback.data == "btn_hamma_topic":
        await callback.message.answer("💥 Barcha topiklarga yuboriladigan yukni kiriting:")
        await state.set_state(MadiWayStates.kutish_hamma_topic_yuk)
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

# --- ADMIN: MADIWAY BO'LIM TANLANDI ---
@dp.callback_query(F.data.startswith("adm_mw_topic_"))
async def adm_mway_topic_chosen(callback: types.CallbackQuery, state: FSMContext):
    await callback.answer()
    tid = int(callback.data.split("_")[3])
    await state.update_data(adm_mway_target_topic=tid)
    await callback.message.answer("📥 Tanlangan bo'lim uchun yukingizni (Matn, Rasm, Albom yoki Video) yuboring:")
    await state.set_state(MadiWayStates.kutish_adm_madiway_all)


# --- 📸 ALBOM KESH TIZIMI (ADMIN VA USER UCHUN SAMARALI ISHLAYDI) ---
async def generic_media_group_processor(mg_id: str, state: FSMContext, handler_func):
    await asyncio.sleep(1.5)
    messages = MEDIA_GROUPS_CACHE.get(mg_id, [])
    if not messages: return
    media_data = await collect_media_group_data(messages)
    await handler_func(messages[0], media_data, state)
    if mg_id in MEDIA_GROUPS_CACHE: del MEDIA_GROUPS_CACHE[mg_id]


# --- ADMIN: MADIWAY UNIVERSAL POST PROCESSING ---
@dp.message(MadiWayStates.kutish_adm_madiway_all)
async def process_adm_madiway_payload(message: types.Message, state: FSMContext):
    if message.media_group_id:
        mg_id = message.media_group_id
        if mg_id not in MEDIA_GROUPS_CACHE:
            MEDIA_GROUPS_CACHE[mg_id] = []
            asyncio.create_task(generic_media_group_processor(mg_id, state, save_and_send_adm_madiway))
        MEDIA_GROUPS_CACHE[mg_id].append(message)
    else:
        media_data = await collect_media_group_data([message])
        await save_and_send_adm_madiway(message, media_data, state)

async def save_and_send_adm_madiway(msg_obj, media_data, state: FSMContext):
    sdata = await state.get_data()
    tid = sdata.get("adm_mway_target_topic", 1)
    m_id = f"adm_mw_{msg_obj.message_id}"
    
    ydb = load_yuk_db()
    ydb[m_id] = {"text": media_data["text"], "media_list": media_data["media_list"], "is_new_group": False, "phone": "Admin"}
    save_yuk_db(ydb)
    
    bot_info = await bot.get_me()
    cap = get_premium_caption(media_data["text"], "ADMIN YUK", is_new_group=False)
    kb = get_group_kb(bot_info.username, m_id)
    
    await send_universal_media_package(GROUP_ID, media_data, cap, kb, tid)
    await msg_obj.answer("✅ MadiWay guruhiga universal yuk muvaffaqiyatli joylandi!")
    await state.clear()


# --- ADMIN: INTERNATIONAL UNIVERSAL POST PROCESSING ---
@dp.message(MadiWayStates.kutish_adm_inter_all)
async def process_adm_inter_payload(message: types.Message, state: FSMContext):
    if message.media_group_id:
        mg_id = message.media_group_id
        if mg_id not in MEDIA_GROUPS_CACHE:
            MEDIA_GROUPS_CACHE[mg_id] = []
            asyncio.create_task(generic_media_group_processor(mg_id, state, save_and_send_adm_inter))
        MEDIA_GROUPS_CACHE[mg_id].append(message)
    else:
        media_data = await collect_media_group_data([message])
        await save_and_send_adm_inter(message, media_data, state)

async def save_and_send_adm_inter(msg_obj, media_data, state: FSMContext):
    m_id = f"adm_int_{msg_obj.message_id}"
    ydb = load_yuk_db()
    ydb[m_id] = {"text": media_data["text"], "media_list": media_data["media_list"], "is_new_group": True, "phone": "Admin"}
    save_yuk_db(ydb)
    
    bot_info = await bot.get_me()
    cap = get_premium_caption(media_data["text"], "ADMIN YUK", is_new_group=True)
    kb = get_group_kb(bot_info.username, m_id)
    
    await send_universal_media_package(NEW_GROUP_ID, media_data, cap, kb)
    await msg_obj.answer("✅ International guruhiga universal yuk muvaffaqiyatli joylandi!")
    await state.clear()


# ─── 🎵 3. MUSIQA FORMATLARINI AVTO-O'ZGARTIRISH VA KANALGA YUBORISH ───
@dp.message(MadiWayStates.kutish_music_upload, F.audio | F.video | F.document)
async def process_incoming_music_file(message: types.Message, state: FSMContext):
    status_msg = await message.answer("🔄 <code>Musiqa fayli qabul qilindi. Qayta ishlanmoqda, iltimos kuting...</code>")
    
    file_id = None
    input_filename = "downloaded_track"
    is_video = False
    
    if message.audio:
        file_id = message.audio.file_id
        input_filename += ".mp3"
    elif message.video:
        file_id = message.video.file_id
        input_filename += ".mp4"
        is_video = True
    elif message.document and message.document.mime_type:
        if "audio" in message.document.mime_type:
            file_id = message.document.file_id
            input_filename += ".mp3"
        elif "video" in message.document.mime_type:
            file_id = message.document.file_id
            input_filename += ".mp4"
            is_video = True

    if not file_id:
        await status_msg.edit("❌ Noto'g'ri fayl turi! Iltimos faqat Audio yoki Video yuboring.")
        return

    try:
        # Faylni yuklab olish
        file_info = await bot.get_file(file_id)
        await bot.download_file(file_info.file_path, input_filename)
        
        output_mp3 = "final_track.mp3"
        
        # Agar video bo'lsa FFmpeg yordamida audio (MP3)ga o'giramiz
        if is_video:
            await status_msg.edit("🎬 MP4 format aniqlandi. Tizim uni MP3 formatga o'giryapti...")
            proc = await asyncio.create_subprocess_exec(
                'ffmpeg', '-y', '-i', input_filename, '-vn', '-ar', '44100', '-ac', '2', '-b:a', '192k', output_mp3,
                stdout=asyncio.subprocess.DEVNULL, stderr=asyncio.subprocess.DEVNULL
            )
            await proc.communicate()
        else:
            if os.path.exists(output_mp3): os.remove(output_mp3)
            os.rename(input_filename, output_mp3)
            
        await status_msg.edit("✍️ Musiqa ichki taglari (Artist: T.me/Yusufxonpro_Zxs, Album: Zxs) yozilmoqda...")
        
        # ID3 Meta Taglarni o'zgartirish
        try:
            audio_tags = MP3(output_mp3, ID3=ID3)
            try: audio_tags.add_tags()
            except: pass
            
            audio_tags.tags.add(TPE1(encoding=3, text='T.me/Yusufxonpro_Zxs')) # Artist tag
            audio_tags.tags.add(TALB(encoding=3, text='Zxs'))                # Album tag
            
            # Agar muqova rasmi mavjud bo'lsa ichiga joylaymiz
            if os.path.exists(MUSIC_COVER_IMAGE):
                with open(MUSIC_COVER_IMAGE, 'rb') as img_f:
                    audio_tags.tags.add(APIC(encoding=3, mime='image/jpeg', type=3, desc=u'Cover', data=img_f.read()))
            audio_tags.save()
        except Exception as e:
            logging.error(f"Tags write error: {e}")

        await status_msg.edit("🚀 Musiqa tayyor! Kanalga yuklanmoqda...")
        
        caption_text = message.html_text or message.caption or "🎵 Premium yangi tarona!"
        music_file = types.FSInputFile(output_mp3, filename="Musiqa_Zxs.mp3")
        
        # 1-QADAM: Birinchi audio/mp3 faylni o'zini yuboramiz
        sent_audio = await bot.send_audio(chat_id=MUSIC_CHANNEL_ID, audio=music_file, performer="T.me/Yusufxonpro_Zxs", title="Zxs Music")
        
        # 2-QADAM: Ketidan unga bog'liq matn (Premium)ni alohida xabar ko'rinishida yuboramiz
        m_id = f"mus_{message.message_id}"
        ydb = load_yuk_db()
        ydb[m_id] = {"text": caption_text, "media_list": [{"type": "audio", "file_id": sent_audio.audio.file_id}], "is_new_group": False, "phone": "Admin"}
        save_yuk_db(ydb)
        
        bot_info = await bot.get_me()
        final_caption = f"🎵 <b>T.me/Yusufxonpro_Zxs Tarbdim Etadi!</b>\n───────────────────────\n{caption_text}"
        await bot.send_message(chat_id=MUSIC_CHANNEL_ID, text=final_caption, reply_markup=get_group_kb(bot_info.username, m_id))
        
        await status_msg.edit("✅ Musiqa muvaffaqiyatli o'zgartirildi va t.me/Yusufxonpro_Zxs kanaliga yuklandi!")
        
        # Tozalash
        for f in [input_filename, output_mp3]:
            if os.path.exists(f): os.remove(f)
            
    except Exception as ex:
        await status_msg.edit(f"❌ Musiqani qayta ishlashda xatolik yuz berdi: {ex}")
    await state.clear()


# --- USER YUK TASHALASH TIZIMI (ALBOM VA BILAN TAYYOR HOLATDA) ---
@dp.callback_query(F.data == "btn_user_send_yuk")
async def user_send_yuk_start(callback: types.CallbackQuery, state: FSMContext):
    await callback.answer()
    if not check_premium(callback.from_user.id):
        await callback.message.answer("❌ Sizda VIP obuna faol emas!")
        return
    kb = types.InlineKeyboardMarkup(inline_keyboard=[
        [types.InlineKeyboardButton(text="MadiWay Asosiy Guruh (Bo'limli)", callback_data="user_target_main")],
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
        await callback.message.answer("📥 <b>International Logistik guruhi uchun Yukingizni yuboring:</b>\n<i>(Matn, rasm, video yoki yaxlit albom yuborishingiz mumkin)</i>")
        await state.set_state(MadiWayStates.user_kutish_yuk)

@dp.callback_query(MadiWayStates.user_kutish_topic_tanlash, F.data.startswith("user_topic_"))
async def user_topic_tanladi(callback: types.CallbackQuery, state: FSMContext):
    await callback.answer()
    tid = int(callback.data.split("_")[2])
    await state.update_data(user_target_topic=tid)
    await callback.message.answer("📥 <b>Yukingizni yuboring:</b>\n<i>(Matn, rasm, video yoki yaxlit albom yuborishingiz mumkin)</i>")
    await state.set_state(MadiWayStates.user_kutish_yuk)

@dp.message(MadiWayStates.user_kutish_yuk)
async def user_get_payload(message: types.Message, state: FSMContext):
    text_check = message.text or message.caption or ""
    user_id = message.from_user.id
    if user_id not in [ADMIN_ID, MADIWAY_ADMIN_ID]:
        if "http" in text_check.lower() or "t.me" in text_check.lower() or "@" in text_check:
            await message.answer("❌ Reklama aniqlandi! Iltimos, havolalarsiz qayta yuboring:")
            return

    if message.media_group_id:
        mg_id = message.media_group_id
        if mg_id not in MEDIA_GROUPS_CACHE:
            MEDIA_GROUPS_CACHE[mg_id] = []
            asyncio.create_task(generic_media_group_processor(mg_id, state, user_ask_phone_stage))
        MEDIA_GROUPS_CACHE[mg_id].append(message)
    else:
        media_data = await collect_media_group_data([message])
        await user_ask_phone_stage(message, media_data, state)

async def user_ask_phone_stage(msg_obj, media_data, state: FSMContext):
    await state.update_data(yuk_text=media_data["text"], media_list=media_data["media_list"])
    await msg_obj.answer("☎️ Bog'lanish uchun <b>Telefon Raqamingizni</b> yozing:")
    await state.set_state(MadiWayStates.user_kutish_tel)

@dp.message(MadiWayStates.user_kutish_tel)
async def user_finish_yuk(message: types.Message, state: FSMContext):
    sdata = await state.get_data()
    yuk_text = sdata.get("yuk_text")
    media_list = sdata.get("media_list", [])
    t_group = sdata.get("user_target_group")
    t_topic = sdata.get("user_target_topic", None)
    phone = message.text
    user_id = message.from_user.id
    
    db = load_db()
    itype = db["users"].get(str(user_id), {}).get("interval_type", "oddiy")
    is_ng = (t_group == "new")
    m_id = f"u{message.message_id}"
    
    ydb = load_yuk_db()
    ydb[m_id] = {"text": yuk_text, "phone": phone, "owner": message.from_user.full_name, "user_id": user_id, "is_new_group": is_ng, "media_list": media_list}
    save_yuk_db(ydb)
    
    tasks = load_tasks()
    tasks[str(user_id)] = {"yuk_id": m_id, "target_group": t_group, "target_topic": t_topic, "interval": 12 if itype == "tezkor" else 300, "last_sent": datetime.now(UZB_TZ).isoformat()}
    save_tasks(tasks)
    
    await message.answer("✅ <b>Yukingiz avto-post tizimiga muvaffaqiyatli joylandi.</b>")
    bot_info = await bot.get_me()
    
    full_info = f"{yuk_text}\n\n☎️ <b>Aloqa uchun:</b> {phone}"
    cap = get_premium_caption(full_info[:150] + "...", "AVTO YUK", is_new_group=is_ng)
    chat = NEW_GROUP_ID if is_ng else GROUP_ID
    
    kb = get_group_kb(bot_info.username, m_id)
    await send_universal_media_package(chat, {"media_list": media_list}, cap, kb, t_topic)
    await state.clear()


# --- KANALGA ODDY YUK TASHALASH ---
@dp.message(MadiWayStates.kutish_kanal_yuk)
async def chan_yuk(message: types.Message, state: FSMContext):
    if message.media_group_id:
        mg_id = message.media_group_id
        if mg_id not in MEDIA_GROUPS_CACHE:
            MEDIA_GROUPS_CACHE[mg_id] = []
            asyncio.create_task(generic_media_group_processor(mg_id, state, send_channel_media_package))
        MEDIA_GROUPS_CACHE[mg_id].append(message)
    else:
        media_data = await collect_media_group_data([message])
        await send_channel_media_package(message, media_data, state)

async def send_channel_media_package(msg_obj, media_data, state: FSMContext):
    m_id = f"c{msg_obj.message_id}"
    ydb = load_yuk_db()
    ydb[m_id] = {"text": media_data["text"], "media_list": media_data["media_list"]}
    save_yuk_db(ydb)
    
    bot_info = await bot.get_me()
    await send_universal_media_package(CHANNEL_ID, media_data, get_premium_caption(media_data["text"]), get_group_kb(bot_info.username, m_id))
    await msg_obj.answer("✅ Kanalga muvaffaqiyatli yuklandi.")
    await state.clear()


# --- ESKI QO'SHIMChA AMALLAR (O'zgarishsiz) ---
@dp.message(MadiWayStates.kutish_hamma_topic_yuk)
async def all_yuk(message: types.Message, state: FSMContext):
    txt = message.html_text or message.caption or ""
    m_id = f"h{message.message_id}"
    ydb = load_yuk_db()
    ydb[m_id] = {"text": txt, "media_list": [], "phone": "Admin", "owner": "Admin", "is_new_group": False}
    save_yuk_db(ydb)
    bot_info = await bot.get_me()
    for n, tid in TOPICS.items():
        await bot.send_message(chat_id=GROUP_ID, text=get_premium_caption(txt[:150] + "..."), reply_markup=get_group_kb(bot_info.username, m_id), message_thread_id=tid)
        await asyncio.sleep(0.3)
    await message.answer("✅ Hamma topikga yuborildi.")
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
    ydb[m_id] = {"text": txt, "media_list": [], "phone": "Admin", "owner": "Admin", "is_new_group": False}
    save_yuk_db(ydb)
    bot_info = await bot.get_me()
    await bot.send_message(chat_id=GROUP_ID, text=get_premium_caption(txt[:150] + "..."), reply_markup=get_group_kb(bot_info.username, m_id), message_thread_id=tid)
    await message.answer("✅ Ketdi.")
    await state.clear()

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


# --- AUTOMATION CRON JOB (AVTO-REPOST TIZIMI UNIVERSAL ALBOM BILAN) ---
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
                    
                    is_ng = yuk_data.get("is_new_group", False)
                    chat = NEW_GROUP_ID if is_ng else GROUP_ID
                    tid = task.get("target_topic", None)
                    kb = get_group_kb(bot_info.username, task["yuk_id"])
                    
                    # Doimiy sarlavha va premium qayta joylash
                    owner_prefix = f"\n\n☎️ <b>Aloqa:</b> {yuk_data['phone']}" if yuk_data.get('phone') != "Admin" else ""
                    cap = get_premium_caption(yuk_data["text"][:150] + owner_prefix + "...", "🔂 AVTO RE-POST", is_new_group=is_ng)
                    
                    try:
                        await send_universal_media_package(chat, yuk_data, cap, kb, tid)
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
