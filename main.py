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

BOT_TOKEN = "8724439262:AAFGNuQQ4IxdqitlcCEtkHLsvyFwSPg_b1c"
CHANNEL_USER = "MADIWAYy"  # Kanal username
GROUP_ID = "-1002130310815" # Guruh IDsi
CHANNEL_ID = "-1002120000000" # Kanal IDsi

# Admin shaxsiy Telegram ID raqamingizni bu yerga yozing:
ADMIN_ID = 123456789  

bot = Bot(token=BOT_TOKEN, parse_mode="HTML")
storage = MemoryStorage()
dp = Dispatcher(bot, storage=storage)

uzb_tz = pytz.timezone('Asia/Tashkent')
START_SETTINGS_FILE = "global_start_settings.json"

DEFAULT_TEXT = (
    "⭐️ <b>𝗠𝗔𝗗𝗜𝗪𝗔𝗬 | 𝗟𝗢𝗚𝗜𝗦𝗧𝗜𝗖𝗦 𝗦𝗬𝗦𝗧𝗘𝗠</b> ⭐️\n"
    "───────────────────────\n"
    "Tizimga xush kelibsiz! Eng tezkor va ishonchli yuklar platformasi.\n"
    "Yuk tashlash va boshqarish paneli faol holatda."
)

