import json
import logging
import asyncio
import os
import subprocess
from datetime import datetime, timedelta, timezone
from typing import List, Dict
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command, CommandObject
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.context import FSMContext
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.client.default import DefaultBotProperties

logging.basicConfig(level=logging.INFO)

# --- SOZLAMALAR ---
BOT_TOKEN = "8724439262:AAFGNuQQ4IxdqitlcCEtkHLsvyFwSPg_b1c"

CHANNEL_USER = "MADIWAYy"         
GROUP_USER = "MADIWAYy_Gr"        
NEW_GROUP_USER = "International_logistik"  

CHANNEL_ID = "-1003996104316"      
GROUP_ID = "-1003963001370"        
NEW_GROUP_ID = "-1004370807037"    
MADINA_GROUP_ID = "-1001456164408"  
MUSIC_CHANNEL_ID = "-1004442364818" 

ADMIN_ID = 6977836294         
MADIWAY_ADMIN_ID = 8112179116  
OWNER_USERNAME = "yusufxonpro1"    

bot = Bot(token=BOT_TOKEN, default=DefaultBotProperties(parse_mode="HTML"))
dp = Dispatcher(storage=MemoryStorage())

# Ma'lumotlar bazasi
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
    "💵 <b>Tariflar:</b>\n"
    "🔹 1 kunlik — 15 000 so'm\n"
    "🔹 2 kunlik — 20 000 so'm\n"
    "🔹 3 kunlik — 30 000 so'm\n"
    "🔹 1 oylik — 50 000 so'm\n\n"
    "⚡️ <b>TEZKOR TARIF (Har 12 minutda avto-post):</b>\n"
    "🚀 1 kunlik — 30 000 so'm"
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
    if any(x in text_lower for x in ["http", "t.me", "@", ".uz", ".ru"]): return True
    return any(bad in text_lower for bad in BAD_WORDS)

def load_db():
    if os.path.exists(USERS_DB_FILE):
        try: 
            with open(USERS_DB_FILE, "r") as f: return json.load(f)
        except: pass
    return {"users": {}, "premium_count": 0}

def save_db(data):
    try:
        with open(USERS_DB_FILE, "w") as f: json.dump(data, f, indent=4)
    except Exception as e:
        logging.error(f"DB saqlashda xato: {e}")

def load_yuk_db():
    if os.path.exists(YUK_DB_FILE):
        try: 
            with open(YUK_DB_FILE, "r", encoding="utf-8") as f: return json.load(f)
        except: pass
    return {}

def save_yuk_db(data):
    try:
        with open(YUK_DB_FILE, "w", encoding="utf-8") as f: json.dump(data, f, ensure_ascii=False, indent=4)
    except Exception as e:
        logging.error(f"Yuk DB saqlashda xato: {e}")

def load_tasks():
    if os.path.exists(AUTO_TASKS_FILE):
        try: 
            with open(AUTO_TASKS_FILE, "r", encoding="utf-8") as f: return json.load(f)
        except: pass
    return {}

