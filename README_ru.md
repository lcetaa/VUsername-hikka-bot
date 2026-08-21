# ⚡️ VUsername Hikka Bot

![Author](https://img.shields.io/badge/Author-%40lceta-blue?style=for-the-badge)
![Version](https://img.shields.io/badge/Version-2.0.3-orange?style=for-the-badge)
![Platform](https://img.shields.io/badge/Platform-Hikka%20Userbot-purple?style=for-the-badge)

## 📥 Установка

```text
.dlm https://raw.githubusercontent.com/lcetaa/VUsername-hikka-bot/refs/heads/main/VUsername.py
```

## 💻 Команды

| Команда | Описание |
| :--- | :--- |
| `.v <юзернейм>` | Проверить доступность юзернейма, с кнопкой «занять» |
| `.vai <юзернейм>` | ИИ-оценка стоимости с учётом данных Fragment |
| `.vfind <число> \| <префикс>` | Поиск свободных юзернеймов (случайных или по префиксу) |
| `.vstop` | Остановить запущенный поиск |
| `.vupdate [-f\|--force]` | Обновить модуль до последней версии |

## ⚙️ Конфиг

| Опция | По умолчанию |
| :--- | :--- |
| `channel_title` — название временного канала при захвате | `This username is reserved.` |
| `channel_about` — описание временного канала | `Made by {me}` |
| `channel_avatar_url` — аватар временного канала | *дефолтный баннер* |
| `channel_message` — первое сообщение после захвата | `Interested in this username? Contact {me}` |
| `delay_min` — минимальная задержка `.vfind` между проверками, сек | `1.2` |
| `delay_max` — максимальная задержка `.vfind` между проверками, сек | `2.0` |
| `ai_provider` — ИИ-провайдер для `.vai` (`auto` / `gemini` / `groq`) | `auto` |
| `ai_api_keys` — ключ(и) Gemini API, через запятую | — |
| `ai_model` — модель Gemini | `gemini-3.5-flash` |
| `groq_api_keys` — ключ(и) Groq API, через запятую | — |
| `groq_model` — модель Groq | `openai/gpt-oss-120b` |

## 🎯 Возможности

Проверка юзернейма через `.v` показывает, свободен ли он, а если занят — сверяется с **Fragment**: был ли продан, его цену и прямую ссылку.

`.vai` даёт ИИ-оценку: диапазон цены в USD, плюсы/минусы, и — если юзернейм явно совпадает с известным брендом или личностью — заметку об этом.

`.vfind` ищет свободные юзернеймы случайно или по заданному префиксу, с прогрессом в реальном времени и пагинацией по результатам; занять любой из них можно прямо из inline-кнопок.

Захват юзернейма (`.v` → «занять») создаёт временный канал для его резервации — название, описание, аватар и первый пост настраиваются выше.

## 🔑 ИИ-ключ

Получи бесплатный ключ Gemini на [aistudio.google.com](https://aistudio.google.com) и укажи его через `.config VUsername ai_api_keys`.

Можно добавить несколько ключей через запятую — это ускоряет оценку и снижает риск упереться в квоту. Ключ Groq добавляется аналогично, как запасной/альтернативный провайдер.

## 📞 Поддержка

[@lceta](https://t.me/lceta)
