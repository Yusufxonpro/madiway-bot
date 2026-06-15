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
from aiogram.utils.media_group import MediaGroupBuilder

logging.basicConfig(level=logging.INFO)

# --- SOZLAMALAR VA ID RAQAMLAR ---
BOT_TOKEN = "8724439262:AAFGNuQQ4IxdqitlcCEtkHLsvyFwSPg_b1c"

CHANNEL_USER = "MADIWAYy"         
GROUP_USER = "MADIWAYy_Gr"        
NEW_GROUP_USER = "International_logistik"  

CHANNEL_ID = "-1003996104316"      
GROUP_ID = "-1003963001370"        
NEW_GROUP_ID = "-1004370807037"    # Yangi guruh IDsi (Faqat shu guruhga ishlaydi)

ADMIN_ID = 6977836294         
MADIWAY_ADMIN_ID = 8112179116  
OWNER_USERNAME = "yusufxonpro1"    

bot = Bot(token=BOT_TOKEN, default=DefaultBotProperties(parse_mode="HTML"))
dp = Dispatcher(storage=MemoryStorage())

USERS_DB_FILE = "users_database.json"
YUK_DB_FILE = "yuklar_database.json"
AUTO_TASKS_FILE = "auto_tasks_database.json"

UZB_TZ = timezone(timedelta(hours=5))
MEDIA_GROUPS_CACHE: Dict[str, List[types.Message]] = {}

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

# --- MA'LUMOTLAR BAZASI OPERATSIYALARI ---
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

def get_premium_caption(main_text, status_label="𝗬𝗨𝗞 𝗘𝗟𝗢𝗡𝗜"):
    now = datetime.now(UZB_TZ)
    sana_soat = now.strftime("📅 %Y-%m-%d  🕒 %I:%M %p") 
    return f"⭐️ <b>𝗠𝗔𝗗𝗜𝗪𝗔𝗬 | {status_label}</b> ⭐️\n───────────────────────\n{main_text}\n───────────────────────\n⏳ Vaqt: {sana_soat}\n📢 Kanal: t.me/{CHANNEL_USER}"

class MadiWayStates(StatesGroup):
    kutish_yangi_guruh_media_yuk = State()
    giving_premium_username = State()
    giving_premium_days = State()
    user_kutish_yuk = State()       # Foydalanuvchi yuk tashlash holati
    user_kutish_tel = State()       # Foydalanuvchi telefon raqami holati