def save_tasks(data):
    try:
        with open(AUTO_TASKS_FILE, "w", encoding="utf-8") as f: json.dump(data, f, ensure_ascii=False, indent=4)
    except Exception as e:
        logging.error(f"Tasks saqlashda xato: {e}")

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
        buttons.append([types.InlineKeyboardButton(text="📥 Yuklab Olish (Chiroyli/Premium)", url=f"https://t.me/{bot_user}?start={msg_id}")])
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
    kutish_music_wm_file = State()
    kutish_music_desc = State()

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
    try:
        await state.clear()  
        user_id = message.from_user.id
        
        db = load_db()
        uid = str(user_id)
        if uid not in db["users"]:
            db["users"][uid] = {"username": message.from_user.username or "yo'q", "full_name": message.from_user.full_name, "premium_until": None, "interval_type": "oddiy", "chosen_group": "International Logistik"}
            save_db(db)
        
        if command.args:
            yuk_id = command.args
            ydb = load_yuk_db()
            data = ydb.get(yuk_id)
            
            if not data:
                await message.answer("⚠️ Ma'lumotlar topilmadi.")
                return

            if not check_premium(user_id) and user_id not in [ADMIN_ID, MADIWAY_ADMIN_ID]:
                await message.answer("❌ <b>Siz ushbu premium musiqani yuklab olish uchun VIP tarif sotib olishingiz kerak!</b>")
                await message.answer(AUTO_PAYMENT_MESSAGE, reply_markup=get_guruh_tanlash_kb())
                return

            txt = data.get("text", "")
            media_list = data.get("media_list", [])
            
            caption = f"🎵 <b>Premium Sifatli Musiqa</b>\n───────────────────────\n{txt}\n───────────────────────\n🔥 @{CHANNEL_USER} orqali yuklab olindi."
            
            if media_list:
                await send_single_media_direct(message.chat.id, media_list[0]["type"], media_list[0]["file_id"], caption)
            else:
                await message.answer(caption)
            return

        if user_id in [ADMIN_ID, MADIWAY_ADMIN_ID]:
            kb = types.InlineKeyboardMarkup(inline_keyboard=[
                [types.InlineKeyboardButton(text="🚛 MADIWAY guruhiga yuklash", callback_data="btn_adm_madiway")],
                [types.InlineKeyboardButton(text="🌍 INTERNATIONAL guruhiga yuklash", callback_data="btn_adm_inter")],
                [types.InlineKeyboardButton(text="📸 KANALGA rasm/fayl yuklash", callback_data="btn_kanal_tashlash")],
                [types.InlineKeyboardButton(text="🎵 Musiqa + Watermark (Boshiga Yopishtirish)", callback_data="btn_adm_music")],
                [types.InlineKeyboardButton(text="🔑 VIP Berish", callback_data="btn_give_vip"), types.InlineKeyboardButton(text="📊 Statistika", callback_data="btn_stats")],
                [types.InlineKeyboardButton(text="🚛 MadiWay Guruh", url=f"https://t.me/{GROUP_USER}"), types.InlineKeyboardButton(text="📢 MadiWay Kanal", url=f"https://t.me/{CHANNEL_USER}")],
                [types.InlineKeyboardButton(text="🌍 International Guruh", url=f"https://t.me/{NEW_GROUP_USER}"), types.InlineKeyboardButton(text="👗 Madina Kilo Kiyimlar", url="https://t.me/c/1456164408/1")]
            ])
            await message.answer("💻 <b>𝗠𝗔𝗗𝗜𝗪𝗔𝗬 | 𝗔𝗗𝗠Ｉ𝗡 𝗣𝗔𝗡Ｅ𝗟</b>\n\nBarcha 20 ta tizimli boshqaruv modullari va FFmpeg Watermark mikseri faol!", reply_markup=kb)
        else:
            kb = types.InlineKeyboardMarkup(inline_keyboard=[
                [types.InlineKeyboardButton(text="💰 Tariflar va VIP sotib olish", callback_data="btn_show_tariffs")],
                [types.InlineKeyboardButton(text="📦 Yuk Tashlash (Avto-Post)", callback_data="btn_user_send_yuk")],
                [types.InlineKeyboardButton(text="🚛 MadiWay Guruh", url=f"https://t.me/{GROUP_USER}"), types.InlineKeyboardButton(text="🌍 International Guruh", url=f"https://t.me/{NEW_GROUP_USER}")]
            ])
            await message.answer(text="🏔 <b>MadiWay logistika botiga xush kelibsiz!</b>", reply_markup=kb)
    except Exception as e:
        logging.error(f"Start buyrug'ida xato: {e}")

# --- REKLAMA FILTRI ---
@dp.message(F.chat.type.in_({"group", "supergroup"}))
async def group_moderator_handler(message: types.Message):
    try:
        if message.new_chat_members or message.left_chat_member:
            try: await message.delete()
            except: pass
            return
        if message.from_user.id in [ADMIN_ID, MADIWAY_ADMIN_ID]: return
        msg_text = message.text or message.caption or ""
        if message.chat.id in [int(GROUP_ID), int(NEW_GROUP_ID), int(MADINA_GROUP_ID)]:
            if is_contains_reklama(msg_text) or message.forward_date:
                try: await message.delete()
                except: pass
    except Exception as e:
        logging.error(f"Moderator xatosi: {e}")

