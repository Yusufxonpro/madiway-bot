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

# Loglarni sozlash
logging.basicConfig(level=logging.INFO)

# --- SOZLAMALAR ---
BOT_TOKEN = "8724439262:AAFGNuQQ4IxdqitlcCEtkHLsvyFwSPg_b1c"
CHANNEL_USER = "MADIWAYy" 
GROUP_ID = "-1002130310815"
CHANNEL_ID = "-1002120000000"

# Adminlarning Telegram ID raqamlari
ADMIN_ID = 6977836294         # Yusufxonpro ID
MADIWAY_ADMIN_ID = 8112179116  # madiways ID

bot = Bot(token=BOT_TOKEN, parse_mode="HTML")
dp = Dispatcher(storage=MemoryStorage())

uzb_tz = pytz.timezone('Asia/Tashkent')
START_SETTINGS_FILE = "global_start_settings.json"

DEFAULT_TEXT = (
    "⭐️ <b>𝗠𝗔𝗗𝗜𝗪𝗔𝗬 | 𝗟𝗢𝗚𝗜𝗦𝗧𝗜𝗖𝗦 𝗦𝗬𝗦𝗧𝗘𝗠</b> ⭐️\n"
    "───────────────────────\n"
    "Tizimga xush kelibsiz! Eng tezkor va ishonchli yuklar platformasi.\n"
    "Yuk tashlash va boshqarish paneli faol holatda."
)

