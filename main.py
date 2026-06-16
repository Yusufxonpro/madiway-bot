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
GROUP_ID = "-1003963001370"        # MadiWay Asosiy Guruh ID
NEW_GROUP_ID = "-1004370807037"    # Yangi guruh ID

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
    "🚀 <b>TEZKOR TARIF (Har 12 minutda avto-qayta tashlash):</b>\n"
    "⚡️ 1 kunlik (Har 12 daqiqada guruhlarga yuborish) — 30 000 so'm\n\n"
    "⚠️ To'lovni amalga oshirib, chekni shu yerga yuboring va adminga aloqaga chiqing!\n"
    "📞 <b>Aloqa:</b> +998 88 325 80 07"
)

TOPICS = {
    "🌍 Europa": 2, "🇩🇪 Germaniya": 14, "🇷🇺 Rossiya": 4, "🇰🇬 Qirg'iziston": 6,
    "🇰🇿 Kazakistan": 8, "🇮🇷 Eron": 10, "🇹🇯 Tojikston": 12, "🇧🇾 Belarusiya": 16,
    "🇬🇪 Gruziya": 18, "📣 Elon berish": 1
}

LINKS_INFO = (
    "🔗 <b>MadiWay guruhlariga ulanish linklari:</b>\n\n"
    "1️⃣ <b>MadiWay Kanali (BEPUL):</b>\n<code>t.me/MADIWAYy</code>\n\n"
    "2️⃣ <b>MadiWay Asosiy Guruh (PULLIK):</b>\n<code>t.me/MADIWAYy_Gr</code>\n\n"
    "3️⃣ <b>MadiWay Yangi Guruh (PULLIK):</b>\n<code>t.me/International_logistik</code>\n\n"
    "⚠️ <i>Guruhga ruxsat olish uchun kerakli guruh havolasini botga yuboring!</i>"
)

# --- BAZA BILAN ISHLASH ---
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

def get_group_kb(bot_user, msg_id=None):
    buttons = []
    if msg_id:
        buttons.append([types.InlineKeyboardButton(text="⭐️ Yukni to'liq ko'rish", url=f"https://t.me/{bot_user}?start={msg_id}")])
    return types.InlineKeyboardMarkup(inline_keyboard=buttons)

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
    kutish_yangi_guruh_yuk = State()
    kutish_yangi_guruh_100_yuk = State()
    kutish_yangi_guruh_media_yuk = State()
    giving_premium_username = State()
    giving_premium_days = State()
    kutish_guruh_linki = State()
    user_kutish_guruh_tanlash = State()
    user_kutish_topic_tanlash = State()
    user_kutish_yuk = State()       
    user_kutish_tel = State()       