# --- TARIFLAR CALLBACKS ---
@dp.callback_query(F.data == "btn_show_tariffs")
async def show_tariffs_menu(callback: types.CallbackQuery):
    try:
        await callback.answer()
        await callback.message.answer(AUTO_PAYMENT_MESSAGE, reply_markup=get_guruh_tanlash_kb())
    except Exception as e: logging.error(e)

@dp.callback_query(F.data.startswith("buy_guruh_"))
async def process_buy_guruh(callback: types.CallbackQuery, state: FSMContext):
    try:
        await callback.answer()
        g_type = callback.data.split("_")[2]
        guruh_nomi = "MadiWay Asosiy Guruh" if g_type == "main" else "International Logistik"
        await state.update_data(tanlangan_guruh=guruh_nomi)
        await callback.message.answer(f"📦 <b>Guruh:</b> {guruh_nomi}\n⏱ Muddatni tanlang:", reply_markup=get_tariff_keyboard())
    except Exception as e: logging.error(e)

@dp.callback_query(F.data.startswith('track_'))
async def track_and_redirect(callback: types.CallbackQuery, state: FSMContext):
    try:
        await callback.answer()
        parts = callback.data.split("_")
        user_data = await state.get_data()
        guruh_nomi = user_data.get("tanlangan_guruh", "International Logistik")
        
        db = load_db()
        uid = str(callback.from_user.id)
        if uid in db["users"]:
            db["users"][uid]["chosen_group"] = guruh_nomi
            save_db(db)
            
        alert = f"🔔 <b>YANGI TO'LOV:</b>\n\n👤 {callback.from_user.full_name}\n🆔 ID: <code>{callback.from_user.id}</code>\n📦 Guruh: {guruh_nomi}\n🛒 Tarif: {parts[1]}"
        admin_kb = types.InlineKeyboardMarkup(inline_keyboard=[[types.InlineKeyboardButton(text="✅ Tasdiqlash", callback_data=f"adm_approve_{callback.from_user.id}")]])
        for adm in [MADIWAY_ADMIN_ID, ADMIN_ID]:
            try: await bot.send_message(chat_id=adm, text=alert, reply_markup=admin_kb)
            except: pass
            
        kb = types.InlineKeyboardMarkup(inline_keyboard=[[types.InlineKeyboardButton(text="🚀 Adminga chek yuborish", url=f"https://t.me/{OWNER_USERNAME}")]])
        await callback.message.answer(f"💳 Karta: <code>4916-9903-5000-8311</code>\n\nChekni adminga tashlang!", reply_markup=kb)
        await state.clear()
    except Exception as e: logging.error(e)

@dp.callback_query(F.data.startswith("adm_approve_"))
async def admin_quick_approve(callback: types.CallbackQuery, state: FSMContext):
    try:
        await callback.answer()
        target_uid = callback.data.split("_")[2]
        await state.update_data(quick_target_uid=target_uid)
        kb = types.InlineKeyboardMarkup(inline_keyboard=[
            [types.InlineKeyboardButton(text="🗓 1 Kun (Oddiy)", callback_data="qset_1_oddiy")],
            [types.InlineKeyboardButton(text="🗓 30 Kun (Oddiy)", callback_data="qset_30_oddiy")],
            [types.InlineKeyboardButton(text="🚀 1 Kun (⚡️ Tezkor)", callback_data="qset_1_tezkor")]
        ])
        await callback.message.answer(f"👤 ID: {target_uid} ga VIP bering:", reply_markup=kb)
        await state.set_state(MadiWayStates.admin_quick_vip_days)
    except Exception as e: logging.error(e)

@dp.callback_query(MadiWayStates.admin_quick_vip_days, F.data.startswith("qset_"))
async def admin_finalize_quick_vip(callback: types.CallbackQuery, state: FSMContext):
    try:
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
            
            await callback.message.answer(f"✅ VIP faollashdi!")
            try: await bot.send_message(chat_id=int(found_uid), text=f"🎉 VIP obunangiz faollashdi!")
            except: pass
        await state.clear()
    except Exception as e: logging.error(e)

