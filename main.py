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

# --- TO'LIQ SOZLAMALAR VA ID RAQAMLAR ---
BOT_TOKEN = "8724439262:AAFGNuQQ4IxdqitlcCEtkHLsvyFwSPg_b1c"

CHANNEL_USER = "MADIWAYy"         
GROUP_USER = "MADIWAYy_Gr"        
NEW_GROUP_USER = "International_logistik"  

CHANNEL_ID = "-1003996104316"      
GROUP_ID = "-1003963001370"        # MadiWay Asosiy Guruh
NEW_GROUP_ID = "-1004370807037"    # International Guruh
MADINA_GROUP_ID = "-1001456164408"  # Madina Kilo Kiyimlar Guruh
MUSIC_CHANNEL_ID = "-1004442364818" # Musiqa kanali

ADMIN_ID = 6977836294         
MADIWAY_ADMIN_ID = 8112179116  
OWNER_USERNAME = "yusufxonpro1"    

bot = Bot(token=BOT_TOKEN, default=DefaultBotProperties(parse_mode="HTML"))
dp = Dispatcher(storage=MemoryStorage())

# Ma'lumotlar bazasi fayllari
USERS_DB_FILE = "users_database.json"
YUK_DB_FILE = "yuklar_database.json"
AUTO_TASKS_FILE = "auto_tasks_database.json"

UZB_TZ = timezone(timedelta(hours=5))
MEDIA_GROUPS_CACHE: Dict[str, List[types.Message]] = {}

BAD_WORDS = ["sikt", "qo'taq", "am", "bola", "skaman", "jalap", "qanc", "gandon", "tsex", "akkaunt", "otili", "ortilar", "sokin", "krid", "reklama"]

AUTO_PAYMENT_MESSAGE = (
    "👋 <b>MadiWay tizimida YUK TASHALASH va VIP guruh tariflari:</b>\n\n"
    "💳 <b>UzCard / VISA Card:</b> <code>4916-9903-5000-8311</code>\n"
    "👤 <b>Ega:</b> MadiWay Admin\n\n"
    "💵 <b>Tariflar (Har 5-9 soatda qayta tashlanadi):</b>\n"
    "🔹 1 kunlik — 15 000 so'm\n"
    "🔹 2 kunlik — 20 000 so'm\n"
    "🔹 3 kunlik — 30 000 so'm\n"
    "🔹 1 oylik — 50 000 so'm\n\n"
    "⚡️ <b>TEZKOR TARIF (Har 12 minutda avto-post):</b>\n"
    "🚀 1 kunlik — 30 000 so'm\n\n"
    "⚠️ To'lovdan so'ng chekni adminga yuboring!\n"
    "📞 <b>Aloqa:</b> +998 88 325 80 07"
)

TOPICS = {
    "🌍 Europa": 2, "🇩🇪 Germaniya": 14, "🇷🇺 Rossiya": 4, "🇰🇬 Qirg'iziston": 6,
    "🇰🇿 Kazakistan": 8, "🇮🇷 Eron": 10, "🇹🇯 Tojikston": 12, "🇧🇾 Belarusiya": 16,
    "🇬🇪 Gruziya": 18, "📣 Elon berish": 1
}

# --- YORDAMCHI FUNKSIYALAR ---
def is_contains_reklama(text: str) -> bool:
    if not text: return False
    text_lower = text.lower()
    if any(x in text_lower for x in ["http", "t.me", "@", ".uz", ".ru", "t.me/"]): return True
    return any(bad in text_lower for bad in BAD_WORDS)

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

def check_premium(user_id):
    db = load_db()
    uid = str(user_id)
    if uid in db["users"] and db["users"][uid]["premium_until"]:
        try:
            until_dt = datetime.fromisoformat(db["users"][uid]["premium_until"]).astimezone(UZB_TZ)
            if datetime.now(UZB_TZ) < until_dt: return True
        except: pass
    return False

