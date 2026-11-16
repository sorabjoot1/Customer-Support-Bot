# Customer Support Bot

Intelligent NovaMart customer support chatbot powered by OpenRouter LLMs. Handles FAQs, complaints, conversation history, and human escalation.

## Features

- Natural-language customer support replies via OpenRouter
- FAQ-aware answers for returns, shipping, refunds, warranties
- Conversation history per session
- Automatic escalation for complex / sensitive queries
- Modern chat UI with loading states and error toasts

## Project structure

```
Customer_Support_Bot/
├── backend/
│   ├── main.py          # FastAPI routes
│   ├── llm.py           # OpenRouter client
│   ├── faq.py           # FAQ knowledge + prompts
│   └── config.py
├── frontend/
│   ├── index.html
│   ├── styles.css
│   └── app.js
├── .env.example
├── requirements.txt
└── README.md
```

## Setup

```powershell
cd Customer_Support_Bot
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
copy .env.example .env
```

Edit `.env` and set:

```
OPENROUTER_API_KEY=sk-or-v1-your-real-key
```

Get a key at [https://openrouter.ai/keys](https://openrouter.ai/keys).

## Run

From the `Customer_Support_Bot` folder:

```powershell
uvicorn backend.main:app --host 0.0.0.0 --port 8001 --reload
```

Open: [http://127.0.0.1:8001](http://127.0.0.1:8001)

## API

| Method | Path | Description |
|--------|------|-------------|
| GET | `/api/health` | Health + LLM config status |
| POST | `/api/session` | Create chat session |
| POST | `/api/chat` | Send message |
| GET | `/api/history/{session_id}` | Get history |
| DELETE | `/api/history/{session_id}` | Clear history |

## Notes

- Conversation history is stored in memory for the running process.
- Port default: **8001**
