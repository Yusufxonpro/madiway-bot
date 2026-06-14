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
from aiogram.client.default import DefaultBotProperties # Yangi aiogram uchun kerak

# Loglarni sozlash
logging.basicConfig(level=logging.INFO)

# --- SOZLAMALAR ---
BOT_TOKEN = "8724439262:AAFGNuQQ4IxdqitlcCEtkHLsvyFwSPg_b1c"
CHANNEL_USER = "MADIWAYy" 
GROUP_ID = "-1002130310815"
CHANNEL_ID = "-1002120000000"

ADMIN_ID = 6977836294         
MADIWAY_ADMIN_ID = 8112179116  

# YANGI AIOGRAM STANDARTI (Xatoni tuzatuvchi qism)
bot = Bot(
    token=BOT_TOKEN, 
    default=DefaultBotProperties(parse_mode="HTML")
)
dp = Dispatcher(storage=MemoryStorage())

uzb_tz = pytz.timezone('Asia/Tashkent')
START_SETTINGS_FILE = "global_start_settings.json"

DEFAULT_TEXT = (
    "⭐️ <b>𝗠𝗔𝗗𝗜𝗪𝗔𝗬 | 𝗟𝗢𝗚𝗜𝗦𝗧𝗜𝗖𝗦 𝗦𝗬𝗦𝗧𝗘𝗠</b> ⭐️\n"
    "───────────────────────\n"
    "Tizimga xush kelibsiz! Eng tezkor va ishonchli yuklar platformasi.\n"
    "Yuk tashlash va boshqarish paneli faol holatda."
)

