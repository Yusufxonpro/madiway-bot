import json
import logging
import asyncio
import os
from datetime import datetime
import pytz
from aiogram import Bot, Dispatcher, types
from aiogram.utils import executor
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters.state import State, StatesGroup
from aiogram.contrib.fsm_storage.memory import MemoryStorage

# Loglarni sozlash
logging.basicConfig(level=logging.INFO)

# --- SOZLAMALAR ---
BOT_TOKEN = "8724439262:AAFGNuQQ4IxdqitlcCEtkHLsvyFwSPg_b1c"
CHANNEL_USER = "MADIWAYy" 
GROUP_ID = "-1002130310815"
CHANNEL_ID = "-1002120000000"

# Siz bergan yangi IDlar
ADMIN_ID = 6977836294  # Yusufxonpro ID
MADIWAY_ADMIN_ID = 8112179116 # madiways ID

bot = Bot(token=BOT_TOKEN, parse_mode="HTML")
storage = MemoryStorage()
dp = Dispatcher(bot, storage=storage)

uzb_tz = pytz.timezone('Asia/Tashkent')
START_SETTINGS_FILE = "global_start_settings.json"

# --- YUK MATNI FORMATI ---
def get_premium_caption(main_text, status_label="𝗬𝗨𝗞 𝗘𝗟𝗢𝗡𝗜"):
    now = datetime.now(uzb_tz)
    # 12-soatlik format (AM/PM)
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
    kb = types.InlineKeyboardMarkup(row_width=1)
    if msg_id:
        kb.add(types.InlineKeyboardButton(text="⭐️ Yukni to'liq ko'rish", callback_data=f"show_full_{msg_id}"))
    kb.add(types.InlineKeyboardButton(text="📢 Kanalga qo'shilish", url=f"https://t.me/{CHANNEL_USER}"))
    return kb

# --- QOLGAN FUNKSIYALAR ---
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

@dp.message_handler(commands=['start'], state="*")
async def intelligent_start(message: types.Message, state: FSMContext):
    await state.finish()
    if message.from_user.id in [ADMIN_ID, MADIWAY_ADMIN_ID]:
        kb = types.InlineKeyboardMarkup(row_width=1)
        kb.add(
            types.InlineKeyboardButton(text="⚙️ Start xabarni sozlash", callback_data="btn_add_start_msg"),
            types.InlineKeyboardButton(text="⭐️ Kanalga yuk tashlash", callback_data="btn_kanal_tashlash"),
            types.InlineKeyboardButton(text="✨ Alohida bitta Topicga", callback_data="btn_bitta_topic"),
            types.InlineKeyboardButton(text="💥 Hammasiga bittada", callback_data="btn_hamma_topic"),
            types.InlineKeyboardButton(text="🚀 Kanal + Hamma Topic", callback_data="btn_kanal_va_hamma")
        )
        await message.answer("💻 <b>MADIWAY ADMIN PANEL</b>", reply_markup=kb)
    else:
        # Oddiy foydalanuvchi uchun start
        kb = get_channel_kb()
        kb.add(types.InlineKeyboardButton(text="🛒 Guruhni sotib olish", callback_data="btn_sotib_olish"))
        await message.answer("Tizimga xush kelibsiz!", reply_markup=kb)

@dp.callback_query_handler(lambda c: c.data.startswith('btn_'), state="*")
async def handle_panels(callback_query: types.CallbackQuery, state: FSMContext):
    data = callback_query.data
    if data == "btn_sotib_olish":
        kb = types.InlineKeyboardMarkup(row_width=1)
        kb.add(
            types.InlineKeyboardButton(text="👤 @madiways", url="https://t.me/madiways"),
            types.InlineKeyboardButton(text="💻 @Yusufxonpro", url="https://t.me/Yusufxonpro")
        )
        await callback_query.message.answer("🛒 Sotib olish uchun adminlar:", reply_markup=kb)
    elif data == "btn_kanal_tashlash":
        await callback_query.message.answer("📥 Kanal uchun yukni yuboring...")
        await MadiWayStates.kutish_kanal_yuk.set()
    elif data == "btn_hamma_topic":
        await callback_query.message.answer("📥 Hamma topiclar uchun yukni yuboring...")
        await MadiWayStates.kutish_hamma_topic_yuk.set()
    elif data == "btn_bitta_topic":
        kb = types.InlineKeyboardMarkup(row_width=2)
        for name, t_id in TOPICS.items():
            kb.insert(types.InlineKeyboardButton(text=name, callback_data=f"select_topic_{t_id}"))
        await callback_query.message.answer("📍 Topicni tanlang:", reply_markup=kb)

@dp.callback_query_handler(lambda c: c.data.startswith('select_topic_'), state="*")
async def topic_selected(callback_query: types.CallbackQuery, state: FSMContext):
    t_id = callback_query.data.split('_')[2]
    await state.update_data(target_topic_id=t_id)
    await callback_query.message.answer("📥 Yuk matnini yuboring...")
    await MadiWayStates.kutish_bitta_topic_yuk.set()

# --- YUKLARNI YUBORISH ---
@dp.message_handler(content_types=['text', 'photo', 'video', 'document'], state=MadiWayStates.kutish_kanal_yuk)
async def process_channel_yuk(message: types.Message, state: FSMContext):
    msg_id = f"chan_{message.message_id}"
    text = message.html_text if message.text else (message.caption if message.caption else "")
    YUK_OMBORI[msg_id] = text
    
    short_text = text[:150] + "..." if len(text) > 150 else text
    caption = get_premium_caption(short_text)
    kb = get_channel_kb(msg_id)
    
    await forward_msg(CHANNEL_ID, message, caption, kb)
    await message.answer("✅ Kanalga yuborildi!")
    await state.finish()

@dp.message_handler(content_types=['text', 'photo', 'video', 'document'], state=MadiWayStates.kutish_hamma_topic_yuk)
async def process_all_topics(message: types.Message, state: FSMContext):
    text = message.html_text if message.text else (message.caption if message.caption else "")
    caption = get_premium_caption(text, "𝗚𝗟𝗢𝗕𝗔𝗟 𝗘𝗟𝗢𝗡")
    kb = get_channel_kb()
    
    for name, thread_id in TOPICS.items():
        try:
            await forward_msg(GROUP_ID, message, caption, kb, thread_id)
            await asyncio.sleep(0.3)
        except: continue
    await message.answer("✅ Hammasiga yuborildi!")
    await state.finish()

async def forward_msg(chat_id, message, caption, kb, thread_id=None):
    if message.photo:
        await bot.send_photo(chat_id, message.photo[-1].file_id, caption=caption, reply_markup=kb, message_thread_id=thread_id)
    elif message.video:
        await bot.send_video(chat_id, message.video.file_id, caption=caption, reply_markup=kb, message_thread_id=thread_id)
    elif message.document:
        await bot.send_document(chat_id, message.document.file_id, caption=caption, reply_markup=kb, message_thread_id=thread_id)
    else:
        await bot.send_message(chat_id, caption, reply_markup=kb, message_thread_id=thread_id)

if __name__ == '__main__':
    executor.start_polling(dp, skip_updates=True)