def load_start_settings():
    if os.path.exists(START_SETTINGS_FILE):
        with open(START_SETTINGS_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {"type": "photo", "file_id": None, "text": DEFAULT_TEXT}

def save_start_settings(data):
    with open(START_SETTINGS_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=4)

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

# ----------------- ADMIN/FOYDALANUVCHI START -----------------
@dp.message_handler(commands=['start'], state="*")
async def intelligent_start(message: types.Message, state: FSMContext):
    await state.finish()
    user_id = message.from_user.id
    start_data = load_start_settings()
    
    if user_id == ADMIN_ID:
        kb = types.InlineKeyboardMarkup(row_width=1)
        kb.add(
            types.InlineKeyboardButton(text="⚙️ Start uchun xabar qo'shish (GLOBAL)", callback_data="btn_add_start_msg"),
            types.InlineKeyboardButton(text="⭐️ Kanalga yuk tashlash", callback_data="btn_kanal_tashlash"),
            types.InlineKeyboardButton(text="⭐️ Guruh Topiclariga yuk tashlash", callback_data="btn_topics_tashlash"),
            types.InlineKeyboardButton(text="✨ Alohida bitta Topicga yuborish", callback_data="btn_bitta_topic"),
            types.InlineKeyboardButton(text="💥 Hammasiga bittada yuborish (Topiclar)", callback_data="btn_hamma_topic"),
            types.InlineKeyboardButton(text="🚀 Kanal va Hamma Topicga birda yuborish", callback_data="btn_kanal_va_hamma")
        )
        await message.answer(
            "💻 <b><b>𝗠𝗔𝗗𝗜𝗪𝗔𝗬 | 𝗔𝗗𝗠𝗜𝗡 𝗣𝗔𝗡𝗘𝗟 v3.0</b></b>\n"
            "───────────────────────\n"
            "Boshqaruv paneli faol:", 
            reply_markup=kb
        )
    else:
        kb = types.InlineKeyboardMarkup(row_width=1)
        kb.add(
            types.InlineKeyboardButton(text="📢 Kanalga qo'shilish", url=f"https://t.me/{CHANNEL_USER}"),
            types.InlineKeyboardButton(text="🛒 Guruhni sotib olish", callback_data="btn_sotib_olish")
        )
        
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
            banner_path = "madiway_banner.png"
            if os.path.exists(banner_path):
                with open(banner_path, "rb") as photo:
                    await bot.send_photo(chat_id=user_id, photo=photo, caption=msg_text, reply_markup=kb)
            else:
                await bot.send_message(chat_id=user_id, text=msg_text, reply_markup=kb)

# ----------------- CALLBACK CONTROL HUB -----------------
@dp.callback_query_handler(lambda c: c.data.startswith('btn_'), state="*")
async def handle_panels(callback_query: types.CallbackQuery, state: FSMContext):
    await callback_query.answer()
    data = callback_query.data
    
    if data == "btn_add_start_msg":
        await callback_query.message.answer("📥 <i>Xabarni multimedia yoki matn holatida hozir yuboring...</i>")
        await MadiWayStates.kutish_global_start.set()
    elif data == "btn_kanal_tashlash":
        await callback_query.message.answer("📥 <b>Yukni tashang...</b>")
        await MadiWayStates.kutish_kanal_yuk.set()
    elif data == "btn_topics_tashlash" or data == "btn_bitta_topic":
        kb = types.InlineKeyboardMarkup(row_width=2)
        for name, t_id in TOPICS.items():
            kb.insert(types.InlineKeyboardButton(text=name, callback_data=f"select_topic_{t_id}"))
        await callback_query.message.answer("📍 <b>Qaysi guruh bo'limiga (Topic) yuk tashlamoqchisiz? Tanlang:</b>", reply_markup=kb)
        if data == "btn_topics_tashlash":
            await state.update_data(mode="qisqa")
        else:
            await state.update_data(mode="premium_bitta")
    elif data == "btn_hamma_topic":
        await callback_query.message.answer("💥 <b>Hamma guruh bo'limlariga (Topiclar) boradigan xabarni tashang...</b>")
        await MadiWayStates.kutish_hamma_topic_yuk.set()
    elif data == "btn_kanal_va_hamma":
        await callback_query.message.answer("🚀 <b>Ham kanalga, ham hamma guruh bo'limlariga baravar ketadigan xabarni tashang...</b>")
        await MadiWayStates.kutish_kanal_va_hamma_topic.set()
    elif data == "btn_sotib_olish":
        kb = types.InlineKeyboardMarkup(row_width=2)
        kb.add(
            types.InlineKeyboardButton(text="👤 @madiways", url="https://t.me/madiways"),
            types.InlineKeyboardButton(text="💻 @yusufxonpro", url="https://t.me/yusufxonpro")
        )
        await callback_query.message.answer("🛒 <b>Guruhni sotib olish uchun adminni tanlang:</b>", reply_markup=kb)

@dp.callback_query_handler(lambda c: c.data.startswith('select_topic_'), state="*")
async def topic_selected(callback_query: types.CallbackQuery, state: FSMContext):
    await callback_query.answer()
    t_id = callback_query.data.split('_')[2]
    await state.update_data(target_topic_id=t_id)
    await callback_query.message.answer("📥 <b>Ushbu bo'lim uchun yuk/xabar matnini tashang...</b>")
    await MadiWayStates.kutish_bitta_topic_yuk.set()

# START XABARINI SAQLASH
@dp.message_handler(content_types=['text', 'photo', 'video', 'document'], state=MadiWayStates.kutish_global_start)
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
    await state.finish()


# ----------------- MULTIMEDIA VA MATN QABUL QILISH TIZIMLARI -----------------

# 1. KANALGA YUK TASHALSA
@dp.message_handler(content_types=['text', 'photo', 'video', 'document'], state=MadiWayStates.kutish_kanal_yuk)
async def process_channel_yuk(message: types.Message, state: FSMContext):
    status_msg = await message.answer("⏳ <code>1 soniya kuting, ketmoqda...</code>")
    await asyncio.sleep(1)
    await status_msg.delete()
    
    msg_id = f"chan_{message.message_id}"
    text = message.html_text if message.text else (message.caption if message.caption else "")
    YUK_OMBORI[msg_id] = text
    
    short_text = text[:120] + "...\n\n<i>(Yuk ma'lumotlari qisqartirildi)</i>" if len(text) > 120 else text
    now = datetime.now(uzb_tz)
    sana_soat = now.strftime("📅 %Y-%m-%d  🕒 %H:%M")
    
    # 🌟 Tavsif ostiga kanal linki matn shaklida mahkamlandi
    premium_caption = (
        f"⭐️ <b>𝗠𝗔𝗗𝗜𝗪𝗔𝗬 | 𝗬𝗨𝗞 𝗘𝗟𝗢𝗡𝗜</b>\n"
        f"───────────────────────\n"
        f"{short_text}\n"
        f"───────────────────────\n"
        f"⏳ Tashilgan vaqt: {sana_soat}\n"
        f"📢 Kanalimiz: https://t.me/{CHANNEL_USER}"
    )
    
    kb = types.InlineKeyboardMarkup(row_width=1)
    kb.add(
        types.InlineKeyboardButton(text="⭐️ Yukni to'liq ko'rish", callback_data=f"show_full_{msg_id}"),
        types.InlineKeyboardButton(text="📢 Kanalga qo'shilish", url=f"https://t.me/{CHANNEL_USER}")
    )
    
    await forward_premium_message(chat_id=CHANNEL_ID, message=message, caption=premium_caption, reply_markup=kb)
    await message.answer("✅ Yuk muvaffaqiyatli kanalga joylandi!")
    await state.finish()

# 2. BITTA TOPICGA TASHALSA
@dp.message_handler(content_types=['text', 'photo', 'video', 'document'], state=MadiWayStates.kutish_bitta_topic_yuk)
async def process_single_topic(message: types.Message, state: FSMContext):
    user_data = await state.get_data()
    t_id = int(user_data.get('target_topic_id'))
    mode = user_data.get('mode')
    
    status_msg = await message.answer("⏳ <code>1 soniya kuting, ketmoqda...</code>")
    await asyncio.sleep(1)
    await status_msg.delete()
    
    msg_id = f"top_{message.message_id}"
    text = message.html_text if message.text else (message.caption if message.caption else "")
    YUK_OMBORI[msg_id] = text
    
    now = datetime.now(uzb_tz)
    sana_soat = now.strftime("📅 %Y-%m-%d  🕒 %H:%M")
    
    kb = types.InlineKeyboardMarkup(row_width=1)
    kb.add(types.InlineKeyboardButton(text="📢 Kanalga qo'shilish", url=f"https://t.me/{CHANNEL_USER}"))
    
    # 🌟 Guruh ichidagi bo'limlarga ham tavsif ostiga kanal linki tushadi
    if mode == "premium_bitta":
        premium_caption = (
            f"⭐️ <b>𝗣𝗥𝗘𝗠𝗜𝗨𝗠 𝗠𝗔𝗗𝗜𝗪𝗔𝗬 𝗘𝗟𝗢𝗡</b> ⭐️\n"
            f"───────────────────────\n"
            f"{text}\n"
            f"───────────────────────\n"
            f"⏳ Vaqt: {sana_soat}\n"
            f"📢 Kanalimiz: https://t.me/{CHANNEL_USER}"
        )
    else:
        short_text = text[:120] + "..." if len(text) > 120 else text
        premium_caption = (
            f"⭐️ <b>𝗠𝗔𝗗𝗜𝗪𝗔𝗬 | 𝗤𝗜𝗦𝗤𝗔𝗖𝗛𝗔 𝗬𝗨𝗞</b>\n"
            f"───────────────────────\n"
            f"{short_text}\n"
            f"───────────────────────\n"
            f"⏳ Vaqt: {sana_soat}\n"
            f"📢 Kanalimiz: https://t.me/{CHANNEL_USER}"
        )
        kb.insert(types.InlineKeyboardButton(text="⭐️ Yukni to'liq ko'rish", callback_data=f"show_full_{msg_id}"))

    await forward_premium_message(chat_id=GROUP_ID, message=message, caption=premium_caption, reply_markup=kb, thread_id=t_id)
    await message.answer("✅ Tanlangan guruh bo'limiga muvaffaqiyatli ketdi!")
    await state.finish()

# 3. HAMMA TOPICGA BITTADA TASHALSA
@dp.message_handler(content_types=['text', 'photo', 'video', 'document'], state=MadiWayStates.kutish_hamma_topic_yuk)
async def process_all_topics(message: types.Message, state: FSMContext):
    status_msg = await message.answer("⏳ <code>1 soniya kuting...</code>")
    await asyncio.sleep(1)
    await status_msg.delete()
    
    text = message.html_text if message.text else (message.caption if message.caption else "")
    now = datetime.now(uzb_tz)
    sana_soat = now.strftime("📅 %Y-%m-%d  🕒 %H:%M")
    
    premium_caption = (
        f"⭐️ <b>𝗠𝗔𝗗𝗜𝗪𝗔𝗬 | 𝗚𝗟𝗢𝗕𝗔𝗟 𝗘𝗟𝗢𝗡</b> ⭐️\n"
        f"───────────────────────\n"
        f"{text}\n"
        f"───────────────────────\n"
        f"⏳ Vaqt: {sana_soat}\n"
        f"📢 Kanalimiz: https://t.me/{CHANNEL_USER}"
    )
    kb = types.InlineKeyboardMarkup().add(types.InlineKeyboardButton(text="📢 Kanalga qo'shilish", url=f"https://t.me/{CHANNEL_USER}"))
    
    for name, thread_id in TOPICS.items():
        try:
            await forward_premium_message(chat_id=GROUP_ID, message=message, caption=premium_caption, reply_markup=kb, thread_id=thread_id)
            await asyncio.sleep(0.2)
        except Exception as e:
            logging.error(f"{name} bo'limiga xabar ketmadi: {e}")
            
    await message.answer("✅ Barcha guruh bo'limlariga tarqatildi!")
    await state.finish()

# 4. KANAL VA HAMMA TOPICGA BARAVAR TASHALSA
@dp.message_handler(content_types=['text', 'photo', 'video', 'document'], state=MadiWayStates.kutish_kanal_va_hamma_topic)
async def process_channel_and_all_topics(message: types.Message, state: FSMContext):
    status_msg = await message.answer("⏳ <code>1 soniya kuting...</code>")
    await asyncio.sleep(1)
    await status_msg.delete()
    
    text = message.html_text if message.text else (message.caption if message.caption else "")
    now = datetime.now(uzb_tz)
    sana_soat = now.strftime("📅 %Y-%m-%d  🕒 %H:%M")
    
    premium_caption = (
        f"⭐️ <b>𝗠𝗔𝗗𝗜𝗪𝗔𝗬 | 𝗠𝗔𝗫𝗦𝗨𝗦 𝗧𝗜𝗭𝗜𝗠 𝗘𝗟𝗢𝗡Ｉ</b> ⭐️\n"
        f"───────────────────────\n"
        f"{text}\n"
        f"───────────────────────\n"
        f"⏳ Vaqt: {sana_soat}\n"
        f"📢 Kanalimiz: https://t.me/{CHANNEL_USER}"
    )
    kb = types.InlineKeyboardMarkup().add(types.InlineKeyboardButton(text="📢 Kanalga qo'shilish", url=f"https://t.me/{CHANNEL_USER}"))
    
    try:
        await forward_premium_message(chat_id=CHANNEL_ID, message=message, caption=premium_caption, reply_markup=kb)
    except Exception as e:
        logging.error(f"Kanalga ketmadi: {e}")
        
    for name, thread_id in TOPICS.items():
        try:
            await forward_premium_message(chat_id=GROUP_ID, message=message, caption=premium_caption, reply_markup=kb, thread_id=thread_id)
            await asyncio.sleep(0.2)
        except Exception as e:
            logging.error(f"{name} topigiga ketmadi: {e}")
            
    await message.answer("🚀 Ham kanalga, ham barcha guruh bo'limlariga yetkazildi!")
    await state.finish()

# ----------------- YUKNI TO'LIQ KO'RISH CALLBACK TIZIMI -----------------
@dp.callback_query_handler(lambda c: c.data.startswith('show_full_'), state="*")
async def show_full_yuk(callback_query: types.CallbackQuery):
    msg_id = callback_query.data.replace("show_full_", "")
    full_text = YUK_OMBORI.get(msg_id, "⚠️ To'liq ma'lumot topilmadi yoki kesh tozalangan.")
    await callback_query.answer("⭐️ Yuk ma'lumotlari to'liq yuklandi!", show_alert=False)
    now = datetime.now(uzb_tz)
    sana_soat = now.strftime("📅 %Y-%m-%d  🕒 %H:%M")
    
    # 🌟 To'liq yuk ko'rinishida ham ostiga kanal linki tushadi
    full_caption = (
        f"⭐️ <b>𝗠𝗔𝗗𝗜𝗪𝗔𝗬 | 𝗧𝗢'𝗟𝗜𝗤 𝗠𝗔'𝗟𝗨𝗠𝗢𝗧</b>\n"
        f"───────────────────────\n"
        f"{full_text}\n"
        f"───────────────────────\n"
        f"⏳ Sana: {sana_soat}\n"
        f"📢 Kanalimiz: https://t.me/{CHANNEL_USER}"
    )
    
    try:
        kb = types.InlineKeyboardMarkup().add(types.InlineKeyboardButton(text="📢 Kanalga qo'shilish", url=f"https://t.me/{CHANNEL_USER}"))
        if callback_query.message.text:
            await callback_query.message.edit_text(text=full_caption, reply_markup=kb)
        else:
            await callback_query.message.edit_caption(caption=full_caption, reply_markup=kb)
    except Exception as e:
        await callback_query.message.answer(full_caption)

# ----------------- TRANSMITTER HELPER -----------------
async def forward_premium_message(chat_id, message: types.Message, caption, reply_markup, thread_id=None):
    if message.photo:
        await bot.send_photo(chat_id=chat_id, photo=message.photo[-1].file_id, caption=caption, reply_markup=reply_markup, message_thread_id=thread_id)
    elif message.video:
        await bot.send_video(chat_id=chat_id, video=message.video.file_id, caption=caption, reply_markup=reply_markup, message_thread_id=thread_id)
    elif message.document:
        await bot.send_document(chat_id=chat_id, document=message.document.file_id, caption=caption, reply_markup=reply_markup, message_thread_id=thread_id)
    else:
        await bot.send_message(chat_id=chat_id, text=caption, reply_markup=reply_markup, message_thread_id=thread_id)

if __name__ == '__main__':
    executor.start_polling(dp, skip_updates=True)