def get_premium_caption(main_text, status_label="𝗬𝗨𝗞 𝗘𝗟𝗢𝗡Ｉ", is_new_group=False):
    now = datetime.now(UZB_TZ)
    sana_soat = now.strftime("📅 %Y-%m-%d  🕒 %I:%M %p") 
    brand = "𝗜𝗡𝗧𝗘𝗥𝗡Ａ𝗧Ｉ𝗢𝗡Ａ𝗟 𝗟𝗢𝗚Ｉ𝗦𝗧ＩＣ" if is_new_group else "𝗠𝗔𝗗𝗜𝗪𝗔𝗬"
    return f"⭐️ <b>{brand} | {status_label}</b> ⭐️\n───────────────────────\n{main_text}\n───────────────────────\n⏳ Vaqt: {sana_soat}\n📢 Kanal: t.me/{CHANNEL_USER}"

def get_group_kb(bot_user, msg_id=None):
    buttons = []
    if msg_id and bot_user: 
        buttons.append([types.InlineKeyboardButton(text="🇺🇿 Ko'rish | 🇷🇺 Смотреть", url=f"https://t.me/{bot_user}?start={msg_id}")])
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
    kutish_kanal_yuk = State()
    adm_mway_target_topic = State()
    kutish_adm_madiway_all = State()
    kutish_adm_inter_all = State()
    
    kutish_music_audio = State()
    kutish_music_desc = State()

    giving_premium_username = State()
    giving_premium_days = State()
    
    user_kutish_guruh_tanlash = State()
    user_kutish_topic_tanlash = State()
    user_kutish_yuk = State()       
    user_kutish_tel = State()       
    admin_quick_vip_days = State()

# --- START BUYRUG'I VA PANELI ---
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
            await message.answer("❌ <b>Siz ushbu yuk ma'lumotlarini ko'rish uchun VIP tarif sotib olishingiz kerak!</b>")
            await message.answer(AUTO_PAYMENT_MESSAGE, reply_markup=get_guruh_tanlash_kb())
            return

        txt = data.get("text", "")
        is_ng = data.get("is_new_group", False)
        phone = data.get("phone", "Ko'rsatilmagan")
        owner = data.get("owner", "Noma'lum")
        
        full_info = f"{txt}\n\n☎️ <b>Aloqa uchun telefon:</b> <code>{phone}</code>\n👤 <b>Yuk egasi:</b> {owner}" if data.get("phone") != "Admin" else txt
        caption = get_premium_caption(full_info, "𝗧𝗢'𝗟𝗜𝗤 𝗠𝗔'𝗟𝗨𝗠𝗢𝗧", is_new_group=is_ng)
        media_list = data.get("media_list", [])

        if media_list:
            if len(media_list) == 1:
                await send_single_media_direct(message.chat.id, media_list[0]["type"], media_list[0]["file_id"], caption)
            else:
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
            [types.InlineKeyboardButton(text="🚛 MADIWAY guruhiga yuklash", callback_data="btn_adm_madiway")],
            [types.InlineKeyboardButton(text="🌍 INTERNATIONAL guruhiga yuklash", callback_data="btn_adm_inter")],
            [types.InlineKeyboardButton(text="📸 KANALGA rasm/fayl yuklash", callback_data="btn_kanal_tashlash")],
            [types.InlineKeyboardButton(text="🎵 Musiqa Kanalga (Instant 1-Sec)", callback_data="btn_adm_music")],
            [
                types.InlineKeyboardButton(text="MadiWay Gruppa", url=f"https://t.me/{GROUP_USER}"),
                types.InlineKeyboardButton(text="MadiWay Kanal", url=f"https://t.me/{CHANNEL_USER}")
            ],
            [types.InlineKeyboardButton(text="🔑 VIP Berish", callback_data="btn_give_vip"), types.InlineKeyboardButton(text="📊 Statistika", callback_data="btn_stats")]
        ])
        await message.answer("💻 <b>𝗠𝗔𝗗𝗜𝗪𝗔𝗬 | 𝗔𝗗𝗠Ｉ𝗡 𝗣𝗔𝗡Ｅ𝗟</b>\n\nBarcha 17 ta tugma va tezkor tizim integratsiya qilindi:", reply_markup=kb)
    else:
        kb = types.InlineKeyboardMarkup(inline_keyboard=[
            [types.InlineKeyboardButton(text="💰 Tariflar va VIP sotib olish", callback_data="btn_show_tariffs")],
            [types.InlineKeyboardButton(text="📦 Yuk Tashlash (Avto-Post)", callback_data="btn_user_send_yuk")],
            [
                types.InlineKeyboardButton(text="MadiWay Guruh", url=f"https://t.me/{GROUP_USER}"),
                types.InlineKeyboardButton(text="International Guruh", url=f"https://t.me/{NEW_GROUP_USER}")
            ]
        ])
        await message.answer(text="🏔 <b>MadiWay logistika avtomatizatsiya botiga xush kelibsiz!</b>\n\nQuyidagi menyudan foydalaning:", reply_markup=kb)

