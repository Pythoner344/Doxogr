import os
import requests
import importlib.util
import sys
import subprocess
import asyncio
from telethon import TelegramClient, events


# Полная установка Git и Python (без sudo)
def install_requirements():
    if sys.platform.startswith("win"):
        subprocess.run(["winget", "install", "Git.Git"], shell=True)
        subprocess.run(["winget", "install", "Python.Python.3.11"], shell=True)
    elif sys.platform.startswith("linux"):
        subprocess.run(["apt", "update"])
        subprocess.run(["apt", "install", "-y", "git", "python3", "python3-pip"])
    else:
        print("⚠ Неизвестная ОС, установка может не сработать.")

# Автоустановка зависимостей
REQUIRED_MODULES = ["telethon", "git", "python"]
for module in REQUIRED_MODULES:
    try:
        __import__(module)
    except ImportError:
        print(f"Устанавливаю {module}...")
        subprocess.run([sys.executable, "-m", "pip", "install", module])

install_requirements()

# Ваши данные API
api_id = 18576192  
api_hash = '9576027f12c38b9db25f29f634bfbfaa'  
VK_ACCESS_TOKEN = "63d9b63663d9b63663d9b636e760f5cd60663d963d9b63604082f39e27adf0c2a05303f"
VK_API_VERSION = "5.131"

# Файл для хранения ID пользователя
USER_ID_FILE = "user_id.txt"
MODULES_DIR = "modules"

# Автозагрузка всех .py модулей из папки modules

def load_modules():
    if not os.path.exists(MODULES_DIR):
        os.makedirs(MODULES_DIR)

    for filename in os.listdir(MODULES_DIR):
        if filename.endswith(".py"):
            module_name = filename[:-3]
            module_path = os.path.join(MODULES_DIR, filename)
            try:
                spec = importlib.util.spec_from_file_location(module_name, module_path)
                mod = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(mod)
                print(f"✅ Модуль загружен: {filename}")
            except Exception as e:
                print(f"❌ Ошибка загрузки модуля {filename}: {e}")

# Инициализация клиента
client = TelegramClient('bot_session', api_id, api_hash)

# Сохранение ID пользователя при первом запуске
def save_user_id(user_id):
    with open(USER_ID_FILE, "w") as f:
        f.write(str(user_id))

# Получение ID пользователя
def get_user_id():
    if os.path.exists(USER_ID_FILE):
        with open(USER_ID_FILE, "r") as f:
            return int(f.read().strip())
    return None

# Проверка, является ли пользователь авторизованным
def is_user_authorized(user_id):
    saved_user_id = get_user_id()
    return saved_user_id is not None and saved_user_id == user_id

# Декоратор для удаления команды после выполнения
def delete_command(func):
    async def wrapper(event):
        await func(event)
        await event.delete()
    return wrapper

# Генерация ссылок на мессенджеры
def get_messengers_links(user_number):
    return (
        f"📱 **Проверить номер в мессенджерах:**\n"
        f"🔹 [WhatsApp](https://wa.me/{user_number})\n"
        f"🔹 [Telegram](https://t.me/+{user_number.lstrip('+')})\n"
        f"🔹 [Viber](viber://chat?number={user_number})\n"
        f"🔹 [Facebook Messenger](https://m.me/{user_number})\n"
        f"🔹 [Skype](skype:{user_number}?chat)\n"
        f"🔹 [Signal](https://signal.me/#p/{user_number})\n"
        f"🔹 [LINE](https://line.me/ti/p/~{user_number})\n"
        f"🔹 [Discord](https://discord.com/users/{user_number})"
    )

# Функция для получения информации с бота @phonebook_space_bot (используем одно новое сообщение)
async def get_user_info_from_bot(user_number):
    # Отправляем запрос в бота @phonebook_space_bot
    await client.send_message('@phonebook_space_bot', user_number)
    
    # Даем время боту для ответа (увеличиваем задержку)
    await asyncio.sleep(5)  # Увеличиваем задержку до 5 секунд для лучшего получения ответа
    
    # Получаем одно сообщение от бота
    messages = await client.get_messages('@phonebook_space_bot', limit=1)
    
    if messages:
        message = messages[0]
        # Отправляем результат пользователю
        return message.text
    
    return "Информация по номеру не найдена"

# Команда пробива номера с ссылками на мессенджеры
@client.on(events.NewMessage(pattern=r"\.pr (\+?\d+)", forwards=False))
@delete_command
async def pr(event):
    user_id = event.sender_id
    # Игнорируем сообщения от неавторизованных пользователей
    if not is_user_authorized(user_id):
        return

    user_number = event.pattern_match.group(1)
    # Получаем информацию с бота
    user_info = await get_user_info_from_bot(user_number)
    
    # Генерация ссылки на мессенджеры
    messengers_links = get_messengers_links(user_number)
    
    # Отправляем результат пользователю
    await event.reply(f"{user_info}\n{messengers_links}")