# --- UNIVERSAL JO'NATISH TIZIMI ---
async def collect_media_group_data(messages: List[types.Message]) -> dict:
    caption_text = next((msg.html_text for msg in messages if msg.html_text), "")
    media_list = []
    for msg in messages:
        if msg.photo: media_list.append({"type": "photo", "file_id": msg.photo[-1].file_id})
        elif msg.video: media_list.append({"type": "video", "file_id": msg.video.file_id})
        elif msg.audio: media_list.append({"type": "audio", "file_id": msg.audio.file_id})
    return {"text": caption_text, "media_list": media_list}

async def send_universal_media_package(chat_id, media_data, caption, kb, t_id=None):
    try:
        media_list = media_data.get("media_list", [])
        if not media_list:
            return await bot.send_message(chat_id, caption, reply_markup=kb, message_thread_id=t_id)
        if len(media_list) == 1:
            return await send_single_media_direct(chat_id, media_list[0]["type"], media_list[0]["file_id"], caption, kb, t_id)
            
        album_items = []
        for idx, media in enumerate(media_list):
            caption_arg = caption if idx == 0 else None
            if media["type"] == "photo": album_items.append(types.InputMediaPhoto(media=media["file_id"], caption=caption_arg))
            elif media["type"] == "video": album_items.append(types.InputMediaVideo(media=media["file_id"], caption=caption_arg))
            elif media["type"] == "audio": album_items.append(types.InputMediaAudio(media=media["file_id"], caption=caption_arg))
                    
        msgs = await bot.send_media_group(chat_id, media=album_items, message_thread_id=t_id)
        if msgs and kb:
            try: await bot.edit_message_reply_markup(chat_id=chat_id, message_id=msgs[-1].message_id, reply_markup=kb)
            except: pass
        return msgs
    except Exception as e:
        logging.error(f"Paket jo'natishda xato: {e}")

async def send_single_media_direct(chat_id, m_type, file_id, caption, kb=None, t_id=None):
    try:
        if m_type == "photo": return await bot.send_photo(chat_id, file_id, caption=caption, reply_markup=kb, message_thread_id=t_id)
        elif m_type == "video": return await bot.send_video(chat_id, file_id, caption=caption, reply_markup=kb, message_thread_id=t_id)
        elif m_type == "audio": return await bot.send_audio(chat_id, file_id, caption=caption, reply_markup=kb, message_thread_id=t_id)
    except Exception as e:
        logging.error(f"Yakka media xatosi: {e}")

# --- ADMIN EVENT PANEL CALLBACKS ---
@dp.callback_query(F.data.startswith('btn_'))
async def admin_buttons(callback: types.CallbackQuery, state: FSMContext):
    try:
        await callback.answer()
        if callback.data == "btn_kanal_tashlash":
            await callback.message.answer("📥 KANALGA yuklash uchun material yuboring:")
            await state.set_state(MadiWayStates.kutish_kanal_yuk)
        elif callback.data == "btn_adm_madiway":
            btns = [types.InlineKeyboardButton(text=n, callback_data=f"adm_mw_topic_{id}") for n, id in TOPICS.items()]
            kb = types.InlineKeyboardMarkup(inline_keyboard=[btns[i:i+2] for i in range(0, len(btns), 2)])
            await callback.message.answer("📍 MADIWAY bo'limini tanlang:", reply_markup=kb)
        elif callback.data == "btn_adm_inter":
            await callback.message.answer("📥 INTERNATIONAL yukini yuboring:")
            await state.set_state(MadiWayStates.kutish_adm_inter_all)
        elif callback.data == "btn_adm_music":
            await callback.message.answer("🎵 Musiqa kanaliga qo'yish uchun asosiy <b>Musiqa (Audio MP3)</b> faylini yuboring:")
            await state.set_state(MadiWayStates.kutish_music_audio)
        elif callback.data == "btn_give_vip":
            await callback.message.answer("🔑 VIP ID yoki Username kiriting:")
            await state.set_state(MadiWayStates.giving_premium_username)
        elif callback.data == "btn_stats":
            db = load_db()
            await callback.message.answer(f"📊 A'zolar: {len(db['users'])}\nVIP: {db.get('premium_count', 0)}")
    except Exception as e: logging.error(e)

