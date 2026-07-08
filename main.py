import os
import sqlite3
from aiogram import Bot, Dispatcher, executor, types
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters.state import State, StatesGroup

# --- BOT SOZLAMALARI ---
TOKEN = "YOUR_BOT_TOKEN"
ADMIN_ID = 123456789  # O'zingizning Telegram ID'ngiz

bot = Bot(token=TOKEN, parse_mode=types.ParseMode.HTML)
storage = MemoryStorage()
dp = Dispatcher(bot, storage=storage)

# --- SQLITE BAZA (VIP a'zolar bot o'chib yonsa ham o'chib ketmaydi) ---
conn = sqlite3.connect("bot_data.db")
cursor = conn.cursor()
cursor.execute("""
CREATE TABLE IF NOT EXISTS vips (
    user_id INTEGER PRIMARY KEY,
    status TEXT DEFAULT 'premium'
)
""")
conn.commit()

# --- FSM STATES (Holatlar) ---
class BotStates(StatesGroup):
    waiting_for_madiway_pics = State()
    waiting_for_intl_pics = State()
    waiting_for_music_cover = State()
    waiting_for_music_file = State()

# --- REPLI VA INLINE KLAVIATURALAR ---
def main_menu():
    keyboard = types.ReplyKeyboardMarkup(resize_keyboard=True)
    keyboard.row(types.KeyboardButton("🔥 Madiway"), types.KeyboardButton("🌍 International"))
    keyboard.row(types.KeyboardButton("🎵 Musiqa Yuklash"), types.KeyboardButton("📊 Statistika"))
    return keyboard

def madiway_inline():
    keyboard = types.InlineKeyboardMarkup(row_width=1)
    keyboard.add(
        types.InlineKeyboardButton("📢 Madiway Kanalga", callback_data="send_madiway_channel"),
        types.InlineKeyboardButton("💬 Madiway Guruhga", callback_data="send_madiway_group")
    )
    return keyboard

def intl_inline():
    keyboard = types.InlineKeyboardMarkup(row_width=1)
    keyboard.add(
        types.InlineKeyboardButton("📢 International Kanalga", callback_data="send_intl_channel"),
        types.InlineKeyboardButton("💬 International Guruhga", callback_data="send_intl_group")
    )
    return keyboard

# Rasmlarni eslab qolish uchun kesh (Global o'zgaruvchilar)
madiway_media_group = {}
intl_media_group = {}
user_covers = {}

# === 1. GURUHNI TOZALASH (KILO KIYIM GURUHI UCHUN) ===
@dp.message_handler(content_types=[types.ContentType.NEW_CHAT_MEMBERS, types.ContentType.LEFT_CHAT_MEMBER])
async def clean_group_messages(message: types.Message):
    try:
        await message.delete()
    except Exception:
        pass

# --- START BUYRUG'I ---
@dp.message_handler(commands=['start'])
async def start_cmd(message: types.Message):
    await message.answer("👋 Tizimga xush kelibsiz! Kerakli bo'limni tanlang:", reply_markup=main_menu())

# === 2. MADIWAY TUGMASI (RASMNI 1 MARTA SO'RAYDI, MAKS 10 TA) ===
@dp.message_handler(lambda message: message.text == "🔥 Madiway")
async def madiway_start(message: types.Message, state: FSMContext):
    user_id = message.from_user.id
    if user_id in madiway_media_group and madiway_media_group[user_id]:
        # Rasm oldin yuborilgan bo'lsa, qayta so'ramaydi, to'g'ridan-to'g'ri menyu chiqaradi
        await message.answer("Madiway bo'limi. Yukni qayerga yuboramiz?", reply_markup=madiway_inline())
    else:
        await message.answer("Madiway uchun rasm yuboring (1 tadan 10 tagacha rasm yuborish mumkin):")
        await BotStates.waiting_for_madiway_pics.set()
        madiway_media_group[user_id] = []

