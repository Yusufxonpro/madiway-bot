import json
import logging
import asyncio
import os
from datetime import datetime
import pytz
from aiogram import Bot, Dispatcher, types, F
from aiogram.filters import Command
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.context import FSMContext
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.client.default import DefaultBotProperties
from aiogram.exceptions import TelegramAPIError

# Loglarni yoqamiz
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# --- SOZLAMALAR ---
BOT_TOKEN = "8724439262:AAFGNuQQ4IxdqitlcCEtkHLsvyFwSPg_b1c"
CHANNEL_USER = "MADIWAYy"  
GROUP_ID = -1003963001370    
CHANNEL_ID = -1003996104316  

ADMIN_ID = 6977836294          
MADIWAY_ADMIN_ID = 8112179116  
ADMINS = [ADMIN_ID, MADIWAY_ADMIN_ID]

bot = Bot(
    token=BOT_TOKEN, 
    default=DefaultBotProperties(parse_mode="HTML")
)
dp = Dispatcher(storage=MemoryStorage())

uzb_tz = pytz.timezone('Asia/Tashkent')
START_SETTINGS_FILE = "global_start_settings.json"
YUK_SETTINGS_FILE = "yuk_settings_images.json"
YUK_OMBORI_FILE = "yuk_ombori.json"
REAKSIYA_FILE = "reaksiyalar.json"  # Reaksiyalarni saqlash uchun

DEFAULT_TEXT = (
    "⭐️ <b>𝗠𝗔𝗗𝗜𝗪𝗔𝗬 | 𝗟𝗢𝗚𝗜𝗦𝗧𝗜𝗖𝗦 𝗦𝗬𝗦𝗧𝗘𝗠</b> ⭐️\n"
    "───────────────────────\n"
    "Tizimga xush kelibsiz! Eng tezkor va ishonchli yuklar platformasi.\n"
    "Yuk tashlash va boshqarish paneli faol holatda."
)

TOPICS = {
    "🌍 Europa": 2, "🇩🇪 Germaniya": 14, "🇷🇺 Rossiya": 4, "🇰🇬 Qirg'iziston": 6,
    "🇰🇿 Kazakistan": 8, "🇮🇷 Eron": 10, "🇹🇯 Tojikston": 12, "🇧🇾 Belarusiya": 16,
    "🇬🇪 Gruziya": 18, "📣 Elon berish": 1,
    
    "📅 Yanvar": 20, "📅 Fevral": 22, "📅 Mart": 24, "📅 Aprel": 26,
    "📅 May": 28, "📅 Iyun": 30, "📅 Iyul": 32, "📅 Avgust": 34,
    "📅 Sentyabr": 36, "📅 Oktyabr": 38, "📅 Noyabr": 40, "📅 Dekabr": 42
}

# --- ADMIN QO'YGAN EMOJILAR ---
# Bu yerga admin o'zi xohlagan emojilarni yozib qo'yishi mumkin:
EMOJIS = ["👍", "🔥", "🤝", "🙌"]

# --- FAYLLAR BILAN ISHLASh ---
def load_json(filename, default_val):
    if os.path.exists(filename):
        with open(filename, "r", encoding="utf-8") as f:
            return json.load(f)
    return default_val

def save_json(filename, data):
    with open(filename, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=4)

def get_next_photo_id():
    cfg = load_json(YUK_SETTINGS_FILE, {"images": [], "current_index": 0})
    images = cfg.get("images", [])
    if not images: return None
    idx = cfg.get("current_index", 0)
    if idx >= len(images): idx = 0
    photo_id = images[idx]
    cfg["current_index"] = (idx + 1) % len(images)
    save_json(YUK_SETTINGS_FILE, cfg)
    return photo_id

def parse_duration_to_seconds(duration_str):
    try:
        val = int(duration_str.split()[0])
        if "min" in duration_str: return val * 60
        elif "soat" in duration_str: return val * 3600
    except: pass
    return 60