@dp.callback_query(F.data.startswith("adm_mw_topic_"))
async def admin_madiway_topic_select(callback: types.CallbackQuery, state: FSMContext):
    try:
        await callback.answer()
        tid = int(callback.data.split("_")[3])
        await state.update_data(adm_mway_target_topic=tid)
        await callback.message.answer("📥 Yuk materialini yuboring:")
        await state.set_state(MadiWayStates.kutish_adm_madiway_all)
    except Exception as e: logging.error(e)

# --- 🎵 PREMIUM WATERMARK MIKSER (FFMPEG INTEGRATSIYA) ---
@dp.message(MadiWayStates.kutish_music_audio, F.audio)
async def process_incoming_music_file(message: types.Message, state: FSMContext):
    try:
        await state.update_data(audio_file_id=message.audio.file_id)
        await message.answer("🎙 Endi musiqaning <b>BOSHIGA</b> yopishtiriladigan chiroyli <b>Watermark (Ovozli belgi MP3)</b> faylini yuboring:")
        await state.set_state(MadiWayStates.kutish_music_wm_file)
    except Exception as e: logging.error(e)

@dp.message(MadiWayStates.kutish_music_wm_file, F.audio | F.voice)
async def process_incoming_watermark_file(message: types.Message, state: FSMContext):
    try:
        wm_id = message.audio.file_id if message.audio else message.voice.file_id
        await state.update_data(watermark_file_id=wm_id)
        await message.answer("📝 Ushbu chiroyli premium trek uchun <b>Tavsif (Description)</b> matnini yuboring:")
        await state.set_state(MadiWayStates.kutish_music_desc)
    except Exception as e: logging.error(e)

@dp.message(MadiWayStates.kutish_music_desc)
async def process_music_description(message: types.Message, state: FSMContext):
    desc_text = message.html_text or message.text or ""
    sdata = await state.get_data()
    file_id = sdata.get("audio_file_id")
    wm_id = sdata.get("watermark_file_id")
    
    status_msg = await message.answer("⚡️ <code>Watermark musiqaning boshiga professional tarzda yopishtirilmoqda, iltimos kuting...</code>")
    
    music_path = f"src_{message.message_id}.mp3"
    wm_path = f"wm_{message.message_id}.mp3"
    output_path = f"out_{message.message_id}.mp3"
    
    try:
        await bot.download(file_id, destination=music_path)
        await bot.download(wm_id, destination=wm_path)
        
        cmd = [
            'ffmpeg', '-y',
            '-i', wm_path,
            '-i', music_path,
            '-filter_complex', '[0:a][1:a]concat=n=2:v=0:a=1[outa]',
            '-map', '[outa]', '-acodec', 'libmp3lame', '-q:a', '2', output_path
        ]
        
        process = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        
        if process.returncode != 0:
            raise Exception("FFmpeg aralashtirishda ichki xato aniqlandi.")
            
        bot_info = await bot.get_me()
        m_id = f"mus_{message.message_id}"
        
        final_caption = (
            f"🎵 <b>PREMIUM TRACK</b>\n"
            f"───────────────────────\n"
            f"{desc_text}\n"
            f"───────────────────────\n"
            f"📥 <i>Pastdagi tugma orqali to'liq va yuqori sifatda yuklab oling:</i>"
        )
        
        audio_file = types.FSInputFile(output_path, filename="Premium_Musiqa.mp3")
        sent_msg = await bot.send_audio(
            chat_id=MUSIC_CHANNEL_ID,
            audio=audio_file,
            caption=final_caption,
            reply_markup=get_group_kb(bot_info.username, m_id)
        )
        
        ydb = load_yuk_db()
        ydb[m_id] = {
            "text": desc_text, 
            "media_list": [{"type": "audio", "file_id": sent_msg.audio.file_id}],
            "is_new_group": False, 
            "phone": "Admin"
        }
        save_yuk_db(ydb)
        
        await status_msg.edit("🚀 <b>Musiqa boshiga watermark yopishtirildi va chiroyli dizaynda kanalga joylandi!</b>")
        
    except Exception as ex:
        await status_msg.edit(f"❌ Xato yuz berdi: {ex}\nServerda ffmpeg borligini va fayllar formatini tekshiring.")
        
    finally:
        for path in [music_path, wm_path, output_path]:
            if os.path.exists(path):
                try: os.remove(path)
                except: pass
            
    await state.clear()

