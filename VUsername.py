#  This file is part of lceta modules
#  Copyright (c) 2026 lceta
#  This software is released under the MIT License.
#  https://opensource.org/licenses/MIT

# Name: VUsername
# meta banner: https://raw.githubusercontent.com/lcetaa/VUsername-hikka-bot/refs/heads/main/meta_banner.png
# meta pic: https://raw.githubusercontent.com/lcetaa/VUsername-hikka-bot/refs/heads/main/meta_pic.png
# meta tags: usernames, fragment, telegram, ai, username_checker, automation
# meta developer: @lceta

__version__ = (2, 0, 1)

# ░█░░░█▀▀░█▀▀░▀█▀░█▀█
# ░█░░░█░░░█▀▀░░█░░█▀█
# ░▀▀▀░▀▀▀░▀▀▀░░▀░░▀░▀

import asyncio,hashlib,html,io,ipaddress,json,logging,random,re,socket,time,unicodedata
from enum import Enum
from urllib.parse import urljoin,urlparse
import aiohttp
from bs4 import BeautifulSoup
from telethon.tl import functions
from telethon.tl.types import InputChatUploadedPhoto
from .. import loader,utils
logger=logging.getLogger(__name__)
EMOJI_IDS={"error":("5220197908342648622","❗️"),"boom":("5219901967916084166","💥"),"fragment":("5219943216781995020","⚡️"),"link":("5902449142575141204","🔗"),"clock":("5985616167740379273","⏰"),"coin":("6039802097916974085","🪙"),"robot":("5406683326750691396","🤖"),"money":("5893473283696759404","💰"),"card":("5902056028513505203","💳"),"star":("5208968969750330825","⭐"),"trophy":("6021644067111180663","🏆"),"success":("5287692511945437157","✅"),"cross":("5287611315588707430","❌"),"person":("5442879640379076105","👤"),"stop":("5287372146039861774","⛔"),"search":("5404439768979252377","🔍"),"sad":("5456343972010016640","😔"),"green":("5339135753316222622","🟢"),"lock":("5404552559115408271","🔒"),"chart":("5994378914636500516","📈"),"stats":("5895444149699612825","📊"),"tag":("6021594546138257831","🏷"),"fire":("5287404392654319394","🔥"),"warning":("6019102674832595118","⚠️"),"hourglass":("5402355073458123173","⏳"),}

def emoji(name:str,glyph:str=None)->str:
    """Возвращает premium-эмодзи тег по имени из EMOJI_IDS."""
    eid,default_glyph=EMOJI_IDS[name]
    return f"<tg-emoji emoji-id='{eid}'>{glyph or default_glyph}</tg-emoji>"

_TG_EMOJI_RE=re.compile(r"<tg-emoji[^>]*>(.*?)</tg-emoji>",re.DOTALL)

def plain_emoji(text):
    """Убирает тег <tg-emoji>, оставляя обычный юникод-эмодзи.
    Нужно для inline-сообщений бота (self.inline.form/call.edit/call.answer) —
    Bot API не поддерживает кастомные premium-эмодзи в этом теге, из-за чего
    он показывается как сырой текст. В обычных сообщениях через аккаунт
    (utils.answer) тег работает штатно и его трогать не нужно."""
    if not text or"<tg-emoji"not in text:return text
    return _TG_EMOJI_RE.sub(r"\1",text)

class UsernameStatus(Enum):
    AVAILABLE="available";UNAVAILABLE="unavailable";INVALID="invalid"
    PURCHASABLE="purchasable";FLOOD_WAIT="flood_wait";ERROR="error"

class FragmentStatus(Enum):
    SOLD="sold";AVAILABLE="available";UNAVAILABLE="unavailable";NOT_FOUND="not_found";ERROR="error"

class GrabStatus(Enum):
    SUCCESS="success";SUCCESS_AVATAR_FAILED="success_avatar_failed"
    SUCCESS_FIRSTPOST_FAILED="success_firstpost_failed";SUCCESS_AVATAR_FIRSTPOST_FAILED="success_avatar_firstpost_failed"
    USERNAME_TAKEN="username_taken";USERNAME_INVALID="username_invalid";USERNAME_PURCHASABLE="username_purchasable"
    FLOOD_WAIT="flood_wait";PUBLIC_LIMIT="public_limit";CHANNEL_LIMIT="channel_limit"
    USER_RESTRICTED="user_restricted";BAD_TITLE="bad_title";BAD_ABOUT="bad_about";NO_RIGHTS="no_rights";ERROR="error"

