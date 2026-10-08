import time
import requests
import vk_api
from vk_api.exceptions import ApiError
import os

# --- НАСТРОЙКИ ---
TELEGRAM_BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID")
VK_DOMAIN = "mouravieffapostol"
# Интервал в секундах больше не нужен, так как запуск управляется GitHub Actions
# CHECK_INTERVAL = 300 

STATE_FILE = "last_post_id.txt"

# --- ФУНКЦИЯ ДЛЯ ЧТЕНИЯ ID ПОСЛЕДНЕГО ПОСТА ---
def get_last_post_id():
    if os.path.exists(STATE_FILE):
        with open(STATE_FILE, "r") as f:
            return int(f.read().strip())
    return None

# --- ФУНКЦИЯ ДЛЯ СОХРАНЕНИЯ ID ---
def save_last_post_id(post_id):
    with open(STATE_FILE, "w") as f:
        f.write(str(post_id))

# --- ИНИЦИАЛИЗАЦИЯ VK ---
# ... (остальная часть кода без изменений)

# --- ОСНОВНОЙ БЛОК (вместо бесконечного цикла while) ---
# Убираем while True и time.sleep. Скрипт просто выполнится один раз.
last_post_id = get_last_post_id()

try:
    # ... (логика получения постов, как в вашем скрипте)
    response = vk.wall.get(domain=VK_DOMAIN, count=5)
    posts = response.get('items', [])
    
    if not posts:
        print("Посты не найдены.")
        exit() # Выходим, если постов нет

    if last_post_id is None:
        # Если ID еще нет, сохраняем последний пост и выходим
        save_last_post_id(posts[0]['id'])
        print(f"Первый запуск. Запомнил последний пост ID: {posts[0]['id']}")
    else:
        new_posts = []
        for post in posts:
            if post['id'] > last_post_id:
                new_posts.append(post)
            else:
                break
        
        if new_posts:
            for post in reversed(new_posts):
                # ... (логика отправки в Telegram, как в вашем скрипте)
                # send_telegram_message(message)
                pass
            # Сохраняем ID самого нового поста
            save_last_post_id(posts[0]['id'])

except Exception as e:
    print(f"Ошибка: {e}")
