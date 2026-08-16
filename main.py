import os
import logging
import asyncio
from typing import Optional, Dict, Any, List
from fastapi import FastAPI, Request, Response, status
import httpx
from aiogram import Bot, Dispatcher, Router, F
from aiogram.types import (
    Update, Message, CallbackQuery,
    InlineKeyboardMarkup, InlineKeyboardButton
)
from aiogram.filters import Command
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode

from config import settings

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

app = FastAPI(title="SB S24 Sports Update Bot")

bot = Bot(
    token=settings.BOT_TOKEN,
    default=DefaultBotProperties(parse_mode=ParseMode.HTML)
)
dp = Dispatcher()
router = Router()

# In-memory simple storage for active users and state tracking
ACTIVE_USERS: set = set()

# Helper: Khmer Main Menu Keyboard
def get_main_menu_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="🏠 ទំព័រដើម", callback_data="menu_home"),
            InlineKeyboardButton(text="🔔 ការប្រកួតថ្មី", callback_data="menu_upcoming")
        ],
        [
            InlineKeyboardButton(text="📅 ការប្រកួតថ្ងៃនេះ", callback_data="menu_today"),
            InlineKeyboardButton(text="🔴 Live", callback_data="menu_live")
        ],
        [
            InlineKeyboardButton(text="✅ លទ្ធផល", callback_data="menu_results"),
            InlineKeyboardButton(text="⚽ បាល់ទាត់", callback_data="menu_football")
        ],
        [
            InlineKeyboardButton(text="🏆 លីគ", callback_data="menu_leagues"),
            InlineKeyboardButton(text="📊 ស្ថិតិ", callback_data="menu_stats")
        ],
        [
            InlineKeyboardButton(text="ℹ️ អំពី", callback_data="menu_about")
        ]
    ])

def get_sample_matches_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="⚽ ក្រុម ក vs ក្រុម ខ (គំរូ)", callback_data="match_sample_1")
        ],
        [
            InlineKeyboardButton(text="⚽ ក្រុម គ vs ក្រុម ង (គំរូ)", callback_data="match_sample_2")
        ],
        [
            InlineKeyboardButton(text="⬅️ ត្រឡប់ក្រោយ", callback_data="menu_home")
        ]
    ])

# Resilient Sports API Fetcher with full error handling
async def fetch_sports_data(endpoint_path: str = "") -> Optional[Any]:
    if not settings.SPORTS_API_URL or not settings.SPORTS_API_KEY:
        return None
    url = f"{settings.SPORTS_API_URL.rstrip('/')}/{endpoint_path.lstrip('/')}"
    headers = {
        "Authorization": f"Bearer {settings.SPORTS_API_KEY}",
        "x-apisports-key": settings.SPORTS_API_KEY
    }
    try:
        async with httpx.AsyncClient(timeout=8.0) as client:
            response = await client.get(url, headers=headers)
            if response.status_code == 200:
                return response.json()
            else:
                logger.warning(f"Sports API returned status code {response.status_code}")
    except httpx.TimeoutException:
        logger.error("Sports API request timed out.")
    except httpx.RequestError as e:
        logger.error(f"Sports API connection error: {e}")
    except Exception as e:
        logger.error(f"Unexpected API error: {e}")
    return None

# Commands & Handlers
@router.message(Command("start"))
async def cmd_start(message: Message):
    ACTIVE_USERS.add(message.from_user.id)
    welcome_text = (
        f"សួស្តី <b>{message.from_user.full_name}</b>! សូមស្វាគមន៍មកកាន់ <b>មានជ័យកីឡាភ្នាល់ - SB S24</b>\n\n"
        "កណ្តាលព័ត៌មានកីឡា ការប្រកួត Live លទ្ធផល និងស្ថិតិយ៉ាងសម្បូរបែប។\n"
        "សូមជ្រើសរើសមុខងារខាងក្រោម៖"
    )
    await message.answer(welcome_text, reply_markup=get_main_menu_keyboard())