# --- GLOBAL START SOZLAMALARI ---
def load_start_settings():
    if os.path.exists(START_SETTINGS_FILE):
        with open(START_SETTINGS_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {"type": "text", "file_id": None, "text": DEFAULT_TEXT}

def save_start_settings(data):
    with open(START_SETTINGS_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=4)

# --- FORMATLASH ---
def get_premium_caption(main_text, status_label="𝗬𝗨𝗞 𝗘𝗟𝗢𝗡𝗜"):
    now = datetime.now(uzb_tz)
    sana_soat = now.strftime("📅 %Y-%m-%d  🕒 %I:%M %p") 
    return (
        f"⭐️ <b>𝗠𝗔𝗗𝗜𝗪𝗔𝗬 | {status_label}</b> ⭐️\n"
        f"───────────────────────\n"
        f"{main_text}\n"
        f"───────────────────────\n"
        f"⏳ Vaqt: {sana_soat}\n"
        f"📢 Kanalimiz: https://t.me/{CHANNEL_USER}"
    )

def get_channel_kb(msg_id=None):
    buttons = []
    if msg_id:
        buttons.append([types.InlineKeyboardButton(text="⭐️ Yukni to'liq ko'rish", callback_data=f"show_full_{msg_id}")])
    buttons.append([types.InlineKeyboardButton(text="📢 Kanalga qo'shilish", url=f"https://t.me/{CHANNEL_USER}")])
    return types.InlineKeyboardMarkup(inline_keyboard=buttons)

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

# --- HANDLERS ---
@dp.message(Command("start"))
async def start_cmd(message: types.Message, state: FSMContext):
    await state.clear()
    user_id = message.from_user.id
    start_data = load_start_settings()
    
    if user_id in [ADMIN_ID, MADIWAY_ADMIN_ID]:
        kb = types.InlineKeyboardMarkup(inline_keyboard=[
            [types.InlineKeyboardButton(text="⚙️ Start sozlash", callback_data="btn_add_start_msg")],
            [types.InlineKeyboardButton(text="⭐️ Kanalga yuk", callback_data="btn_kanal_tashlash")],
            [types.InlineKeyboardButton(text="✨ Bitta Topicga", callback_data="btn_bitta_topic")],
            [types.InlineKeyboardButton(text="💥 Hammasiga", callback_data="btn_hamma_topic")],
            [types.InlineKeyboardButton(text="🚀 Kanal + Hammasi", callback_data="btn_kanal_va_hamma")]
        ])
        await message.answer("💻 <b>𝗔𝗗𝗠𝗜𝗡 𝗣𝗔𝗡𝗘𝗟</b>", reply_markup=kb)
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
        await callback.message.answer("⚙️ Yangi start xabarni yuboring (rasm yoki matn):")
        await state.set_state(MadiWayStates.kutish_global_start)
    elif callback.data == "btn_kanal_tashlash":
        await callback.message.answer("📥 Kanal yukini yuboring:")
        await state.set_state(MadiWayStates.kutish_kanal_yuk)
    elif callback.data == "btn_hamma_topic":
        await callback.message.answer("💥 Hammasiga yuboring:")
        await state.set_state(MadiWayStates.kutish_hamma_topic_yuk)
    elif callback.data == "btn_bitta_topic":
        btns = [types.InlineKeyboardButton(text=n, callback_data=f"select_topic_{id}") for n, id in TOPICS.items()]
        kb = types.InlineKeyboardMarkup(inline_keyboard=[btns[i:i+2] for i in range(0, len(btns), 2)])
        await callback.message.answer("📍 Bo'limni tanlang:", reply_markup=kb)

@dp.callback_query(F.data.startswith('select_topic_'))
async def topic_sel(callback: types.CallbackQuery, state: FSMContext):
    await state.update_data(target_topic_id=callback.data.split('_')[2])
    await callback.message.answer("📥 Yukni yuboring:")
    await state.set_state(MadiWayStates.kutish_bitta_topic_yuk)

# --- SAVERS & FORWARDERS ---
@dp.message(MadiWayStates.kutish_global_start)
async def save_start(message: types.Message, state: FSMContext):
    txt = message.html_text or message.caption or ""
    cfg = {"type": "text", "file_id": None, "text": txt}
    if message.photo: cfg.update({"type": "photo", "file_id": message.photo[-1].file_id})
    elif message.video: cfg.update({"type": "video", "file_id": message.video.file_id})
    save_start_settings(cfg)
    await message.answer("✅ Start xabari saqlandi!")
    await state.clear()

async def send_all(chat_id, message, caption, kb, t_id=None):
    if message.photo: await bot.send_photo(chat_id, message.photo[-1].file_id, caption=caption, reply_markup=kb, message_thread_id=t_id)
    elif message.video: await bot.send_video(chat_id, message.video.file_id, caption=caption, reply_markup=kb, message_thread_id=t_id)
    else: await bot.send_message(chat_id, caption, reply_markup=kb, message_thread_id=t_id)

@dp.message(MadiWayStates.kutish_kanal_yuk)
async def chan_yuk(message: types.Message, state: FSMContext):
    txt = message.html_text or message.caption or ""
    m_id = f"c_{message.message_id}"
    YUK_OMBORI[m_id] = txt
    cap = get_premium_caption(txt[:150] + "...")
    await send_all(CHANNEL_ID, message, cap, get_channel_kb(m_id))
    await message.answer("✅ Kanalga ketdi!")
    await state.clear()

@dp.message(MadiWayStates.kutish_hamma_topic_yuk)
async def all_yuk(message: types.Message, state: FSMContext):
    cap = get_premium_caption(message.html_text or message.caption or "")
    for n, tid in TOPICS.items():
        try: await send_all(GROUP_ID, message, cap, get_channel_kb(), tid); await asyncio.sleep(0.3)
        except: continue
    await message.answer("✅ Hammasiga yuborildi!")
    await state.clear()

@dp.callback_query(F.data.startswith('show_full_'))
async def full(cb: types.CallbackQuery):
    txt = YUK_OMBORI.get(cb.data.replace("show_full_", ""), "O'chib ketgan")
    cap = get_premium_caption(txt, "𝗧𝗢'𝗟𝗜𝗤")
    try: await cb.message.edit_caption(caption=cap, reply_markup=get_channel_kb())
    except: await cb.message.answer(cap)

async def main():
    await dp.start_polling(bot)

if __name__ == '__main__':
    asyncio.run(main())