@loader.tds
class VUsernameMod(loader.Module):
    """Check usernames, AI valuation, and search for available ones via Fragment."""
    strings={"name":"VUsername","no_args":"<b>{E_error} specify a username!!</b>","bad_length":"<b>{E_error} username must be 4 to 32 characters long!!</b>","bad_chars":"<b>{E_error} only latin letters, digits and _ are allowed in the username!!</b>","available":"username <b>@{username}</b> is available!!!\n\nwant to claim this username?","available_no_inline":"{E_boom} <b>@{username}</b> is available, but the inline form could not be created. Try the command again later.","grab_button":"✔ claim","close_button":"✖ close","checking":"<b>checking.. @{username}...</b>","fragment_sold":"{E_error} <b>@{username}</b> was sold on Fragment.\n\n{E_fragment} <b>found on Fragment:</b>\n{price_line}{E_link} <b>link:</b> <a href=\"{url}\">{url}</a>","fragment_available":"{E_error} <b>@{username}</b> is taken.\n\n{E_fragment} <b>found on Fragment:</b>\n{price_line}{E_link} <b>link:</b> <a href=\"{url}\">{url}</a>","fragment_unavailable":"{E_error} <b>@{username}</b> is taken or unavailable for assignment.\n\n{E_fragment} <b>Fragment:</b> <code>Unavailable</code> — not for sale.\n{E_link} <b>link:</b> <a href=\"{url}\">{url}</a>","price_line":"{E_coin} <b>price:</b> <code>{price}</code> GRAM\n","occupied":"{E_error} <b>@{username}</b> is taken or unavailable for assignment.","purchasable":"{E_coin} <b>@{username}</b> is only available as a collectible username.","fragment_error":"\n\n{E_error} <i>Fragment could not be checked temporarily.</i>","check_error":"{E_error} <b>Failed to check @{username} due to a Telegram error. Try again later.</b>","flood_wait":"<b>{E_clock} Telegram limited checks. Try again in {wait}.</b>","flood_wait_unknown":"{E_error} <b>@{username}</b> — <b>unknown</b>.","flood_wait_fragment_available":"{E_error} <b>@{username}</b> — <b>taken</b>.\n\n{E_fragment} <b>found on Fragment:</b>\n{price_line}{E_link} <b>link:</b> <a href=\"{url}\">{url}</a>","flood_wait_fragment_sold":"{E_error} <b>@{username}</b> — <b>possibly taken</b>.\n\n{E_fragment} <b>Fragment:</b> username was sold.\n{price_line}{E_link} <b>link:</b> <a href=\"{url}\">{url}</a>","flood_wait_fragment_unavailable":"{E_error} <b>@{username}</b> — <b>unknown</b>.\n\n{E_fragment} <b>Fragment:</b> <code>Unavailable</code> — not for sale.\n{E_link} <b>link:</b> <a href=\"{url}\">{url}</a>","flood_wait_fragment_note":"\n\n<b>{E_clock} FloodWait: {wait}.</b>\n<i>Because of the FloodWait it's impossible to know for sure whether the username is taken. But you can try to claim it by tapping the inline button below.</i>","prefix_bad":"<b>{E_error} prefix must contain only latin letters, digits and _ and be no longer than 31 characters.</b>","count_bad":"<b>{E_error} the check count must be a number from 1 to {maximum}.</b>","vfind_usage":"<b>{E_error} format: <code>.vfind</code>, <code>.vfind 100</code> or <code>.vfind user 100</code>.</b>","ai_evaluating":"<b>{E_robot} AI is analyzing @{username}...</b>","ai_result":"{body}","ai_no_key":"<b>{E_error} No API key set for AI evaluation.</b>\n\nGet key(s) at <code>aistudio.google.com</code> and set them via:\n<code>.config VUsername</code> → <code>ai_api_keys</code>\nYou can specify multiple keys separated by commas — this speeds things up and lowers the risk of hitting the quota.","ai_error_quota":"{E_error} Gemini API quota exceeded. Check your limits in the settings.","ai_error_quota_retry":"{E_error} Gemini API quota exceeded.\nTry again in about {seconds} sec.","ai_error_auth":"{E_error} <b>Invalid Gemini API key. Check your settings.</b>","ai_error_server":"{E_error} Temporary Gemini error. Try again later.","ai_error_model_not_found":"{E_error} Gemini model unavailable.\n\nCheck: <code>.config VUsername ai_model</code>\nRecommended: <code>gemini-3.5-flash</code>","ai_error_unknown":"{E_error} <b>AI error:</b> {error}","ai_note_available":"{E_green} <b>Available</b>, not on Fragment — claim: <code>.v {username}</code>\n","ai_note_taken_regular":"{E_lock} <b>The username is taken by a regular user, the estimate is theoretical.</b>\n","find_running":"<b>{E_hourglass} a search is already running, please wait...</b>","find_stop_button":"⛔ Stop","find_stopping":"Stopping the search...","find_start":"<b>{E_search} searching for available usernames {mode}...\nchecked: 0 / {total}</b>","find_progress":"<b>{E_search} searching {mode}...\nchecked: {checked} / {total}\n\nfound: {found_count}\n{preview}</b>","find_nothing":"<b>{E_sad} no available usernames found {mode}.\nTry a different prefix or run it again.</b>","find_stopped":"<b>{E_stop} search stopped.\nChecked: {checked} / {total}.\nFound: {found_count}.</b>","find_flood":"<b>{E_clock} search stopped due to a Telegram limit.\nChecked: {checked} / {total}.\nFloodWait: {wait}.</b>","find_error":"<b>{E_error} search stopped due to a Telegram error.\nChecked: {checked} / {total}. Try again later.</b>","find_preview_empty":"nothing yet...","find_result":"{E_boom} <b>found available usernames {mode}:</b>\n\n{lines}\n\n<i>Page {page}/{pages} · found: {total_found}</i>\n\ntap to claim:","find_result_fallback":"{E_boom} <b>found available usernames {mode}:</b>\n\n{lines}{more_line}","find_more":"\n\n<i>Showing the first {shown} of {total_found} found; inline pagination unavailable.</i>","find_page_empty":"The list of found usernames is no longer available.","stop_ok":"<b>{E_stop} search stopped.</b>","stop_idle":"<b>ℹ️ no search is running.</b>","stop_idle_alert":"ℹ️ No search is running.","grab_busy":"Another claim is already in progress, try again.","grabbing":"claiming...","grab_success":"{E_boom} <b>@{username}</b> claimed successfully!\n\nChannel: {channel}","grab_success_avatar_failed":"{E_boom} <b>@{username}</b> claimed successfully!\n\nChannel: {channel}\n\n<i>Failed to set the avatar; the username is already assigned to the channel.</i>","grab_success_firstpost_failed":"{E_boom} <b>@{username}</b> claimed successfully!\n\nChannel: {channel}\n\n<i>Failed to send the first post; the username is already assigned to the channel.</i>","grab_success_avatar_firstpost_failed":"{E_boom} <b>@{username}</b> claimed successfully!\n\nChannel: {channel}\n\n<i>The username is assigned, but the avatar and first post could not be set.</i>","grab_taken":"The username is already taken. It may have been claimed right after the check.","grab_invalid":"Telegram rejected this username as invalid.","grab_purchasable":"This username is only available as a collectible.","grab_flood":"{E_clock} Telegram limited the operation. Try again in {wait}.","grab_public_limit":"The account's limit of public channels/usernames has been reached.","grab_channel_limit":"The account's channel creation limit has been reached.","grab_restricted":"Telegram has restricted channel creation for this account.","grab_bad_title":"The channel title in settings is empty or invalid.","grab_bad_about":"The channel description in settings is too long or invalid.","grab_no_rights":"Telegram did not allow modifying the created channel.","grab_error":"Failed to claim the username due to a Telegram error. Details were written to the log.","rollback_warning":"\n\n<b>{E_warning} Failed to automatically delete the temporary channel after the error. Check your channel list manually.</b>","grab_error_title":"{E_error} <b>Error:</b>\n<code>{error}</code>{rollback_warning}","mode_prefix":"by prefix <b>@{prefix}</b>","mode_random":"random (<b>{length} characters</b>)","ai_pros_label":"Pros","ai_cons_label":"Cons","ai_figure_label":"Known figure","upd_checking":"{E_search} <b>checking for updates...</b>","upd_downloading":"{E_search} <b>updating VUsername...</b>","upd_done":"{E_success} <b>VUsername updated successfully!</b>","upd_none":"{E_success} <b>you already have the latest version.</b>","upd_none_force":"{E_success} <b>you already have the latest version. Update anyway?</b>","upd_force_btn":"↻ update anyway","upd_cancel_btn":"✖ cancel","upd_fail":"{E_error} <b>update failed. Check the logs.</b>","upd_fetch_fail":"{E_error} <b>could not reach the update source. Try again later.</b>","upd_busy":"{E_error} <b>an update check/install is already running in the background. Try again in a bit.</b>","upd_no_loader":"{E_error} <b>Loader module not found; can't self-update.</b>",}
    strings_ru={"name":"VUsername","_cls_doc":"Проверка юзернеймов, ИИ-оценка и поиск свободных через Fragment.","no_args":"<b>{E_error} укажи юзак!!</b>","bad_length":"<b>{E_error} юзернейм должен содержать от 4 до 32 символов!!</b>","bad_chars":"<b>{E_error} в юзернейме допустимы только латинские буквы, цифры и _ !!</b>","available":"юзак <b>@{username}</b> — свободен!!!\n\nхочешь занять этот юзернейм?","available_no_inline":"{E_boom} <b>@{username}</b> — свободен, но inline-форму создать не удалось. Повтори команду позже.","grab_button":"✔ занять","close_button":"✖ закрыть","checking":"<b>проверяю.. @{username}...</b>","fragment_sold":"{E_error} <b>@{username}</b> — продан на Fragment.\n\n{E_fragment} <b>найден на Fragment:</b>\n{price_line}{E_link} <b>ссылка:</b> <a href=\"{url}\">{url}</a>","fragment_available":"{E_error} <b>@{username}</b> — занят.\n\n{E_fragment} <b>найден на Fragment:</b>\n{price_line}{E_link} <b>ссылка:</b> <a href=\"{url}\">{url}</a>","fragment_unavailable":"{E_error} <b>@{username}</b> — занят или недоступен для назначения.\n\n{E_fragment} <b>Fragment:</b> <code>Unavailable</code> — не продаётся.\n{E_link} <b>ссылка:</b> <a href=\"{url}\">{url}</a>","price_line":"{E_coin} <b>цена:</b> <code>{price}</code> GRAM\n","occupied":"{E_error} <b>@{username}</b> — занят или недоступен для назначения.","purchasable":"{E_coin} <b>@{username}</b> доступен только как коллекционный юзернейм.","fragment_error":"\n\n{E_error} <i>Fragment временно не удалось проверить.</i>","check_error":"{E_error} <b>Не удалось проверить @{username} из-за ошибки Telegram. Попробуй позже.</b>","flood_wait":"<b>{E_clock} Telegram ограничил проверки. Повтори через {wait}.</b>","flood_wait_unknown":"{E_error} <b>@{username}</b> — <b>неизвестно</b>.","flood_wait_fragment_available":"{E_error} <b>@{username}</b> — <b>занят</b>.\n\n{E_fragment} <b>найден на Fragment:</b>\n{price_line}{E_link} <b>ссылка:</b> <a href=\"{url}\">{url}</a>","flood_wait_fragment_sold":"{E_error} <b>@{username}</b> — <b>Возможно, занят</b>.\n\n{E_fragment} <b>Fragment:</b> юзернейм продан.\n{price_line}{E_link} <b>ссылка:</b> <a href=\"{url}\">{url}</a>","flood_wait_fragment_unavailable":"{E_error} <b>@{username}</b> — <b>неизвестно</b>.\n\n{E_fragment} <b>Fragment:</b> <code>Unavailable</code> — не продаётся.\n{E_link} <b>ссылка:</b> <a href=\"{url}\">{url}</a>","flood_wait_fragment_note":"\n\n<b>{E_clock} FloodWait: {wait}.</b>\n<i>Из-за FloodWait точно проверить, занят ли юзернейм, невозможно. Но вы можете попробовать занять его, нажав на inline-кнопку ниже.</i>","prefix_bad":"<b>{E_error} префикс должен содержать только латинские буквы, цифры и _ и быть не длиннее 31 символа.</b>","count_bad":"<b>{E_error} количество проверок должно быть числом от 1 до {maximum}.</b>","vfind_usage":"<b>{E_error} формат: <code>.vfind</code>, <code>.vfind 100</code> или <code>.vfind user 100</code>.</b>","ai_evaluating":"<b>{E_robot} ИИ анализирует @{username}...</b>","ai_result":"{body}","ai_no_key":"<b>{E_error} Не задан API-ключ для ИИ-оценки.</b>\n\nПолучи ключ(и) на <code>aistudio.google.com</code> и укажи их командой:\n<code>.config VUsername</code> → <code>ai_api_keys</code>\nМожно указать несколько ключей через запятую — это ускоряет работу и снижает риск упереться в квоту.","ai_error_quota":"{E_error} Превышена квота Gemini API. Проверьте лимиты в настройках.","ai_error_quota_retry":"{E_error} Превышена квота Gemini API.\nПовторите запрос примерно через {seconds} сек.","ai_error_auth":"{E_error} <b>Неверный API-ключ Gemini. Проверьте настройки.</b>","ai_error_server":"{E_error} Временная ошибка Gemini. Попробуйте позже.","ai_error_model_not_found":"{E_error} Модель Gemini недоступна.\n\nПроверьте: <code>.config VUsername ai_model</code>\nРекомендуется: <code>gemini-3.5-flash</code>","ai_error_unknown":"{E_error} <b>Ошибка ИИ:</b> {error}","ai_note_available":"{E_green} <b>Свободен</b>, не продаётся на Fragment — занять: <code>.v {username}</code>\n","ai_note_taken_regular":"{E_lock} <b>Юзернейм занят обычным пользователем, оценка теоретическая.</b>\n","find_running":"<b>{E_hourglass} уже идёт поиск, подожди...</b>","find_stop_button":"⛔ Стоп","find_stopping":"Останавливаю поиск...","find_start":"<b>{E_search} ищу свободные юзернеймы {mode}...\nпроверено: 0 / {total}</b>","find_progress":"<b>{E_search} ищу {mode}...\nпроверено: {checked} / {total}\n\nнайдено: {found_count}\n{preview}</b>","find_nothing":"<b>{E_sad} свободных юзернеймов {mode} не найдено.\nПопробуй другой префикс или запусти снова.</b>","find_stopped":"<b>{E_stop} поиск остановлен.\nПроверено: {checked} / {total}.\nНайдено: {found_count}.</b>","find_flood":"<b>{E_clock} поиск остановлен из-за ограничения Telegram.\nПроверено: {checked} / {total}.\nFloodWait: {wait}.</b>","find_error":"<b>{E_error} поиск остановлен из-за ошибки Telegram.\nПроверено: {checked} / {total}. Попробуй позже.</b>","find_preview_empty":"пока ничего...","find_result":"{E_boom} <b>найдены свободные юзернеймы {mode}:</b>\n\n{lines}\n\n<i>Страница {page}/{pages} · найдено: {total_found}</i>\n\nнажми чтобы занять:","find_result_fallback":"{E_boom} <b>найдены свободные юзернеймы {mode}:</b>\n\n{lines}{more_line}","find_more":"\n\n<i>Показаны первые {shown} из {total_found} найденных; inline-пагинация недоступна.</i>","find_page_empty":"Список найденных юзернеймов уже недоступен.","stop_ok":"<b>{E_stop} поиск остановлен.</b>","stop_idle":"<b>ℹ️ поиск не запущен.</b>","stop_idle_alert":"ℹ️ Поиск не запущен.","grab_busy":"Уже выполняется другой захват, попробуй ещё раз.","grabbing":"захватываю...","grab_success":"{E_boom} <b>@{username}</b> успешно занят!\n\nКанал: {channel}","grab_success_avatar_failed":"{E_boom} <b>@{username}</b> успешно занят!\n\nКанал: {channel}\n\n<i>Аватар установить не удалось; юзернейм уже закреплён за каналом.</i>","grab_success_firstpost_failed":"{E_boom} <b>@{username}</b> успешно занят!\n\nКанал: {channel}\n\n<i>Первый пост отправить не удалось; юзернейм уже закреплён за каналом.</i>","grab_success_avatar_firstpost_failed":"{E_boom} <b>@{username}</b> успешно занят!\n\nКанал: {channel}\n\n<i>Юзернейм закреплён, но аватар установить и первый пост отправить не удалось.</i>","grab_taken":"Юзернейм уже занят. Возможно, его успели забрать после проверки.","grab_invalid":"Telegram отклонил этот юзернейм как недопустимый.","grab_purchasable":"Этот юзернейм доступен только как коллекционный.","grab_flood":"{E_clock} Telegram ограничил операцию. Повтори через {wait}.","grab_public_limit":"Достигнут лимит публичных каналов/юзернеймов аккаунта.","grab_channel_limit":"Достигнут лимит создаваемых каналов аккаунта.","grab_restricted":"Telegram ограничил создание каналов для этого аккаунта.","grab_bad_title":"Название канала в настройках пустое или недопустимое.","grab_bad_about":"Описание канала в настройках слишком длинное или недопустимое.","grab_no_rights":"Telegram не разрешил изменить созданный канал.","grab_error":"Не удалось занять юзернейм из-за ошибки Telegram. Подробности записаны в лог.","rollback_warning":"\n\n<b>{E_warning} Не удалось автоматически удалить временный канал после ошибки. Проверь список своих каналов вручную.</b>","grab_error_title":"{E_error} <b>Ошибка:</b>\n<code>{error}</code>{rollback_warning}","mode_prefix":"по префиксу <b>@{prefix}</b>","mode_random":"случайные (<b>{length} символов</b>)","ai_pros_label":"Преимущества","ai_cons_label":"Недостатки","ai_figure_label":"Известная личность","upd_checking":"{E_search} <b>проверяю обновления...</b>","upd_downloading":"{E_search} <b>обновляю VUsername...</b>","upd_done":"{E_success} <b>VUsername успешно обновлён!</b>","upd_none":"{E_success} <b>у тебя уже последняя версия.</b>","upd_none_force":"{E_success} <b>у тебя уже последняя версия. Обновить всё равно?</b>","upd_force_btn":"↻ обновить всё равно","upd_cancel_btn":"✖ отмена","upd_fail":"{E_error} <b>обновление не удалось. Смотри логи.</b>","upd_fetch_fail":"{E_error} <b>не удалось достучаться до источника обновления. Попробуй позже.</b>","upd_busy":"{E_error} <b>проверка/установка обновления уже выполняется в фоне. Попробуй чуть позже.</b>","upd_no_loader":"{E_error} <b>модуль Loader не найден, самообновление невозможно.</b>",}
    for _dict in(strings,strings_ru):
        for _key,_val in list(_dict.items()):
            if isinstance(_val,str)and"{E_"in _val:
                for _ename in EMOJI_IDS:
                    _val=_val.replace("{E_"+_ename+"}",emoji(_ename))
                _dict[_key]=_val
    del _dict,_key,_val,_ename
    USERNAME_RE=re.compile(r"^[A-Za-z0-9_]+$")
    PREFIX_RE=re.compile(r"^[A-Za-z0-9_]+$")
    TG_LINK_RE=re.compile(r"^(?:https?://)?(?:www\.)?(?:t\.me|telegram\.me|telegram\.dog)/(?:@)?",re.IGNORECASE)
    RANDOM_USERNAME_LENGTH=5
    RANDOM_CANDIDATES=25
    MAX_RANDOM_CANDIDATES=1000
    DEFAULT_PREFIX_CANDIDATES=500
    MAX_PREFIX_CANDIDATES=1000
    RESULTS_PER_PAGE=5
    FALLBACK_DISPLAY_FOUND=25
    PROGRESS_PREVIEW_LIMIT=10
    PROGRESS_EVERY=5
    PROGRESS_MIN_INTERVAL=2.5
    FRAGMENT_TIMEOUT=(5,10)
    FRAGMENT_CACHE_TTL=90.0
    FRAGMENT_CACHE_MAX_ENTRIES=500
    AI_TIMEOUT=(5,40)
    AI_CACHE_TTL=900.0
    TON_USD_RATE=1.322
    AVATAR_TIMEOUT=(5,10)
    AVATAR_MAX_BYTES=10*1024*1024
    AVATAR_MAX_REDIRECTS=3
    HTTP_USER_AGENT="Mozilla/5.0 (VUsername/1.1)"
    MAX_RETRIES_FRAGMENT=3
    UPDATE_URL="https://raw.githubusercontent.com/lcetaa/VUsername-hikka-bot/refs/heads/main/vusername.py"
    UPDATE_LOCK_WAIT=15
    UPDATE_INSTALL_TIMEOUT=60
    MAX_RETRIES_GEMINI=3
    MAX_RETRIES_GROQ=3
    _KEY_PATTERN=re.compile(r'\b[A-Za-z0-9_-]{20,}\b')
    _KEY_QUERY_PATTERN=re.compile(r'([?&]key=)[^&\s]+',re.IGNORECASE)

    def __init__(self):
        self.config=loader.ModuleConfig(loader.ConfigValue("channel_title","This username is reserved.","Channel title",validator=loader.validators.String()),loader.ConfigValue("channel_about","Made by {me}","Channel description",validator=loader.validators.String()),loader.ConfigValue("channel_avatar_url","https://raw.githubusercontent.com/lcetaa/VUsername-hikka-bot/refs/heads/main/rezerv.png","Avatar URL",validator=loader.validators.String()),loader.ConfigValue("channel_message","<b>Interested in this username? Contact {me}</b>","Post-grab channel message",validator=loader.validators.String()),loader.ConfigValue("delay_min",1.2,".vfind minimum delay, sec",validator=loader.validators.Float(minimum=0.0)),loader.ConfigValue("delay_max",2.0,".vfind maximum delay, sec",validator=loader.validators.Float(minimum=0.0)),loader.ConfigValue("ai_provider","auto","AI provider (.vai)",validator=loader.validators.Choice(["auto","gemini","groq"])),loader.ConfigValue("ai_api_keys","","Gemini API keys, comma-separated",validator=loader.validators.Hidden()),loader.ConfigValue("ai_model","gemini-3.5-flash","Gemini model",validator=loader.validators.String()),loader.ConfigValue("groq_api_keys","","Groq API keys, comma-separated",validator=loader.validators.Hidden()),loader.ConfigValue("groq_model","openai/gpt-oss-120b","Groq model",validator=loader.validators.String()),)
        self._find_running=False
        self._find_stop_event=None
        self._grab_lock=None
        self._ai_cache={}
        self._fragment_cache={}
        self._fragment_cache_lock=asyncio.Lock()
        self._own_usernames=None
        self.api_keys=[]
        self.key_status={}
        self.current_key_index=0
        self.key_lock=asyncio.Lock()
        self.groq_api_keys=[]
        self.groq_key_status={}
        self.groq_current_key_index=0
        self.groq_key_lock=asyncio.Lock()
        self._session=None
        self._connector=None
        self._cleaner_task=None
        self._update_lock=asyncio.Lock()

    def _redact(self,text:str)->str:
        if not text:return text
        for key in(*self.api_keys,*self.groq_api_keys):
            if key and len(key)>=8:text=text.replace(key,key[:6]+'…redacted…')
        text=self._KEY_QUERY_PATTERN.sub(lambda m:m.group(1)+'…redacted…',text)
        text=self._KEY_PATTERN.sub(lambda m:m.group(0)[:6]+'…redacted…'if len(m.group(0))>=20 else m.group(0),text)
        return text

    async def _get_session(self)->aiohttp.ClientSession:
        if self._session is None or self._session.closed:
            if self._connector is None or self._connector.closed:
                self._connector=aiohttp.TCPConnector(limit=20,ttl_dns_cache=300)
            timeout=aiohttp.ClientTimeout(connect=self.FRAGMENT_TIMEOUT[0],sock_read=self.FRAGMENT_TIMEOUT[1],total=30)
            self._session=aiohttp.ClientSession(timeout=timeout,connector=self._connector,headers={"User-Agent":self.HTTP_USER_AGENT})
        return self._session

    async def _close_session(self):
        if self._session and not self._session.closed:
            await self._session.close()
        if self._connector and not self._connector.closed:
            await self._connector.close()

    async def _request_with_retry(self,url,method="GET",max_retries=3,backoff_factor=2.0,retryable_statuses=(500,502,503,504),**kwargs):
        session=await self._get_session()
        last_error=None
        for attempt in range(max_retries):
            try:
                async with session.request(method,url,**kwargs)as resp:
                    status=resp.status
                    try:
                        if"application/json"in resp.headers.get("Content-Type",""):
                            data=await resp.json()
                        else:
                            data=await resp.read()
                    except Exception as e:
                        logger.warning("Failed to read response: %s",self._redact(str(e)))
                        data=None
                    if status in retryable_statuses and attempt<max_retries-1:
                        await asyncio.sleep(backoff_factor**attempt)
                        continue
                    return status,data
            except(aiohttp.ClientError,asyncio.TimeoutError)as e:
                last_error=e
                if attempt<max_retries-1:
                    await asyncio.sleep(backoff_factor**attempt)
                    continue
            except Exception as e:
                logger.exception("Unexpected error: %s",self._redact(str(e)))
                raise
        if last_error:
            logger.warning("Request to %s failed after %d retries: %s",url,max_retries,self._redact(str(last_error)))
        return 500,None

    async def _check_fragment_async(self,username:str):
        url=f"https://fragment.com/username/{username}"
        status_code,content=await self._request_with_retry(url,max_retries=self.MAX_RETRIES_FRAGMENT)
        if status_code==404:return FragmentStatus.NOT_FOUND,None
        if status_code!=200 or content is None:
            logger.warning("Fragment HTTP %s for @%s",status_code,username)
            return FragmentStatus.ERROR,None
        if isinstance(content,dict):return FragmentStatus.ERROR,None
        try:
            soup=BeautifulSoup(content,"html.parser")
        except Exception:
            logger.exception("Failed to parse Fragment HTML for @%s",username)
            return FragmentStatus.ERROR,None

        def normalize_text(v):return" ".join(v.split()).strip().lower()

        def classify_visible_status(v):
            v=normalize_text(v)
            if re.search(r"(?:^|\s)sold(?:\s|$)",v):return FragmentStatus.SOLD
            if"unavailable"in v or"not for sale"in v:return FragmentStatus.UNAVAILABLE
            if("on auction"in v or"auction"in v or"minimum bid"in v or"for sale"in v or re.search(r"(?:^|\s)available(?:\s|$)",v)):
                return FragmentStatus.AVAILABLE
            return None

        def extract_price():
            selectors=("div.table-cell-value.tm-value.icon-before.icon-ton",".tm-section-bid-info .tm-value.icon-ton",".tm-section-bid-info .tm-value",".tm-section-auction-info .tm-value.icon-ton",".tm-section-auction-info .tm-value",".tm-bid-info .tm-value.icon-ton",".tm-bid-info .tm-value",".tm-price .tm-value")
            for sel in selectors:
                for el in soup.select(sel):
                    value=" ".join(el.get_text(" ",strip=True).split())
                    if not value or"@"in value:continue
                    lowered=value.lower()
                    if"unknown"in lowered or"not for sale"in lowered:continue
                    match=re.search(r"(?<![A-Za-z0-9_])(\d[\d\s,.]*)(?![A-Za-z0-9_])",value)
                    if match:
                        price=match.group(1).strip().rstrip(".,")
                        if price:
                            logger.info("Fragment[@%s]: цена=%r",username,price)
                            return price
            return None
        for node in soup.select(".tm-section-header-status"):
            badge_text=node.get_text(" ",strip=True)
            status=classify_visible_status(badge_text)
            if status is not None:
                price=extract_price()if status in(FragmentStatus.SOLD,FragmentStatus.AVAILABLE)else None
                logger.info("Fragment[@%s]: статус-бейдж %r -> %s",username,badge_text,status)
                return status,price
        username_lower=username.lower()
        result_selectors=("tr",".tm-row-selectable",".tm-table-row",".tm-search-result",".table-row",".tm-row")
        seen_nodes=set()
        for sel in result_selectors:
            for node in soup.select(sel):
                node_id=id(node)
                if node_id in seen_nodes:continue
                seen_nodes.add(node_id)
                text=normalize_text(node.get_text(" ",strip=True))
                if not text:continue
                if f"@{username_lower}"not in text and f"{username_lower}.t.me"not in text and f"t.me/{username_lower}"not in text:
                    continue
                status=classify_visible_status(text)
                if status is not None:
                    price=extract_price()if status in(FragmentStatus.SOLD,FragmentStatus.AVAILABLE)else None
                    logger.info("Fragment[@%s]: строка поиска %r -> %s",username,text,status)
                    return status,price
        logger.info("Fragment[@%s]: статус не распознан",username)
        return FragmentStatus.NOT_FOUND,None

    async def _check_fragment(self,username):
        key=username.lower()
        now=time.monotonic()
        async with self._fragment_cache_lock:
            cached=self._fragment_cache.get(key)
            if cached and now-cached[0]<self.FRAGMENT_CACHE_TTL:
                return cached[1],cached[2]
        status,price=await self._check_fragment_async(username)
        async with self._fragment_cache_lock:
            self._fragment_cache[key]=(now,status,price)
            if len(self._fragment_cache)>self.FRAGMENT_CACHE_MAX_ENTRIES:
                expired=[k for k,(ts,_,_)in self._fragment_cache.items()if now-ts>=self.FRAGMENT_CACHE_TTL]
                for k in expired:self._fragment_cache.pop(k,None)
        return status,price

    def _build_ai_prompt(self,username,fragment_status,price):
        is_ru=self._is_ru()
        comparable_usd=None
        if is_ru:
            context_lines=[f"Юзернейм: @{username}",f"Длина: {len(username)} символов"]
        else:
            context_lines=[f"Username: @{username}",f"Length: {len(username)} characters"]
        if fragment_status in(FragmentStatus.SOLD,FragmentStatus.AVAILABLE)and price:
            try:
                gram_amount=float(re.sub(r"[^\d.]","",price.replace(",","")))
                comparable_usd=round(gram_amount*self.TON_USD_RATE)
            except(ValueError,TypeError):
                comparable_usd=None
            usd_hint=f" (~${comparable_usd})"if comparable_usd else""
            if fragment_status is FragmentStatus.SOLD:
                if is_ru:
                    context_lines.append(f"На Fragment уже продан за {price} GRAM{usd_hint} — это ФАКТИЧЕСКАЯ рыночная цена именно этого юзернейма.")
                else:
                    context_lines.append(f"Already sold on Fragment for {price} GRAM{usd_hint} — this is the ACTUAL market price of this exact username.")
            else:
                if is_ru:
                    context_lines.append(f"Сейчас выставлен на аукцион Fragment, минимальная ставка {price} GRAM{usd_hint} — это РЕАЛЬНАЯ цена этого конкретного юзернейма на Fragment, а не абстрактная оценка.")
                else:
                    context_lines.append(f"Currently listed on the Fragment auction, minimum bid {price} GRAM{usd_hint} — this is the REAL price of this specific username on Fragment, not an abstract estimate.")
        elif fragment_status is FragmentStatus.UNAVAILABLE:
            context_lines.append("Fragment отмечает нейм как Unavailable (премиальный)."if is_ru else"Fragment marks the name as Unavailable (premium).")
        elif fragment_status is FragmentStatus.ERROR:
            context_lines.append("Не удалось проверить Fragment (техническая ошибка) — данных о цене нет, но продажа не исключена."if is_ru else"Could not check Fragment (technical error) — no price data, but a sale is not ruled out.")
        else:
            context_lines.append("Данных о цене на Fragment нет, продаж не найдено."if is_ru else"No Fragment price data, no sales found.")
        logger.info("AI-промпт[@%s]: fragment_status=%s, price=%r",username,fragment_status,price)
        if is_ru:
            prompt=("Ты — эксперт по оценке Telegram-юзернеймов на маркетплейсе Fragment. Оцени указанный юзернейм по критериям: длина, запоминаемость, является ли словом/брендом/аббревиатурой, читаемость, наличие цифр или подчёркиваний, потенциальный спрос среди коллекционеров. Если юзернейм ЯВНО совпадает с известной публичной персоной, брендом или проектом — укажи это в public_figure. Считай совпадением: 1) точное имя/ник; 2) leetspeak-варианты (замена букв на похожие цифры/символы: o→0, i→1, e→3 и т.п.); 3) случаи, когда узнаваемое имя/ник СОДЕРЖИТСЯ внутри юзернейма как подстрока, даже если до или после него есть дополнительные символы, буквы, цифры или подчёркивания (например, 'samsepi0l_ovf' содержит 'samsepiol' — узнаваемый ник Сэма Сепиола / Эллиота Алдерсона из сериала «Мистер Робот», даже с приставкой '_ovf' на конце — это ЗАСЧИТЫВАЕТСЯ как совпадение). Не отбрасывай совпадение только из-за лишних символов вокруг узнаваемой части — если ядро (сама узнаваемая часть) читается однозначно, указывай public_figure. НЕ считай совпадением случайные сокращения, натянутые ассоциации или аббревиатуры, которые можно трактовать десятками способов (например, 'dcequ' — это НЕ явное совпадение с DC Extended Universe, это просто короткая строка, потому что тут нет узнаваемой подстроки-имени). Если сомневаешься — оставляй public_figure null. ВАЖНО про цену: если в контексте указана фактическая цена продажи на Fragment — твой диапазон price_low_usd/price_high_usd должен быть БЛИЗКИМ к этой цене (примерно от 0.6x до 1.5x от неё), а не в разы выше. Если фактической цены нет — давай МАКСИМАЛЬНО СКРОМНЫЙ, консервативный диапазон, как для рядового непроданного юзернейма без подтверждённого спроса: по умолчанию склоняйся к нижней части реальных рыночных цен похожих ниш на Fragment, а не к верхней. Для юзернейма без public_figure, БЕЗ смысла (случайный набор букв, не слово и не аббревиатура) и без цифр — типичная адекватная цена не должна превышать 40$, но ОБЯЗАТЕЛЬНО варьируй конкретное число в зависимости от длины, произносимости и качества звучания конкретного юзернейма — НЕ возвращай один и тот же диапазон для разных юзернеймов, разные строки должны получать заметно разные оценки. БЕЗ фантастических завышений — не пиши сотни или тысячи долларов за обычный короткий нейм без подтверждённого спроса, даже если он короткий и без цифр. Лучше немного занизить, чем завысить. ЕСЛИ public_figure не null: НЕ указывай price_low_usd/price_high_usd для бренда/персоны самостоятельно — вместо этого заполни поле figure_scale одной из категорий: \"mega\" (глобальный супербренд/суперзвезда с сотнями миллионов-миллиардами пользователей/фанатов, например TikTok, Google, Apple, топовая мировая звезда), \"major\" (известный международный бренд/публичная персона, но менее масштабный, например средняя по размеру компания, известный в своей стране актёр/блогер), \"moderate\" (узнаваемый, но нишевый бренд/персонаж, известный ограниченной аудитории), \"minor\" (местный/малоизвестный бренд или персонаж, известность которого сомнительна). В этом случае price_low_usd и price_high_usd можно оставить null. В cons пиши пункт, только если недостаток реально есть; если явных недостатков нет — верни пустой массив [], НЕ пиши 'нету'/'отсутствуют'/подобные заглушки. То же для pros. Учти контекст ниже.\n\n"+"\n".join(context_lines)+"\n\nОтветь СТРОГО в виде JSON без пояснений вне JSON, формат:\n{\"price_low_usd\": число (грубая нижняя оценка в $, ОБЯЗАТЕЛЬНО заполни даже если не уверен — ориентируйся на длину/качество и типичные цены похожих юзернеймов (null допустим только если public_figure не null — тогда используется figure_scale вместо этого)), \"price_high_usd\": число (грубая верхняя оценка в $, те же правила), \"creation_cost_gram\": число (обычно 10 для 5+ символов, больше для коротких), \"creation_cost_usd\": число или null, \"rank\": целое число 0-10, \"pros\": [\"короткие пункты-преимущества, 3-6 слов, максимум 3 шт\"], \"cons\": [\"короткие пункты-недостатки, 3-6 слов, максимум 3 шт\"], \"public_figure\": \"имя персоны/бренда, если юзернейм явно на неё указывает, иначе null\", \"figure_note\": \"1 короткое предложение о персоне/бренде на русском БЕЗ повторения самого имени персоны/бренда в начале (имя уже выводится отдельно перед этим полем, начинай сразу с сути, например 'Глобальная платформа коротких видео.', а НЕ 'TikTok — глобальная платформа...'), если public_figure не null, иначе null\", \"figure_scale\": \"mega|major|moderate|minor, только если public_figure не null, иначе null\", \"has_meaning\": true/false (true — ТОЛЬКО если юзернейм ЦЕЛИКОМ читается как настоящее слово, реальное имя/ник, узнаваемый бренд или осмысленная аббревиатура, БЕЗ существенного 'мусора' вокруг — то есть лишние буквы/цифры не должны занимать значительную часть юзернейма и не должны ломать восприятие как единого осмысленного слова/имени. false — если юзернейм это набор случайных букв, произвольная комбинация с цифрами/приставками/суффиксами, даже если где-то внутри случайно угадывается часть известного слова/бренда (например 'sbajaj2892' — false, потому что цифры и лишняя 's' делают это бессмысленным набором символов, а не осмысленным ником, несмотря на то что внутри есть 'bajaj'). Будь строгим: при малейшем сомнении ставь false.)}")
        else:
            prompt=("You are an expert in valuing Telegram usernames on the Fragment marketplace. Evaluate the given username by: length, memorability, whether it's a word/brand/abbreviation, readability, presence of digits or underscores, potential demand among collectors. If the username CLEARLY and UNAMBIGUOUSLY matches a known public figure, brand, or project (e.g. an exact name/handle of a person or an official brand abbreviation) — state it in public_figure. Do NOT count random abbreviations, far-fetched associations, or acronyms that could be read a dozen different ways (e.g. 'dcequ' is NOT a clear match for the DC Extended Universe, it's just a short string). If unsure, leave public_figure null. IMPORTANT about price: if the context states an actual Fragment sale price — your price_low_usd/price_high_usd range must be CLOSE to that price (roughly 0.6x to 1.5x of it), not several times higher. If there is no actual price — give a MAXIMALLY MODEST, conservative range, as for an ordinary unsold username with no confirmed demand: default toward the lower end of real market prices for similar niches on Fragment, not the upper end. For a username with no public_figure, NO clear meaning (random string of letters, not a word or abbreviation) and no digits — a fair price should not exceed 40$, but you MUST vary the exact number based on the specific username's length, pronounceability and sound quality — do NOT return the same range for different usernames, different strings should get noticeably different estimates. NO unrealistic inflation — don't write hundreds or thousands of dollars for an ordinary short name with no confirmed demand, even if it's short and has no digits. Better to slightly underestimate than overestimate. IF public_figure is not null: do NOT set price_low_usd/price_high_usd for the brand/person yourself — instead fill the figure_scale field with one of: \"mega\" (a global superbrand/superstar with hundreds of millions to billions of users/fans, e.g. TikTok, Google, Apple, a top-tier world-famous celebrity), \"major\" (a well-known international brand/public figure but smaller in scale, e.g. a mid-size company, an actor/creator famous within their own country), \"moderate\" (a recognizable but niche brand/character known to a limited audience), \"minor\" (a local or little-known brand/character whose fame is questionable). In this case price_low_usd and price_high_usd can be left null. Only include a cons item if the drawback genuinely exists; if there are no clear drawbacks, return an empty array [], do NOT write 'none'/'n/a'/similar placeholders. Same for pros. Take the context below into account.\n\n"+"\n".join(context_lines)+"\n\nRespond STRICTLY as JSON with no explanation outside the JSON, format:\n{\"price_low_usd\": number (rough low estimate in $, MUST be filled even if unsure — base it on length/quality and typical prices of similar usernames (null is only allowed if public_figure is not null — figure_scale is used instead in that case)), \"price_high_usd\": number (rough high estimate in $, same rules), \"creation_cost_gram\": number (usually 10 for 5+ characters, more for shorter ones), \"creation_cost_usd\": number or null, \"rank\": integer 0-10, \"pros\": [\"short bullet advantages, 3-6 words, max 3 items\"], \"cons\": [\"short bullet drawbacks, 3-6 words, max 3 items\"], \"public_figure\": \"name of the person/brand if the username clearly points to it, otherwise null\", \"figure_note\": \"1 short sentence about the person/brand WITHOUT repeating the person/brand name itself at the start (the name is already shown separately before this field — start directly with the description, e.g. 'Global short-video platform.', NOT 'TikTok — global short-video platform...'), if public_figure is not null, otherwise null\", \"figure_scale\": \"mega|major|moderate|minor, only if public_figure is not null, otherwise null\", \"has_meaning\": true/false (true ONLY if the username AS A WHOLE reads as a real word, an actual name/handle, a recognizable brand, or a meaningful abbreviation, WITHOUT substantial 'noise' around it — extra letters/digits must not make up a significant portion of the username or break the perception of it as a single meaningful word/name. false if the username is a random string of letters, an arbitrary combination with digits/prefixes/suffixes, even if part of a known word/brand can accidentally be spotted inside it (e.g. 'sbajaj2892' is false, because the digits and the extra 's' make it a meaningless jumble of characters rather than a meaningful handle, even though 'bajaj' appears inside it). Be strict: when in doubt, set false.)}")
        return prompt,comparable_usd

    def _parse_ai_json(self,raw_text):
        cleaned=raw_text.strip().lstrip("\ufeff")
        if cleaned.startswith("```"):
            cleaned=re.sub(r"^```(?:json)?\s*","",cleaned,flags=re.IGNORECASE)
            cleaned=re.sub(r"\s*```$","",cleaned).strip()
        parsed=None
        try:
            parsed=json.loads(cleaned,strict=False)
        except(TypeError,ValueError,json.JSONDecodeError):
            decoder=json.JSONDecoder(strict=False)

            def try_decode(text):
                try:
                    candidate,_=decoder.raw_decode(text)
                    return candidate if isinstance(candidate,dict)else None
                except json.JSONDecodeError:
                    return None

            def close_truncated(text):
                text=re.sub(r",\s*$","",text.rstrip())
                stack=[]
                in_string=False
                escape=False
                for ch in text:
                    if in_string:
                        if escape:
                            escape=False
                        elif ch=="\\":
                            escape=True
                        elif ch=='"':
                            in_string=False
                        continue
                    if ch=='"':
                        in_string=True
                    elif ch in"{[":
                        stack.append(ch)
                    elif ch in"}]":
                        if stack and((ch=="}"and stack[-1]=="{")or(ch=="]"and stack[-1]=="[")):
                            stack.pop()
                result=text
                if in_string:result+='"'
                closers={"{":"}","[":"]"}
                result+="".join(closers[c]for c in reversed(stack))
                return result
            for match in re.finditer(r"\{",cleaned):
                substring=cleaned[match.start():]
                no_trailing_commas=re.sub(r",\s*([}\]])",r"\1",substring)
                for candidate_text in(substring,no_trailing_commas,close_truncated(no_trailing_commas)):
                    candidate=try_decode(candidate_text)
                    if candidate is not None:
                        parsed=candidate
                        break
                if parsed is not None:break
        return parsed

    async def _ai_evaluate_async(self,api_key,model,username,fragment_status,price,is_taken=False):
        prompt,comparable_usd=self._build_ai_prompt(username,fragment_status,price)
        is_gemini_3=bool(re.match(r"gemini-3",model,flags=re.IGNORECASE))
        thinking_config={"thinkingLevel":"minimal"}if is_gemini_3 else{"thinkingBudget":0}
        payload={"contents":[{"role":"user","parts":[{"text":prompt}]}],"generationConfig":{"maxOutputTokens":1024,"responseMimeType":"application/json","thinkingConfig":thinking_config}}
        url=f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent"
        params={"key":api_key}
        session=await self._get_session()
        max_retries=self.MAX_RETRIES_GEMINI
        for attempt in range(max_retries):
            try:
                async with session.post(url,params=params,json=payload)as resp:
                    status=resp.status
                    try:
                        data=await resp.json()
                    except Exception:
                        data=None
                    if status==429:
                        retry_delay=None
                        if data:
                            try:
                                for detail in data.get("error",{}).get("details",[]):
                                    if detail.get("@type","").endswith("RetryInfo"):
                                        raw_delay=str(detail.get("retryDelay",""))
                                        match=re.match(r"(\d+(?:\.\d+)?)s?",raw_delay)
                                        if match:
                                            retry_delay=float(match.group(1))
                                        break
                            except(ValueError,TypeError,json.JSONDecodeError):
                                pass
                        logger.warning("Gemini quota исчерпана для @%s",username)
                        return False,(str(int(retry_delay))if retry_delay else""),"quota"
                    if status in(400,401,403):
                        error_message="";error_reason=""
                        if data:
                            try:
                                err_obj=data.get("error",{})
                                error_message=str(err_obj.get("message",""))[:300]
                                for detail in err_obj.get("details",[]):
                                    if detail.get("reason"):error_reason=str(detail.get("reason"));break
                            except Exception:error_message=error_message or""
                        if not error_message:
                            try:error_message=(await resp.text())[:300]
                            except Exception:error_message=''
                        logger.error("Gemini HTTP %s: %s",status,self._redact(error_message))
                        is_invalid_key=error_reason=="API_KEY_INVALID"or"api key not valid"in error_message.lower()
                        error_type="auth"if(status in(401,403)or is_invalid_key)else"unknown"
                        body=""if error_type=="auth"else f"HTTP {status}: {error_message}"if error_message else f"HTTP {status}"
                        return False,body,error_type
                    if status==404:
                        logger.error("Gemini 404 (модель не найдена) для @%s",username)
                        return False,"","model_not_found"
                    if status>=500:
                        logger.error("Gemini server error %s",status)
                        if attempt<max_retries-1:
                            await asyncio.sleep(2**attempt)
                            continue
                        return False,"","server"
                    if status!=200:
                        try:detail=(await resp.text())[:300]
                        except Exception:detail=''
                        return False,f"HTTP {status}: {detail}","unknown"
                    candidates=data.get("candidates",[])
                    raw_text="".join(part.get("text","")for candidate in candidates for part in candidate.get("content",{}).get("parts",[])).strip()
                    finish_reason=candidates[0].get("finishReason")if candidates else None
                    if not raw_text:
                        if finish_reason=="MAX_TOKENS":return False,self._t("Ответ модели обрезан по лимиту токенов","Model response truncated due to token limit"),"unknown"
                        return False,self._t("Пустой ответ от модели","Empty response from the model"),"unknown"
                    if finish_reason=="MAX_TOKENS":return False,self._t("Ответ модели обрезан по лимиту токенов до завершения JSON","Model response truncated by token limit before JSON completion"),"unknown"
                    parsed=self._parse_ai_json(raw_text)
                    if parsed is None:
                        logger.warning("Gemini non-JSON response: %s",self._redact(raw_text[:500]))
                        return False,self._t("Модель вернула некорректный JSON. Попробуйте ещё раз.","The model returned invalid JSON. Please try again."),"json_parse"
                    return self._process_ai_response(parsed,username,fragment_status,price,comparable_usd,model,is_taken)
            except(aiohttp.ClientError,asyncio.TimeoutError)as e:
                logger.warning("Gemini request error (attempt %d): %s",attempt+1,self._redact(str(e)))
                if attempt<max_retries-1:
                    await asyncio.sleep(2**attempt)
                    continue
                return False,self._t(f"Сетевая ошибка: {e}",f"Network error: {e}"),"network"
            except Exception as e:
                logger.exception("Gemini unexpected error: %s",self._redact(str(e)))
                return False,str(e),"unknown"
        return False,self._t("Превышено число попыток","Retry limit exceeded"),"unknown"

    async def _ai_evaluate_groq_async(self,api_key,model,username,fragment_status,price,is_taken=False):
        prompt,comparable_usd=self._build_ai_prompt(username,fragment_status,price)
        payload={"model":model,"messages":[{"role":"user","content":prompt}],"response_format":{"type":"json_object"},"max_tokens":1024,"temperature":0.3,"stream":False}
        url="https://api.groq.com/openai/v1/chat/completions"
        headers={"Authorization":f"Bearer {api_key}"}
        session=await self._get_session()
        max_retries=self.MAX_RETRIES_GROQ
        for attempt in range(max_retries):
            try:
                async with session.post(url,headers=headers,json=payload)as resp:
                    status=resp.status
                    try:
                        data=await resp.json()
                    except Exception:
                        data=None
                    if status==429:
                        return False,"","quota"
                    if status in(401,403):
                        logger.error("Groq HTTP %s: %s",status,self._redact(str(data)[:300]if data else''))
                        return False,"","auth"
                    if status==404:
                        logger.error("Groq 404 (модель не найдена) для @%s",username)
                        return False,"","model_not_found"
                    if status>=500:
                        logger.error("Groq server error %s",status)
                        if attempt<max_retries-1:
                            await asyncio.sleep(2**attempt)
                            continue
                        return False,"","server"
                    if status!=200:
                        if data:
                            detail=str(data)[:300]
                        else:
                            try:detail=(await resp.text())[:300]
                            except Exception:detail=''
                        logger.error("Groq HTTP %s: %s",status,self._redact(detail))
                        return False,f"HTTP {status}: {detail}","unknown"
                    choices=(data or{}).get("choices",[])
                    raw_text=(choices[0].get("message",{}).get("content","")if choices else"").strip()
                    finish_reason=choices[0].get("finish_reason")if choices else None
                    if not raw_text:
                        if finish_reason=="length":return False,self._t("Ответ модели обрезан по лимиту токенов","Model response truncated due to token limit"),"unknown"
                        return False,self._t("Пустой ответ от модели","Empty response from the model"),"unknown"
                    if finish_reason=="length":return False,self._t("Ответ модели обрезан по лимиту токенов до завершения JSON","Model response truncated by token limit before JSON completion"),"unknown"
                    parsed=self._parse_ai_json(raw_text)
                    if parsed is None:
                        logger.warning("Groq non-JSON response: %s",self._redact(raw_text[:500]))
                        return False,self._t("Модель вернула некорректный JSON. Попробуйте ещё раз.","The model returned invalid JSON. Please try again."),"json_parse"
                    return self._process_ai_response(parsed,username,fragment_status,price,comparable_usd,model,is_taken)
            except(aiohttp.ClientError,asyncio.TimeoutError)as e:
                logger.warning("Groq request error (attempt %d): %s",attempt+1,self._redact(str(e)))
                if attempt<max_retries-1:
                    await asyncio.sleep(2**attempt)
                    continue
                return False,self._t(f"Сетевая ошибка: {e}",f"Network error: {e}"),"network"
            except Exception as e:
                logger.exception("Groq unexpected error: %s",self._redact(str(e)))
                return False,str(e),"unknown"
        return False,self._t("Превышено число попыток","Retry limit exceeded"),"unknown"

    def _process_ai_response(self,parsed,username,fragment_status,price,comparable_usd,model=None,is_taken=False):
        def esc(v):return html.escape(str(v),quote=True)if v is not None else""
        is_ru=self._is_ru()
        lines=[]
        fragment_url=f"https://fragment.com/username/{username}"
        show_link=bool(price)and fragment_status in(FragmentStatus.SOLD,FragmentStatus.AVAILABLE)
        if fragment_status is FragmentStatus.SOLD and price:
            label=f"<b>Продан на Fragment | Цена: {esc(price)} GRAM</b>"if is_ru else f"<b>Sold on Fragment | Price: {esc(price)} GRAM</b>"
            lines.append(f"{self._emoji('stats')} {self._emoji('success')} {label}")
        elif fragment_status is FragmentStatus.AVAILABLE and price:
            label=f"<b>Аукцион на Fragment | Ставка: {esc(price)} GRAM</b>"if is_ru else f"<b>Fragment auction | Bid: {esc(price)} GRAM</b>"
            lines.append(f"{self._emoji('stats')} {self._emoji('fire')} {label}")
        public_figure=parsed.get("public_figure")
        length=len(username);has_digits=any(ch.isdigit()for ch in username);has_underscore="_"in username
        base={4:15,5:10,6:6,7:4,8:3}.get(length,2)
        if has_digits:base=max(1,base//3)
        if has_underscore:base=max(1,base//2)
        fallback_low,fallback_high=base,round(base*1.5)
        price_low=parsed.get("price_low_usd");price_high=parsed.get("price_high_usd")
        if price_low is None or price_high is None:
            price_low,price_high=fallback_low,fallback_high
        if comparable_usd:
            try:
                price_low=float(price_low);price_high=float(price_high)
            except(TypeError,ValueError):
                price_low,price_high=comparable_usd,comparable_usd
            price_low=max(price_low,comparable_usd*0.5)
            price_high=min(price_high,comparable_usd*1.2)
            if price_low>price_high:
                price_low,price_high=comparable_usd*0.7,comparable_usd*1.0
        else:
            figure_scale=str(parsed.get("figure_scale")or"").strip().lower()if public_figure else None
            scale_ranges={"mega":(4000,25000),"major":(30,100),"moderate":(8,30),"minor":(3,15)}
            if public_figure and figure_scale in scale_ranges:
                lo_bound,hi_bound=scale_ranges[figure_scale]
                h=int(hashlib.sha256(username.lower().encode()).hexdigest(),16)
                frac_low=(h%1000)/1000
                frac_high=((h//1000)%1000)/1000
                span=hi_bound-lo_bound
                price_low=lo_bound+span*(0.10+0.30*frac_low)
                price_high=lo_bound+span*(0.55+0.45*frac_high)
                core=re.sub(r"[^a-z0-9]","",str(public_figure).lower())
                dilution=1.0
                if has_underscore:dilution*=0.6
                if has_digits:dilution*=0.7
                extra_chars=max(0,length-len(core))
                if extra_chars>0:
                    dilution*=max(0.45,1-0.08*extra_chars)
                price_low*=dilution
                price_high*=dilution
                lo_bound*=dilution;hi_bound*=dilution
                round_to=100 if price_low>=1000 else(10 if price_low>=100 else 1)
                price_low=round(price_low/round_to)*round_to
                price_high=round(price_high/round_to)*round_to
                price_low=max(price_low,1)
                price_high=max(price_high,price_low+round_to)
                if price_low>=price_high:
                    price_low,price_high=max(lo_bound,price_high*0.7),price_high
            else:
                try:
                    price_low=float(price_low);price_high=float(price_high)
                except(TypeError,ValueError):
                    price_low,price_high=fallback_low,fallback_high
                try:
                    ai_rank_val=float(parsed.get("rank"))
                    if ai_rank_val!=ai_rank_val:raise ValueError
                    rank_weight=max(0.0,min(10.0,ai_rank_val))/10
                except(TypeError,ValueError):
                    rank_weight=1.0
                rank_weight=rank_weight**2
                price_low=fallback_low+rank_weight*(price_low-fallback_low)
                price_high=fallback_high+rank_weight*(price_high-fallback_high)
                beauty_floor_low=max(1,round(base*0.3))
                beauty_floor_high=max(beauty_floor_low+1,round(base*0.5))
                price_low=max(price_low,beauty_floor_low)
                price_high=max(price_high,beauty_floor_high)
                hard_cap=30
                price_low=min(price_low,hard_cap)
                price_high=min(price_high,hard_cap)
                if price_low>price_high:
                    price_low,price_high=price_high,price_low
                h=int(hashlib.sha256(username.lower().encode()).hexdigest(),16)
                jitter=((h%1000)/1000-0.5)*0.5
                price_low=max(1.0,price_low*(1+jitter))
                price_high=max(price_low+1.0,price_high*(1+jitter))
                price_low=min(price_low,hard_cap)
                price_high=min(price_high,hard_cap)
                if price_low>price_high:
                    price_low,price_high=price_high,price_low

        if not comparable_usd and parsed.get("has_meaning")is False:
            cap=max(1,min(5,10-length))
            if has_digits:cap=max(1,cap-1)
            if has_underscore:cap=max(1,cap-1)
            try:
                ai_rank_val=float(parsed.get("rank"))
                if ai_rank_val!=ai_rank_val:raise ValueError
                rank_frac=max(0.0,min(10.0,ai_rank_val))/10
            except(TypeError,ValueError):
                rank_frac=0.3
            cap=max(1,round(cap*(1+rank_frac)))
            if cap<=1:
                price_low=1;price_high=1
            else:
                h=int(hashlib.sha256(username.lower().encode()).hexdigest(),16)
                spread=min(1+(h%3),cap-1)
                price_high=cap
                price_low=max(1,cap-spread)

        if is_taken and not comparable_usd:
            is_beautiful=(not has_digits)and(not has_underscore)and length<=7
            taken_multiplier=2.2 if is_beautiful else 1.5
            price_low=min(round(price_low*taken_multiplier),30)
            price_high=min(round(price_high*taken_multiplier),30)
            if price_low>=price_high:price_high=price_low+1

        def fmt_price(v):
            try:
                num=float(v)
            except(TypeError,ValueError):
                return esc(v)
            return f"{num:,.0f}"
        if comparable_usd and fragment_status in(FragmentStatus.SOLD,FragmentStatus.AVAILABLE)and price:
            price_range=f"{fmt_price(comparable_usd)}$"
        elif price_low==price_high:
            price_range=f"{fmt_price(price_low)}$"
        else:
            price_range=f"{fmt_price(price_low)} - {fmt_price(price_high)}$"
        rank_int,potential_int=self._resolve_rank(username,comparable_usd,parsed.get("rank"))
        placeholder_words={"нету","нет","отсутствуют","отсутствует","-","—","none","no","n/a","нет недостатков","нет преимуществ","отсутствуют недостатки"}

        def clean_points(raw):
            points=[]
            for item in raw or[]:
                text=str(item).strip()
                if not text:continue
                if text.strip(".!").lower()in placeholder_words:continue
                points.append(text)
            return points[:3]
        pros=clean_points(parsed.get("pros"))
        cons=clean_points(parsed.get("cons"))
        if comparable_usd and fragment_status in(FragmentStatus.SOLD,FragmentStatus.AVAILABLE)and price:
            lines.append(f"<i>{self._emoji('chart')} <b>@{esc(username)}</b> — {esc(price)} GRAM (~${fmt_price(comparable_usd)})</i>")
        else:
            lines.append(f"<i>{self._emoji('chart')} <b>@{esc(username)}</b> — {price_range}</i>")
        link_part=f" | {self._emoji('link')} <a href=\"{fragment_url}\">{'Ссылка'if is_ru else'Link'}</a>"if show_link else""
        lines.append(f"<i>{self._emoji('robot')} {esc(model)if model else'—'} | {self._emoji('trophy')} {rank_int}/10 | {self._emoji('star')} {potential_int}/5{link_part}</i>")
        if pros:
            pros_text="\n".join(f"{i}. {esc(p)}"for i,p in enumerate(pros,1))
            lines.append(f"{self._emoji('success')} <b>{self.strings['ai_pros_label']}:</b>\n<blockquote expandable>{pros_text}</blockquote>")
        if cons:
            cons_text="\n".join(f"{i}. {esc(c)}"for i,c in enumerate(cons,1))
            lines.append(f"{self._emoji('cross')} <b>{self.strings['ai_cons_label']}:</b>\n<blockquote expandable>{cons_text}</blockquote>")
        if public_figure:
            figure_note=str(parsed.get("figure_note")or"").strip()
            pf_str=str(public_figure).strip()
            if figure_note:
                fn_stripped=figure_note.lstrip()
                if fn_stripped.lower().startswith(pf_str.lower()):
                    fn_stripped=fn_stripped[len(pf_str):].lstrip(" —-:,.")
                    figure_note=fn_stripped
            figure_text=f"{esc(public_figure)}"
            if figure_note:figure_text+=f" — {esc(figure_note)}"
            lines.append(f"{self._emoji('chart')} <b>{self.strings['ai_figure_label']}:</b>\n<blockquote expandable>{figure_text}</blockquote>")
        return True,"\n".join(lines),None

    async def _run_gemini_provider(self,username,fragment_status,price,is_taken=False):
        model=str(self.config["ai_model"]or"").strip()or"gemini-3.5-flash"
        max_attempts=3
        last_result=(False,"","no_key")
        for attempt in range(1,max_attempts+1):
            api_key=await self._get_next_ai_key()
            if not api_key:break
            result=await self._ai_evaluate_async(api_key,model,username,fragment_status,price,is_taken)
            success,body,error_type=result
            last_result=result
            if success:return result
            if error_type in("quota","auth"):await self._mark_ai_key_bad(api_key)
            if error_type not in("network","server","json_parse","quota","auth"):break
            if attempt>=max_attempts:break
            has_other_key=error_type in("quota","auth")and any(self.key_status.get(k,True)for k in self.api_keys if k!=api_key)
            if has_other_key:
                continue
            if error_type=="quota":
                logger.warning("AI-запрос для @%s: квота Gemini исчерпана",username)
                break
            if error_type=="auth":
                logger.warning("AI-запрос для @%s: нет рабочих ключей Gemini (auth)",username)
                break
            delay=min(attempt,3)
            logger.warning("AI-запрос для @%s не удался (попытка %d/%d, тип=%s), повтор через %ss",username,attempt,max_attempts,error_type,delay)
            await asyncio.sleep(delay)
        return last_result

    async def _run_groq_provider(self,username,fragment_status,price,is_taken=False):
        groq_keys=self._refresh_groq_api_keys()
        if not groq_keys:return(False,"","no_key")
        groq_model=str(self.config["groq_model"]or"").strip()or"openai/gpt-oss-120b"
        last_result=(False,"","no_key")
        ds_max_attempts=min(len(groq_keys),self.MAX_RETRIES_GROQ)
        for ds_attempt in range(1,ds_max_attempts+1):
            ds_key=await self._get_next_groq_key()
            if not ds_key:break
            ds_result=await self._ai_evaluate_groq_async(ds_key,groq_model,username,fragment_status,price,is_taken)
            ds_success,ds_body,ds_error_type=ds_result
            last_result=ds_result
            if ds_success:return ds_result
            if ds_error_type in("quota","auth"):await self._mark_groq_key_bad(ds_key)
            if ds_error_type not in("network","server","json_parse","quota","auth"):break
            has_other_ds_key=ds_error_type in("quota","auth")and any(self.groq_key_status.get(k,True)for k in self.groq_api_keys if k!=ds_key)
            if not has_other_ds_key and ds_attempt>=ds_max_attempts:break
        return last_result

    async def _ai_evaluate(self,username,fragment_status,price,is_taken=False):
        provider=str(self.config["ai_provider"]or"auto").strip().lower()
        if provider=="groq":
            return await self._run_groq_provider(username,fragment_status,price,is_taken)
        if provider=="gemini":
            return await self._run_gemini_provider(username,fragment_status,price,is_taken)
        primary_name,primary,fallback_name,fallback="Gemini",self._run_gemini_provider,"Groq",self._run_groq_provider
        primary_result=await primary(username,fragment_status,price,is_taken)
        if primary_result[0]:return primary_result
        logger.info("%s не сработал для @%s (тип=%s), пробуем %s как fallback",primary_name,username,primary_result[2],fallback_name)
        fallback_result=await fallback(username,fragment_status,price,is_taken)
        if fallback_result[0]:
            logger.info("%s fallback сработал для @%s",fallback_name,username)
            return fallback_result
        if primary_result[2]=="no_key"and fallback_result[2]!="no_key":return fallback_result
        return primary_result

    async def _download_avatar_async(self,url):
        current_url=url
        for redirect_index in range(self.AVATAR_MAX_REDIRECTS+1):
            self._ensure_public_http_url(current_url)
            session=await self._get_session()
            try:
                async with session.get(current_url,allow_redirects=False,timeout=aiohttp.ClientTimeout(total=10))as resp:
                    if 300<=resp.status<400:
                        location=resp.headers.get("Location")
                        if not location:raise ValueError("avatar redirect has no Location header")
                        if redirect_index>=self.AVATAR_MAX_REDIRECTS:raise ValueError("too many avatar redirects")
                        current_url=urljoin(current_url,location)
                        continue
                    if resp.status!=200:raise ValueError(f"HTTP {resp.status}")
                    content_type=resp.headers.get("Content-Type","").split(";",1)[0].strip().lower()
                    if content_type and not content_type.startswith("image/"):raise ValueError("avatar URL does not return an image")
                    data=bytearray()
                    async for chunk in resp.content.iter_chunked(64*1024):
                        data.extend(chunk)
                        if len(data)>self.AVATAR_MAX_BYTES:raise ValueError("avatar is too large")
                    if not data:raise ValueError("avatar response is empty")
                    image_data=bytes(data)
                    extension=self._detect_image_extension(image_data)
                    if extension is None:raise ValueError("avatar data is not a supported image")
                    return image_data,extension
            except aiohttp.ClientError as e:
                logger.warning("Avatar download error: %s",self._redact(str(e)))
                raise ValueError(f"network error: {e}")
        raise ValueError("too many avatar redirects")

    def _ensure_public_http_url(self,url):
        parsed=urlparse(url)
        if parsed.scheme.lower()not in("http","https")or not parsed.hostname:raise ValueError("avatar URL must use http or https")
        if parsed.username or parsed.password:raise ValueError("credentials in avatar URL are not allowed")
        hostname=parsed.hostname.rstrip(".").lower()
        if hostname=="localhost"or hostname.endswith(".localhost"):raise ValueError("localhost is not allowed")
        try:
            addresses=socket.getaddrinfo(hostname,parsed.port,type=socket.SOCK_STREAM)
        except socket.gaierror as e:
            raise ValueError("avatar hostname cannot be resolved")from e
        if not addresses:raise ValueError("avatar hostname has no addresses")
        for address in addresses:
            ip=ipaddress.ip_address(address[4][0].split("%",1)[0])
            if not ip.is_global:raise ValueError("private, loopback or link-local avatar hosts are not allowed")

    @staticmethod
    def _detect_image_extension(data):
        if data.startswith(b"\xff\xd8\xff"):return".jpg"
        if data.startswith(b"\x89PNG\r\n\x1a\n"):return".png"
        if data.startswith((b"GIF87a",b"GIF89a")):return".gif"
        if len(data)>=12 and data[:4]==b"RIFF"and data[8:12]==b"WEBP":return".webp"
        return None

    async def _set_channel_avatar(self,channel):
        avatar_url=str(self.config["channel_avatar_url"]or"").strip()
        if not avatar_url:return True
        try:
            image_data,extension=await self._download_avatar_async(avatar_url)
            buffer=io.BytesIO(image_data)
            buffer.name=f"avatar{extension}"
            uploaded=await self._client.upload_file(buffer)
            await self._client(functions.channels.EditPhotoRequest(channel=channel,photo=InputChatUploadedPhoto(file=uploaded)))
            return True
        except Exception:
            logger.exception("Не удалось установить аватар канала")
            return False

    async def _cleanup_service_messages(self,channel):
        try:
            async for message in self._client.iter_messages(channel,limit=10):
                if not message.action:continue
                try:await message.delete()
                except Exception as e:logger.debug("Не удалось удалить сервисное сообщение %s: %s",getattr(message,"id","?"),e)
        except Exception as e:logger.debug("Не удалось очистить сервисные сообщения: %s",e)

    async def _rollback_channel(self,channel):
        try:
            await self._client(functions.channels.DeleteChannelRequest(channel=channel))
            return True
        except Exception:
            logger.exception("Не удалось удалить временный канал после ошибки захвата")
            return False

    async def _grab_username(self,username):
        channel=None
        title=str(self.config["channel_title"]or"")
        about=str(self.config["channel_about"]or"")
        if"{me}"in about:
            own_username=None
            try:
                me=await self._client.get_me()
                own_username=getattr(me,"username",None)
            except Exception:logger.debug("Не удалось получить собственный юзернейм для описания канала")
            about=about.replace("{me}",f"@{own_username}"if own_username else"")
        channel_message=str(self.config["channel_message"]or"").strip()or None
        if channel_message and"{me}"in channel_message:
            own_username_msg=None
            try:
                me_msg=await self._client.get_me()
                own_username_msg=getattr(me_msg,"username",None)
            except Exception:logger.debug("Не удалось получить собственный юзернейм для сообщения канала")
            channel_message=channel_message.replace("{me}",f"@{own_username_msg}"if own_username_msg else"")
        if not title.strip():return GrabStatus.BAD_TITLE,None,False
        try:
            result=await self._client(functions.channels.CreateChannelRequest(title=title,about=about,broadcast=True,megagroup=False))
            chats=getattr(result,"chats",None)
            if not chats:
                logger.error("CreateChannelRequest вернул результат без chats")
                return GrabStatus.ERROR,None,False
            channel=chats[0]
            update_result=await self._client(functions.channels.UpdateUsernameRequest(channel=channel,username=username))
            if not update_result:
                logger.error("UpdateUsernameRequest вернул False для @%s",username)
                rollback_failed=not await self._rollback_channel(channel)
                return GrabStatus.ERROR,None,rollback_failed
        except Exception as error:
            status,detail=self._classify_grab_error(error)
            if status is GrabStatus.ERROR:
                logger.exception("Ошибка при захвате @%s",username)
            else:
                logger.warning("Не удалось занять @%s: %s",username,type(error).__name__)
            rollback_failed=False
            if channel is not None:
                rollback_failed=not await self._rollback_channel(channel)
            return status,detail,rollback_failed
        avatar_ok=await self._set_channel_avatar(channel)
        await self._cleanup_service_messages(channel)
        firstpost_ok=True
        if channel_message is not None:
            try:
                await self._client.send_message(channel,channel_message,parse_mode="html")
            except Exception:
                firstpost_ok=False
                logger.exception("Не удалось отправить первый пост в канал @%s",username)
        if avatar_ok and firstpost_ok:status=GrabStatus.SUCCESS
        elif not avatar_ok and firstpost_ok:status=GrabStatus.SUCCESS_AVATAR_FAILED
        elif avatar_ok and not firstpost_ok:status=GrabStatus.SUCCESS_FIRSTPOST_FAILED
        else:status=GrabStatus.SUCCESS_AVATAR_FIRSTPOST_FAILED
        return status,f"t.me/{username}",False

    def _generate_variants(self,prefix,count=None):
        target_count=self.DEFAULT_PREFIX_CANDIDATES if count is None else max(1,min(count,self.MAX_PREFIX_CANDIDATES))
        variants=[];seen=set()

        def add(candidate):
            if len(variants)>=target_count:return
            if candidate in seen:return
            if not 5<=len(candidate)<=32:return
            if not self.USERNAME_RE.fullmatch(candidate):return
            seen.add(candidate);variants.append(candidate)
        add(prefix)
        priority_suffixes=["_","__","x","xx","official","real","pro","me","its","im","ok","hi","gg","tv","xo","neo","one","go","top","best","dev","app","web","bot"]+list("0123456789")
        for suffix in priority_suffixes:add(f"{prefix}{suffix}")
        alphabet="abcdefghijklmnopqrstuvwxyz"
        suffix_pool=[]
        suffix_pool.extend(str(n)for n in range(1000))
        suffix_pool.extend(f"{n:02d}"for n in range(100))
        suffix_pool.extend(f"{n:03d}"for n in range(300))
        suffix_pool.extend(alphabet)
        suffix_pool.extend(a+b for a in alphabet for b in alphabet)
        suffix_pool.extend(f"_{n}"for n in range(200))
        suffix_pool.extend(f"x{n}"for n in range(200))
        suffix_pool.extend(f"_{c}"for c in alphabet)
        suffix_pool.extend(f"x{c}"for c in alphabet)
        random.shuffle(suffix_pool)
        for suffix in suffix_pool:
            if len(variants)>=target_count:break
            add(f"{prefix}{suffix}")
        return variants

    def _generate_random_usernames(self,length=5,count=25):
        vowels="aeiou";consonants="bcdfghjklmnpqrstvwxyz";patterns=["cvcvc","vcvcv","cvvcc","ccvcv"]
        result=[];seen=set();attempts=0;max_attempts=max(1000,count*40)
        while len(result)<count and attempts<max_attempts:
            attempts+=1
            if length==5:pattern=random.choice(patterns)
            else:
                first=random.choice(("c","v"))
                pattern="".join(first if i%2==0 else("v"if first=="c"else"c")for i in range(length))
            username="".join(random.choice(consonants if kind=="c"else vowels)for kind in pattern)
            if username in seen:continue
            seen.add(username);result.append(username)
        return result

    async def _edit_status(self,status_message,message,text):
        target=status_message or message
        try:
            updated=await utils.answer(target,text)
            return updated or target
        except Exception as e:logger.warning("Не удалось обновить статус поиска: %s",e)
        if target is not message:
            try:
                updated=await utils.answer(message,text)
                return updated or message
            except Exception as e:logger.warning("Не удалось восстановить статус поиска: %s",e)
        return status_message

    def _get_search_delay(self):
        delay_min=float(self.config["delay_min"]);delay_max=float(self.config["delay_max"])
        return random.uniform(min(delay_min,delay_max),max(delay_min,delay_max))

    async def _wait_search_delay(self,delay):
        if self._find_stop_event is None:
            await asyncio.sleep(delay);return False
        try:
            await asyncio.wait_for(self._find_stop_event.wait(),timeout=delay)
            return True
        except asyncio.TimeoutError:
            return False

    def _refresh_ai_api_keys(self):
        raw_keys=str(self.config["ai_api_keys"]or"")
        new_keys=[k.strip()for k in raw_keys.split(",")if k.strip()]
        if new_keys!=self.api_keys:
            self.api_keys=new_keys
            self.key_status.clear()
            self.current_key_index=0
        return self.api_keys

    async def _get_next_ai_key(self):
        async with self.key_lock:
            self._refresh_ai_api_keys()
            if not self.api_keys:return None
            start=self.current_key_index
            for i in range(len(self.api_keys)):
                idx=(start+i)%len(self.api_keys)
                key=self.api_keys[idx]
                if self.key_status.get(key,True):
                    self.current_key_index=(idx+1)%len(self.api_keys)
                    return key
            self.key_status.clear();self.current_key_index=0
            return self.api_keys[0]if self.api_keys else None

    async def _mark_ai_key_bad(self,key):
        async with self.key_lock:
            self.key_status[key]=False
            logger.warning("Gemini-ключ %s… временно исключён из ротации",key[:8])

    def _refresh_groq_api_keys(self):
        raw_keys=str(self.config["groq_api_keys"]or"")
        new_keys=[k.strip()for k in raw_keys.split(",")if k.strip()]
        if new_keys!=self.groq_api_keys:
            self.groq_api_keys=new_keys
            self.groq_key_status.clear()
            self.groq_current_key_index=0
        return self.groq_api_keys

    async def _get_next_groq_key(self):
        async with self.groq_key_lock:
            self._refresh_groq_api_keys()
            if not self.groq_api_keys:return None
            start=self.groq_current_key_index
            for i in range(len(self.groq_api_keys)):
                idx=(start+i)%len(self.groq_api_keys)
                key=self.groq_api_keys[idx]
                if self.groq_key_status.get(key,True):
                    self.groq_current_key_index=(idx+1)%len(self.groq_api_keys)
                    return key
            self.groq_key_status.clear();self.groq_current_key_index=0
            return self.groq_api_keys[0]if self.groq_api_keys else None

    async def _mark_groq_key_bad(self,key):
        async with self.groq_key_lock:
            self.groq_key_status[key]=False
            logger.warning("Groq-ключ %s… временно исключён из ротации",key[:8])

    @staticmethod
    def _error_signature(error):
        class_name=re.sub(r"(?<!^)(?=[A-Z])","_",type(error).__name__).upper()
        parts=[class_name,str(error).upper()]
        message=getattr(error,"message",None)
        if message:parts.append(str(message).upper())
        return" ".join(parts)

    @classmethod
    def _extract_flood_wait(cls,error):
        seconds=getattr(error,"seconds",None)
        if isinstance(seconds,(int,float))and seconds>=0:return int(seconds)
        match=re.search(r"FLOOD_WAIT[_\s-]*(\d+)",cls._error_signature(error))
        return int(match.group(1))if match else 0

    def _format_wait(self,seconds):
        total=max(int(seconds or 0),1)
        hours,remainder=divmod(total,3600)
        minutes,secs=divmod(remainder,60)
        if self._is_ru():
            return f"{hours} ч {minutes:02d} мин {secs:02d} сек"
        return f"{hours}h {minutes:02d}m {secs:02d}s"

    @classmethod
    def _classify_check_error(cls,error):
        sig=cls._error_signature(error)
        if"FLOOD_WAIT"in sig:return UsernameStatus.FLOOD_WAIT,cls._extract_flood_wait(error)
        if"USERNAME_PURCHASE_AVAILABLE"in sig:return UsernameStatus.PURCHASABLE,None
        if"USERNAME_INVALID"in sig:return UsernameStatus.INVALID,None
        if"USERNAME_OCCUPIED"in sig:return UsernameStatus.UNAVAILABLE,None
        return UsernameStatus.ERROR,None

    @classmethod
    def _classify_grab_error(cls,error):
        sig=cls._error_signature(error)
        if"FLOOD_WAIT"in sig:return GrabStatus.FLOOD_WAIT,cls._extract_flood_wait(error)
        if"USERNAME_PURCHASE_AVAILABLE"in sig:return GrabStatus.USERNAME_PURCHASABLE,None
        if"USERNAME_OCCUPIED"in sig:return GrabStatus.USERNAME_TAKEN,None
        if"USERNAME_INVALID"in sig:return GrabStatus.USERNAME_INVALID,None
        if"CHANNELS_ADMIN_PUBLIC_TOO_MUCH"in sig:return GrabStatus.PUBLIC_LIMIT,None
        if"CHANNELS_TOO_MUCH"in sig:return GrabStatus.CHANNEL_LIMIT,None
        if"USER_RESTRICTED"in sig:return GrabStatus.USER_RESTRICTED,None
        if"CHAT_TITLE_EMPTY"in sig:return GrabStatus.BAD_TITLE,None
        if"CHAT_ABOUT_TOO_LONG"in sig:return GrabStatus.BAD_ABOUT,None
        if"CHAT_ADMIN_REQUIRED"in sig or"CHANNEL_INVALID"in sig or"CHANNEL_PRIVATE"in sig or"CHAT_WRITE_FORBIDDEN"in sig:
            return GrabStatus.NO_RIGHTS,None
        return GrabStatus.ERROR,None

    @classmethod
    def _normalize_username_input(cls,raw):
        value=unicodedata.normalize("NFKC",str(raw or"")).strip()
        value="".join(ch for ch in value if unicodedata.category(ch)!="Cf").strip()
        value=cls.TG_LINK_RE.sub("",value)
        value=value.split("?",1)[0].split("#",1)[0].rstrip("/")
        return value.lstrip("@").strip()

    @classmethod
    def _validate_username(cls,raw):
        username=cls._normalize_username_input(raw)
        if not username:return None,"empty"
        if not 4<=len(username)<=32:return None,"length"
        if not cls.USERNAME_RE.fullmatch(username):return None,"chars"
        return username,None

    @classmethod
    def _validate_prefix(cls,raw):
        prefix=cls._normalize_username_input(raw)
        if not prefix or len(prefix)>31:return None
        if not cls.PREFIX_RE.fullmatch(prefix):return None
        return prefix

    async def _get_username_arg(self,message):
        raw=utils.get_args_raw(message)
        if not raw or not raw.strip():
            reply_username=await self._get_reply_username(message)
            if reply_username:
                return reply_username
        username,error=self._validate_username(raw)
        if error=="empty":await utils.answer(message,self.strings["no_args"])
        elif error=="length":await utils.answer(message,self.strings["bad_length"])
        elif error=="chars"or username is None:await utils.answer(message,self.strings["bad_chars"])
        else:return username
        return None

    async def _get_reply_username(self,message):
        try:
            reply=await message.get_reply_message()
            if not reply:return None
            text=(getattr(reply,"raw_text",None)or getattr(reply,"text",None)or"").strip()
            if text:
                match=re.search(r"@([A-Za-z0-9_]{4,32})\b",text)
                if match:
                    valid,error=self._validate_username(match.group(1))
                    if not error:return valid
            sender=await reply.get_sender()
            if not sender:return None
            username=getattr(sender,"username",None)
            if not username:
                for extra in getattr(sender,"usernames",None)or[]:
                    value=getattr(extra,"username",None)
                    if value:
                        username=value
                        break
            if not username:return None
            valid,error=self._validate_username(username)
            if error:return None
            return valid
        except Exception:
            logger.exception("Не удалось получить юзернейм из реплая")
            return None

    async def _get_own_usernames(self):
        if self._own_usernames is not None:return self._own_usernames
        usernames=set()
        try:
            me=await self._client.get_me()
            primary=getattr(me,"username",None)
            if primary:usernames.add(primary.lower())
            for extra in getattr(me,"usernames",None)or[]:
                value=getattr(extra,"username",None)
                if value:usernames.add(value.lower())
        except Exception:logger.exception("Не удалось получить собственные юзернеймы аккаунта")
        self._own_usernames=usernames
        return usernames

    async def _check(self,username):
        try:
            available=await self._client(functions.account.CheckUsernameRequest(username=username))
            if available:
                own_usernames=await self._get_own_usernames()
                if username.lower()in own_usernames:return UsernameStatus.UNAVAILABLE,None
                return UsernameStatus.AVAILABLE,None
            return UsernameStatus.UNAVAILABLE,None
        except Exception as e:
            status,wait=self._classify_check_error(e)
            if status is UsernameStatus.ERROR:logger.exception("Ошибка при проверке юзернейма @%s",username)
            elif status is UsernameStatus.FLOOD_WAIT:logger.warning("FloodWait %ss при проверке @%s",wait or 0,username)
            return status,wait

    @classmethod
    def _quality_base(cls,username):
        length=len(username)
        has_digits=any(ch.isdigit()for ch in username)
        has_underscore="_"in username
        base={4:9,5:7,6:5,7:4,8:3}.get(length,2)
        if has_digits:base=max(0,base-3)
        if has_underscore:base=max(0,base-2)
        return base

    @classmethod
    def _price_floor(cls,comparable_usd):
        if not comparable_usd:return 0
        if comparable_usd>=500:return 9
        if comparable_usd>=150:return 7
        if comparable_usd>=50:return 5
        if comparable_usd>=20:return 3
        return 0

    @classmethod
    def _compute_rank(cls,username,comparable_usd):
        base=cls._quality_base(username)
        rank=base
        if comparable_usd:
            floor=(base+cls._price_floor(comparable_usd))/2
            rank=max(base,floor)
        rank_int=max(0,min(10,round(rank)))
        potential_int=max(0,min(5,round(rank_int/2)))
        return rank_int,potential_int

    @classmethod
    def _resolve_rank(cls,username,comparable_usd,ai_rank):
        try:
            rank_val=float(ai_rank)
            if rank_val!=rank_val:raise ValueError
        except(TypeError,ValueError):
            return cls._compute_rank(username,comparable_usd)
        if comparable_usd:
            floor=(cls._quality_base(username)+cls._price_floor(comparable_usd))/2
            rank_val=max(rank_val,floor)
        rank_int=max(0,min(10,round(rank_val)))
        potential_int=max(0,min(5,round(rank_int/2)))
        return rank_int,potential_int

    async def _show_unavailable_result(self,message,username,telegram_status,allow_grab=False,flood_wait=None):
        safe_username=html.escape(username,quote=True)
        loading=await self.inline.form(text=plain_emoji(self.strings["checking"].format(username=safe_username)),message=message,reply_markup=[[{"text":self.strings["close_button"],"callback":self._close_cb}]])
        inline_loading=bool(loading)
        if not loading:loading=await utils.answer(message,self.strings["checking"].format(username=safe_username))
        fragment_status,price=await self._check_fragment(username)
        fragment_url=f"https://fragment.com/username/{username}"
        safe_url=html.escape(fragment_url,quote=True)
        safe_price=html.escape(str(price),quote=True)if price else""
        price_line=self.strings["price_line"].format(price=safe_price)if price else""
        if telegram_status is UsernameStatus.FLOOD_WAIT:
            if fragment_status is FragmentStatus.AVAILABLE:
                text=self.strings["flood_wait_fragment_available"].format(username=safe_username,price_line=price_line,url=safe_url)
            elif fragment_status is FragmentStatus.SOLD:
                text=self.strings["flood_wait_fragment_sold"].format(username=safe_username,price_line=price_line,url=safe_url)
            elif fragment_status is FragmentStatus.UNAVAILABLE:
                text=self.strings["flood_wait_fragment_unavailable"].format(username=safe_username,url=safe_url)
            elif fragment_status is FragmentStatus.NOT_FOUND:
                text=self.strings["flood_wait_unknown"].format(username=safe_username)
            else:
                text=self.strings["flood_wait_unknown"].format(username=safe_username)+self.strings["fragment_error"]
            if flood_wait is not None:text+=self.strings["flood_wait_fragment_note"].format(wait=self._format_wait(flood_wait))
        elif fragment_status is FragmentStatus.SOLD:
            text=self.strings["fragment_sold"].format(username=safe_username,price_line=price_line,url=safe_url)
        elif fragment_status is FragmentStatus.AVAILABLE:
            text=self.strings["fragment_available"].format(username=safe_username,price_line=price_line,url=safe_url)
        elif fragment_status is FragmentStatus.UNAVAILABLE:
            text=self.strings["fragment_unavailable"].format(username=safe_username,url=safe_url)
        elif telegram_status is UsernameStatus.PURCHASABLE:
            text=self.strings["purchasable"].format(username=safe_username)
            if fragment_status is FragmentStatus.ERROR:text+=self.strings["fragment_error"]
        else:
            text=self.strings["occupied"].format(username=safe_username)
            if fragment_status is FragmentStatus.ERROR:text+=self.strings["fragment_error"]
        result_markup=[]
        if allow_grab:
            result_markup.append([{"text":self.strings["grab_button"],"callback":self._grab_cb,"args":(username,)},{"text":self.strings["close_button"],"callback":self._close_cb}])
        else:
            result_markup.append([{"text":self.strings["close_button"],"callback":self._close_cb}])
        if inline_loading:
            try:
                await loading.edit(text=plain_emoji(text),reply_markup=result_markup)
                return
            except Exception as e:logger.warning("Не удалось обновить inline-результат: %s",e)
        await self._edit_status(loading,message,text)

    @loader.command(ru_doc="[юзернейм] — проверяет доступность и даёт кнопку \"занять\".",en_doc="[username] — checks availability and gives a \"claim\" button.")
    async def v(self,message):
        if self._find_running:
            await utils.answer(message,self.strings["find_running"]);return
        username=await self._get_username_arg(message)
        if username is None:return
        status,wait=await self._check(username)
        safe_username=html.escape(username,quote=True)
        if status is UsernameStatus.AVAILABLE:
            form=await self.inline.form(text=plain_emoji(self.strings["available"].format(username=safe_username)),message=message,reply_markup=[[{"text":self.strings["grab_button"],"callback":self._grab_cb,"args":(username,)},{"text":"✖","callback":self._close_cb}]])
            if not form:await utils.answer(message,self.strings["available_no_inline"].format(username=safe_username))
            return
        if status is UsernameStatus.FLOOD_WAIT:
            await self._show_unavailable_result(message,username,status,allow_grab=True,flood_wait=max(wait or 0,1));return
        if status is UsernameStatus.ERROR:
            await utils.answer(message,self.strings["check_error"].format(username=safe_username));return
        if status is UsernameStatus.INVALID:
            await self._show_unavailable_result(message,username,status);return
        await self._show_unavailable_result(message,username,status)

    @loader.command(ru_doc="[юзернейм] — ИИ‑оценка стоимости с учётом Fragment.",en_doc="[username] — AI price estimate with Fragment data.")
    async def vai(self,message):
        if self._find_running:
            await utils.answer(message,self.strings["find_running"]);return
        username=await self._get_username_arg(message)
        if username is None:return
        if not self._refresh_ai_api_keys()and not self._refresh_groq_api_keys():
            await utils.answer(message,self.strings["ai_no_key"]);return
        safe_username=html.escape(username,quote=True)
        status_message=await utils.answer(message,self.strings["ai_evaluating"].format(username=safe_username))
        fragment_status,price=await self._check_fragment(username)
        username_status,_=await self._check(username)
        is_taken=username_status is UsernameStatus.UNAVAILABLE
        cache_key=f"{username}|{fragment_status.value}|{price or''}|{int(is_taken)}"
        now=time.monotonic()
        cached=self._ai_cache.get(cache_key)
        if cached and now-cached[0]<self.AI_CACHE_TTL:
            success,body,error_type=cached[1]
        else:
            success,body,error_type=await self._ai_evaluate(username,fragment_status,price,is_taken)
            if success:
                self._ai_cache[cache_key]=(now,(success,body,error_type))
                if len(self._ai_cache)>200:
                    expired=[k for k,(ts,_)in self._ai_cache.items()if now-ts>=self.AI_CACHE_TTL]
                    for k in expired:self._ai_cache.pop(k,None)
        if not success:
            if error_type=="no_key":text=self.strings["ai_no_key"]
            elif error_type=="quota":text=self.strings["ai_error_quota_retry"].format(seconds=body)if body else self.strings["ai_error_quota"]
            elif error_type=="auth":text=self.strings["ai_error_auth"]
            elif error_type=="server":text=self.strings["ai_error_server"]
            elif error_type=="model_not_found":text=self.strings["ai_error_model_not_found"]
            else:text=self.strings["ai_error_unknown"].format(error=html.escape(body,quote=True))
            await utils.answer(status_message or message,text);return
        availability_note=""
        if username_status is UsernameStatus.AVAILABLE:
            availability_note=self.strings["ai_note_available"].format(username=safe_username)
        elif username_status is UsernameStatus.UNAVAILABLE and fragment_status not in(FragmentStatus.SOLD,FragmentStatus.AVAILABLE):
            availability_note=self.strings["ai_note_taken_regular"]
        result_text=self.strings["ai_result"].format(username=safe_username,body=availability_note+body)
        await utils.answer(status_message or message,result_text)

    def _find_stop_markup(self):
        return[[{"text":self.strings["find_stop_button"],"callback":self._find_stop_cb}]]

    async def _update_find_status(self,status_message,message,text,inline_status):
        if inline_status and status_message is not None:
            try:
                await status_message.edit(text=plain_emoji(text),reply_markup=self._find_stop_markup())
                return status_message
            except Exception as e:logger.warning("Не удалось обновить inline-прогресс поиска: %s",e);return status_message
        return await self._edit_status(status_message,message,text)

    async def _finish_find_text(self,status_message,message,text,inline_status):
        if inline_status and status_message is not None:
            try:
                await status_message.edit(text=plain_emoji(text),reply_markup=[[{"text":self.strings["close_button"],"callback":self._close_cb}]])
                return
            except Exception:logger.exception("Не удалось обновить финальное inline-состояние поиска")
        await self._edit_status(status_message,message,text)

    async def _finish_find_results(self,status_message,message,found,mode_text,inline_status):
        found_count=len(found)
        found_tuple=tuple(found)
        page_text,page_buttons=self._build_find_page(found_tuple,0,mode_text)
        if inline_status and status_message is not None:
            try:
                await status_message.edit(text=plain_emoji(page_text),reply_markup=page_buttons)
                return
            except Exception:logger.exception("Не удалось превратить прогресс поиска в результаты")
        form=await self.inline.form(text=plain_emoji(page_text),message=message,reply_markup=page_buttons)
        if form:
            if status_message is not None and not inline_status:
                try:await status_message.delete()
                except Exception as e:logger.debug("Не удалось удалить сообщение прогресса после поиска: %s",e)
            return
        fallback_items=found[:self.FALLBACK_DISPLAY_FOUND]
        fallback_lines="\n".join(f"• <code>@{html.escape(username)}</code>"for username in fallback_items)
        more_line=self.strings["find_more"].format(shown=len(fallback_items),total_found=found_count)if found_count>len(fallback_items)else""
        await self._edit_status(status_message,message,self.strings["find_result_fallback"].format(mode=mode_text,lines=fallback_lines,more_line=more_line))

    async def _find_stop_cb(self,call):
        if not self._find_running or self._find_stop_event is None:
            try:await call.answer(plain_emoji(self.strings["stop_idle_alert"]),show_alert=False)
            except Exception as e:logger.debug("Не удалось ответить на неактуальную кнопку стоп: %s",e)
            return
        self._find_stop_event.set()
        try:await call.answer(plain_emoji(self.strings["find_stopping"]),show_alert=False)
        except Exception as e:logger.debug("Не удалось подтвердить остановку поиска: %s",e)

    def _build_find_page(self,usernames,page,mode_text):
        if not usernames:
            return self.strings["find_page_empty"],[[{"text":self.strings["close_button"],"callback":self._close_cb}]]
        pages=max(1,(len(usernames)+self.RESULTS_PER_PAGE-1)//self.RESULTS_PER_PAGE)
        page=max(0,min(page,pages-1))
        start=page*self.RESULTS_PER_PAGE
        page_items=usernames[start:start+self.RESULTS_PER_PAGE]
        lines="\n".join(f"• <code>@{html.escape(username)}</code>"for username in page_items)
        buttons=[[{"text":f"@{username}","callback":self._grab_cb,"args":(username,)}]for username in page_items]
        if pages>1:
            nav=[]
            if page>0:nav.append({"text":"◀️","callback":self._find_page_cb,"args":(usernames,page-1,mode_text)})
            nav.append({"text":f"{page+1}/{pages}","callback":self._find_page_cb,"args":(usernames,page,mode_text)})
            if page+1<pages:nav.append({"text":"▶️","callback":self._find_page_cb,"args":(usernames,page+1,mode_text)})
            buttons.append(nav)
        buttons.append([{"text":self.strings["close_button"],"callback":self._close_cb}])
        text=self.strings["find_result"].format(mode=mode_text,lines=lines,page=page+1,pages=pages,total_found=len(usernames))
        return text,buttons

    async def _find_page_cb(self,call,usernames,page,mode_text):
        try:await call.answer()
        except Exception as e:logger.debug("Не удалось подтвердить callback пагинации: %s",e)
        if not usernames:
            try:await call.edit(text=plain_emoji(self.strings["find_page_empty"]),reply_markup=[[{"text":self.strings["close_button"],"callback":self._close_cb}]])
            except Exception:logger.exception("Не удалось показать пустую страницу результатов")
            return
        text,buttons=self._build_find_page(tuple(usernames),int(page),mode_text)
        try:await call.edit(text=plain_emoji(text),reply_markup=buttons)
        except Exception:logger.exception("Не удалось переключить страницу результатов")

    @loader.command(ru_doc="[число] | [префикс] — поиск свободных юзернеймов.",en_doc="[number] | [prefix] — search for available usernames.")
    async def vfind(self,message):
        raw_args=utils.get_args_raw(message).strip()
        if self._find_running:
            await utils.answer(message,self.strings["find_running"]);return
        parts=raw_args.split()
        if len(parts)>2:
            await utils.answer(message,self.strings["vfind_usage"]);return
        if not parts:
            length=self.RANDOM_USERNAME_LENGTH
            candidates=self._generate_random_usernames(length=length,count=self.RANDOM_CANDIDATES)
            mode_text=self.strings["mode_random"].format(length=length)
        elif len(parts)==1 and parts[0].isdigit():
            check_count=int(parts[0])
            if not 1<=check_count<=self.MAX_RANDOM_CANDIDATES:
                await utils.answer(message,self.strings["count_bad"].format(maximum=self.MAX_RANDOM_CANDIDATES));return
            length=self.RANDOM_USERNAME_LENGTH
            candidates=self._generate_random_usernames(length=length,count=check_count)
            mode_text=self.strings["mode_random"].format(length=length)
        else:
            prefix=self._validate_prefix(parts[0])
            if prefix is None:await utils.answer(message,self.strings["prefix_bad"]);return
            prefix_count=self.DEFAULT_PREFIX_CANDIDATES
            if len(parts)==2:
                if not parts[1].isdigit():
                    await utils.answer(message,self.strings["vfind_usage"]);return
                prefix_count=int(parts[1])
                if not 1<=prefix_count<=self.MAX_PREFIX_CANDIDATES:
                    await utils.answer(message,self.strings["count_bad"].format(maximum=self.MAX_PREFIX_CANDIDATES));return
            candidates=self._generate_variants(prefix,count=prefix_count)
            safe_prefix=html.escape(prefix,quote=True)
            mode_text=self.strings["mode_prefix"].format(prefix=safe_prefix)
            if not candidates:
                await utils.answer(message,self.strings["find_nothing"].format(mode=mode_text));return
        self._find_running=True
        if self._find_stop_event is None:self._find_stop_event=asyncio.Event()
        self._find_stop_event.clear()
        status_message=None;inline_status=False;found=[];found_count=0;checked=0;stop_reason=None;flood_wait=0;last_progress_update=time.monotonic()
        try:
            start_text=self.strings["find_start"].format(mode=mode_text,total=len(candidates))
            status_message=await self.inline.form(text=plain_emoji(start_text),message=message,reply_markup=self._find_stop_markup())
            inline_status=bool(status_message)
            if not status_message:status_message=await utils.answer(message,start_text)
            for index,username in enumerate(candidates):
                if self._find_stop_event.is_set():
                    stop_reason="user";break
                status,wait=await self._check(username)
                checked=index+1
                if status is UsernameStatus.AVAILABLE:
                    found_count+=1;found.append(username)
                elif status is UsernameStatus.FLOOD_WAIT:
                    stop_reason="flood";flood_wait=max(wait or 0,1);break
                elif status is UsernameStatus.ERROR:
                    stop_reason="error";break
                now=time.monotonic()
                if checked%self.PROGRESS_EVERY==0 and now-last_progress_update>=self.PROGRESS_MIN_INTERVAL:
                    preview_items=found[:self.PROGRESS_PREVIEW_LIMIT]
                    found_preview="\n".join(f"• @{html.escape(item)}"for item in preview_items)if preview_items else self.strings["find_preview_empty"]
                    status_message=await self._update_find_status(status_message,message,self.strings["find_progress"].format(mode=mode_text,checked=checked,total=len(candidates),found_count=found_count,preview=found_preview),inline_status)
                    last_progress_update=now
                if index+1<len(candidates):
                    stopped=await self._wait_search_delay(self._get_search_delay())
                    if stopped:stop_reason="user";break
            if stop_reason=="flood":
                await self._finish_find_text(status_message,message,self.strings["find_flood"].format(checked=checked,total=len(candidates),wait=self._format_wait(flood_wait)),inline_status);return
            if stop_reason=="error":
                await self._finish_find_text(status_message,message,self.strings["find_error"].format(checked=checked,total=len(candidates)),inline_status);return
            if stop_reason=="user":
                if found_count:await self._finish_find_results(status_message,message,found,mode_text,inline_status)
                else:await self._finish_find_text(status_message,message,self.strings["find_stopped"].format(checked=checked,total=len(candidates),found_count=found_count),inline_status)
                return
            if found_count==0:
                await self._finish_find_text(status_message,message,self.strings["find_nothing"].format(mode=mode_text),inline_status);return
            await self._finish_find_results(status_message,message,found,mode_text,inline_status)
        except asyncio.CancelledError:raise
        except Exception:
            logger.exception("Неожиданная ошибка поиска юзернеймов")
            await self._finish_find_text(status_message,message,self.strings["find_error"].format(checked=checked,total=len(candidates)),inline_status)
        finally:
            self._find_running=False
            if self._find_stop_event is not None:self._find_stop_event.clear()

    @loader.command(ru_doc="— остановить поиск.",en_doc="— stop the search.")
    async def vstop(self,message):
        if self._find_running:
            if self._find_stop_event is not None:self._find_stop_event.set()
            await utils.answer(message,self.strings["stop_ok"])
        else:await utils.answer(message,self.strings["stop_idle"])

    def _grab_error_text(self,status,detail):
        if status is GrabStatus.FLOOD_WAIT:return self.strings["grab_flood"].format(wait=self._format_wait(detail))
        keys={GrabStatus.USERNAME_TAKEN:"grab_taken",GrabStatus.USERNAME_INVALID:"grab_invalid",GrabStatus.USERNAME_PURCHASABLE:"grab_purchasable",GrabStatus.PUBLIC_LIMIT:"grab_public_limit",GrabStatus.CHANNEL_LIMIT:"grab_channel_limit",GrabStatus.USER_RESTRICTED:"grab_restricted",GrabStatus.BAD_TITLE:"grab_bad_title",GrabStatus.BAD_ABOUT:"grab_bad_about",GrabStatus.NO_RIGHTS:"grab_no_rights"}
        return self.strings[keys.get(status,"grab_error")]

    async def _grab_cb(self,call,username):
        username,error=self._validate_username(username)
        if error or username is None:
            try:await call.answer(plain_emoji(self.strings["grab_invalid"]),show_alert=True)
            except Exception as e:logger.debug("Не удалось ответить на устаревший callback: %s",e)
            return
        if self._grab_lock is None:self._grab_lock=asyncio.Lock()
        if self._grab_lock.locked():
            try:await call.answer(plain_emoji(self.strings["grab_busy"]),show_alert=False)
            except Exception as e:logger.debug("Не удалось ответить на callback: %s",e)
            return
        async with self._grab_lock:
            try:await call.answer(plain_emoji(self.strings["grabbing"]),show_alert=False)
            except Exception as e:logger.debug("Не удалось показать статус callback: %s",e)
            status,info,rollback_failed=await self._grab_username(username)
            safe_username=html.escape(username,quote=True)
            if status in(GrabStatus.SUCCESS,GrabStatus.SUCCESS_AVATAR_FAILED,GrabStatus.SUCCESS_FIRSTPOST_FAILED,GrabStatus.SUCCESS_AVATAR_FIRSTPOST_FAILED):
                safe_channel=html.escape(str(info),quote=True)
                success_keys={GrabStatus.SUCCESS:"grab_success",GrabStatus.SUCCESS_AVATAR_FAILED:"grab_success_avatar_failed",GrabStatus.SUCCESS_FIRSTPOST_FAILED:"grab_success_firstpost_failed",GrabStatus.SUCCESS_AVATAR_FIRSTPOST_FAILED:"grab_success_avatar_firstpost_failed"}
                text=self.strings[success_keys[status]].format(username=safe_username,channel=safe_channel)
            else:
                error_text=html.escape(plain_emoji(self._grab_error_text(status,info)),quote=True)
                rollback_warning=self.strings["rollback_warning"]if rollback_failed else""
                text=self.strings["grab_error_title"].format(error=error_text,rollback_warning=rollback_warning)
            chat_id=None
            try:chat_id=call.form.get("chat")
            except Exception as e:logger.debug("Не удалось получить chat id из inline-формы: %s",e)
            if chat_id is None:
                logger.error("Не удалось отправить отдельный результат захвата @%s: chat id отсутствует в inline unit",username)
                try:await call.answer(plain_emoji(self.strings["grab_error"]),show_alert=True)
                except Exception as e:logger.debug("Не удалось показать fallback alert: %s",e)
                return
            try:
                result_form=await self.inline.form(text=plain_emoji(text),message=chat_id,reply_markup=[[{"text":self.strings["close_button"],"callback":self._close_cb}]],silent=True)
            except Exception:
                logger.exception("Не удалось создать отдельную inline-форму результата @%s",username)
                result_form=False
            if result_form:return
            try:
                await self._client.send_message(chat_id,text,parse_mode="html",link_preview=False)
            except TypeError:await self._client.send_message(chat_id,text,parse_mode="html")
            except Exception:logger.exception("Не удалось отправить отдельное сообщение результата @%s",username)

    async def _close_cb(self,call):
        try:await call.delete()
        except Exception as e:logger.debug("Не удалось закрыть inline-форму: %s",e)

    def _emoji(self,name:str,glyph:str=None)->str:
        """Обёртка над модульной функцией emoji() для вызовов вида self._emoji('success')."""
        return emoji(name,glyph)

    def _is_ru(self)->bool:
        """Определяет, выбран ли сейчас русский язык интерфейса модуля.

        self.strings["..."] уже проходит внутреннее разрешение языка (ru/en),
        а self.strings_ru — это наш собственный «сырой» русский словарь.
        Если резолвнутое значение совпадает с русским — значит активен русский.
        """
        try:
            return self.strings["close_button"]==self.strings_ru["close_button"]
        except Exception:
            return False

    def _t(self,ru:str,en:str)->str:
        """Короткий помощник локализации для строк, формируемых в коде (не из словаря strings)."""
        return ru if self._is_ru()else en

    async def _get_local_source(self):
        """Возвращает исходный код текущего загруженного модуля (через loader либо inspect)."""
        import sys,inspect
        mod=sys.modules.get(self.__class__.__module__)
        ldr_obj=getattr(mod,"__loader__",None)
        if ldr_obj and hasattr(ldr_obj,"get_source"):
            try:
                src=ldr_obj.get_source(self.__class__.__module__)
                if src:return src
            except Exception as e:logger.debug("Не удалось получить исходник через __loader__.get_source(): %s",e)
        if mod:
            try:return inspect.getsource(mod)
            except Exception as e:logger.debug("Не удалось получить исходник через inspect.getsource(): %s",e)
        return None

    def _hash_source(self,src)->str:
        return hashlib.sha256(src.encode("utf-8")).hexdigest()

    async def _fetch_remote_source(self):
        """Скачивает актуальный код модуля с GitHub (raw). Возвращает bytes или None при ошибке."""
        try:
            session=await self._get_session()
            headers={"Cache-Control":"no-cache","Pragma":"no-cache"}
            bust_url=f"{self.UPDATE_URL}?_={int(time.time())}"
            async with session.get(bust_url,headers=headers,timeout=aiohttp.ClientTimeout(total=20))as resp:
                if resp.status!=200:
                    logger.warning("Автообновление: сервер вернул статус %s",resp.status)
                    return None
                return await resp.read()
        except Exception as e:
            logger.warning("Автообновление: не удалось скачать исходник — %s",e)
            return None

    async def _safe_install_update(self)->bool:
        """Устанавливает свежую версию модуля через Loader."""
        ldr=self.lookup("Loader")
        if not ldr or not hasattr(ldr,"download_and_install"):
            logger.error("Автообновление: модуль Loader недоступен")
            return False
        try:
            res=await asyncio.wait_for(ldr.download_and_install(self.UPDATE_URL),timeout=self.UPDATE_INSTALL_TIMEOUT)
            if getattr(ldr,"fully_loaded",False):
                ldr.update_modules_in_db()
            return res==1
        except asyncio.TimeoutError:
            logger.warning("Автообновление: установка не удалась — таймаут (%s сек)",self.UPDATE_INSTALL_TIMEOUT)
            return False
        except Exception as e:
            logger.warning("Автообновление: установка не удалась — %s",e)
            return False

    async def _check_update_hashes(self):
        """Сравнивает хэш локального и удалённого кода. Возвращает (differs:bool|None, remote_ok:bool)."""
        remote_bytes=await self._fetch_remote_source()
        if not remote_bytes:return None,False
        remote_hash=hashlib.sha256(remote_bytes).hexdigest()
        local_src=await self._get_local_source()
        local_hash=self._hash_source(local_src)if local_src else""
        if not local_hash:
            logger.warning("Автообновление: не удалось получить хэш локальной версии, считаем что различаются")
            return True,True
        return remote_hash!=local_hash,True

    async def _upd_force_cb(self,call):
        try:await call.answer()
        except Exception as e:logger.debug("Не удалось ответить на callback обновления: %s",e)
        try:await call.edit(plain_emoji(self.strings["upd_downloading"]))
        except Exception as e:logger.debug("Не удалось обновить текст формы обновления: %s",e)
        ok=await self._safe_install_update()
        text=self.strings["upd_done"]if ok else self.strings["upd_fail"]
        try:await call.edit(plain_emoji(text))
        except Exception as e:logger.debug("Не удалось показать результат обновления: %s",e)

    async def _upd_cancel_cb(self,call):
        try:await call.delete()
        except Exception as e:logger.debug("Не удалось закрыть форму обновления: %s",e)

    @loader.command(ru_doc="[-f|--force] — проверить и установить обновление модуля вручную.",en_doc="[-f|--force] — manually check for and install a module update.")
    async def vupdate(self,message):
        args=utils.get_args_raw(message)
        force="-f"in args or"--force"in args
        await utils.answer(message,self.strings["upd_downloading"]if force else self.strings["upd_checking"])
        try:
            await asyncio.wait_for(self._update_lock.acquire(),timeout=self.UPDATE_LOCK_WAIT)
        except asyncio.TimeoutError:
            await utils.answer(message,self.strings["upd_busy"])
            return
        try:
            if force:
                ok=await self._safe_install_update()
                await utils.answer(message,self.strings["upd_done"]if ok else self.strings["upd_fail"])
                return
            differs,remote_ok=await self._check_update_hashes()
            if not remote_ok:
                await utils.answer(message,self.strings["upd_fetch_fail"])
                return
            if not differs:
                try:
                    await self.inline.form(text=plain_emoji(self.strings["upd_none_force"]),message=message,reply_markup=[[{"text":self.strings["upd_force_btn"],"callback":self._upd_force_cb},{"text":self.strings["upd_cancel_btn"],"callback":self._upd_cancel_cb}]])
                except Exception:
                    await utils.answer(message,self.strings["upd_none"])
                return
            await utils.answer(message,self.strings["upd_downloading"])
            ok=await self._safe_install_update()
            await utils.answer(message,self.strings["upd_done"]if ok else self.strings["upd_fail"])
        finally:
            self._update_lock.release()

    async def client_ready(self,client,db):
        self._client=client
        self._find_stop_event=asyncio.Event()
        self._grab_lock=asyncio.Lock()
        self._refresh_ai_api_keys()
        self._cleaner_task=asyncio.create_task(self._cache_cleaner())

    async def _cache_cleaner(self):
        while True:
            await asyncio.sleep(300)
            now=time.monotonic()
            async with self._fragment_cache_lock:
                expired=[k for k,(ts,_,_)in self._fragment_cache.items()if now-ts>=self.FRAGMENT_CACHE_TTL]
                for k in expired:self._fragment_cache.pop(k,None)
            expired_ai=[k for k,(ts,_)in self._ai_cache.items()if now-ts>=self.AI_CACHE_TTL]
            for k in expired_ai:self._ai_cache.pop(k,None)
            logger.debug("Cache cleaner: removed %d fragment, %d ai entries",len(expired),len(expired_ai))

    async def on_unload(self):
        if self._cleaner_task and not self._cleaner_task.done():
            self._cleaner_task.cancel()
            try:await self._cleaner_task
            except asyncio.CancelledError:pass
        await self._close_session()