# --- START BUYRUG'I VA DEEPLINK ---
@dp.message(Command("start"))
async def start_cmd(message: types.Message, command: CommandObject, state: FSMContext):
    await state.clear()
    user_id = message.from_user.id
    
    # Ro'yxatdan o'tkazish
    db = load_db(); uid = str(user_id)
    if uid not in db["users"]:
        db["users"][uid] = {"username": message.from_user.username or "yo'q", "full_name": message.from_user.full_name, "premium_until": None, "interval_type": "oddiy"}
        save_db(db)
    
    if command.args:
        yuk_id = command.args
        ydb = load_yuk_db()
        data = ydb.get(yuk_id)
        
        # KANALIDAN KELGAN YUKLAR -> MUTLOQ BEPUL KO'RADI
        if yuk_id.startswith("c"):
            if data:
                txt = data if isinstance(data, str) else data.get("text", "")
                await message.answer(get_premium_caption(txt, "𝗧𝗢'𝗟𝗜𝗤 𝗠𝗔'𝗟𝗨𝗠𝗢𝗧"))
            else:
                await message.answer("⚠️ Yuk ma'lumotlari topilmadi.")
            return

        # GURUXLARDAN KELGAN YUKLAR -> PULLIK TEKSHIRUV
        if check_premium(user_id) or user_id in [ADMIN_ID, MADIWAY_ADMIN_ID]:
            if data:
                if isinstance(data, str):
                    await message.answer(get_premium_caption(data, "𝗧𝗢'𝗟𝗜𝗤 𝗠𝗔'𝗟𝗨𝗠𝗢𝗧"))
                else:
                    text = data.get("text", "")
                    phone = data.get("phone", "Ko'rsatilmagan")
                    owner = data.get("owner", "Noma'lum")
                    full_info = f"{text}\n\n☎️ <b>Aloqa uchun telefon:</b> <code>{phone}</code>\n👤 <b>Yuk egasi:</b> {owner}"
                    await message.answer(get_premium_caption(full_info, "𝗧𝗢'𝗟𝗜𝗤 𝗠𝗔'𝗟𝗨𝗠𝗢𝗧 VA RAQAM"))
            else:
                await message.answer("⚠️ Yuk topilmadi.")
            return
        else:
            guruh_nomi = "MadiWay Guruhlari"
            if yuk_id.startswith("g"): guruh_nomi = "MadiWay Yangi Guruh"
            elif yuk_id.startswith("b") or yuk_id.startswith("h"): guruh_nomi = "MadiWay Asosiy Guruh"
            
            await state.set_state(MadiWayStates.kutish_guruh_linki)
            await state.update_data(tanlangan_guruh=guruh_nomi)
            await message.answer(f"❌ <b>Ushbu guruhdagi ({guruh_nomi}) yukni to'liq ko'rish va raqamni olish uchun VIP obuna faol emas!</b>", reply_markup=get_tariff_keyboard())
            return

    # Admin Panel
    if user_id in [ADMIN_ID, MADIWAY_ADMIN_ID]:
        kb = types.InlineKeyboardMarkup(inline_keyboard=[
            [types.InlineKeyboardButton(text="⚙️ Start sozlash", callback_data="btn_add_start_msg"), types.InlineKeyboardButton(text="📊 Statistika", callback_data="btn_stats")],
            [types.InlineKeyboardButton(text="⭐️ Kanalga yuk (BEPUL)", callback_data="btn_kanal_tashlash"), types.InlineKeyboardButton(text="✨ Bitta Topicga", callback_data="btn_bitta_topic")],
            [types.InlineKeyboardButton(text="💥 Hammasiga yuborish", callback_data="btn_hamma_topic")],
            [types.InlineKeyboardButton(text="🆕 Yangi Guruhga xabar", callback_data="btn_yangi_guruh"), types.InlineKeyboardButton(text="🚛 Yangi Guruh 100 ta yuk", callback_data="btn_yangi_guruh_100")],
            [types.InlineKeyboardButton(text="📸 Yangi Guruh (10 rasm)", callback_data="btn_yangi_guruh_media"), types.InlineKeyboardButton(text="🔑 VIP Faollashtirish", callback_data="btn_give_vip")]
        ])
        await message.answer("💻 <b>𝗠𝗔𝗗𝗜𝗪𝗔𝗬 | 𝗔𝗗𝗠𝗜𝗡 𝗣𝗔𝗡𝗘𝗟</b>", reply_markup=kb)
    else:
        buttons = [[types.InlineKeyboardButton(text="💰 Guruhga qo'shilish / Tariflar", callback_data="btn_show_tariffs")]]
        if check_premium(user_id):
            buttons.append([types.InlineKeyboardButton(text="📦 Yuk Tashlash (Avto-Post)", callback_data="btn_user_send_yuk")])
        kb = types.InlineKeyboardMarkup(inline_keyboard=buttons)
        await message.answer("🏔 <b>MadiWay logistika tizimiga xush kelibsiz!</b>\n\nYuklar haqida ma'lumot olish hamda guruhlarda yuk e'lon qilish uchun quyidagi tugmalardan foydalaning:", reply_markup=kb)

# --- TARIFLAR VA HAVOLA TEKSHIRUV ---
@dp.callback_query(F.data == "btn_show_tariffs")
async def show_tariffs_menu(callback: types.CallbackQuery, state: FSMContext):
    await callback.answer()
    await callback.message.answer(LINKS_INFO)
    await state.set_state(MadiWayStates.kutish_guruh_linki)