@dp.message_handler(content_types=[types.ContentType.PHOTO], state=BotStates.waiting_for_madiway_pics)
async def handle_madiway_pics(message: types.Message, state: FSMContext):
    user_id = message.from_user.id
    photo_id = message.photo[-1].file_id
    
    if len(madiway_media_group[user_id]) < 10:
        madiway_media_group[user_id].append(photo_id)
        
    if message.is_media_group():
        return  # Albom tugashini kutadi
        
    await message.answer("Rasmlar muvaffaqiyatli saqlandi! Endi maqsadni tanlang:", reply_markup=madiway_inline())
    await state.finish()

# === 3. INTERNATIONAL TUGMASI (MADIWAY BILAN BIR XIL LOGIKA) ===
@dp.message_handler(lambda message: message.text == "🌍 International")
async def intl_start(message: types.Message, state: FSMContext):
    user_id = message.from_user.id
    if user_id in intl_media_group and intl_media_group[user_id]:
        await message.answer("International bo'limi. Yukni qayerga yuboramiz?", reply_markup=intl_inline())
    else:
        await message.answer("International uchun rasm yuboring (1 tadan 10 tagacha):")
        await BotStates.waiting_for_intl_pics.set()
        intl_media_group[user_id] = []

@dp.message_handler(content_types=[types.ContentType.PHOTO], state=BotStates.waiting_for_intl_pics)
async def handle_intl_pics(message: types.Message, state: FSMContext):
    user_id = message.from_user.id
    photo_id = message.photo[-1].file_id
    
    if len(intl_media_group[user_id]) < 10:
        intl_media_group[user_id].append(photo_id)
        
    if message.is_media_group():
        return
        
    await message.answer("International rasmlari saqlandi! Tanlang:", reply_markup=intl_inline())
    await state.finish()

# --- INLINE TUGMALAR BOSILGANDA KANAL VA GURUHGA YUBORISH ---
@dp.callback_query_handler(lambda call: call.data.startswith("send_"))
async def send_media_target(call: types.CallbackQuery):
    user_id = call.from_user.id
    action = call.data
    
    # ID larni o'zingiznikiga o'zgartiring:
    MADIWAY_CHANNEL = "@madiway_ch" 
    MADIWAY_GROUP = -100123456789
    INTL_CHANNEL = "@intl_ch"
    INTL_GROUP = -100987654321
    
    media = types.MediaGroup()
    
    if "madiway" in action:
        photos = madiway_media_group.get(user_id, [])
        target = MADIWAY_CHANNEL if "channel" in action else MADIWAY_GROUP
    else:
        photos = intl_media_group.get(user_id, [])
        target = INTL_CHANNEL if "channel" in action else INTL_GROUP

    if not photos:
        await call.answer("Xatolik: Rasmlar topilmadi. Qayta yuborib ko'ring.", show_alert=True)
        return

    for i, p_id in enumerate(photos):
        if i == 0:
            media.attach_photo(p_id, caption="🔥 <b>YANGI YUK KELDI!</b>\nPremium tizim orqali yuborildi.")
        else:
            media.attach_photo(p_id)

    try:
        await bot.send_media_group(chat_id=target, media=media)
        await call.message.answer("✅ Yuk muvaffaqiyatli yuborildi!")
    except Exception as e:
        await call.message.answer(f"Yuborishda xatolik: {e}")
        
    await call.answer()

# === 4. MUSIQA VA KUTUBXONASIZ WATERMARK (BINARY MERGE) ===
@dp.message_handler(lambda message: message.text == "🎵 Musiqa Yuklash")
async def music_start(message: types.Message):
    await message.answer("Musiqa uchun Cover (Muqova rasmi) yuboring:")
    await BotStates.waiting_for_music_cover.set()

@dp.message_handler(content_types=[types.ContentType.PHOTO], state=BotStates.waiting_for_music_cover)
async def get_music_cover(message: types.Message, state: FSMContext):
    user_covers[message.from_user.id] = message.photo[-1].file_id
    await message.answer("Rasm qabul qilindi. Endi <b>Audio (MP3)</b> faylini yuboring:")
    await BotStates.waiting_for_music_file.set()

