import telebot
import openai
import json
from datetime import datetime, timedelta
import time


# Загрузка ключей из файла конфигурации или установка их напрямую
# Предположим, что ключи хранятся в файле config.py
from config import OpenAIKey, TgKey

# Функция для чтения файла
def read_file(file_name):
    with open(file_name, 'r', encoding='utf-8') as f:
        data = f.read()
    return data

# Устанавливаем ключ OpenAI API
openai.api_key = OpenAIKey

# Инициализируем бота с помощью токена Telegram API
bot = telebot.TeleBot(TgKey)

# Читаем данные из файла
data = read_file('data.txt')

# Переменная для отслеживания времени последнего активного взаимодействия
last_active_time = datetime.now()

# Максимальное количество диалогов для хранения в файле JSON
MAX_DIALOGS = 100

# Функция для загрузки диалогов из файла JSON
def load_dialogs():
    try:
        with open("dialogs.json", "r", encoding="utf-8") as file:
            dialogs = json.load(file)
    except FileNotFoundError:
        dialogs = []
    return dialogs

# Функция для сохранения диалогов в файл JSON
def save_dialogs(dialogs):
    with open("dialogs.json", "w", encoding="utf-8") as file:
        json.dump(dialogs, file, ensure_ascii=False, indent=4)


dialogs = []

@bot.message_handler(func=lambda m: True)
def handle_message(message):
    global dialogs  # Объявляем переменную dialogs как глобальную
    global last_active_time
    user_id = message.chat.id
    now = datetime.now()

    # Проверяем, если пользователь отправил одну из ключевых фраз
    keywords = ["администратор", "оператор", "стоп", "позовите человека", "позовите оператора",
                "позовите администратора", "позови человека"]
    if any(keyword in message.text.lower() for keyword in keywords):
        last_active_time = now + timedelta(hours=3)
        bot.send_message(message.chat.id, "Мне очень жаль, что я не смог вам помочь, побежал звать человека. Вы согласны?")
        return

    # Проверяем, если пользователь отправил слово "Фоксик"
    if "фоксик" in message.text.lower():
        last_active_time = now
        bot.send_message(message.chat.id, "Да-да?")
        return

    # Проверяем, если прошло более 3 часов с последнего активного взаимодействия
    if now < last_active_time:
        # Бот не будет отвечать на сообщения пользователя
        return

    # Добавляем задержку перед запросом к API OpenAI
    time.sleep(2)  # Задержка в 2 секунды


    # Формируем запрос к OpenAI
    response = openai.ChatCompletion.create(
        model="gpt-4",
        messages=[
            {"role": "system", "content": data},  # Добавляем данные из файла
            {"role": "user", "content": message.text}
        ],
        stream=False,
    )

    # Проверка успешности запроса и обработка ответа
    if response.choices and len(response.choices) > 0:
        # Извлечение текстового ответа
        gpt_text = response.choices[0].message.content.strip()

        # Замена слова "OpenAI" на "Фоксик"
        gpt_text = gpt_text.replace("OpenAI", "Фоксик")

        # Отправка ответа пользователю
        bot.send_message(message.chat.id, gpt_text)


        # Загружаем текущие диалоги из файла
        dialogs = load_dialogs()


        # Добавляем новый диалог
        dialogs.append({
            "user_id": user_id,
            "question": message.text,
            "answer": gpt_text
        })
        # Проверяем, если количество диалогов превышает максимальное значение
        if len(dialogs) > MAX_DIALOGS:
            # Удаляем самый старый диалог
            dialogs.pop(0)

        # Сохраняем обновленные диалоги в файл
        save_dialogs(dialogs)

    else:
        # Если ответ пустой или произошла ошибка
        bot.send_message(message.chat.id, "Получен пустой ответ от OpenAI API.")

        # Обновляем время последнего запроса
    last_active_time = now

# Запускаем бота
bot.polling(none_stop=True)