@dp.message(MadiWayStates.kutish_guruh_linki)
async def process_group_link(message: types.Message, state: FSMContext):
    link_text = message.text.lower() if message.text else ""
    if "madiwayy_gr" in link_text: guruh_nomi = "MadiWay Asosiy Guruh"
    elif "international_logistik" in link_text: guruh_nomi = "MadiWay Yangi Guruh"
    else: guruh_nomi = "MadiWay Guruhlari"

    await state.update_data(tanlangan_guruh=guruh_nomi)
    await message.answer(f"✅ <b>Guruh aniqlandi:</b> {guruh_nomi}\n\n⏱ Obuna muddatini tanlang:", reply_markup=get_tariff_keyboard())

@dp.callback_query(MadiWayStates.kutish_guruh_linki, F.data.startswith('track_'))
async def track_and_redirect(callback: types.CallbackQuery, state: FSMContext):
    await callback.answer()
    parts = callback.data.split("_")
    user_data = await state.get_data()
    guruh_nomi = user_data.get("tanlangan_guruh", "MadiWay Guruhlari")
    
    alert = f"🔔 <b>YANGI TO'LOV SO'ROVI:</b>\n\n👤 Foydalanuvchi: {callback.from_user.full_name}\n🆔 ID: <code>{callback.from_user.id}</code>\n📦 Guruh: {guruh_nomi}\n🛒 Tarif: {parts[1]} {parts[2]}"
    for adm in [MADIWAY_ADMIN_ID, ADMIN_ID]:
        try: await bot.send_message(chat_id=adm, text=alert)
        except: pass
        
    kb = types.InlineKeyboardMarkup(inline_keyboard=[[types.InlineKeyboardButton(text="🚀 Adminga chek yuborish", url=f"https://t.me/{OWNER_USERNAME}")]])
    await callback.message.answer(f"💳 <b>To'lov ma'lumotlari:</b>\nKarta: <code>4916-9903-5000-8311</code>\n\n👇 Pastdagi tugma orqali adminga chekni yuboring, admin sizni guruhlarga qo'shadi!", reply_markup=kb)
    await state.clear()

# --- FOYDALANUVCHILAR YUK TASHALASH TIZIMI (AVTO INTERVAL) ---
@dp.callback_query(F.data == "btn_user_send_yuk")
async def user_send_yuk_start(callback: types.CallbackQuery, state: FSMContext):
    await callback.answer()
    if not check_premium(callback.from_user.id):
        await callback.message.answer("❌ Sizda VIP aktiv emas!")
        return
    
    kb = types.InlineKeyboardMarkup(inline_keyboard=[
        [types.InlineKeyboardButton(text="Asosiy Guruh (MadiWay Yuklar)", callback_data="user_target_main")],
        [types.InlineKeyboardButton(text="Yangi Guruh (International)", callback_data="user_target_new")]
    ])
    await callback.message.answer("🎯 <b>Yukingiz qaysi guruhga avtomatik va vaqtli joylab turilsin?</b>", reply_markup=kb)
    await state.set_state(MadiWayStates.user_kutish_guruh_tanlash)

@dp.callback_query(MadiWayStates.user_kutish_guruh_tanlash, F.data.startswith("user_target_"))
async def user_guruh_tanladi(callback: types.CallbackQuery, state: FSMContext):
    await callback.answer()
    target = callback.data.split("_")[2]
    await state.update_data(user_target_group=target)
    
    if target == "main":
        btns = [types.InlineKeyboardButton(text=n, callback_data=f"user_topic_{id}") for n, id in TOPICS.items()]
        kb = types.InlineKeyboardMarkup(inline_keyboard=[btns[i:i+2] for i in range(0, len(btns), 2)])
        await callback.message.answer("📍 <b>MadiWay Asosiy guruhidan kerakli bo'limni (Topic) tanlang:</b>", reply_markup=kb)
        await state.set_state(MadiWayStates.user_kutish_topic_tanlash)
    else:
        await callback.message.answer("📥 <b>Yangi guruhga yuboriladigan yuk matnini kiriting:</b>")
        await state.set_state(MadiWayStates.user_kutish_yuk)