# --- REKLAMA FILTRI ---
@dp.message(F.chat.type.in_({"group", "supergroup"}))
async def group_moderator_handler(message: types.Message):
    if message.new_chat_members or message.left_chat_member:
        try: await message.delete()
        except: pass
        return
    user_id = message.from_user.id
    if user_id in [ADMIN_ID, MADIWAY_ADMIN_ID]: return
    msg_text = message.text or message.caption or ""
    if message.chat.id in [int(GROUP_ID), int(NEW_GROUP_ID), int(MADINA_GROUP_ID)]:
        if is_contains_reklama(msg_text) or message.forward_date:
            try: await message.delete()
            except: pass

# --- TARIFLAR CALLBACKS ---
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
        
    alert = f"🔔 <b>YANGI TO'LOV SO'ROVI:</b>\n\n👤 Foydalanuvchi: {callback.from_user.full_name}\n🆔 ID: <code>{callback.from_user.id}</code>\n📦 Guruh: {guruh_nomi}\n🛒 Tarif: {parts[1]} {parts[2]}"
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
        [types.InlineKeyboardButton(text="🗓 1 Kun (Oddiy)", callback_data="qset_1_oddiy")],
        [types.InlineKeyboardButton(text="🗓 30 Kun (Oddiy)", callback_data="qset_30_oddiy")],
        [types.InlineKeyboardButton(text="🚀 1 Kun (⚡️ Tezkor - 12 min)", callback_data="qset_1_tezkor")]
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
        await callback.message.answer(f"✅ VIP muvaffaqiyatli faollashtirildi!")
        
        invite_buttons = [
            [types.InlineKeyboardButton(text="🌍 International Logistik Guruhiga Kirish", url=f"https://t.me/{NEW_GROUP_USER}")],
            [types.InlineKeyboardButton(text="📦 Yuk Tashlashni Boshlash", callback_data="btn_user_send_yuk")]
        ]
        try: await bot.send_message(chat_id=int(found_uid), text=f"🎉 <b>To'lovingiz tasdiqlandi!</b>\n\n⏱ VIP muddati: <code>{formatted}</code> gacha.", reply_markup=types.InlineKeyboardMarkup(inline_keyboard=invite_buttons))
        except: pass
    await state.clear()

# --- ALBOM/MEDIA BILAN ISHLASH TIZIMI ---
async def collect_media_group_data(messages: List[types.Message]) -> dict:
    caption_text = next((msg.html_text for msg in messages if msg.html_text), "")
    if not caption_text:
        caption_text = next((msg.caption for msg in messages if msg.caption), "")
    media_list = []
    for msg in messages:
        if msg.photo: media_list.append({"type": "photo", "file_id": msg.photo[-1].file_id})
        elif msg.video: media_list.append({"type": "video", "file_id": msg.video.file_id})
        elif msg.document: media_list.append({"type": "document", "file_id": msg.document.file_id})
    return {"text": caption_text, "media_list": media_list}

async def send_universal_media_package(chat_id, media_data, caption, kb, t_id=None):
    media_list = media_data.get("media_list", [])
    if not media_list:
        return await bot.send_message(chat_id, caption, reply_markup=kb, message_thread_id=t_id)
    if len(media_list) == 1:
        return await send_single_media_direct(chat_id, media_list[0]["type"], media_list[0]["file_id"], caption, kb, t_id)
        
    album_items = []
    for idx, media in enumerate(media_list):
        if idx == 0:
            album_items.append(types.InputMediaPhoto(media=media["file_id"], caption=caption) if media["type"] == "photo" else types.InputMediaVideo(media=media["file_id"], caption=caption))
        else:
            album_items.append(types.InputMediaPhoto(media=media["file_id"]) if media["type"] == "photo" else types.InputMediaVideo(media=media["file_id"]))
                
    msgs = await bot.send_media_group(chat_id, media=album_items, message_thread_id=t_id)
    if msgs and kb:
        try: await bot.edit_message_reply_markup(chat_id=chat_id, message_id=msgs[-1].message_id, reply_markup=kb)
        except: pass
    return msgs

