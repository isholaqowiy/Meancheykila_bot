# មានជ័យកីឡាភ្នាល់ - SB S24 Sports Update Bot

A production-ready Khmer-language sports fixture, live updates, and match results Telegram bot built with **Python 3.11+**, **aiogram 3.x**, and **FastAPI**, optimized for deployment on **Render.com**.

## Project Files
- `main.py` - Core bot logic, Khmer inline keyboards, handlers, and FastAPI webhook server.
- `config.py` - Environment configuration via Pydantic Settings.
- `requirements.txt` - Python dependencies list.
- `render.yaml` - Render blueprint configuration.
- `README.md` - Documentation.

## Local Configuration (.env.example)
Create a `.env` file locally for development using these variables:
```env
BOT_TOKEN=your_telegram_bot_token_here
ADMIN_ID=your_telegram_numeric_id_here
SPORTS_API_URL=[https://api.your-sports-provider.com](https://api.your-sports-provider.com)
SPORTS_API_KEY=your_api_key_here
WEBHOOK_SECRET=your_secure_random_secret_string
RENDER_EXTERNAL_URL=[https://your-service-name.onrender.com](https://your-service-name.onrender.com)

