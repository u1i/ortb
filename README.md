# OpenRouterTelegram LLM Chatbot Framework

A reusable Python framework for building Telegram chat-bots powered by large language models (LLMs) via the [OpenRouter](https://openrouter.ai) API.  
Features:

* **Text, voice & image** handling – voice is auto-transcribed with Whisper.
* **Conversation persistence** in Redis (keyed by bot name / user id / conversation id).
* **User whitelist** stored in Redis.
* Fully **environment-driven configuration** via `.env`.
* Simple async architecture using `python-telegram-bot` v21.

---

## Quick start

1. **Clone** this repo and create a Python 3.11 virtualenv:

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

2. **Create `.env`** by copying `env_template` and filling in values:

```bash
cp env_template .env
# edit .env with your favourite editor
```

Minimal required variables:

```
BOT_NAME=monty
TELEGRAM_BOT_TOKEN=<your telegram token>
OPENROUTER_API_KEY=<your openrouter key>
OPENROUTER_LLM=openai/gpt-4o
```

If the chosen model supports temperature, leave `OPENROUTER_LLM_TEMPERATURE_SUPPORTED=true`; otherwise set it to `false`.

3. **Get Redis** (local or hosted).  Update `REDIS_HOST/PORT/PASSWORD` in `.env`.

4. **Whitelist** yourself:  in Redis set a key `<BOT_NAME>.<your_telegram_user_id>` with any value.  Example with `redis-cli`:

```bash
SET monty.123456 true EX 31536000  # 1-year TTL
```

5. **Run the bot**:

```bash
python -m bot.main
```

The bot should start and greet you when you `/start` it in Telegram.

---

## How it works

* **Handlers** in `bot/handlers.py` route `/start`, `/help`, text, voice, and photo messages.
* **Conversation** objects in `bot/session.py` persist message history (`system`, `user`, `assistant`) in JSON arrays with a TTL (`HISTORY_TTL_SECONDS`).  A fresh conversation id is generated on every `/start` (timestamp-based).
* **LLM calls** happen in `bot/llm.py` via the OpenAI SDK, pointed at the OpenRouter endpoint.  Temperature is only sent when the model supports it.
* **Settings** are loaded once at startup from `.env` via `bot/config.py`.

---

## Deploying

The framework is designed so students can fork and redeploy easily:

1. Create a new Telegram bot with `@BotFather` and grab the token.
2. Obtain an OpenRouter key (or switch `OPENROUTER_LLM` to an OpenAI model & key).
3. Provision a Redis instance (e.g. Redis Cloud free tier).
4. Set the required env vars, push to your own repo, and deploy on a server / fly.io / Render / etc.

---

## Extending

* Add new commands by creating functions in `bot/handlers.py` and registering them in `bot/main.py`.
* Swap out the LLM by changing `OPENROUTER_LLM` (and turning off temperature if unsupported).
* Replace Redis with another datastore by implementing the small API in `bot/redis_store.py`.

PRs welcome!