# --- FOYDALANUVCHI INTERFEYSI (START) ---
@dp.message(Command("start"))
async def start_cmd(message: types.Message, command: CommandObject, state: FSMContext):
    await state.clear()
    user_id = message.from_user.id
    
    # Ro'yxatdan o'tkazish
    db = load_db(); uid = str(user_id)
    if uid not in db["users"]:
        db["users"][uid] = {"username": message.from_user.username or "yo'q", "full_name": message.from_user.full_name, "premium_until": None, "interval_type": "oddiy"}
        save_db(db)
        
    # Deeplink (Yukni to'liq ko'rish va telefon olish)
    if command.args:
        yuk_id = command.args
        if check_premium(user_id) or user_id in [ADMIN_ID, MADIWAY_ADMIN_ID]:
            ydb = load_yuk_db()
            data = ydb.get(yuk_id)
            if data:
                text = data.get("text", "")
                phone = data.get("phone", "Ko'rsatilmagan")
                owner = data.get("owner", "Noma'lum")
                
                full_info = f"{text}\n\n☎️ <b>Aloqa uchun telefon:</b> <code>{phone}</code>\n👤 <b>Yuk egasi:</b> {owner}"
                await message.answer(get_premium_caption(full_info, "𝗧𝗢'𝗟𝗜𝗤 𝗠𝗔'𝗟𝗨𝗠𝗢𝗧 VA RAQAM"))
            else:
                await message.answer("⚠️ Yuk topilmadi yoki eskirgan.")
        else:
            kb = types.InlineKeyboardMarkup(inline_keyboard=[[types.InlineKeyboardButton(text="💰 VIP tariflarni ko'rish", callback_data="btn_show_tariffs")]])
            await message.answer("❌ <b>Ushbu yuk egasining telefon raqamini va to'liq ma'lumotlarini ko'rish uchun sizda VIP obuna faol emas!</b>", reply_markup=kb)
        return

    # Admin yoki foydalanuvchi menyusi
    if user_id in [ADMIN_ID, MADIWAY_ADMIN_ID]:
        kb = types.InlineKeyboardMarkup(inline_keyboard=[
            [types.InlineKeyboardButton(text="📸 Yangi Guruh (10 ta rasm)", callback_data="btn_yangi_guruh_media")],
            [types.InlineKeyboardButton(text="🔑 VIP va Yuk Huquqini Berish", callback_data="btn_give_vip")],
            [types.InlineKeyboardButton(text="📊 Statistika", callback_data="btn_stats")]
        ])
        await message.answer("💻 <b>MADIWAY | ADMIN PANEL</b>", reply_markup=kb)
    else:
        buttons = [[types.InlineKeyboardButton(text="💰 VIP Guruh & Yuk Tariflari", callback_data="btn_show_tariffs")]]
        # Agar odam pul to'lagan bo'lsa, yuk tashlash tugmasi chiqadi
        if check_premium(user_id):
            buttons.append([types.InlineKeyboardButton(text="📦 Yuk Tashlash (Yangi Guruhga)", callback_data="btn_user_send_yuk")])
            
        kb = types.InlineKeyboardMarkup(inline_keyboard=buttons)
        await message.answer("🏔 <b>MadiWay xalqaro logistika botiga xush kelibsiz!</b>\n\nQuyidagi tugmalardan foydalaning:", reply_markup=kb)

# --- TARIFLAR KO'RSATISH ---
@dp.callback_query(F.data == "btn_show_tariffs")
async def show_tariffs(callback: types.CallbackQuery):
    await callback.answer()
    await callback.message.answer(AUTO_PAYMENT_MESSAGE)

# --- USER YUK TASHALASH JARAYONI ---
@dp.callback_query(F.data == "btn_user_send_yuk")
async def user_send_yuk_start(callback: types.CallbackQuery, state: FSMContext):
    await callback.answer()
    if not check_premium(callback.from_user.id):
        await callback.message.answer("❌ Sizning tarifingiz tugagan!")
        return
    await callback.message.answer("📥 <b>Iltimos, yangi guruhga yuboriladigan YUK matnini (tavsifini) kiriting:</b>")
    await state.set_state(MadiWayStates.user_kutish_yuk)

@dp.message(MadiWayStates.user_kutish_yuk)
async def user_process_yuk_text(message: types.Message, state: FSMContext):
    await state.update_data(yuk_text=message.html_text)
    await message.answer("☎️ Endi, haydovchilar siz bilan bog'lanishi uchun **Telefon Raqamingizni** yuboring (Masalan: +998901234567):")
    await state.set_state(MadiWayStates.user_kutish_tel)