async def auto_delete_message(chat_id, message_id, delay_seconds):
    await asyncio.sleep(delay_seconds)
    try:
        await bot.delete_message(chat_id=chat_id, message_id=message_id)
        # O'chgan xabarning reaksiyalarini ham bazadan o'chiramiz
        reaksiyalar = load_json(REAKSIYA_FILE, {})
        if str(message_id) in reaksiyalar:
            del reaksiyalar[str(message_id)]
            save_json(REAKSIYA_FILE, reaksiyalar)
    except TelegramAPIError: pass

# --- DINAMIK TUGMALAR (REAKSIYA BILAN) ---
def get_post_keyboard(msg_db_id=None, message_id=None):
    reaksiyalar = load_json(REAKSIYA_FILE, {})
    
    # Agar xabar hali yuborilmagan bo'lsa (yoki yangi bo'lsa) nollardan boshlanadi
    msg_id_str = str(message_id) if message_id else "new"
    msg_data = reaksiyalar.get(msg_id_str, {})
    
    reaction_buttons = []
    for emoji in EMOJIS:
        count = msg_data.get(emoji, {}).get("count", 0)
        text = f"{emoji} {count}" if count > 0 else emoji
        reaction_buttons.append(types.InlineKeyboardButton(text=text, callback_data=f"react_{emoji}_{msg_id_str}"))
    
    # Emojilarni inline qatorga joylaymiz
    keyboard_grid = [reaction_buttons]
    
    # Agar kanal uchun to'liq ko'rish yoki guruh havolasi kerak bo'lsa
    extra_buttons = []
    if msg_db_id:
        extra_buttons.append(types.InlineKeyboardButton(text="⭐️ Yukni to'liq ko'rish", callback_data=f"show_full_{msg_db_id}"))
    extra_buttons.append(types.InlineKeyboardButton(text="📢 Kanalga qo'shilish", url=f"https://t.me/{CHANNEL_USER}"))
    
    for btn in extra_buttons:
        keyboard_grid.append([btn])
        
    return types.InlineKeyboardMarkup(inline_keyboard=keyboard_grid)

def get_premium_caption(main_text, status_label="𝗬𝗨𝗞 𝗘𝗟𝗢𝗡𝗜", duration_text=None):
    now = datetime.now(uzb_tz)
    sana_soat = now.strftime("📅 %Y-%m-%d  🕒 %I:%M %p") 
    caption = f"⭐️ <b>𝗠𝗔𝗗𝗜𝗪𝗔𝗬 | {status_label}</b> ⭐️\n───────────────────────\n{main_text}\n───────────────────────\n"
    if duration_text: caption += f"⏱ Amal qilish muddati: {duration_text}\n"
    caption += f"⏳ Vaqt: {sana_soat}\n📢 Kanalimiz: https://t.me/{CHANNEL_USER}"
    return caption

def get_duration_keyboard():
    time_options = [
        "1 min", "2 min", "3 min", "4 min", "5 min", "6 min", "7 min", "8 min", "9 min", "10 min",
        "15 min", "20 min", "22 min", "30 min", "1 soat", "2 soat", "4 soat", "5 soat", "6 soat",
        "7 soat", "8 soat", "9 soat", "❌ Atmen qilish"
    ]
    buttons = [types.KeyboardButton(text=t) for t in time_options]
    return types.ReplyKeyboardMarkup(keyboard=[buttons[i:i+4] for i in range(0, len(buttons), 4)], resize_keyboard=True)

class MadiWayStates(StatesGroup):
    kutish_global_start = State()
    kutish_yuk_photo = State()
    kutish_kanal_yuk = State()
    kutish_bitta_topic_yuk = State()
    kutish_hamma_topic_yuk = State()
    kutish_kanal_va_hamma_topic = State()
    kutish_muddat = State()

