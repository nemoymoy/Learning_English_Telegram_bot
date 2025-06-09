
import random

from telebot import types, TeleBot, custom_filters
from telebot.storage import StateMemoryStorage
from telebot.handler_backends import State, StatesGroup

import psycopg2

# Создаем функцию подключения к БД и отправки SQL-запросов
def query_to_bd(sql_query, *arg):
    conn = psycopg2.connect(dbname="learning_english_telegram_bot_v2",
                            host="127.0.0.1",
                            user="postgres",
                            password="101917",
                            port="5432")
    with conn.cursor() as cur:
        cur.execute(sql_query, *arg)
        conn.commit()
        if "CREATE" in sql_query or "ALTER" in sql_query:
            result = cur.statusmessage
        else:
            result = cur.fetchall()
    conn.close()
    return result

# Создаем функцию создания БД
def create_bd(sql_query):
    conn_create = psycopg2.connect(
        dbname="postgres",
        user="postgres",
        password="101917",
        host="127.0.0.1",
        port="5432"
    )
    cur_create = conn_create.cursor()
    conn_create.autocommit = True
    cur_create.execute(sql_query)
    result = cur_create.fetchall()
    cur_create.close()
    conn_create.close()
    return result

if create_bd("""
                SELECT 1 
                FROM pg_database 
                WHERE datname='learning_english_telegram_bot_v2'
                """
             )[0][0] != 1:
    create_bd("CREATE DATABASE learning_english_telegram_bot_v2")
    print("Создана новая БД - learning_english_telegram_bot_v2")
else:
    print("БД 'learning_english_telegram_bot_v2' уже существует.")

# Проверяем есть ли в БД таблица 'users'
if not query_to_bd("""
                    SELECT EXISTS (
                        SELECT 1
                        FROM information_schema.tables
                        WHERE table_name = 'users')
                        """
                   )[0][0]:
    # Если таблицы не существует, то создаем таблицу
    print(query_to_bd("""
                        CREATE TABLE IF NOT EXISTS users (
                        id BIGINT PRIMARY KEY NOT NULL)
                        """
                      ), 'users')
else:
    print("Таблица 'users' уже существует.")

# Проверяем есть ли в БД таблица 'words'
if not query_to_bd("""
                    SELECT EXISTS (
                        SELECT 1 
                        FROM information_schema.tables 
                        WHERE table_name = 'words')
                        """
                   )[0][0]:
    # Если таблицы не существует, то создаем таблицу
    print(query_to_bd("""
                        CREATE TABLE IF NOT EXISTS words (
                            id SERIAL PRIMARY KEY NOT NULL, 
                            title VARCHAR(100) NOT NULL,
                            translate VARCHAR(100) NOT NULL)
                """
                ), 'words')
else:
    print("Таблица 'words' уже существует.")

# Если таблица 'words' существует, то проверяем есть ли в ней слова пользователь '1000000000'
if query_to_bd("""
                    SELECT COUNT(*)
                    FROM words
                    """
                   )[0][0] == 0:
    # Если нет, то добавляем слова "по-умолчанию"
    print('Добавлены слова', query_to_bd("""
                                                INSERT INTO words
                                                VALUES	
                                                    (1, 'мир', 'peace'),
		                                            (2, 'красный', 'red'),
		                                            (3, 'музыка', 'music'),
		                                            (4, 'автомобиль', 'car'),
		                                            (5, 'столица', 'capital'),
		                                            (6, 'стол', 'table'),
		                                            (7, 'счастливый', 'happy'),
		                                            (8, 'кино', 'movie'),
		                                            (9, 'улица', 'street'),
		                                            (10, 'победа', 'victory')
                                                RETURNING *
                                                """
                                             ))
else:
    print("В таблице 'words' уже есть записи.")

# Проверяем есть ли в БД таблица 'user_words'
if not query_to_bd("""
                    SELECT EXISTS (
                        SELECT 1 
                        FROM information_schema.tables 
                        WHERE table_name = 'user_words')
                        """
                   )[0][0]:
    # Если таблицы не существует, то создаем таблицу
    print(query_to_bd("""
                        CREATE TABLE IF NOT EXISTS user_words (
                            id SERIAL PRIMARY KEY NOT NULL, 
                            title VARCHAR(100) NOT NULL,
                            translate VARCHAR(100) NOT NULL,
                            user_id BIGINT NOT NULL)
                """
                ), 'user_words')
    print(query_to_bd("""
                        ALTER TABLE public.user_words
                        ADD CONSTRAINT user_words_users_fk
                        FOREIGN KEY (user_id) REFERENCES users(id)
                        ON DELETE CASCADE ON UPDATE CASCADE
                        """
                        ), 'user_words')
else:
    print("Таблица 'user_words' уже существует.")

state_storage = StateMemoryStorage()