@router.message(Command("help"))
async def cmd_help(message: Message):
    help_text = (
        "<b>ជំនួយការប្រើប្រាស់ (Help Guide)</b>\n\n"
        "បញ្ជីបញ្ជាដែលមាន៖\n"
        "/start - ចាប់ផ្តើមប្រើប្រាស់\n"
        "/help - បង្ហាញជំនួយ\n"
        "/menu - បង្ហាញម៉ឺនុយដើម\n"
        "/today - ការប្រកួតថ្ងៃនេះ\n"
        "/live - ការប្រកួតផ្សាយផ្ទាល់\n"
        "/results - លទ្ធផលប្រកួត\n"
        "/leagues - ព័ត៌មានលីគ\n"
        "/about - អំពីពួកយើង"
    )
    await message.answer(help_text, reply_markup=get_main_menu_keyboard())

@router.message(Command("menu"))
async def cmd_menu(message: Message):
    await message.answer("🏠 <b>ម៉ឺនុយមេ (Main Menu)</b>", reply_markup=get_main_menu_keyboard())

@router.message(Command("today"))
async def cmd_today(message: Message):
    data = await fetch_sports_data("fixtures/today")
    if not data:
        await message.answer(
            "📅 <b>ការប្រកួតថ្ងៃនេះ</b>\n\n"
            "⚠️ <i>ទិន្នន័យកីឡាផ្ទាល់មិនទាន់មាន ឬគ្មានการกำหนด API ទេ។ សូមជ្រើសរើសការប្រកួតគំរូខាងក្រោម៖</i>",
            reply_markup=get_sample_matches_keyboard()
        )
    else:
        await message.answer(f"📅 <b>ការប្រកួតថ្ងៃនេះ:</b>\n<pre>{str(data)[:3500]}</pre>", reply_markup=get_main_menu_keyboard())

@router.message(Command("live"))
async def cmd_live(message: Message):
    data = await fetch_sports_data("fixtures/live")
    if not data:
        await message.answer(
            "🔴 <b>ការប្រកួតផ្សាយផ្ទាល់ (Live Matches)</b>\n\n"
            "⚠️ <i>គ្មានទិន្នន័យ Live ពី API នាពេលនេះទេ។ ប្រព័ន្ធមិនបង្ហាញទិន្នន័យក្លែងក្លាយទេ។</i>",
            reply_markup=get_main_menu_keyboard()
        )
    else:
        await message.answer(f"🔴 <b>Live Matches:</b>\n<pre>{str(data)[:3500]}</pre>", reply_markup=get_main_menu_keyboard())

@router.message(Command("results"))
async def cmd_results(message: Message):
    data = await fetch_sports_data("fixtures/results")
    if not data:
        await message.answer(
            "✅ <b>លទ្ធផលការប្រកួត (Match Results)</b>\n\n"
            "⚠️ <i>មិនអាចទាញយកលទ្ធផលពី API បានទេ។</i>",
            reply_markup=get_main_menu_keyboard()
        )
    else:
        await message.answer(f"✅ <b>លទ្ធផល:</b>\n<pre>{str(data)[:3500]}</pre>", reply_markup=get_main_menu_keyboard())

@router.message(Command("leagues"))
async def cmd_leagues(message: Message):
    data = await fetch_sports_data("leagues")
    if not data:
        await message.answer(
            "🏆 <b>ព័ត៌មានលីគ (League Information)</b>\n\n"
            "• Premier League\n• La Liga\n• Serie A\n• Bundesliga\n\n"
            "⚠️ <i>ទិន្នន័យលីគជាក់លាក់ទាមទារការកំណត់ API ឱ្យបានត្រឹមត្រូវ។</i>",
            reply_markup=get_main_menu_keyboard()
        )
    else:
        await message.answer(f"🏆 <b>លីគ:</b>\n<pre>{str(data)[:3500]}</pre>", reply_markup=get_main_menu_keyboard())

@router.message(Command("about"))
async def cmd_about(message: Message):
    about_text = (
        "ℹ️ <b>អំពី មានជ័យកីឡាភ្នាល់ - SB S24</b>\n\n"
        "ប្រព័ន្ធផ្តល់ព័ត៌មានកីឡា ការប្រកួត Live លទ្ធផល និងការវិភាគស្ថិតិសាធារណៈ។\n\n"
        "ចំណាំ៖ ប្រព័ន្ធនេះមិនគាំទ្រ ឬដំណើរការការភ្នាល់ ការដាក់ប្រាក់ ដកប្រាក់ ឬធានាលទ្ធផលប្រាក់ពិតប្រាកដទេ។"
    )
    await message.answer(about_text, reply_markup=get_main_menu_keyboard())

