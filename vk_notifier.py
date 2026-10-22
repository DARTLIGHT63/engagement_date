import os
import time
import requests
from bs4 import BeautifulSoup

# ==========================================
# 1. НАСТРОЙКИ
# ==========================================
TELEGRAM_BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID")

# Имя канала для мониторинга (без @)
TG_CHANNEL = "mouravieffapostol"

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
        "parse_mode": "HTML",
        "disable_web_page_preview": False
    }
    try:
        response = requests.post(url, data=payload)
        response.raise_for_status()
        return True
    except requests.exceptions.RequestException as e:
        print(f"Ошибка отправки в Telegram: {e}")
        return False

# ==========================================
# 3. ОСНОВНАЯ ЛОГИКА
# ==========================================
def main():
    print(f"Начинаю проверку Telegram-канала t.me/{TG_CHANNEL}...")
    
    last_post_id = get_last_post_id()

    # Имитируем браузер, чтобы Telegram не блокировал запросы с GitHub
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    }
    
    url = f"https://t.me/s/{TG_CHANNEL}"
    
    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Находим все посты на странице
        posts = soup.find_all('div', class_='tgme_widget_message_wrap')
        
        if not posts:
            print("Посты не найдены. Возможно, изменилась верстка Telegram или канал пуст.")
            if last_post_id is None:
                save_last_post_id(0)
            return

        # Извлекаем данные (ID и текст) для каждого поста
        parsed_posts = []
        for post in posts:
            # Ищем уникальный идентификатор поста (например, mouravieffapostol/123)
            message_div = post.find('div', class_='tgme_widget_message')
            if not message_div or 'data-post' not in message_div.attrs:
                continue
            
            data_post = message_div['data-post']
            post_id = int(data_post.split('/')[-1]) # Достаем только цифры (123)
            
            # Ищем текст поста
            text_div = post.find('div', class_='tgme_widget_message_text')
            text = text_div.get_text(separator='\n', strip=True) if text_div else "[Медиафайл без текста]"
            
            # Ссылка на пост
            post_url = f"https://t.me/{data_post}"
            
            parsed_posts.append({
                "id": post_id,
                "text": text,
                "url": post_url
            })

        if last_post_id is None:
            # Первый запуск: просто запоминаем последний пост
            newest_id = parsed_posts[-1]['id']
            save_last_post_id(newest_id)
            print(f"Первый запуск. Запомнил последний пост ID: {newest_id}")
            return

        # Ищем новые посты (их ID больше, чем сохраненный)
        new_posts = [p for p in parsed_posts if p['id'] > last_post_id]
        
        if new_posts:
            # Сортируем от старых к новым, чтобы в ТГ они пришли в правильном порядке
            new_posts.sort(key=lambda x: x['id'])
            
            for post in new_posts:
                message = (
                    f"<b>📝 Новый пост в канале @{TG_CHANNEL}!</b>\n\n"
                    f"{post['text'][:800]}{'...' if len(post['text']) > 800 else ''}\n\n"
                    f"<a href='{post['url']}'>🔗 Читать полностью</a>"
                )
                
                if send_telegram_message(message):
                    print(f"Отправлено уведомление о посте ID: {post['id']}")
                
                time.sleep(1) # Пауза, чтобы Telegram не забанил бота за спам
            
            # Обновляем ID последнего поста
            save_last_post_id(parsed_posts[-1]['id'])
        else:
            print("Новых постов нет.")

    except Exception as e:
        print(f"Непредвиденная ошибка: {e}")
        if last_post_id is None:
            save_last_post_id(0)

if __name__ == "__main__":
    main()
