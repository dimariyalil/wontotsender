
import os
import time
from datetime import datetime
from telethon.sync import TelegramClient
from telethon.errors import RPCError
from telethon.errors.rpcerrorlist import UsernameNotOccupiedError, PeerIdInvalidError
import gspread
from google.oauth2.service_account import Credentials

# === CONFIG ===
api_id = 22483560
api_hash = 'b0d6834ddeb4927dbf4de8713fb8c96c'
session_name = 'wontot_session'
sleep_sec = 65

# Google Sheets settings
spreadsheet_id = '13WJZwc0fGYqrzDq3XYYu_IFEooX81LVaW6oI5LdvTxE'
sheet_name = 'Sheet1'
json_keyfile = 'wontotsender-62f0d9912f01.json'

# === AUTH ===
scopes = ["https://www.googleapis.com/auth/spreadsheets"]
credentials = Credentials.from_service_account_file(json_keyfile, scopes=scopes)
gc = gspread.authorize(credentials)
sh = gc.open_by_key(spreadsheet_id)
sheet = sh.worksheet(sheet_name)

client = TelegramClient(session_name, api_id, api_hash)

message_text = """Здравствуйте, я Мария
Пишу вам по поводу сотрудничества с вашим пабликом или пабликами, если у вас не один.

Я представитель стартапа в телеграме @wontot_bot 
Мы делаем "Первый турнир между спортивными пабликами в телеграме по прогнозам на футбольные матчи" с призовым фондом 1000 USDT и с аудиторией до 5000.

Хотим вас и ваших подписчиков пригласить поучаствовать в турнире бесплатно.
На этапе отбора мы вам создадим арену, где вы сможете определить 5 лучших прогнозистов среди вашей аудитории, которые вместе с вами попадут в финал и разыграют среди других финалистов 1000 usdt. Пример арены в нашем боте: 
https://t.me/WONToT_bot/app?startapp=arena_IPVpysGPyKhLLoDgFT2f::@wontot_bot_arena

Никаких взносов, донатов, оплат и никакой рекламы.
Если у вас будут вопросы, я с радостью отвечу 😊

Аудио/Видео преза:
https://youtu.be/E6cRFd6EdgU?si=xs7oHNvu5igkXaaY 
Лендинг проекта:
https://tg-football-cup-1-xdocvmc.gamma.site"""


def get_archived_usernames():
    try:
        records = sheet.get_all_records()
        return set(str(row['username']).strip() for row in records if row['username'])
    except Exception as e:
        print(f"[ERROR] Ошибка при чтении архива из Google Sheets: {str(e)}")
        return set()


def update_archive(username, status="success"):
    try:
        sheet.append_row([username, status, datetime.now().isoformat()])
        print(f"[ARCHIVE ✅] Добавлен в Google Sheets: {username}")
    except Exception as e:
        print(f"[ARCHIVE ❌] Ошибка добавления {username}: {str(e)}")


def load_usernames(filename="usernames.txt"):
    if not os.path.exists(filename):
        print("[ERROR] Нет файла usernames.txt")
        return []
    with open(filename, "r", encoding="utf-8") as f:
        return [line.strip() for line in f if line.strip().startswith("@")]


async def main():
    usernames = load_usernames()
    archive = get_archived_usernames()

    for username in usernames:
        if username in archive:
            print(f"[SKIP] Уже в архиве (Google Sheets): {username}")
            continue

        update_archive(username)

        try:
            print(f"[INFO] Отправка сообщения: {username}")
            await client.send_message(username, message_text)
            time.sleep(sleep_sec)
        except RPCError as e:
            if "Flood" in str(e):
                print(f"[WAIT] FloodWait: ждём 60 сек (общее RPC исключение).")
                time.sleep(60)
            else:
                print(f"[RPCError] {username}: {str(e)}")
                update_archive(username, f"rpc_error:{str(e)}")
        except UsernameNotOccupiedError:
            print(f"[ERROR] Не найден: {username}")
            update_archive(username, "not_found")
        except PeerIdInvalidError:
            print(f"[ERROR] PeerIdInvalid: {username}")
            update_archive(username, "peer_invalid")
        except Exception as e:
            print(f"[ERROR] {username}: {str(e)}")
            update_archive(username, f"error:{str(e)}")

with client:
    client.loop.run_until_complete(main())