# --- REAKSIYA BOSILGANDA ISHLOVCHI HANDLER ---
@dp.callback_query(F.data.startswith('react_'))
async def handle_reaction(callback: types.CallbackQuery):
    _, emoji, msg_id_str = callback.data.split('_')
    user_id = callback.from_user.id
    
    # Agar xabar yuborilgan vaqtda hali ID berilmagan bo'lsa qaytaramiz
    if msg_id_str == "new":
        await callback.answer("⚠️ Bu xabarga hozircha reaksiya bildirib bo'lmaydi.")
        return
        
    reaksiyalar = load_json(REAKSIYA_FILE, {})
    
    if msg_id_str not in reaksiyalar:
        reaksiyalar[msg_id_str] = {}
        
    if emoji not in reaksiyalar[msg_id_str]:
        reaksiyalar[msg_id_str][emoji] = {"count": 0, "users": []}
        
    msg_emoji_data = reaksiyalar[msg_id_str][emoji]
    user_list = msg_emoji_data.get("users", [])
    
    # --- LOGIKA: ADMIN VS FOYDALANUVChI ---
    if user_id in ADMINS:
        # Admin xohlagancha bosaveradi
        msg_emoji_data["count"] += 1
        await callback.answer(f"Admin sifatida {emoji} qo'shdingiz!")
    else:
        # Oddiy foydalanuvchi faqat 1 marta bosa oladi
        if user_id in user_list:
            # Ikkinchi marta bossa reaksiyani olib tashlaydi
            msg_emoji_data["count"] -= 1
            user_list.remove(user_id)
            await callback.answer("Reaksiyangiz olib tashlandi.")
        else:
            # Birinchi marta bosganda qo'shadi
            msg_emoji_data["count"] += 1
            user_list.append(user_id)
            await callback.answer(f"Siz {emoji} bosdingiz!")
            
    msg_emoji_data["users"] = user_list
    reaksiyalar[msg_id_str][emoji] = msg_emoji_data
    save_json(REAKSIYA_FILE, reaksiyalar)
    
    # Tugmalarni yangilaymiz (Kanal uchun mos ma'lumot ID si bormi tekshiramiz)
    # Callback query inline_message_id yoki oddiy xabardan kelishiga qarab markup yangilanadi
    msg_db_id = None
    if callback.message.reply_markup:
        for row in callback.message.reply_markup.inline_keyboard:
            for btn in row:
                if btn.callback_data and btn.callback_data.startswith("show_full_"):
                    msg_db_id = btn.callback_data.replace("show_full_", "")
                    
    try:
        await callback.message.edit_reply_markup(
            reply_markup=get_post_keyboard(msg_db_id=msg_db_id, message_id=int(msg_id_str))
        )
    except TelegramAPIError:
        pass

# --- START VA PANEL HANDLERS ---
@dp.message(Command("start"))
async def start_cmd(message: types.Message, state: FSMContext):
    await state.clear()
    user_id = message.from_user.id
    start_data = load_json(START_SETTINGS_FILE, {"type": "text", "file_id": None, "text": DEFAULT_TEXT})
    
    if user_id in ADMINS:
        kb = types.InlineKeyboardMarkup(inline_keyboard=[
            [types.InlineKeyboardButton(text="⚙️ Start sozlash", callback_data="btn_add_start_msg"),
             types.InlineKeyboardButton(text="📸 10 ta Rasm Sozlash", callback_data="btn_add_yuk_photo")],
            [types.InlineKeyboardButton(text="⭐️ Kanalga yuk", callback_data="btn_kanal_tashlash")],
            [types.InlineKeyboardButton(text="📍 Bitta Bo'lim/Oyga", callback_data="btn_bitta_topic")],
            [types.InlineKeyboardButton(text="💥 Hammasiga", callback_data="btn_hamma_topic")],
            [types.InlineKeyboardButton(text="🚀 Kanal + Hammasi", callback_data="btn_kanal_va_hamma")]
        ])
        await message.answer("💻 <b>𝗔𝗗𝗠𝗜𝗡 𝗣𝗔𝗡𝗘𝗟 (𝗠𝗔𝗗𝗜𝗪𝗔𝗬)</b>", reply_markup=kb)
    else:
        kb = types.InlineKeyboardMarkup(inline_keyboard=[
            [types.InlineKeyboardButton(text="📢 Kanal", url=f"https://t.me/{CHANNEL_USER}")],
            [types.InlineKeyboardButton(text="🛒 Guruhni sotib olish", callback_data="btn_sotib_olish")]
        ])
        t, f_type, f_id = start_data.get("text"), start_data.get("type"), start_data.get("file_id")
        if f_type == "photo" and f_id: await message.answer_photo(f_id, caption=t, reply_markup=kb)
        elif f_type == "video" and f_id: await message.answer_video(f_id, caption=t, reply_markup=kb)
        else: await message.answer(t or DEFAULT_TEXT, reply_markup=kb)