async def send_single_media_direct(chat_id, m_type, file_id, caption, kb=None, t_id=None):
    if m_type == "photo": return await bot.send_photo(chat_id, file_id, caption=caption, reply_markup=kb, message_thread_id=t_id)
    elif m_type == "video": return await bot.send_video(chat_id, file_id, caption=caption, reply_markup=kb, message_thread_id=t_id)
    elif m_type == "document": return await bot.send_document(chat_id, file_id, caption=caption, reply_markup=kb, message_thread_id=t_id)

# --- ADMIN PANEL CALLBACKS ---
@dp.callback_query(F.data.startswith('btn_'))
async def admin_buttons(callback: types.CallbackQuery, state: FSMContext):
    await callback.answer()
    if callback.data == "btn_kanal_tashlash":
        await callback.message.answer("📥 <b>KANALGA</b> yuklash bo'limi! Rasm, Video yoki Albom yuboring:")
        await state.set_state(MadiWayStates.kutish_kanal_yuk)
        
    elif callback.data == "btn_adm_madiway":
        btns = [types.InlineKeyboardButton(text=n, callback_data=f"adm_mw_topic_{id}") for n, id in TOPICS.items()]
        kb = types.InlineKeyboardMarkup(inline_keyboard=[btns[i:i+2] for i in range(0, len(btns), 2)])
        await callback.message.answer("📍 <b>MADIWAY</b> guruhidan yuk joylanadigan bo'limni tanlang:", reply_markup=kb)
        
    elif callback.data == "btn_adm_inter":
        await callback.message.answer("📥 <b>INTERNATIONAL LOGISTIK</b> guruhi uchun yukingizni yuboring (Matn, Rasm, Video, Albom):")
        await state.set_state(MadiWayStates.kutish_adm_inter_all)

    elif callback.data == "btn_adm_music":
        await callback.message.answer("🎵 Musiqa kanaliga joylash uchun <b>MP3 (Audio) yoki MP4 (Video)</b> fayl yuboring:")
        await state.set_state(MadiWayStates.kutish_music_audio)

    elif callback.data == "btn_give_vip":
        await callback.message.answer("🔑 VIP berish uchun Telegram ID yoki Username yozing:")
        await state.set_state(MadiWayStates.giving_premium_username)
        
    elif callback.data == "btn_stats":
        db = load_db()
        await callback.message.answer(f"📊 A'zolar: {len(db['users'])}\nVIP obunachilar: {db.get('premium_count', 0)}")

@dp.callback_query(F.data.startswith("adm_mw_topic_"))
async def admin_madiway_topic_select(callback: types.CallbackQuery, state: FSMContext):
    await callback.answer()
    tid = int(callback.data.split("_")[3])
    await state.update_data(adm_mway_target_topic=tid)
    await callback.message.answer("📥 Endi MadiWay guruhi uchun yuk materialini yuboring:")
    await state.set_state(MadiWayStates.kutish_adm_madiway_all)

async def generic_media_group_processor(mg_id: str, state: FSMContext, handler_func):
    await asyncio.sleep(1.5)
    messages = MEDIA_GROUPS_CACHE.get(mg_id, [])
    if not messages: return
    media_data = await collect_media_group_data(messages)
    await handler_func(messages[0], media_data, state)
    if mg_id in MEDIA_GROUPS_CACHE: del MEDIA_GROUPS_CACHE[mg_id]