# --- GLOBAL START SOZLAMALARINI BOSHQARISH ---
def load_start_settings():
    if os.path.exists(START_SETTINGS_FILE):
        with open(START_SETTINGS_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {"type": "text", "file_id": None, "text": DEFAULT_TEXT}

def save_start_settings(data):
    with open(START_SETTINGS_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=4)

# --- PREMIUM YUK MATNI FORMATI ---
def get_premium_caption(main_text, status_label="𝗬𝗨𝗞 𝗘𝗟𝗢𝗡𝗜"):
    now = datetime.now(uzb_tz)
    sana_soat = now.strftime("📅 %Y-%m-%d  🕒 %I:%M %p") 
    
    caption = (
        f"⭐️ <b>𝗠𝗔𝗗𝗜𝗪𝗔𝗬 | {status_label}</b> ⭐️\n"
        f"───────────────────────\n"
        f"{main_text}\n"
        f"───────────────────────\n"
        f"⏳ Vaqt: {sana_soat}\n"
        f"📢 Kanalimiz: https://t.me/{CHANNEL_USER}"
    )
    return caption

def get_channel_kb(msg_id=None):
    kb = types.InlineKeyboardMarkup(inline_keyboard=[])
    buttons = []
    if msg_id:
        buttons.append([types.InlineKeyboardButton(text="⭐️ Yukni to'liq ko'rish", callback_data=f"show_full_{msg_id}")])
    buttons.append([types.InlineKeyboardButton(text="📢 Kanalga qo'shilish", url=f"https://t.me/{CHANNEL_USER}")])
    kb.inline_keyboard = buttons
    return kb

YUK_OMBORI = {}

class MadiWayStates(StatesGroup):
    kutish_global_start = State()
    kutish_kanal_yuk = State()
    kutish_bitta_topic_yuk = State()
    kutish_hamma_topic_yuk = State()
    kutish_kanal_va_hamma_topic = State()

TOPICS = {
    "🌍 Europa": 2, "🇩🇪 Germaniya": 14, "🇷🇺 Rossiya": 4, "🇰🇬 Qirg'iziston": 6,
    "🇰🇿 Kazakistan": 8, "🇮🇷 Eron": 10, "🇹🇯 Tojikston": 12, "🇧🇾 Belarusiya": 16,
    "🇬🇪 Gruziya": 18, "📣 Elon berish": 1
}

# ----------------- INTELLECTUAL START ENGINE -----------------
@dp.message_handler(Command("start"))
async def intelligent_start(message: types.Message, state: FSMContext):
    await state.clear()
    user_id = message.from_user.id
    start_data = load_start_settings()
    
    # ADMINLAR UCHUN
    if user_id in [ADMIN_ID, MADIWAY_ADMIN_ID]:
        kb = types.InlineKeyboardMarkup(inline_keyboard=[
            [types.InlineKeyboardButton(text="⚙️ Start xabarni sozlash (GLOBAL)", callback_data="btn_add_start_msg")],
            [types.InlineKeyboardButton(text="⭐️ Kanalga yuk tashlash", callback_data="btn_kanal_tashlash")],
            [types.InlineKeyboardButton(text="✨ Alohida bitta Topicga yuborish", callback_data="btn_bitta_topic")],
            [types.InlineKeyboardButton(text="💥 Hammasiga bittada yuborish", callback_data="btn_hamma_topic")],
            [types.InlineKeyboardButton(text="🚀 Kanal va Hamma Topicga baravar", callback_data="btn_kanal_va_hamma")]
        ])
        await message.answer("💻 <b><b>𝗠𝗔𝗗𝗜𝗪𝗔𝗬 | 𝗔𝗗𝗠𝗜𝗡 𝗣𝗔𝗡𝗘𝗟</b></b>\n───────────────────────\nBoshqaruv paneli faol:", reply_markup=kb)
        
    # ODDIY FOYDALANUVCHILAR UCHUN
    else:
        kb = types.InlineKeyboardMarkup(inline_keyboard=[
            [types.InlineKeyboardButton(text="📢 Kanalga qo'shilish", url=f"https://t.me/{CHANNEL_USER}")],
            [types.InlineKeyboardButton(text="🛒 Guruhni sotib olish", callback_data="btn_sotib_olish")]
        ])
        
        msg_text = start_data.get("text", DEFAULT_TEXT)
        f_type = start_data.get("type")
        f_id = start_data.get("file_id")
        
        if f_type == "photo" and f_id:
            await bot.send_photo(chat_id=user_id, photo=f_id, caption=msg_text, reply_markup=kb)
        elif f_type == "video" and f_id:
            await bot.send_video(chat_id=user_id, video=f_id, caption=msg_text, reply_markup=kb)
        elif f_type == "document" and f_id:
            await bot.send_document(chat_id=user_id, document=f_id, caption=msg_text, reply_markup=kb)
        else:
            await bot.send_message(chat_id=user_id, text=msg_text, reply_markup=kb)

# ----------------- CALLBACK CONTROL HUB -----------------
@dp.callback_query(F.data.startswith('btn_'))
async def handle_panels(callback_query: types.CallbackQuery, state: FSMContext):
    await callback_query.answer()
    data = callback_query.data
    
    if data == "btn_sotib_olish":
        kb = types.InlineKeyboardMarkup(inline_keyboard=[
            [types.InlineKeyboardButton(text="👤 @madiways", url="https://t.me/madiways")],
            [types.InlineKeyboardButton(text="💻 @Yusufxonpro", url="https://t.me/Yusufxonpro")]
        ])
        await callback_query.message.answer("🛒 <b>Guruhni sotib olish yoki hamkorlik bo'yicha adminlarga yozing:</b>", reply_markup=kb)
    elif data == "btn_add_start_msg":
        await callback_query.message.answer("⚙️ <b>GLOBAL START XABARINI YUBORING</b>\n\nIstalgan formatda rasm, video yoki matn yuborishingiz mumkin.")
        await state.set_state(MadiWayStates.kutish_global_start)
    elif data == "btn_kanal_tashlash":
        await callback_query.message.answer("📥 <b>Kanalga boradigan yukni yuboring:</b>")
        await state.set_state(MadiWayStates.kutish_kanal_yuk)
    elif data == "btn_hamma_topic":
        await callback_query.message.answer("💥 <b>Hamma guruh bo'limlariga (Topiclar) boradigan yukni yuboring:</b>")
        await state.set_state(MadiWayStates.kutish_hamma_topic_yuk)
    elif data == "btn_kanal_va_hamma":
        await callback_query.message.answer("🚀 <b>Ham kanalga, ham hamma guruhlarga boradigan yukni yuboring:</b>")
        await state.set_state(MadiWayStates.kutish_kanal_va_hamma_topic)
    elif data == "btn_bitta_topic":
        buttons = []
        for name, t_id in TOPICS.items():
            buttons.append(types.InlineKeyboardButton(text=name, callback_data=f"select_topic_{t_id}"))
        
        # Tugmalarni 2 qatordan taxlash
        inline_kb = [buttons[i:i + 2] for i in range(0, len(buttons), 2)]
        kb = types.InlineKeyboardMarkup(inline_keyboard=inline_kb)
        await callback_query.message.answer("📍 <b>Qaysi guruh bo'limiga yuk tashlamoqchisiz? Tanlang:</b>", reply_markup=kb)

@dp.callback_query(F.data.startswith('select_topic_'))
async def topic_selected(callback_query: types.CallbackQuery, state: FSMContext):
    await callback_query.answer()
    t_id = callback_query.data.split('_')[2]
    await state.update_data(target_topic_id=t_id)
    await callback_query.message.answer("📥 <b>Ushbu bo'lim uchun yukni yuboring:</b>")
    await state.set_state(MadiWayStates.kutish_bitta_topic_yuk)

# --- CUSTOM GLOBAL START SAVER ---
@dp.message_handler(MadiWayStates.kutish_global_start)
async def save_global_start_payload(message: types.Message, state: FSMContext):
    caption = message.html_text if message.text else (message.caption if message.caption else "")
    config = {"type": "text", "file_id": None, "text": caption}
    if message.photo:
        config["type"] = "photo"
        config["file_id"] = message.photo[-1].file_id
    elif message.video:
        config["type"] = "video"
        config["file_id"] = message.video.file_id
    elif message.document:
        config["type"] = "document"
        config["file_id"] = message.document.file_id
    save_start_settings(config)
    await message.answer("🔥 <b>Global start xabari muvaffaqiyatli saqlandi!</b>")
    await state.clear()

# --- YUKLARNI TARQATISH ---
@dp.message_handler(MadiWayStates.kutish_kanal_yuk)
async def process_channel_yuk(message: types.Message, state: FSMContext):
    msg_id = f"chan_{message.message_id}"
    text = message.html_text if message.text else (message.caption if message.caption else "")
    YUK_OMBORI[msg_id] = text
    
    short_text = text[:150] + "..." if len(text) > 150 else text
    caption = get_premium_caption(short_text)
    kb = get_channel_kb(msg_id)
    
    await forward_msg(CHANNEL_ID, message, caption, kb)
    await message.answer("✅ Kanalga yuborildi!")
    await state.clear()

@dp.message_handler(MadiWayStates.kutish_bitta_topic_yuk)
async def process_single_topic(message: types.Message, state: FSMContext):
    user_data = await state.get_data()
    t_id = int(user_data.get('target_topic_id'))
    text = message.html_text if message.text else (message.caption if message.caption else "")
    
    caption = get_premium_caption(text, "𝗣𝗥𝗘𝗠𝗜𝗨𝗠 𝗘𝗟𝗢𝗡")
    kb = get_channel_kb()
    
    await forward_msg(GROUP_ID, message, caption, kb, t_id)
    await message.answer("✅ Tanlangan bo'limga yuborildi!")
    await state.clear()

@dp.message_handler(MadiWayStates.kutish_hamma_topic_yuk)
async def process_all_topics(message: types.Message, state: FSMContext):
    text = message.html_text if message.text else (message.caption if message.caption else "")
    caption = get_premium_caption(text, "𝗚𝗟𝗢𝗕𝗔𝗟 𝗘𝗟𝗢𝗡")
    kb = get_channel_kb()
    
    for name, thread_id in TOPICS.items():
        try:
            await forward_msg(GROUP_ID, message, caption, kb, thread_id)
            await asyncio.sleep(0.3)
        except: continue
    await message.answer("✅ Barcha bo'limlarga tarqatildi!")
    await state.clear()

@dp.message_handler(MadiWayStates.kutish_kanal_va_hamma_topic)
async def process_channel_and_all_topics(message: types.Message, state: FSMContext):
    text = message.html_text if message.text else (message.caption if message.caption else "")
    caption = get_premium_caption(text, "𝗠𝗔𝗫𝗦𝗨𝗦 𝗧𝗜𝗭𝗜𝗠 𝗘𝗟𝗢𝗡𝗜")
    kb = get_channel_kb()
    
    try:
        await forward_msg(CHANNEL_ID, message, caption, kb)
    except: pass
        
    for name, thread_id in TOPICS.items():
        try:
            await forward_msg(GROUP_ID, message, caption, kb, thread_id)
            await asyncio.sleep(0.3)
        except: continue
    await message.answer("🚀 Kanal va guruhlarga yetkazildi!")
    await state.clear()

# --- YUKNI TO'LIQ KO'RISH ---
@dp.callback_query(F.data.startswith('show_full_'))
async def show_full_yuk(callback_query: types.CallbackQuery):
    msg_id = callback_query.data.replace("show_full_", "")
    full_text = YUK_OMBORI.get(msg_id, "⚠️ To'liq ma'lumot keshdan o'chib ketgan.")
    await callback_query.answer()
    
    full_caption = get_premium_caption(full_text, "𝗧𝗢'𝗟𝗜𝗤 𝗠𝗔'𝗟𝗨𝗠𝗢𝗧")
    kb = get_channel_kb()
    
    try:
        if callback_query.message.text:
            await callback_query.message.edit_text(text=full_caption, reply_markup=kb)
        else:
            await callback_query.message.edit_caption(caption=full_caption, reply_markup=kb)
    except:
        await callback_query.message.answer(full_caption, reply_markup=kb)

# --- TRANSMITTER ---
async def forward_msg(chat_id, message, caption, kb, thread_id=None):
    if message.photo:
        await bot.send_photo(chat_id, message.photo[-1].file_id, caption=caption, reply_markup=kb, message_thread_id=thread_id)
    elif message.video:
        await bot.send_video(chat_id, message.video.file_id, caption=caption, reply_markup=kb, message_thread_id=thread_id)
    elif message.document:
        await bot.send_document(chat_id, message.document.file_id, caption=caption, reply_markup=kb, message_thread_id=thread_id)
    else:
        await bot.send_message(chat_id, caption, reply_markup=kb, message_thread_id=thread_id)

async def main():
    await dp.start_polling(bot)

if __name__ == '__main__':
    asyncio.run(main())