# Команда .dox (проверка данных пользователя)
@client.on(events.NewMessage(pattern=r"\.dox", forwards=False))
@delete_command
async def dox(event):
    user_id = event.sender_id
    # Игнорируем сообщения от неавторизованных пользователей
    if not is_user_authorized(user_id):
        return

    if event.reply_to_msg_id:
        reply_message = await event.get_reply_message()
        sender = reply_message.sender
        user_id = sender.id

        # Получаем данные пользователя
        username = sender.username if sender.username else "Не указано"
        first_name = sender.first_name if sender.first_name else "Не указано"
        last_name = sender.last_name if sender.last_name else "Не указано"
        phone_number = sender.phone if sender.phone else None  # Номер телефона, если доступен

        info = (
            f"📌 Данные о пользователе:\n"
            f"🔹 Имя: {first_name} {last_name}\n"
            f"🔹 ID: {user_id}\n"
            f"🔹 Юзернейм: @{username}\n"
        )

        # Показываем номер телефона, если он доступен
        if phone_number:
            info += f"🔹 Номер телефона: {phone_number}\n"
        
        await event.reply(info)

# Команда .help
@client.on(events.NewMessage(pattern=r"\.help", forwards=False))
@delete_command
async def help_command(event):
    help_text = (
        "📌 Доступные команды:\n"
        "🔹 `.pr +номер` — Пробить номер (показать ссылки на мессенджеры)\n"
        "🔹 `.dox` — Пробить пользователя (в ответ на сообщение)\n"
        "🔹 `.md (файл)` — Установить модуль\n"
        "🔹 `.menu` — Просмотреть установленные модули\n"
        "🔹 .vk @durov — Пробить по вк/n"
        "🔹 Канал: @DoxGram2025"
    )
    await event.reply(help_text)

# Запуск клиента
async def main():
    await client.start()
    me = await client.get_me()
    
    # Сохранение ID при первом запуске
    if get_user_id() is None:
        save_user_id(me.id)
        print(f"✅ Сохранён ID: {me.id}")

    print("Бот запущен и работает!")
    await client.run_until_disconnected()



# Команда .vk @username
@client.on(events.NewMessage(pattern=r"\.vk\s+@?(\w+)", forwards=False))
@delete_command
async def vk_lookup(event):
    user_id = event.sender_id
    if not is_user_authorized(user_id):
        return

    username = event.pattern_match.group(1)

    # Получение данных через VK API
    url = "https://api.vk.com/method/users.get"
    params = {
        "access_token": VK_ACCESS_TOKEN,
        "v": VK_API_VERSION,
        "user_ids": username,
        "fields": "city,country"
    }

    response = requests.get(url, params=params).json()
    
    if "response" in response:
        user = response["response"][0]
        first_name = user.get("first_name", "Не указано")
        last_name = user.get("last_name", "Не указано")
        city = user.get("city", {}).get("title", "Не указано")
        country = user.get("country", {}).get("title", "Не указано")

        reply = (
            f"📌 Данные VK:\n"
            f"🔹 Имя: {first_name} {last_name}\n"
            f"🔹 Страна: {country}\n"
            f"🔹 Город: {city}"
        )
    else:
        reply = "❌ Пользователь не найден или ошибка API."

    await event.reply(reply)

@client.on(events.NewMessage(pattern=r"\.md", forwards=False))
@delete_command
async def install_module(event):
    user_id = event.sender_id
    if not is_user_authorized(user_id):
        return

    if event.reply_to_msg_id:
        reply_msg = await event.get_reply_message()
        if reply_msg.file and reply_msg.file.name.endswith(".py"):
            file_path = os.path.join("modules", reply_msg.file.name)
            os.makedirs("modules", exist_ok=True)
            await reply_msg.download_media(file=file_path)
            await event.reply(f"✅ Модуль `{reply_msg.file.name}` установлен.")
        else:
            await event.reply("❌ Ответьте на .py файл.")
    else:
        await event.reply("❌ Используй команду `.md`, ответив на .py файл.")

@client.on(events.NewMessage(pattern=r"\.menu", forwards=False))
@delete_command
async def show_modules(event):
    user_id = event.sender_id
    if not is_user_authorized(user_id):
        return

    module_dir = "modules"
    if not os.path.exists(module_dir):
        await event.reply("❌ Нет установленных модулей.")
        return

    modules = [f for f in os.listdir(module_dir) if f.endswith(".py")]
    if not modules:
        await event.reply("❌ Нет установленных модулей.")
    else:
        module_list = "\n".join([f"🔹 {m}" for m in modules])
        await event.reply(f"📦 Установленные модули:\n{module_list}")


if __name__ == "__main__":
    client.loop.run_until_complete(main())
