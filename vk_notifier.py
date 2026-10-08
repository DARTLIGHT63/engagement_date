import os
import time
import requests
import vk_api
from vk_api.exceptions import ApiError

# --- НАСТРОЙКИ ---
# Читаем токен и chat_id из переменных окружения (секретов GitHub)
TELEGRAM_BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID")
VK_TOKEN = os.environ.get("VK_TOKEN")

# ID или короткое имя страницы ВК для отслеживания
VK_DOMAIN = "mouravieffapostol"

# Имя файла для хранения ID последнего поста
STATE_FILE = "last_post_id.txt"

# --- ФУНКЦИИ ДЛЯ РАБОТЫ С ФАЙЛОМ СОСТОЯНИЯ ---
def get_last_post_id():
    if os.path.exists(STATE_FILE):
        with open(STATE_FILE, "r") as f:
            content = f.read().strip()
            if content:
                return int(content)
    return None

def save_last_post_id(post_id):
    with open(STATE_FILE, "w") as f:
        f.write(str(post_id))

# --- ФУНКЦИЯ ОТПРАВКИ В TELEGRAM ---
def send_telegram_message(text):
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    payload = {
        "chat_id": TELEGRAM_CHAT_ID,
        "text": text,
        "parse_mode": "HTML"
    }
    try:
        response = requests.post(url, data=payload)
        response.raise_for_status()
        return True
    except requests.exceptions.RequestException as e:
        print(f"Ошибка отправки в Telegram: {e}")
        return False

# --- ИНИЦИАЛИЗАЦИЯ VK ---
# ВОТ ЭТОТ БЛОК БЫЛ ПРОПУЩЕН. Без него переменная vk не существует.
try:
     if VK_TOKEN:
        print("Использую токен VK для авторизации.")
        vk_session = vk_api.VkApi(token=VK_TOKEN)
    else:
        print("ВНИМАНИЕ: Токен VK не найден! Пробую анонимно (скорее всего, будет ошибка).")
        vk_session = vk_api.VkApi()
except Exception as e:
    print(f"Ошибка подключения к VK API: {e}")
    exit(1)

# --- ОСНОВНАЯ ЛОГИКА ---
def main():
    print(f"Начинаю проверку страницы vk.com/{VK_DOMAIN}...")
    
    last_post_id = get_last_post_id()

    try:
        # Получаем последние 5 постов со стены
        response = vk.wall.get(domain=VK_DOMAIN, count=5)
        posts = response.get('items', [])
        
        if not posts:
            print("Посты не найдены. Пропускаем проверку.")
            return

        if last_post_id is None:
            # Первый запуск: запоминаем последний пост и выходим
            save_last_post_id(posts[0]['id'])
            print(f"Первый запуск. Запомнил последний пост ID: {posts[0]['id']}")
        else:
            # Ищем новые посты
            new_posts = []
            for post in posts:
                if post['id'] > last_post_id:
                    new_posts.append(post)
                else:
                    break # Дошли до уже известного поста

            if new_posts:
                # Отправляем уведомления от старых к новым
                for post in reversed(new_posts):
                    post_text = post.get('text', 'Без текста')
                    post_id = post['id']
                    post_url = f"https://vk.com/{VK_DOMAIN}?w=wall-{post['owner_id']}_{post_id}"
                    
                    message = (
                        f"<b>📝 Новый пост на странице!</b>\n\n"
                        f"{post_text[:500]}{'...' if len(post_text) > 500 else ''}\n\n"
                        f"<a href='{post_url}'>🔗 Читать полностью</a>"
                    )
                    
                    if send_telegram_message(message):
                        print(f"Отправлено уведомление о посте ID: {post_id}")
                    
                    time.sleep(1) # Пауза, чтобы не заспамить Telegram
                
                # Обновляем ID последнего известного поста
                save_last_post_id(posts[0]['id'])
            else:
                print("Новых постов нет.")

    except ApiError as e:
        print(f"Ошибка VK API: {e}")
    except Exception as e:
        print(f"Непредвиденная ошибка: {e}")

if __name__ == "__main__":
    main()

print(f"VK_TOKEN получен: {'Да' if VK_TOKEN else 'НЕТ'}")