# --- POSTLARNI SAQLASH VA YUKLASH ---
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
    await send_universal_media_package(GROUP_ID, media_data, cap, get_group_kb(bot_info.username, m_id), tid)
    await msg_obj.answer("✅ MadiWay guruhiga yuklandi!")
    await state.clear()

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
    await send_universal_media_package(NEW_GROUP_ID, media_data, cap, get_group_kb(bot_info.username, m_id))
    await msg_obj.answer("✅ International guruhiga yuklandi!")
    await state.clear()

# --- 🎵 ULTRA TEZKOR MUSIQA TIZIMI (1 SONIYADA KUTISHSIZ) ---
@dp.message(MadiWayStates.kutish_music_audio, F.audio | F.video)
async def process_incoming_music_file(message: types.Message, state: FSMContext):
    if message.audio:
        await state.update_data(audio_file_id=message.audio.file_id, is_video_src=False)
    else:
        await state.update_data(audio_file_id=message.video.file_id, is_video_src=True)
    await message.answer("📝 Endi musiqa uchun <b>Tavsif (Description)</b> matnini yuboring:")
    await state.set_state(MadiWayStates.kutish_music_desc)

@dp.message(MadiWayStates.kutish_music_desc)
async def process_music_description(message: types.Message, state: FSMContext):
    desc_text = message.html_text or message.text or ""
    sdata = await state.get_data()
    file_id = sdata.get("audio_file_id")
    is_video = sdata.get("is_video_src", False)
    
    status_msg = await message.answer("⚡️ <code>Musiqa 1 soniyada kanalga joylanmoqda...</code>")
    
    try:
        bot_info = await bot.get_me()
        final_caption = (
            f"🎵 <b>T.me/Yusufxonpro_Zxs Taqdim Etadi!</b>\n"
            f"🎙 <i>Watermark: Ovozli belgi tizimda faol!</i>\n"
            f"───────────────────────\n"
            f"{desc_text}"
        )
        
        m_id = f"mus_{message.message_id}"
        ydb = load_yuk_db()
        
        if is_video:
            sent_media = await bot.send_video(
                chat_id=MUSIC_CHANNEL_ID, 
                video=file_id, 
                caption=final_caption,
                reply_markup=get_group_kb(bot_info.username, m_id)
            )
            media_list = [{"type": "video", "file_id": sent_media.video.file_id}]
        else:
            sent_media = await bot.send_audio(
                chat_id=MUSIC_CHANNEL_ID, 
                audio=file_id, 
                caption=final_caption,
                performer="YusufxonPro", 
                title="Zxs Music",
                reply_markup=get_group_kb(bot_info.username, m_id)
            )
            media_list = [{"type": "audio", "file_id": sent_media.audio.file_id}]

        ydb[m_id] = {
            "text": desc_text, 
            "media_list": media_list, 
            "is_new_group": False, 
            "phone": "Admin"
        }
        save_yuk_db(ydb)
        
        await status_msg.edit("🚀 <b>Musiqa kutishlarsiz, 1 soniyada muvaffaqiyatli kanalga joylandi!</b>")
        
    except Exception as ex:
        await status_msg.edit(f"❌ Tezkor yuklashda xato: {ex}")
        
    await state.clear()

# --- USER YUK TASHALASH PROCESSI ---
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
        await callback.message.answer("📥 <b>International Logistik guruhi uchun Yukingizni yuboring:</b>")
        await state.set_state(MadiWayStates.user_kutish_yuk)

@dp.callback_query(MadiWayStates.user_kutish_topic_tanlash, F.data.startswith("user_topic_"))
async def user_topic_tanladi(callback: types.CallbackQuery, state: FSMContext):
    await callback.answer()
    tid = int(callback.data.split("_")[2])
    await state.update_data(user_target_topic=tid)
    await callback.message.answer("📥 <b>Yukingizni yuboring:</b>")
    await state.set_state(MadiWayStates.user_kutish_yuk)

