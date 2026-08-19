# ⚡️ VUsername Hikka Bot

![Author](https://img.shields.io/badge/Author-%40lceta-blue?style=for-the-badge)
![Version](https://img.shields.io/badge/Version-2.0.1-orange?style=for-the-badge)
![Platform](https://img.shields.io/badge/Platform-Hikka%20Userbot-purple?style=for-the-badge)

## 📥 Installation

```text
.dlm https://raw.githubusercontent.com/lcetaa/VUsername-hikka-bot/refs/heads/main/VUsername.py
```

## 💻 Commands

| Command | Description |
| :--- | :--- |
| `.v <username>` | Check if a username is available, with a "claim" button |
| `.vai <username>` | AI price estimate with Fragment marketplace data |
| `.vfind <number> \| <prefix>` | Search for available usernames (random or by prefix) |
| `.vstop` | Stop a running search |
| `.vupdate [-f\|--force]` | Update the module to the latest version |

## ⚙️ Config

| Option | Default |
| :--- | :--- |
| `channel_title` — title of the temporary channel created on claim | `This username is reserved.` |
| `channel_about` — description of the temporary channel | `Made by {me}` |
| `channel_avatar_url` — avatar set on the temporary channel | *default banner* |
| `channel_message` — first message posted after claiming | `Interested in this username? Contact {me}` |
| `delay_min` — `.vfind` minimum delay between checks, sec | `1.2` |
| `delay_max` — `.vfind` maximum delay between checks, sec | `2.0` |
| `ai_provider` — AI provider for `.vai` (`auto` / `gemini` / `groq`) | `auto` |
| `ai_api_keys` — Gemini API key(s), comma-separated | — |
| `ai_model` — Gemini model | `gemini-3.5-flash` |
| `groq_api_keys` — Groq API key(s), comma-separated | — |
| `groq_model` — Groq model | `openai/gpt-oss-120b` |

## 🎯 Features

Checking a username with `.v` shows whether it's free, and if it's taken — cross-references it against **Fragment** to show whether it was sold, its price, and a direct link.

`.vai` gives an AI-powered valuation: a price range in USD, pros/cons, and — if the username clearly matches a known brand or public figure — a note about it.

`.vfind` searches for available usernames either randomly or by a given prefix, with live progress and pagination through the results; claim any of them straight from the inline buttons.

Claiming a username (`.v` → "claim") creates a temporary channel to reserve it — title, description, avatar, and first post are all configurable above.

## 🔑 AI Key

Get a free Gemini key at [aistudio.google.com](https://aistudio.google.com) and set it via `.config VUsername ai_api_keys`.

You can add multiple keys, comma-separated, to speed up evaluation and reduce the chance of hitting the quota. A Groq key can be added the same way as a fallback/alternative provider.

## 📞 Support

[@lceta](https://t.me/lceta)