# Подключаемся к ранее созданному в Телеграм боту, токен загружаем из файла "key.txt"
with open('key.txt') as f:
    token_bot = f.readline().strip()
bot = TeleBot(token_bot, state_storage=state_storage)
print('Start telegram bot...')

# Объявляем переменную для сохранения кнопок бота
buttons = list()

# Функция формирования текста ответа бота
def show_hint(*lines):
    return '\n'.join(lines)

# Функция формирования строки целевого слова и перевода
def show_target(data):
    return f"{data['target_word']} -> {data['translate_word']}"

# Класс команд кнопок бота
class Command:
    ADD_WORD = 'Добавить слово ➕'
    DELETE_WORD = 'Удалить слово🔙'
    NEXT = 'Дальше ⏭'

# Класс состояний
class MyStates(StatesGroup):
    target_word = State()
    translate_word = State()
    another_words = State()

# Функция добавления нового пользователя в БД
def get_user(uid):
    if query_to_bd("""
                    SELECT id 
                    FROM users 
                    WHERE id=%s
                    """, (uid,)
                   ):
        return uid
    else:
        print('Обнаружен новый пользователь, который ещё не использовал команду \"/start\"')
        query_to_bd("""
                    INSERT INTO users 
                    VALUES (%s) 
                    RETURNING id
                    """, (uid,)
                    )
        print(f'В БД добавлен новый пользователь: {uid}')
        return 0

# Функция обработки команды "/start"
@bot.message_handler(commands=['start'])
def send_wellcome(message):
    get_user(int(message.from_user.id))
    bot.send_message(message.chat.id, f'Привет👋, {message.from_user.first_name} {message.from_user.last_name}!\n'
                                      f'Давай попрактикуемся в английском языке. Тренировки можешь проходить '
                                      f'в удобном для себя темпе.\n'
                                      f'Команда "/cards" или кнопка "Дальше ⏭" предложит новое задание.'
                                      f'У тебя есть возможность использовать тренажёр, как конструктор, и собирать '
                                      f'свою собственную базу для обучения.\n'
                                      f'Для этого воспользуйся инструментами:\n'
                                      f'- добавить слово ➕;\n- удалить слово 🔙.\nНу что, начнём ⏭')

# Функция обработки команды /cards
@bot.message_handler(commands=['cards'])
def create_cards(message):
    uid = get_user(int(message.from_user.id))
    markup = types.ReplyKeyboardMarkup(row_width=2)
    buttons.clear()
    # Определяем возможный набор русских слов для задания
    possible_rus_words = query_to_bd("""
                                        SELECT title, translate  --получаем слово и перевод
                                        FROM (
                                            SELECT title, translate  --получаем слово и перевод
                                            FROM words  --из таблицы общих слов
                                            UNION
                                            SELECT title, translate  --получаем слово и перевод
                                            FROM user_words  --из таблицы персональных слов
                                            WHERE user_id=%s  --где айди пользователя равно искомому айди
                                            )
                                        ORDER BY RANDOM()  --сортируем по рандому
                                        LIMIT 4  --берем 4 слова
                                    """, (uid,))

    # Если есть неизученные слова для задания, то
    if len(possible_rus_words) > 0:
        # Выбираем случайное русское слово из возможных
        translate = possible_rus_words[0][0]
        print(f'Заданное слово: {translate}')
        # Выбираем английский перевод к выбранному слову
        target_word = possible_rus_words[0][1]
        print(f'Перевод: {target_word}')

        # Присваиваем текст кнопке с правильным переводом
        target_word_btn = types.KeyboardButton(target_word)
        buttons.append(target_word_btn)

        # Выбираем три случайных английских слова
        others = list()
        for word in possible_rus_words[1 :]:
            others.append(word[1])
        print(f'Три других варианта: {others}')

        # Присваиваем текст трем другим кнопкам
        other_words_btns = [types.KeyboardButton(word) for word in others]
        buttons.extend(other_words_btns)
        random.shuffle(buttons)

        # Отображаем функциональные кнопки
        next_btn = types.KeyboardButton(Command.NEXT)
        add_word_btn = types.KeyboardButton(Command.ADD_WORD)
        delete_word_btn = types.KeyboardButton(Command.DELETE_WORD)
        buttons.extend([next_btn, add_word_btn, delete_word_btn])
        markup.add(*buttons)

        # Выводим слово задание
        greeting = f"Выбери перевод слова:\n🇷🇺 {translate}"
        bot.send_message(message.chat.id, greeting, reply_markup=markup)
        bot.set_state(message.from_user.id, MyStates.target_word, message.chat.id)
        with bot.retrieve_data(message.from_user.id, message.chat.id) as data:
            data['target_word'] = target_word
            data['translate_word'] = translate
            data['other_words'] = others
    # Если все слова изучены, то
    else:
        bot.send_message(message.chat.id, "В базе данных нет слов! Проверьте БД!")