# Admin Commands
@router.message(Command("admin"))
async def cmd_admin(message: Message):
    if message.from_user.id != settings.ADMIN_ID:
        await message.answer("⛔ អ្នកគ្មានសិទ្ធិប្រើប្រាស់បញ្ជាទុគ្គលិកនេះទេ។")
        return
    admin_text = (
        "🛠 <b>ផ្ទាំងគ្រប់គ្រងរដ្ឋបាល (Admin Panel)</b>\n\n"
        "/admin_stats - មើលស្ថិតិអ្នកប្រើប្រាស់\n"
        "/admin_broadcast [សារ] - ផ្ញើសារផ្សាយជូនអ្នកប្រើប្រាស់"
    )
    await message.answer(admin_text)

@router.message(Command("admin_stats"))
async def cmd_admin_stats(message: Message):
    if message.from_user.id != settings.ADMIN_ID:
        return
    await message.answer(f"📊 <b>ស្ថិតិប្រព័ន្ធ:</b>\n- អ្នកប្រើប្រាស់សរុបក្នុងអង្គចងចាំ: {len(ACTIVE_USERS)}")

@router.message(Command("admin_broadcast"))
async def cmd_admin_broadcast(message: Message):
    if message.from_user.id != settings.ADMIN_ID:
        return
    parts = message.text.split(maxsplit=1)
    if len(parts) < 2:
        await message.answer("⚠️ សូមបញ្ចូលសារ៖ <code>/admin_broadcast [សាររបស់អ្នក]</code>")
        return
    broadcast_text = parts[1]
    success_count = 0
    for uid in ACTIVE_USERS:
        try:
            await bot.send_message(chat_id=uid, text=f"📢 <b>សេចក្តីប្រកាសពីរដ្ឋបាល៖</b>\n\n{broadcast_text}")
            success_count += 1
        except Exception:
            pass
    await message.answer(f"✅ បានផ្សាយសារជោគជ័យទៅកាន់អ្នកប្រើប្រាស់ចំនួន {success_count} នាក់។")

# Callback Handlers for Menus and Sample Matches
@router.callback_query(F.data.startswith("menu_"))
async def callback_menu(callback: CallbackQuery):
    action = callback.data.split("_")[1]
    await callback.answer()
    
    if action == "home":
        await callback.message.edit_text(
            "🏠 <b>មានជ័យកីឡាភ្នាល់ - SB S24</b>\n\nសូមជ្រើសរើសមុខងារខាងក្រោម៖",
            reply_markup=get_main_menu_keyboard()
        )
    elif action == "upcoming":
        await callback.message.edit_text(
            "🔔 <b>ការប្រកួតថ្មី (Upcoming Fixtures)</b>\n\nសូមជ្រើសរើសការប្រកួតគំរូខាងក្រោម៖",
            reply_markup=get_sample_matches_keyboard()
        )
    elif action == "today":
        await callback.message.edit_text(
            "📅 <b>ការប្រកួតថ្ងៃនេះ</b>\n\nគ្មានទិន្នន័យ API ពេលនេះទេ។",
            reply_markup=get_sample_matches_keyboard()
        )
    elif action == "live":
        await callback.message.edit_text(
            "🔴 <b>ការប្រកួតផ្សាយផ្ទាល់ (Live)</b>\n\nគ្មានការប្រកួត Live ពេលនេះទេ។",
            reply_markup=get_main_menu_keyboard()
        )
    elif action == "results":
        await callback.message.edit_text(
            "✅ <b>លទ្ធផលការប្រកួត</b>\n\nគ្មានទិន្នន័យពេលនេះទេ។",
            reply_markup=get_main_menu_keyboard()
        )
    elif action == "football":
        await callback.message.edit_text(
            "⚽ <b>បាល់ទាត់ (Football)</b>\n\nជ្រើសរើសការប្រកួតដើម្បីមើលស្ថិតិ៖",
            reply_markup=get_sample_matches_keyboard()
        )
    elif action == "leagues":
        await callback.message.edit_text(
            "🏆 <b>ព័ត៌មានលីគ</b>\n\n- Premier League\n- La Liga\n- Serie A",
            reply_markup=get_main_menu_keyboard()
        )
    elif action == "stats":
        await callback.message.edit_text(
            "📊 <b>ស្ថិតិការប្រកួត</b>\n\nជ្រើសរើសការប្រកួតខាងក្រោមដើម្បីមើលការវិភាគស្ថិតិ។",
            reply_markup=get_sample_matches_keyboard()
        )
    elif action == "about":
        await callback.message.edit_text(
            "ℹ️ <b>អំពី មានជ័យកីឡាភ្នាល់ - SB S24</b>\nប្រព័ន្ធព័ត៌មានកីឡា និងស្ថិតិ។",
            reply_markup=get_main_menu_keyboard()
        )