@dp.callback_query(MadiWayStates.user_kutish_topic_tanlash, F.data.startswith("user_topic_"))
async def user_topic_tanladi(callback: types.CallbackQuery, state: FSMContext):
    await callback.answer()
    tid = int(callback.data.split("_")[2])
    await state.update_data(user_target_topic=tid)
    await callback.message.answer("📥 <b>Tanlangan bo'lim uchun yuk matnini kiriting:</b>")
    await state.set_state(MadiWayStates.user_kutish_yuk)

@dp.message(MadiWayStates.user_kutish_yuk)
async def user_get_text(message: types.Message, state: FSMContext):
    await state.update_data(yuk_text=message.html_text)
    await message.answer("☎️ Haydovchilar bog'lanishi uchun <b>Telefon Raqamingizni</b> yuboring:")
    await state.set_state(MadiWayStates.user_kutish_tel)

@dp.message(MadiWayStates.user_kutish_tel)
async def user_finish_yuk(message: types.Message, state: FSMContext):
    sdata = await state.get_data()
    yuk_text = sdata.get("yuk_text")
    t_group = sdata.get("user_target_group")
    t_topic = sdata.get("user_target_topic", None)
    phone = message.text
    user_id = message.from_user.id
    
    db = load_db()
    itype = db["users"].get(str(user_id), {}).get("interval_type", "oddiy")
    
    m_id = f"u{message.message_id}"
    ydb = load_yuk_db(); ydb[m_id] = {"text": yuk_text, "phone": phone, "owner": message.from_user.full_name, "user_id": user_id}
    save_yuk_db(ydb)
    
    tasks = load_tasks()
    tasks[str(user_id)] = {
        "yuk_id": m_id,
        "target_group": t_group,
        "target_topic": t_topic,
        "interval": 12 if itype == "tezkor" else 300,
        "last_sent": datetime.now(UZB_TZ).isoformat()
    }
    save_tasks(tasks)
    
    await message.answer("✅ <b>Tasdiqlandi! Yukingiz tizimga tushdi va guruhlarga muntazam ravishda avto-post qilinadi!</b>")
    
    # Ilk postni darhol chiqarish
    bot_info = await bot.get_me()
    cap = get_premium_caption(yuk_text[:150] + "...", "AVTO YUK")
    kb = get_group_kb(bot_info.username, m_id)
    chat = NEW_GROUP_ID if t_group == "new" else GROUP_ID
    
    await bot.send_message(chat_id=chat, text=cap, reply_markup=kb, message_thread_id=t_topic)
    await state.clear()

# --- ADMIN PANEL FUNKSIYALARI ---
@dp.callback_query(F.data.startswith('btn_'))
async def admin_buttons(callback: types.CallbackQuery, state: FSMContext):
    await callback.answer()
    if callback.data == "btn_add_start_msg":
        await callback.message.answer("⚙️ Yangi start xabarni yuboring:")
        await state.set_state(MadiWayStates.kutish_global_start)
    elif callback.data == "btn_kanal_tashlash":
        await callback.message.answer("📥 Kanal yukini yuboring (BEPUL KO'RILADI):")
        await state.set_state(MadiWayStates.kutish_kanal_yuk)
    elif callback.data == "btn_hamma_topic":
        await callback.message.answer("💥 Barcha topiklarga yuboriladigan yukni kiriting:")
        await state.set_state(MadiWayStates.kutish_hamma_topic_yuk)
    elif callback.data == "btn_yangi_guruh":
        await callback.message.answer("📥 Yangi guruhga oddiy xabarni kiriting:")
        await state.set_state(MadiWayStates.kutish_yangi_guruh_yuk)
    elif callback.data == "btn_yangi_guruh_100":
        await callback.message.answer("🚛 Yangi guruhga 100 ta yuk xabarini yuboring (Limit 0.4s):")
        await state.set_state(MadiWayStates.kutish_yangi_guruh_100_yuk)
    elif callback.data == "btn_yangi_guruh_media":
        await callback.message.answer("📸 10 tagacha rasm/videoli albomni yuboring:")
        await state.set_state(MadiWayStates.kutish_yangi_guruh_media_yuk)
    elif callback.data == "btn_bitta_topic":
        btns = [types.InlineKeyboardButton(text=n, callback_data=f"select_topic_{id}") for n, id in TOPICS.items()]
        kb = types.InlineKeyboardMarkup(inline_keyboard=[btns[i:i+2] for i in range(0, len(btns), 2)])
        await callback.message.answer("📍 Bo'limni tanlang:", reply_markup=kb)
    elif callback.data == "btn_give_vip":
        await callback.message.answer("🔑 VIP va Yuk huquqi berish uchun Telegram ID yoki @username yozing:")
        await state.set_state(MadiWayStates.giving_premium_username)
    elif callback.data == "btn_stats":
        db = load_db()
        await callback.message.answer(f"📊 <b>Statistika:</b>\n\n👤 A'zolar: <code>{len(db['users'])}</code> ta\n👑 VIP: <code>{db.get('premium_count', 0)}</code> ta")