@dp.callback_query(F.data.startswith('btn_'))
async def btns(callback: types.CallbackQuery, state: FSMContext):
    await callback.answer()
    if callback.data == "btn_sotib_olish":
        kb = types.InlineKeyboardMarkup(inline_keyboard=[
            [types.InlineKeyboardButton(text="👤 @madiways", url="https://t.me/madiways")],
            [types.InlineKeyboardButton(text="💻 @Yusufxonpro", url="https://t.me/Yusufxonpro")]
        ])
        await callback.message.answer("🛒 Sotib olish bo'yicha murojaat qiling:", reply_markup=kb)
    elif callback.data == "btn_add_start_msg":
        await callback.message.answer("⚙️ Yangi start xabarni yuboring:")
        await state.set_state(MadiWayStates.kutish_global_start)
    elif callback.data == "btn_add_yuk_photo":
        cfg = load_json(YUK_SETTINGS_FILE, {"images": [], "current_index": 0})
        await callback.message.answer(f"📸 <b>Bazada {len(cfg.get('images', []))} ta rasm bor.</b>\nYangi rasm yuboring:")
        await state.set_state(MadiWayStates.kutish_yuk_photo)
    elif callback.data == "btn_kanal_tashlash":
        await callback.message.answer("📥 Kanal yukini yuboring:")
        await state.set_state(MadiWayStates.kutish_kanal_yuk)
    elif callback.data == "btn_hamma_topic":
        await callback.message.answer("💥 Hammasiga ketadigan yukni yuboring:")
        await state.set_state(MadiWayStates.kutish_hamma_topic_yuk)
    elif callback.data == "btn_kanal_va_hamma":
        await callback.message.answer("🚀 Kanal + Hamma joyga ketadigan yukni yuboring:")
        await state.set_state(MadiWayStates.kutish_kanal_va_hamma_topic)
    elif callback.data == "btn_bitta_topic":
        btns = [types.InlineKeyboardButton(text=n, callback_data=f"select_topic_{id}") for n, id in TOPICS.items()]
        await callback.message.answer("📍 Bo'lim yoki Oyni tanlang:", reply_markup=types.InlineKeyboardMarkup(inline_keyboard=[btns[i:i+2] for i in range(0, len(btns), 2)]))

@dp.callback_query(F.data.startswith('select_topic_'))
async def topic_sel(callback: types.CallbackQuery, state: FSMContext):
    await state.update_data(target_topic_id=int(callback.data.split('_')[2]))
    await callback.message.answer("📥 Yuk matnini yuboring:")
    await state.set_state(MadiWayStates.kutish_bitta_topic_yuk)

