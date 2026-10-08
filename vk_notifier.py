import os
import time
import requests
import vk_api
from vk_api.exceptions import ApiError

# ==========================================
# 1. НАСТРОЙКИ
# ==========================================
TELEGRAM_BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID")
VK_TOKEN = os.environ.get("VK_TOKEN")

VK_DOMAIN = "mouravieffapostol"
STATE_FILE = "last_post_id.txt"

# ==========================================
# 2. ВСПОМОГАТЕЛЬНЫЕ ФУНКЦИИ
# ==========================================
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
    print(f"Сохранил ID поста: {post_id}")

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

# ==========================================
# 3. ОСНОВНАЯ ЛОГИКА (Инициализация VK теперь здесь!)
# ==========================================
def main():
    print(f"Начинаю проверку страницы vk.com/{VK_DOMAIN}...")
    
    # Инициализируем VK прямо внутри main()
    try:
        if VK_TOKEN:
            print("Использую токен VK для авторизации.")
            vk_session = vk_api.VkApi(token=VK_TOKEN)
        else:
            print("ВНИМАНИЕ: Токен VK не найден! Пробую анонимно...")
            vk_session = vk_api.VkApi()
        
        vk = vk_session.get_api()
    except Exception as e:
        print(f"Ошибка подключения к VK API: {e}")
        return # Выходим из функции, если не удалось подключиться

    last_post_id = get_last_post_id()

    try:
        # Теперь переменная vk точно доступна, так как мы создали её выше
        response = vk.wall.get(domain=VK_DOMAIN, count=5)
        posts = response.get('items', [])
        
        if not posts:
            print("Посты не найдены. Пропускаем проверку.")
            if last_post_id is None:
                save_last_post_id(0)
            return

        if last_post_id is None:
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
                    
                    time.sleep(1)
                
                save_last_post_id(posts[0]['id'])
            else:
                print("Новых постов нет.")
                if last_post_id is None:
                     save_last_post_id(posts[0]['id'])

    except ApiError as e:
        print(f"Ошибка VK API: {e}")
        if last_post_id is None:
            save_last_post_id(0)
    except Exception as e:
        print(f"Непредвиденная ошибка: {e}")
        if last_post_id is None:
            save_last_post_id(0)

# ==========================================
# 4. ТОЧКА ВХОДА
# ==========================================
if __name__ == "__main__":
    main()