@dp.message_handler(content_types=[types.ContentType.AUDIO], state=BotStates.waiting_for_music_file)
async def handle_music_processing(message: types.Message, state: FSMContext):
    user_id = message.from_user.id
    cover_id = user_covers.get(user_id)
    
    status_msg = await message.answer("🔄 Audio qayta ishlanmoqda (Kutubxonasiz Watermark qo'shish)...")
    
    raw_audio_path = f"raw_{user_id}.mp3"
    output_audio_path = f"ready_{user_id}.mp3"
    watermark_path = "watermark.mp3"  # Bot papkasida 4 soniyalik shu nomli mp3 bo'lishi kerak
    
    # Asl musiqani yuklab olish
    audio_file = await bot.get_file(message.audio.file_id)
    await bot.download_file(audio_file.file_path, raw_audio_path)
    
    if os.path.exists(watermark_path):
        try:
            # FAQAT PYTHON IMKONIYATLARI BILAN BAYTLARNI BIRLASHTIRISH (BINARY APPEND)
            # Watermark faylini va asl musiqani baytma-bayt qo'shib yangi fayl yaratadi
            with open(watermark_path, "rb") as w_file, open(raw_audio_path, "rb") as a_file, open(output_audio_path, "wb") as out_file:
                out_file.write(w_file.read())  # Boshiga watermark yoziladi
                out_file.write(a_file.read())  # Ketidan musiqa yoziladi
            
            caption_text = "💎 <b>PREMIUM MUSIC</b> 💎\n\n✨ <i>Musiqa muqova rasm va watermark bilan tayyorlandi!</i>"
            
            # Kanalga muqova rasmi (thumb) bilan chiroyli premium qilib yuborish
            with open(output_audio_path, 'rb') as audio_to_send:
                await bot.send_audio(
                    chat_id="@your_music_channel",  # Musiqa kanalingiz uzi
                    audio=audio_to_send,
                    caption=caption_text,
                    thumb=cover_id,  # Siz yuborgan rasm muqova bo'ladi
                    title=message.audio.title or "Premium Track",
                    performer=message.audio.performer or "YusufxonPro"
                )
            
            await status_msg.edit_text("✅ Musiqa muvaffaqiyatli birlashtirildi va kanalga yuborildi!")
            
        except Exception as e:
            await status_msg.edit_text(f"Audioni birlashtirishda xatolik: {e}")
    else:
        await status_msg.edit_text("❌ Bot papkasida 'watermark.mp3' fayli topilmadi!")
        
    # Vaqtinchalik fayllarni tozalash
    if os.path.exists(raw_audio_path): os.remove(raw_audio_path)
    if os.path.exists(output_audio_path): os.remove(output_audio_path)
    await state.finish()

# === 5. STATISTIKA TUGMASI ===
@dp.message_handler(lambda message: message.text == "📊 Statistika")
async def show_stats(message: types.Message):
    cursor.execute("SELECT COUNT(*) FROM vips")
    vips_count = cursor.fetchone()[0]
    
    stats_text = (
        "📊 <b>Barcha Tizim Statistikasi</b>\n"
        "━━━━━━━━━━━━━━━━━━━━\n"
        f"💎 Premium (VIP) a'zolar: <code>{vips_count} ta</code>\n"
        "🤖 VIP ma'lumotlar xavfsiz bazada saqlanmoqda.\n"
        "━━━━━━━━━━━━━━━━━━━━"
    )
    await message.answer(stats_text)

# --- ADMIN BUYRUG'I: VIP QO'SHISH (Bot o'chib yonsa ham o'chmaydi) ---
@dp.message_handler(commands=['addvip'], user_id=ADMIN_ID)
async def add_vip_user(message: types.Message):
    try:
        target_id = int(message.get_args())
        cursor.execute("INSERT OR REPLACE INTO vips (user_id, status) VALUES (?, 'premium')", (target_id,))
        conn.commit()
        await message.answer(f"✅ Foydalanuvchi {target_id} VIP bazasiga qo'shildi. Kod o'zgarsa ham saqlanib qoladi.")
    except Exception:
        await message.answer("Xato! Format: `/addvip USER_ID`")

if __name__ == "__main__":
    executor.start_polling(dp, skip_updates=True)