# Функция обработки кнопки "Далее"
@bot.message_handler(func=lambda message: message.text == Command.NEXT)
def next_cards(message):
    create_cards(message)

# Функция обработки кнопки "Удалить слово"
list_user_words = list()
@bot.message_handler(func=lambda message: message.text == Command.DELETE_WORD)
def delete_word(message):
    uid = get_user(message.from_user.id)
    # Запрашиваем из БД русские слова, которые можно удалить пользователю
    user_words = query_to_bd("""
                                SELECT title
                                FROM user_words
                                WHERE user_id=%s
                                """, (uid,))
    text = ""
    list_user_words.clear()
    for word in user_words:
        text += word[0] + "\n"
        list_user_words.append(word[0])
    chat_id = message.chat.id
    msg = bot.send_message(chat_id,f'Ваши слова в БД:\n{text}Напишите слово для удаления:')
    bot.register_next_step_handler(msg, del_word_to_bd)

# Функция удаления слова из БД
def del_word_to_bd(message):
    uid = get_user(message.from_user.id)
    if message.text in list_user_words:
        target = message.text
        result = query_to_bd("""
                                DELETE FROM user_words
                                WHERE title=%s AND user_id=%s
                                RETURNING *
                                """, (target, uid)
                             )[0][1]
        bot.send_message(message.chat.id,f'Из БД удалено слово: {result}.')
        print(f'Из БД удалено слово: {result}')
    else:
        msg = bot.send_message(message.chat.id,f"Можно удалить только эти слова: {"; ".join(list_user_words)}\n."
                                               f"Напишите слово для удаления:")
        bot.register_next_step_handler(msg, del_word_to_bd)

# Функция обработки кнопки "Добавит слово"
@bot.message_handler(func=lambda message: message.text == Command.ADD_WORD)
def add_word(message):
    chat_id = message.chat.id
    msg = bot.send_message(chat_id, 'Введите слово на русском и после двоеточия его перевод по шаблону:\n язык:language')
    bot.register_next_step_handler(msg, add_word_to_bd)

# Функция добавления слова в БД
def add_word_to_bd(message):
    uid = get_user(message.from_user.id)
    if ':' in message.text:
        source = message.text[: message.text.find(':')]
        print(source)
        target = message.text[message.text.rfind(':') + 1 :]
        print(target)
        result = query_to_bd("""
                                        INSERT INTO user_words (title, translate, user_id)
                                        VALUES (%s, %s, %s)
                                        RETURNING *
                                        """, (source, target, uid)
                            )
        print(f"В БД добавлены слово {result[0][1]} и перевод {result[0][2]}.")
        count_possible_words = query_to_bd("""
                                                SELECT COUNT(title)
                                                FROM (
                                                        SELECT title
                                                        FROM words
                                                        UNION
                                                        SELECT title
                                                        FROM user_words
                                                        WHERE user_id=%s)
                                                    """, (uid,)
                                           )[0][0]
        bot.send_message(message.chat.id, f'Пара слов: {source} и {target} добавлена в БД.\n'
                                          f'Общее количество слов для обучения - {count_possible_words}')
    else:
        chat_id = message.chat.id
        msg = bot.send_message(chat_id,
                               'Введите слово на русском и после двоеточия его перевод по шаблону:\n язык:language')
        bot.register_next_step_handler(msg, add_word_to_bd)

# Функция обработки выбора ответа на задание
@bot.message_handler(func=lambda message: True, content_types=['text'])
def message_reply(message):
    uid = get_user(message.from_user.id)
    text = message.text
    markup = types.ReplyKeyboardMarkup(row_width=2)
    with bot.retrieve_data(uid, message.chat.id) as data:
        target_word = data['target_word']
        if text == target_word:
            hint = show_target(data)
            hint_text = ["Отлично!❤", hint]
            buttons.clear()
            next_btn = types.KeyboardButton(Command.NEXT)
            add_word_btn = types.KeyboardButton(Command.ADD_WORD)
            delete_word_btn = types.KeyboardButton(Command.DELETE_WORD)
            buttons.extend([next_btn, add_word_btn, delete_word_btn])
            hint = show_hint(*hint_text)
        else:
            for btn in buttons:
                if btn.text == text:
                    btn.text = text + '❌'
                    break
            hint = show_hint("Допущена ошибка!",
                             f"Попробуй ещё раз вспомнить слово 🇷🇺{data['translate_word']}")
    markup.add(*buttons)
    bot.send_message(message.chat.id, hint, reply_markup=markup)
bot.add_custom_filter(custom_filters.StateFilter(bot))
bot.infinity_polling(skip_pending=True)

if __name__ == '__main__':
    bot.polling()