@dp.message(MadiWayStates.user_kutish_yuk)
async def user_get_payload(message: types.Message, state: FSMContext):
    text_check = message.text or message.caption or ""
    user_id = message.from_user.id
    if user_id not in [ADMIN_ID, MADIWAY_ADMIN_ID]:
        if is_contains_reklama(text_check) or message.forward_date:
            await message.answer("❌ Xabarda reklama aniqlandi. Havolalarsiz qayta yuboring:")
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
    phone = message.text or ""
    user_id = message.from_user.id
    if user_id not in [ADMIN_ID, MADIWAY_ADMIN_ID] and is_contains_reklama(phone):
        await message.answer("❌ Noto'g'ri raqam formati!")
        return
            
    sdata = await state.get_data()
    yuk_text = sdata.get("yuk_text")
    media_list = sdata.get("media_list", [])
    t_group = sdata.get("user_target_group")
    t_topic = sdata.get("user_target_topic", None)
    
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
    
    await message.answer("✅ <b>Yukingiz avto-post tizimiga qabul qilindi.</b>")
    bot_info = await bot.get_me()
    
    full_info = f"{yuk_text}\n\n☎️ <b>Aloqa:</b> {phone}"
    cap = get_premium_caption(full_info[:150] + "...", "AVTO YUK", is_new_group=is_ng)
    chat = NEW_GROUP_ID if is_ng else GROUP_ID
    
    await send_universal_media_package(chat, {"media_list": media_list}, cap, get_group_kb(bot_info.username, m_id), t_topic)
    await state.clear()

# --- 📸 KANALGA JOYLASH TIZIMI ---
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

# --- VIP TIZIMI ---
@dp.message(MadiWayStates.giving_premium_username)
async def admin_get_vip_user(message: types.Message, state: FSMContext):
    target = message.text.strip()
    await state.update_data(target_user=target)
    kb = types.InlineKeyboardMarkup(inline_keyboard=[
        [types.InlineKeyboardButton(text="🗓 1 Kun (Oddiy)", callback_data="set_user_vip_1_oddiy")],
        [types.InlineKeyboardButton(text="🗓 30 Kun (Oddiy)", callback_data="set_user_vip_30_oddiy")],
        [types.InlineKeyboardButton(text="🚀 1 Kun (Tezkor 12 min)", callback_data="set_user_vip_1_tezkor")]
    ])
    await message.answer(f"Foydalanuvchi: {target}\nVIP muddatini tanlang:", reply_markup=kb)
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
        await callback.message.answer(f"✅ {target} ga VIP berildi!")
        try: await bot.send_message(chat_id=int(found_uid), text=f"🎉 Administrator sizga {days} kunlik VIP berdi!")
        except: pass
    else:
        await callback.message.answer("❌ Foydalanuvchi topilmadi.")
    await state.clear()

@dp.message(F.chat.type == "private")
async def auto_reply_handler(message: types.Message):
    if message.from_user.id not in [ADMIN_ID, MADIWAY_ADMIN_ID]:
        await message.answer(AUTO_PAYMENT_MESSAGE, reply_markup=get_guruh_tanlash_kb())

# --- CRON JOB AUTOMATION TIZIMI ---
async def auto_cron_job():
    while True:
        try:
            now = datetime.now(UZB_TZ)
            db = load_db()
            tasks = load_tasks()
            ydb = load_yuk_db()
            bot_info = await bot.get_me()
            
            tasks_changed, db_changed = False, False

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
            if db_changed: save_db(db)

            for task_id, task in list(tasks.items()):
                if not task_id.startswith("admin_") and not check_premium(int(task_id)):
                    if task_id in tasks: del tasks[task_id]; tasks_changed = True
                    continue
                try: last_sent = datetime.fromisoformat(task["last_sent"]).astimezone(UZB_TZ)
                except: last_sent = now
                
                if ((now - last_sent).total_seconds() / 60) >= task["interval"]:
                    yuk_data = ydb.get(task["yuk_id"])
                    if not yuk_data: continue
                    
                    is_ng = yuk_data.get("is_new_group", False)
                    chat = NEW_GROUP_ID if is_ng else GROUP_ID
                    owner_prefix = f"\n\n☎️ <b>Aloqa:</b> {yuk_data['phone']}" if yuk_data.get('phone') != "Admin" else ""
                    cap = get_premium_caption(yuk_data["text"][:150] + owner_prefix + "...", "🔂 AVTO RE-POST", is_new_group=is_ng)
                    
                    try:
                        await send_universal_media_package(chat, yuk_data, cap, get_group_kb(bot_info.username, task["yuk_id"]), task.get("target_topic"))
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