@dp.message(MadiWayStates.user_kutish_tel)
async def user_process_yuk_final(message: types.Message, state: FSMContext):
    data = await state.get_data()
    yuk_text = data.get("yuk_text")
    phone = message.text
    user_id = message.from_user.id
    
    db = load_db()
    u_cfg = db["users"].get(str(user_id), {})
    interval_type = u_cfg.get("interval_type", "oddiy") # oddiy (5-9 soat) yoki tezkor (12 minut)

    # Yukni bazaga saqlash
    m_id = f"u{message.message_id}"
    ydb = load_yuk_db()
    ydb[m_id] = {
        "text": yuk_text,
        "phone": phone,
        "owner": message.from_user.full_name,
        "user_id": user_id
    }
    save_yuk_db(ydb)

    # Avtomatik interval vazifalariga qo'shish
    tasks = load_tasks()
    tasks[str(user_id)] = {
        "yuk_id": m_id,
        "interval": 12 if interval_type == "tezkor" else 300, # 12 minut yoki 5 soat (300 minut)
        "last_sent": datetime.now(UZB_TZ).isoformat()
    }
    save_tasks(tasks)

    await message.answer("✅ <b>Tasdiqlandi! Yukingiz tizimga tushmoqda va avtomatik ravishda yangi guruhga yo'llandi!</b>")
    
    # Birinchi marta guruhga darhol yuboramiz
    bot_info = await bot.get_me()
    short_txt = yuk_text[:150] + "..." if len(yuk_text) > 150 else yuk_text
    cap = get_premium_caption(short_txt, "TEZKOR AVTO YUK" if interval_type == "tezkor" else "AVTO YUK")
    
    kb = types.InlineKeyboardMarkup(inline_keyboard=[[
        types.InlineKeyboardButton(text="⭐️ To'liq ko'rish va Raqam olish", url=f"https://t.me/{bot_info.username}?start={m_id}")
    ]])
    await bot.send_message(chat_id=NEW_GROUP_ID, text=cap, reply_markup=kb)
    await state.clear()

# --- ADMIN PANEL: VIP VA TARIF BERISH (BLOCKDAN OCHISH BILAN) ---
@dp.callback_query(F.data == "btn_give_vip")
async def admin_give_vip_start(callback: types.CallbackQuery, state: FSMContext):
    await callback.answer()
    await callback.message.answer("🔑 <b>VIP/Yuk ruxsatnomasi berish uchun foydalanuvchi Telegram ID yoki @username kiriting:</b>")
    await state.set_state(MadiWayStates.giving_premium_username)

@dp.message(MadiWayStates.giving_premium_username)
async def admin_process_vip_user(message: types.Message, state: FSMContext):
    await state.update_data(target_user=message.text.replace("@", "").strip())
    kb = types.InlineKeyboardMarkup(inline_keyboard=[
        [types.InlineKeyboardButton(text="🗓 1 Kun (Oddiy - 5/9 soat)", callback_data="set_user_vip_1_oddiy")],
        [types.InlineKeyboardButton(text="🗓 1 Oy (Oddiy - 5/9 soat)", callback_data="set_user_vip_30_oddiy")],
        [types.InlineKeyboardButton(text="🚀 1 Kun (⚡️ Tezkor - 12 minutlik)", callback_data="set_user_vip_1_tezkor")]
    ])
    await message.answer("⏱ <b>To'lov turiga qarab tarif muddatini tanlang:</b>", reply_markup=kb)
    await state.set_state(MadiWayStates.giving_premium_days)

@dp.callback_query(MadiWayStates.giving_premium_days, F.data.startswith("set_user_vip_"))
async def admin_finalize_vip(callback: types.CallbackQuery, state: FSMContext):
    await callback.answer()
    parts = callback.data.split("_")
    days = int(parts[3])
    itype = parts[4] # oddiy yoki tezkor
    
    data = await state.get_data()
    target = data.get("target_user")
    db = load_db()
    found_uid = None
    
    for uid, uinfo in db["users"].items():
        if uid == target or uinfo["username"].lower() == target.lower():
            found_uid = uid
            break
            
    if found_uid:
        end_date = datetime.now(UZB_TZ) + timedelta(days=days)
        db["users"][found_uid]["premium_until"] = end_date.isoformat()
        db["users"][found_uid]["interval_type"] = itype
        db["premium_count"] = db.get("premium_count", 0) + 1
        save_db(db)
        
        # AVTOMATIK BLOCKDAN OCHISH (UNBAN)
        try:
            await bot.unban_chat_member(chat_id=NEW_GROUP_ID, user_id=int(found_uid), only_if_banned=True)
        except Exception as e:
            logging.error(f"Unban qilishda xato (balki blockda emasdir): {e}")

        formatted = end_date.strftime("%d-%m-%Y %H:%M")
        await callback.message.answer(f"✅ VIP va Yuk Huquqi Tasdiqlandi!\n👤 Rejim: {itype.upper()}\n⏱ Muddat: {formatted} gacha.")
        
        # Foydalanuvchiga xabar berish va yuk tashlash tugmasini ko'rsatish
        u_kb = types.InlineKeyboardMarkup(inline_keyboard=[[types.InlineKeyboardButton(text="📦 Yuk Tashlash", callback_data="btn_user_send_yuk")]])
        try:
            await bot.send_message(
                chat_id=int(found_uid), 
                text=f"🎉 <b>Administrator tomonidan to'lov qabul qilindi va tasdiqlandi!</b>\n\n"
                     f"Siz muvaffaqiyatli VIP tizimiga qo'shildingiz va guruh blockidan ochildingiz. "
                     f"Endi bemalol yuk tashishingiz mumkin!\n"
                     f"⏱ Amal qilish muddati: <code>{formatted}</code> gacha.",
                reply_markup=u_kb
            )
        except: pass
    else:
        await callback.message.answer("❌ Foydalanuvchi bot bazasidan topilmadi. Avval botga kirib /start bosgan bo'lishi kerak!")
    await state.clear()