# --- SAVERS ---
@dp.message(MadiWayStates.kutish_global_start)
async def save_start(message: types.Message, state: FSMContext):
    txt = message.html_text or message.caption or ""
    cfg = {"type": "text", "file_id": None, "text": txt}
    if message.photo: cfg.update({"type": "photo", "file_id": message.photo[-1].file_id})
    elif message.video: cfg.update({"type": "video", "file_id": message.video.file_id})
    save_json(START_SETTINGS_FILE, cfg)
    await message.answer("✅ Start xabari saqlandi!")
    await state.clear()

@dp.message(MadiWayStates.kutish_yuk_photo)
async def save_yuk_photo(message: types.Message, state: FSMContext):
    if message.photo:
        new_photo_id = message.photo[-1].file_id
        cfg = load_json(YUK_SETTINGS_FILE, {"images": [], "current_index": 0})
        images = cfg.get("images", [])
        if new_photo_id not in images:
            if len(images) >= 10: images.pop(0)
            images.append(new_photo_id)
            cfg["images"] = images
            save_json(YUK_SETTINGS_FILE, cfg)
            await message.answer(f"✅ Rasm bazaga qo'shildi! Jami: {len(images)}/10 ta.")
        else: await message.answer("ℹ️ Bu rasm allaqachon mavjud.")
    else: await message.answer("❌ Iltimos, faqat rasm yuboring.")
    await state.clear()

# --- KAFILLI YUBORISH VA DINAMIK UPDATE TIZIMI ---
async def send_and_setup_keyboard(chat_id, caption, msg_db_id=None, t_id=None):
    rotated_photo_id = get_next_photo_id()
    thread_id = None
    if t_id is not None:
        try: thread_id = int(t_id)
        except: pass

    # Avval "new" markupli vaqtinchalik xabar yuboramiz
    initial_kb = get_post_keyboard(msg_db_id=msg_db_id, message_id=None)
    try:
        if rotated_photo_id:
            msg = await bot.send_photo(chat_id=chat_id, photo=rotated_photo_id, caption=caption, reply_markup=initial_kb, message_thread_id=thread_id)
        else:
            msg = await bot.send_message(chat_id=chat_id, text=caption, reply_markup=initial_kb, message_thread_id=thread_id)
        
        # Xabar yuborilgach uning aniq message_id sini tugmalarga joylab, qayta yangilaymiz
        await bot.edit_reply_markup(chat_id=chat_id, message_id=msg.message_id, reply_markup=get_post_keyboard(msg_db_id=msg_db_id, message_id=msg.message_id))
        return msg
    except TelegramAPIError as e:
        logger.error(f"Xatolik: {e}")
        return None

# --- PROCESS MULTI-POSTING ---
@dp.message(MadiWayStates.kutish_kanal_yuk)
@dp.message(MadiWayStates.kutish_bitta_topic_yuk)
@dp.message(MadiWayStates.kutish_hamma_topic_yuk)
@dp.message(MadiWayStates.kutish_kanal_va_hamma_topic)
async def process_yuk_content(message: types.Message, state: FSMContext):
    current_state = await state.get_state()
    await state.update_data(yuk_text=(message.html_text or message.caption or ""), prev_state=current_state)
    await message.answer("⏱ <b>Ushbu yuk e'loni necha vaqt davomida amal qilsin?</b>", reply_markup=get_duration_keyboard())
    await state.set_state(MadiWayStates.kutish_muddat)