# --- ADMIN: VIP / YUK RUXSATI BERISH (UNBAN TIZIMI BILAN) ---
@dp.message(MadiWayStates.giving_premium_username)
async def admin_vip_user(message: types.Message, state: FSMContext):
    await state.update_data(target_user=message.text.replace("@", "").strip())
    kb = types.InlineKeyboardMarkup(inline_keyboard=[
        [types.InlineKeyboardButton(text="🗓 1 Kun (Oddiy - 5 soat)", callback_data="set_user_vip_1_oddiy")],
        [types.InlineKeyboardButton(text="🗓 1 Oy (Oddiy - 5 soat)", callback_data="set_user_vip_30_oddiy")],
        [types.InlineKeyboardButton(text="🚀 1 Kun (⚡️ Tezkor - 12 minut)", callback_data="set_user_vip_1_tezkor")]
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
    db = load_db(); found_uid = None
    
    for uid, info in db["users"].items():
        if uid == target or info["username"].lower() == target.lower():
            found_uid = uid; break
            
    if found_uid:
        end_date = datetime.now(UZB_TZ) + timedelta(days=days)
        db["users"][found_uid]["premium_until"] = end_date.isoformat()
        db["users"][found_uid]["interval_type"] = itype
        db["premium_count"] = db.get("premium_count", 0) + 1
        save_db(db)
        
        # IKKALA GURUXDAN HAM BAN BO'LSA OCHISH
        for gid in [NEW_GROUP_ID, GROUP_ID]:
            try: await bot.unban_chat_member(chat_id=gid, user_id=int(found_uid), only_if_banned=True)
            except: pass

        formatted = end_date.strftime("%d-%m-%Y %H:%M")
        await callback.message.answer(f"✅ VIP va Yuk Huquqi Berildi!\n⏱ Muddat: {formatted} gacha.")
        
        u_kb = types.InlineKeyboardMarkup(inline_keyboard=[[types.InlineKeyboardButton(text="📦 Yuk Tashlash", callback_data="btn_user_send_yuk")]])
        try:
            await bot.send_message(
                chat_id=int(found_uid), 
                text=f"🎉 <b>Administrator to'lovingizni qabul qildi va tasdiqladi!</b>\n\nSizga yuk tashlash imkoniyati ochildi va guruh cheklovlaridan ozod bo'ldingiz.\n⏱ VIP muddati: <code>{formatted}</code> gacha.",
                reply_markup=u_kb
            )
        except: pass
    else:
        await callback.message.answer("❌ Foydalanuvchi bazadan topilmadi!")
    await state.clear()

# --- ADMIN: 100 TA YUK YUBORISH (FLOOD LIMITSIZ) ---
@dp.message(MadiWayStates.kutish_yangi_guruh_100_yuk)
async def yangi_guruh_100_yuk(message: types.Message, state: FSMContext):
    txt = message.html_text or message.caption or ""
    m_id = f"g{message.message_id}"
    ydb = load_yuk_db(); ydb[m_id] = {"text": txt, "phone": "Admin", "owner": "Admin"}; save_yuk_db(ydb)
    
    bot_info = await bot.get_me()
    cap = get_premium_caption(txt[:150] + "...")
    await asyncio.sleep(0.4) # Flood-control joriy qilindi
    await send_all(NEW_GROUP_ID, message, cap, get_group_kb(bot_info.username, m_id))
    await message.answer("✅ Yuk yangi guruhga limitlarsiz xavfsiz ketdi!")
    await state.clear()

# --- ADMIN: MEDIA GROUP (ALBOM) ---
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
    caption_text = next((msg.caption for msg in messages if msg.caption), "")
            
    m_id = f"g{original_msg_id}"
    ydb = load_yuk_db(); ydb[m_id] = {"text": caption_text, "phone": "MadiWay", "owner": "Admin"}; save_yuk_db(ydb)
    
    bot_info = await bot.get_me()
    cap = get_premium_caption(caption_text[:150] + "...", "𝗫𝗔𝗩𝗙𝗦𝗜𝗭 𝗠𝗘𝗗𝗜𝗔")
    
    media_group = MediaGroupBuilder()
    is_first = True
    for msg in messages:
        current_cap = cap if is_first else None
        if msg.photo: media_group.add_photo(media=msg.photo[-1].file_id, caption=current_cap); is_first = False
        elif msg.video: media_group.add_video(media=msg.video.file_id, caption=current_cap); is_first = False
            
    try:
        await bot.send_media_group(chat_id=NEW_GROUP_ID, media=media_group.build())
        await bot.send_message(chat_id=NEW_GROUP_ID, text="▲ <b>Ma'lumotlar:</b>", reply_markup=get_group_kb(bot_info.username, m_id))
        await bot.send_message(chat_id=user_id, text="✅ Albom yangi guruhga muvaffaqiyatli ketdi!")
    except Exception as e:
        await bot.send_message(chat_id=user_id, text=f"❌ Xato: {e}")
        
    if mg_id in MEDIA_GROUPS_CACHE: del MEDIA_GROUPS_CACHE[mg_id]
    await state.clear()

# --- STANDART ADMIN YUK OPERATSIYALARI ---
@dp.message(MadiWayStates.kutish_kanal_yuk)
async def chan_yuk(message: types.Message, state: FSMContext):
    txt = message.html_text or message.caption or ""
    m_id = f"c{message.message_id}"
    ydb = load_yuk_db(); ydb[m_id] = txt; save_yuk_db(ydb)
    bot_info = await bot.get_me()
    await send_all(CHANNEL_ID, message, get_premium_caption(txt), get_group_kb(bot_info.username, m_id))
    await message.answer("✅ Kanalga ketdi (Foydalanuvchilar bepul ko'rishadi).")
    await state.clear()

@dp.message(MadiWayStates.kutish_hamma_topic_yuk)
async def all_yuk(message: types.Message, state: FSMContext):
    txt = message.html_text or message.caption or ""
    m_id = f"h{message.message_id}"
    ydb = load_yuk_db(); ydb[m_id] = {"text": txt, "phone": "Admin", "owner": "Admin"}; save_yuk_db(ydb)
    bot_info = await bot.get_me()
    for n, tid in TOPICS.items():
        await send_all(GROUP_ID, message, get_premium_caption(txt[:150] + "..."), get_group_kb(bot_info.username, m_id), tid)
        await asyncio.sleep(0.4)
    await message.answer("✅ Barcha topiklarga yuborildi.")
    await state.clear()

@dp.callback_query(F.data.startswith('select_topic_'))
async def topic_sel(callback: types.CallbackQuery, state: FSMContext):
    await state.update_data(target_topic_id=callback.data.split('_')[2])
    await callback.message.answer("📥 Yukni kiriting:")
    await state.set_state(MadiWayStates.kutish_bitta_topic_yuk)

@dp.message(MadiWayStates.kutish_bitta_topic_yuk)
async def bitta_topic_yuk(message: types.Message, state: FSMContext):
    tid = int((await state.get_data()).get("target_topic_id", 1))
    txt = message.html_text or message.caption or ""
    m_id = f"b{message.message_id}"
    ydb = load_yuk_db(); ydb[m_id] = {"text": txt, "phone": "Admin", "owner": "Admin"}; save_yuk_db(ydb)
    bot_info = await bot.get_me()
    await send_all(GROUP_ID, message, get_premium_caption(txt[:150] + "..."), get_group_kb(bot_info.username, m_id), tid)
    await message.answer("✅ Tanlangan topikka ketdi!")
    await state.clear()

@dp.message(MadiWayStates.kutish_yangi_guruh_yuk)
async def yangi_guruh_yuk(message: types.Message, state: FSMContext):
    txt = message.html_text or message.caption or ""
    await send_all(NEW_GROUP_ID, message, get_premium_caption(txt, "YANGI GURUH"), get_group_kb(None))
    await message.answer("✅ Xabar yuborildi.")
    await state.clear()

async def send_all(chat_id, message, caption, kb, t_id=None):
    try:
        if message.photo: return await bot.send_photo(chat_id, message.photo[-1].file_id, caption=caption, reply_markup=kb, message_thread_id=t_id)
        elif message.video: return await bot.send_video(chat_id, message.video.file_id, caption=caption, reply_markup=kb, message_thread_id=t_id)
        else: return await bot.send_message(chat_id, caption, reply_markup=kb, message_thread_id=t_id)
    except Exception as e: return None

@dp.message(MadiWayStates.kutish_global_start)
async def save_start(message: types.Message, state: FSMContext):
    await message.answer("✅ Saqlandi!")
    await state.clear()

@dp.message()
async def auto_reply_handler(message: types.Message):
    if message.chat.type == "private" and message.from_user.id not in [ADMIN_ID, MADIWAY_ADMIN_ID]:
        await message.answer(AUTO_PAYMENT_MESSAGE)

# --- 🔄 FONDA ISHLOVCHI MULTI-GURUH CRON (KICK & AVTO INTERVAL TIZIMI) ---
async def auto_cron_job():
    while True:
        try:
            now = datetime.now(UZB_TZ)
            
            # 1. MUDDATI TUGAGANLARNI IKKALA GURUXDAN HAM CHIQARISH (KICK)
            db = load_db()
            for uid, info in list(db["users"].items()):
                if info["premium_until"]:
                    until_dt = datetime.fromisoformat(info["premium_until"]).astimezone(UZB_TZ)
                    if now > until_dt:
                        # Muddat tugasa ikkala guruhdan ham kick bo'ladi
                        for gid in [NEW_GROUP_ID, GROUP_ID]:
                            try:
                                await bot.ban_chat_member(chat_id=gid, user_id=int(uid))
                                await bot.unban_chat_member(chat_id=gid, user_id=int(uid))
                            except: pass
                        db["users"][uid]["premium_until"] = None
                        save_db(db)
                        try: await bot.send_message(chat_id=int(uid), text="⚠️ <b>VIP obunangiz muddati yakunlandi. Tizim sizni avtomatik ravishda guruhlardan chiqardi!</b>")
                        except: pass

            # 2. FOYDALANUVCHILAR RE-POST INTERVALI (ASOSIY GURUH VA YANGI GURUH UCHUN)
            tasks = load_tasks()
            ydb = load_yuk_db()
            bot_info = await bot.get_me()
            
            for uid, task in list(tasks.items()):
                if not check_premium(int(uid)): continue
                    
                last_sent = datetime.fromisoformat(task["last_sent"]).astimezone(UZB_TZ)
                diff_minutes = (now - last_sent).total_seconds() / 60
                
                if diff_minutes >= task["interval"]:
                    yuk_data = ydb.get(task["yuk_id"])
                    if yuk_data:
                        cap = get_premium_caption(yuk_data["text"][:150] + "...", "🔂 AVTO RE-POST")
                        kb = get_group_kb(bot_info.username, task["yuk_id"])
                        
                        chat = NEW_GROUP_ID if task["target_group"] == "new" else GROUP_ID
                        tid = task.get("target_topic", None)
                        
                        try:
                            await bot.send_message(chat_id=chat, text=cap, reply_markup=kb, message_thread_id=tid)
                            tasks[uid]["last_sent"] = now.isoformat()
                            save_tasks(tasks)
                        except: pass
                            
        except Exception as ex: logging.error(f"Cron error: {ex}")
        await asyncio.sleep(30)

async def main():
    asyncio.create_task(auto_cron_job())
    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)

if __name__ == '__main__':
    asyncio.run(main())