# --- USER POST PROCESSI VA QOLGAN INTEGRATSIYALAR ---
async def generic_media_group_processor(mg_id: str, state: FSMContext, handler_func):
    await asyncio.sleep(1.5)
    messages = MEDIA_GROUPS_CACHE.get(mg_id, [])
    if not messages: return
    media_data = await collect_media_group_data(messages)
    try:
        await handler_func(messages[0], media_data, state)
    except Exception as e:
        logging.error(f"Media guruh handleri xatosi: {e}")
    if mg_id in MEDIA_GROUPS_CACHE: del MEDIA_GROUPS_CACHE[mg_id]

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

@dp.callback_query(F.data == "btn_user_send_yuk")
async def user_send_yuk_start(callback: types.CallbackQuery, state: FSMContext):
    try:
        await callback.answer()
        if not check_premium(callback.from_user.id):
            await callback.message.answer("❌ Sizda VIP obuna faol emas!")
            return
        kb = types.InlineKeyboardMarkup(inline_keyboard=[
            [types.InlineKeyboardButton(text="MadiWay Asosiy Guruh", callback_data="user_target_main")],
            [types.InlineKeyboardButton(text="🌍 International Logistik", callback_data="user_target_new")]
        ])
        await callback.message.answer("🎯 <b>Yukingiz qaysi guruhga joylab borilsin?</b>", reply_markup=kb)
        await state.set_state(MadiWayStates.user_kutish_guruh_tanlash)
    except Exception as e: logging.error(e)

@dp.callback_query(MadiWayStates.user_kutish_guruh_tanlash, F.data.startswith("user_target_"))
async def user_guruh_tanladi(callback: types.CallbackQuery, state: FSMContext):
    try:
        await callback.answer()
        target = callback.data.split("_")[2]
        await state.update_data(user_target_group=target)
        if target == "main":
            btns = [types.InlineKeyboardButton(text=n, callback_data=f"user_topic_{id}") for n, id in TOPICS.items()]
            kb = types.InlineKeyboardMarkup(inline_keyboard=[btns[i:i+2] for i in range(0, len(btns), 2)])
            await callback.message.answer("📍 <b>Bo'limni tanlang:</b>", reply_markup=kb)
            await state.set_state(MadiWayStates.user_kutish_topic_tanlash)
        else:
            await callback.message.answer("📥 <b>International guruhi uchun Yukingizni yuboring:</b>")
            await state.set_state(MadiWayStates.user_kutish_yuk)
    except Exception as e: logging.error(e)

@dp.callback_query(MadiWayStates.user_kutish_topic_tanlash, F.data.startswith("user_topic_"))
async def user_topic_tanladi(callback: types.CallbackQuery, state: FSMContext):
    try:
        await callback.answer()
        tid = int(callback.data.split("_")[2])
        await state.update_data(user_target_topic=tid)
        await callback.message.answer("📥 <b>Yukingizni yuboring:</b>")
        await state.set_state(MadiWayStates.user_kutish_yuk)
    except Exception as e: logging.error(e)

@dp.message(MadiWayStates.user_kutish_yuk)
async def user_get_payload(message: types.Message, state: FSMContext):
    text_check = message.text or message.caption or ""
    if message.from_user.id not in [ADMIN_ID, MADIWAY_ADMIN_ID] and is_contains_reklama(text_check):
        await message.answer("❌ Reklama aniqlandi!")
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
    await msg_obj.answer("☎️ Telefon Raqamingizni yozing:")
    await state.set_state(MadiWayStates.user_kutish_tel)