@router.callback_query(F.data.startswith("match_"))
async def callback_match_detail(callback: CallbackQuery):
    await callback.answer()
    match_id = callback.data.split("_")[2]
    
    if match_id == "1":
        analysis_text = (
            "⚽ <b>Match Analysis & Statistics</b>\n\n"
            "<b>ក្រុម ក vs ក្រុម ខ</b>\n"
            "⏰ ម៉ោង: 20:00 | 🏟️ កីឡដ្ឋាន: National Stadium\n\n"
            "🔥 <b>Recent Form</b>\n"
            "ក្រុម ក: W-W-D-W-W\n"
            "ក្រុម ខ: W-D-L-W-D\n\n"
            "⚽ <b>Scoring Statistics</b>\n"
            "ក្រុម ក: 2.1 goals/game\n"
            "ក្រុម ខ: 1.6 goals/game\n\n"
            "📊 <b>Statistical Observation:</b>\n"
            "ក្រុម ក មានទម្រង់លេងនិងស្ថិតិស៊ុតបញ្ចូលទីរឹងមាំជាង។\n\n"
            "🎯 <i>ការប៉ាន់ស្មានផ្អែកលើស្ថិតិ (Statistical estimate): ក្រុម ក មានភាគរយអំណោយផលជាង ប៉ុន្តែមិនមែនជាការធានាលទ្ធផលទេ។</i>"
        )
    else:
        analysis_text = (
            "⚽ <b>Match Analysis & Statistics</b>\n\n"
            "<b>ក្រុម គ vs ក្រុម ង</b>\n"
            "⏰ ម៉ោង: 22:30 | 🏟️ កីឡដ្ឋាន: City Arena\n\n"
            "🔥 <b>Recent Form</b>\n"
            "ក្រុម គ: L-W-W-D-L\n"
            "ក្រុម ង: W-W-W-W-D\n\n"
            "⚽ <b>Scoring Statistics</b>\n"
            "ក្រុម គ: 1.2 goals/game\n"
            "ក្រុម ង: 2.3 goals/game\n\n"
            "📊 <b>Statistical Observation:</b>\n"
            "ក្រុម ង មានទម្រង់ការប្រកួតក្រៅដីល្អប្រសើរ។\n\n"
            "🎯 <i>ការប៉ាន់ស្មានផ្អែកលើស្ថិតិ (Statistical estimate): ក្រុម ង មានស្ថិតិអំណោយផលខ្ពស់ ប៉ុន្តែមិនមែនជាការធានាលទ្ធផលទេ។</i>"
        )
        
    await callback.message.edit_text(analysis_text, reply_markup=get_main_menu_keyboard())

dp.include_router(router)

# FastAPI Lifespan Webhook Setup
@app.on_event("startup")
async def on_startup():
    webhook_url = f"{settings.RENDER_EXTERNAL_URL.rstrip('/')}/webhook/{settings.WEBHOOK_SECRET}"
    await bot.set_webhook(webhook_url)
    logger.info(f"Webhook set to: {webhook_url}")

@app.on_event("shutdown")
async def on_shutdown():
    await bot.delete_webhook()
    await bot.session.close()
    logger.info("Bot stopped and webhook deleted.")

@app.get("/health")
async def health_check():
    return {"status": "ok"}

@app.post(f"/webhook/{settings.WEBHOOK_SECRET}")
async def telegram_webhook(request: Request) -> Response:
    json_data = await request.json()
    update = Update.model_validate(json_data, context={"bot": bot})
    await dp.feed_update(bot, update)
    return Response(status_code=status.HTTP_200_OK)
Citation: For all generated content, I want you to add citations at the end of each paragraph, like a sentence. [2025-12-28]