# --- 10 TA RASMLI ALBOM YUBORISH (ADMIN UCHUN) ---
@dp.callback_query(F.data == "btn_yangi_guruh_media")
async def admin_media_start(callback: types.CallbackQuery, state: FSMContext):
    await callback.answer()
    await callback.message.answer("📸 Yangi guruh uchun 10 tagacha rasm/videoni bitta albom qilib (caption yozib) yuboring:")
    await state.set_state(MadiWayStates.kutish_yangi_guruh_media_yuk)

@dp.message(MadiWayStates.kutish_yangi_guruh_media_yuk, F.media_group_id)
async def handle_media_group(message: types.Message, state: FSMContext):
    mg_id = message.media_group_id
    if mg_id not in MEDIA_GROUPS_CACHE:
        MEDIA_GROUPS_CACHE[mg_id] = []
        asyncio.create_task(process_media_group_delayed(mg_id, state, message.message_id, message.from_user.id))
    MEDIA_GROUPS_CACHE[mg_id].append(message)

async def process_media_group_delayed(mg_id: str, state: FSMContext, original_msg_id: int, user_id: int):
    await asyncio.sleep(1.5)
    messages = MEDIA_GROUPS_CACHE.get(mg_id, [])
    if not messages: return
    
    caption_text = ""
    for msg in messages:
        if msg.caption: caption_text = msg.caption; break
            
    m_id = f"g{original_msg_id}"
    ydb = load_yuk_db()
    ydb[m_id] = {"text": caption_text, "phone": "Admin bilan bog'laning", "owner": "MadiWay Admin"}
    save_yuk_db(ydb)
    
    bot_info = await bot.get_me()
    short_txt = caption_text[:150] + "..." if len(caption_text) > 150 else caption_text
    cap = get_premium_caption(short_txt, "𝗫𝗔𝗩𝗙𝗦𝗜𝗭 𝗠𝗘𝗗𝗜𝗔 𝗬𝗨𝗞")
    
    media_group = MediaGroupBuilder()
    is_first = True
    for msg in messages:
        current_cap = cap if is_first else None
        if msg.photo: media_group.add_photo(media=msg.photo[-1].file_id, caption=current_cap); is_first = False
        elif msg.video: media_group.add_video(media=msg.video.file_id, caption=current_cap); is_first = False
            
    try:
        await bot.send_media_group(chat_id=NEW_GROUP_ID, media=media_group.build())
        kb = types.InlineKeyboardMarkup(inline_keyboard=[[types.InlineKeyboardButton(text="⭐️ To'liq ko'rish", url=f"https://t.me/{bot_info.username}?start={m_id}")]])
        await bot.send_message(chat_id=NEW_GROUP_ID, text="▲ <b>Yuqoridagi yuk ma'lumotlari:</b>", reply_markup=kb)
        await bot.send_message(chat_id=user_id, text="✅ Albom muvaffaqiyatli ketdi!")
    except Exception as e:
        await bot.send_message(chat_id=user_id, text=f"❌ Xato: {e}")
        
    if mg_id in MEDIA_GROUPS_CACHE: del MEDIA_GROUPS_CACHE[mg_id]
    await state.clear()