@dp.message(MadiWayStates.user_kutish_tel)
async def user_finish_yuk(message: types.Message, state: FSMContext):
    try:
        phone = message.text or ""
        sdata = await state.get_data()
        yuk_text = sdata.get("yuk_text")
        media_list = sdata.get("media_list", [])
        t_group = sdata.get("user_target_group")
        t_topic = sdata.get("user_target_topic", None)
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
        
        await message.answer("✅ Yukingiz qabul qilindi.")
        bot_info = await bot.get_me()
        
        full_info = f"{yuk_text}\n\n☎️ <b>Aloqa:</b> {phone}"
        cap = get_premium_caption(full_info, "AVTO YUK", is_new_group=is_ng)
        chat = NEW_GROUP_ID if is_ng else GROUP_ID
        await send_universal_media_package(chat, {"media_list": media_list}, cap, get_group_kb(bot_info.username, m_id), t_topic)
        await state.clear()
    except Exception as e: logging.error(e)

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
    await msg_obj.answer("✅ Kanalga yuklandi.")
    await state.clear()

@dp.message(MadiWayStates.giving_premium_username)
async def admin_get_vip_user(message: types.Message, state: FSMContext):
    try:
        target = message.text.strip()
        await state.update_data(target_user=target)
        kb = types.InlineKeyboardMarkup(inline_keyboard=[
            [types.InlineKeyboardButton(text="🗓 1 Kun (Oddiy)", callback_data="set_user_vip_1_oddiy")],
            [types.InlineKeyboardButton(text="🗓 30 Kun (Oddiy)", callback_data="set_user_vip_30_oddiy")]
        ])
        await message.answer(f"Foydalanuvchi: {target}\nVIP muddatini tanlang:", reply_markup=kb)
        await state.set_state(MadiWayStates.giving_premium_days)
    except Exception as e: logging.error(e)

@dp.callback_query(MadiWayStates.giving_premium_days, F.data.startswith("set_user_vip_"))
async def admin_finalize_vip(callback: types.CallbackQuery, state: FSMContext):
    try:
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
    except Exception as e: logging.error(e)

@dp.message(F.chat.type == "private")
async def auto_reply_handler(message: types.Message):
    try:
        if message.from_user.id not in [ADMIN_ID, MADIWAY_ADMIN_ID]:
            await message.answer(AUTO_PAYMENT_MESSAGE, reply_markup=get_guruh_tanlash_kb())
    except Exception as e: logging.error(e)

async def auto_cron_job():
    while True:
        try:
            now = datetime.now(UZB_TZ)
            db = load_db()
            tasks = load_tasks()
            ydb = load_yuk_db()
            bot_info = await bot.get_me()
            t_changed, d_changed = False, False
            for uid, info in list(db["users"].items()):
                if info.get("premium_until"):
                    try: until_dt = datetime.fromisoformat(info["premium_until"]).astimezone(UZB_TZ)
                    except: continue
                    if now > until_dt:
                        db["users"][uid]["premium_until"] = None
                        d_changed = True
                        if uid in tasks: del tasks[uid]; t_changed = True
            if d_changed: save_db(db)
            for task_id, task in list(tasks.items()):
                if not check_premium(int(task_id)): continue
                try: last_sent = datetime.fromisoformat(task["last_sent"]).astimezone(UZB_TZ)
                except: last_sent = now
                if ((now - last_sent).total_seconds() / 60) >= task["interval"]:
                    yuk_data = ydb.get(task["yuk_id"])
                    if yuk_data:
                        is_ng = yuk_data.get("is_new_group", False)
                        chat = NEW_GROUP_ID if is_ng else GROUP_ID
                        cap = get_premium_caption(yuk_data["text"], "🔂 AVTO RE-POST", is_new_group=is_ng)
                        try:
                            await send_universal_media_package(chat, yuk_data, cap, get_group_kb(bot_info.username, task["yuk_id"]), task.get("target_topic"))
                            tasks[task_id]["last_sent"] = now.isoformat()
                            t_changed = True
                        except: pass
            if t_changed: save_tasks(tasks)
        except Exception as cron_ex: 
            logging.error(f"Cron xatosi: {cron_ex}")
        await asyncio.sleep(30)

async def main():
    asyncio.create_task(auto_cron_job())
    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)

if __name__ == '__main__':
    try:
        asyncio.run(main())
    except Exception as main_e:
        logging.critical(f"Bot butkul to'xtadi: {main_e}")