@dp.message(MadiWayStates.kutish_muddat)
async def process_duration(message: types.Message, state: FSMContext):
    if message.text == "❌ Atmen qilish":
        await message.answer("❌ Amaliyat bekor qilindi.", reply_markup=types.ReplyKeyboardRemove())
        await state.clear()
        return

    data = await state.get_data()
    txt, prev_state, duration = data.get("yuk_text"), data.get("prev_state"), message.text
    delay_seconds = parse_duration_to_seconds(duration)
    success_flag = False
    YUK_OMBORI = load_json(YUK_OMBORI_FILE, {})

    # 1. KANALGA
    if prev_state == MadiWayStates.kutish_kanal_yuk.state:
        m_id = f"c_{int(datetime.now().timestamp())}"
        YUK_OMBORI[m_id] = txt
        save_json(YUK_OMBORI_FILE, YUK_OMBORI)
        msg = await send_and_setup_keyboard(CHANNEL_ID, get_premium_caption(txt[:150] + "...", duration_text=duration), msg_db_id=m_id)
        if msg:
            success_flag = True
            asyncio.create_task(auto_delete_message(CHANNEL_ID, msg.message_id, delay_seconds))

    # 2. BITTA BO'LIM/OYGA
    elif prev_state == MadiWayStates.kutish_bitta_topic_yuk.state:
        tid = data.get("target_topic_id")
        msg = await send_and_setup_keyboard(GROUP_ID, get_premium_caption(txt, duration_text=duration), t_id=tid)
        if msg:
            success_flag = True
            asyncio.create_task(auto_delete_message(GROUP_ID, msg.message_id, delay_seconds))

    # 3. HAMMA INTERFEYSGA
    elif prev_state == MadiWayStates.kutish_hamma_topic_yuk.state:
        sent_count = 0
        for n, tid in TOPICS.items():
            msg = await send_and_setup_keyboard(GROUP_ID, get_premium_caption(txt, duration_text=duration), t_id=tid)
            if msg:
                sent_count += 1
                asyncio.create_task(auto_delete_message(GROUP_ID, msg.message_id, delay_seconds))
            await asyncio.sleep(0.3)
        if sent_count > 0: success_flag = True

    # 4. KANAL + HAMMA JOYGA
    elif prev_state == MadiWayStates.kutish_kanal_va_hamma_topic.state:
        m_id = f"c_{int(datetime.now().timestamp())}"
        YUK_OMBORI[m_id] = txt
        save_json(YUK_OMBORI_FILE, YUK_OMBORI)
        
        msg_chan = await send_and_setup_keyboard(CHANNEL_ID, get_premium_caption(txt[:150] + "...", duration_text=duration), msg_db_id=m_id)
        if msg_chan: asyncio.create_task(auto_delete_message(CHANNEL_ID, msg_chan.message_id, delay_seconds))
        
        sent_count = 0
        for n, tid in TOPICS.items():
            msg_grp = await send_and_setup_keyboard(GROUP_ID, get_premium_caption(txt, duration_text=duration), t_id=tid)
            if msg_grp:
                sent_count += 1
                asyncio.create_task(auto_delete_message(GROUP_ID, msg_grp.message_id, delay_seconds))
            await asyncio.sleep(0.3)
        if sent_count > 0: success_flag = True

    if success_flag:
        await message.answer(f"🚀 <b>Tasdiqlandi! Reaksiyali tugmalar qo'shildi va xabarlar {duration}dan keyin o'chadi.</b>", reply_markup=types.ReplyKeyboardRemove())
    else:
        await message.answer("❌ <b>Xatolik!</b> Ma'lumot yuborilmadi.", reply_markup=types.ReplyKeyboardRemove())
    await state.clear()

@dp.callback_query(F.data.startswith('show_full_'))
async def full(cb: types.CallbackQuery):
    YUK_OMBORI = load_json(YUK_OMBORI_FILE, {})
    txt = YUK_OMBORI.get(cb.data.replace("show_full_", ""), "Topilmadi")
    try: await cb.message.edit_caption(caption=get_premium_caption(txt, "𝗧𝗢'𝗟𝗜𝗤"), reply_markup=get_post_keyboard(message_id=cb.message.message_id))
    except: await cb.message.answer(get_premium_caption(txt, "𝗧𝗢'𝗟𝗜𝗤"))

async def main():
    print("-----------------------------------------")
    print("MADIWAY Tizimi (Reaksiyalar va Karusel) Faol.")
    print("-----------------------------------------")
    await dp.start_polling(bot)

if __name__ == '__main__':
    asyncio.run(main())