@dp.callback_query(F.data == "btn_stats")
async def show_stats(callback: types.CallbackQuery):
    await callback.answer()
    db = load_db()
    await callback.message.answer(f"📊 <b>Statistika:</b>\n\n👤 Umumiy a'zolar: <code>{len(db['users'])}</code> ta\n👑 VIP a'zolar: <code>{db.get('premium_count', 0)}</code> ta")

@dp.message()
async def auto_reply_handler(message: types.Message):
    if message.chat.type == "private" and message.from_user.id not in [ADMIN_ID, MADIWAY_ADMIN_ID]:
        await message.answer(AUTO_PAYMENT_MESSAGE)

# --- 🔄 FONDA ISHLOVCHI AVTOMATIK INTERVALLAR VA KICK TIMERI ---
async def auto_cron_job():
    while True:
        try:
            now = datetime.now(UZB_TZ)
            
            # 1. MUDDATI TUGAGANLARNI GURUXDAN CHIQARISH (KICK)
            db = load_db()
            for uid, info in list(db["users"].items()):
                if info["premium_until"]:
                    until_dt = datetime.fromisoformat(info["premium_until"]).astimezone(UZB_TZ)
                    if now > until_dt:
                        # Muddat tugagan - guruhdan chiqaramiz
                        try:
                            await bot.ban_chat_member(chat_id=NEW_GROUP_ID, user_id=int(uid))
                            await bot.unban_chat_member(chat_id=NEW_GROUP_ID, user_id=int(uid)) # Tark etgan holatda qoldirish uchun unban
                            db["users"][uid]["premium_until"] = None # Tizimda o'chirish
                            save_db(db)
                            await bot.send_message(chat_id=int(uid), text="⚠️ <b>Sizning VIP obuna muddatingiz tugadi va siz yangi guruhdan chiqarildingiz!</b>\nQayta qo'shilish uchun to'lov qiling.")
                        except Exception as e:
                            logging.error(f"Foydalanuvchini kick qilishda xatolik {uid}: {e}")

            # 2. AVTO-YUK TASHALASH INTERVALI (12 MINUT VA ODDY REJIM)
            tasks = load_tasks()
            ydb = load_yuk_db()
            bot_info = await bot.get_me()
            
            for uid, task in list(tasks.items()):
                # Foydalanuvchi VIP holatini tekshirish
                if not check_premium(int(uid)):
                    continue
                    
                last_sent = datetime.fromisoformat(task["last_sent"]).astimezone(UZB_TZ)
                diff_minutes = (now - last_sent).total_seconds() / 60
                
                if diff_minutes >= task["interval"]:
                    yuk_data = ydb.get(task["yuk_id"])
                    if yuk_data:
                        short_txt = yuk_data["text"][:150] + "..." if len(yuk_data["text"]) > 150 else yuk_data["text"]
                        cap = get_premium_caption(short_txt, "🔂 AVTO RE-POST YUK")
                        kb = types.InlineKeyboardMarkup(inline_keyboard=[[
                            types.InlineKeyboardButton(text="⭐️ To'liq ko'rish va Raqam olish", url=f"https://t.me/{bot_info.username}?start={task['yuk_id']}")
                        ]])
                        
                        try:
                            await bot.send_message(chat_id=NEW_GROUP_ID, text=cap, reply_markup=kb)
                            # Vaqtni yangilash
                            tasks[uid]["last_sent"] = now.isoformat()
                            save_tasks(tasks)
                        except Exception as e:
                            logging.error(f"Interval yuk yuborishda xato: {e}")
                            
        except Exception as ex:
            logging.error(f"Cron xatosi: {ex}")
            
        await asyncio.sleep(30) # Har 30 soniyada fonda bazani tekshirib turadi

async def main():
    # Fondagi vazifani ishga tushirish
    asyncio.create_task(auto_cron_job())
    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)

if __name__ == '__main__':
    asyncio.run(main())
