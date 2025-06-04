
import random

from telebot import types, TeleBot, custom_filters
from telebot.storage import StateMemoryStorage
from telebot.handler_backends import State, StatesGroup

import psycopg2

def query_to_bd(sql_query):
    conn = psycopg2.connect(dbname="learning_english_telegram_bot", host="127.0.0.1", user="guest", password="guest", port="5432")
    with conn.cursor() as cur:
        cur.execute(sql_query)
        conn.commit()
        result = cur.fetchall()
    conn.close()
    return result

state_storage = StateMemoryStorage()
with open('key.txt') as f:
    token_bot = f.readline().strip()
bot = TeleBot(token_bot, state_storage=state_storage)

print('Start telegram bot...')

known_users = list()
for row in query_to_bd("SELECT user_name FROM tab_users"):
    known_users.append(row[0])
print(known_users)

userStep = dict()
for row in query_to_bd("SELECT user_name, user_step FROM tab_users"):
    userStep[row[0]] = row[1]
print(userStep)
# global buttons
buttons = list()



def show_hint(*lines):
    return '\n'.join(lines)


def show_target(data):
    return f"{data['target_word']} -> {data['translate_word']}"


class Command:
    ADD_WORD = 'Добавить слово ➕'
    DELETE_WORD = 'Удалить слово🔙'
    NEXT = 'Дальше ⏭'
    CLEAR = 'Очистить рейтинг 🆑'


class MyStates(StatesGroup):
    target_word = State()
    translate_word = State()
    another_words = State()


def get_user_step(uid):
    print(uid)
    if uid in userStep:

        return userStep[uid]
    else:
        known_users.append(uid)
        userStep[uid] = 0
        print('Обнаружен новый пользователь, который ещё не использовал команду \"/start\"')
        print(f'В БД добавлен новый пользователь: '
              f'{query_to_bd(f"INSERT INTO tab_users (user_name, user_step) VALUES ({uid}, {0}) RETURNING user_name")[0][0]}')
        return 0

@bot.message_handler(commands=['start'])
def send_wellcome(message):
    bot.send_message(message.chat.id, f'Привет👋, {message.from_user.first_name} {message.from_user.last_name}!\n'
                                      f'Давай попрактикуемся в английском языке. Тренировки можешь проходить '
                                      f'в удобном для себя темпе.\n'
                                      f'У тебя есть возможность использовать тренажёр, как конструктор, и собирать '
                                      f'свою собственную базу для обучения.\n'
                                      f'Для этого воспользуйся инструментами:\n'
                                      f'- добавить слово ➕;\n- удалить слово 🔙.\nНу что, начнём ⏭')
    bot.send_message(message.chat.id, f'Текущий рейтинг - {get_user_step(str(message.from_user.id))} слов.')

@bot.message_handler(commands=['cards'])
def create_cards(message):
    cid = message.chat.id
    # tid = message.from_user
    # print(cid)
    # print(tid)
    # if cid not in known_users:
    #     known_users.append(cid)
    #     userStep[cid] = 0
        # bot.send_message(cid, "Hello, stranger, let study English...")
    markup = types.ReplyKeyboardMarkup(row_width=2)

    # global buttons
    buttons.clear()

    possible_rus_words = query_to_bd(f"select rus_word "
                                            f"from tab_russian_words "
                                            f"where id_user='1' or id_user='{query_to_bd(f"select id_user from tab_users where user_name='{cid}'")[0][0]}'"
                                            f"except select rus_word "
                                            f"from tab_russian_words "
                                            f"join tab_user_step on tab_russian_words.id_rus_word = tab_user_step.id_rus_word "
                                            f"join tab_users on tab_user_step.id_user = tab_users.id_user "
                                            f"where user_name='{cid}'")
    if len(possible_rus_words) > 0:
        # translate = 'Мир'  # брать из БД
        translate = random.choice(possible_rus_words)[0]

        print(f'Заданное слово: {translate}')

        # target_word = 'Peace'  # брать из БД
        target_word = query_to_bd(f"select eng_word "
                                  f"from tab_english_words "
                                  f"join tab_russian_words on tab_english_words.id_rus_word = tab_russian_words.id_rus_word "
                                  f"where rus_word='{translate}'")[0][0]
        print(f'Перевод: {target_word}')

        target_word_btn = types.KeyboardButton(target_word)
        buttons.append(target_word_btn)

        # others = ['Green', 'White', 'Hello']  # брать из БД
        others = list()
        for word in query_to_bd(f"select eng_word from tab_english_words where eng_word != '{target_word}' order by random() limit 3"):
            others.append(word[0])
        print(f'Три других варианта: {others}')

        other_words_btns = [types.KeyboardButton(word) for word in others]
        buttons.extend(other_words_btns)
        random.shuffle(buttons)


        next_btn = types.KeyboardButton(Command.NEXT)
        add_word_btn = types.KeyboardButton(Command.ADD_WORD)
        delete_word_btn = types.KeyboardButton(Command.DELETE_WORD)
        clear_rating_btn = types.KeyboardButton(Command.CLEAR)
        buttons.extend([next_btn, add_word_btn, delete_word_btn, clear_rating_btn])

        markup.add(*buttons)

        greeting = f"Выбери перевод слова:\n🇷🇺 {translate}"
        bot.send_message(message.chat.id, greeting, reply_markup=markup)
        bot.set_state(message.from_user.id, MyStates.target_word, message.chat.id)
        with bot.retrieve_data(message.from_user.id, message.chat.id) as data:
            data['target_word'] = target_word
            data['translate_word'] = translate
            data['other_words'] = others
    else:
        user_step = query_to_bd(f"SELECT user_name, user_step FROM tab_users WHERE user_name='{message.from_user.id}'")[0][1]
        bot.send_message(message.chat.id, f'Вы достигли максимального рейтинга - '
                                          f'{user_step}.'
                                          f'\nДля продолжения воспользуйтесь инструментами:'
                                          f'\n- добавить слово ➕;'
                                          f'\n- очистить рейтинг 🆑.')

@bot.message_handler(func=lambda message: message.text == Command.NEXT)
def next_cards(message):
    create_cards(message)

list_user_words = list()
@bot.message_handler(func=lambda message: message.text == Command.DELETE_WORD)
def delete_word(message):
    # with bot.retrieve_data(message.from_user.id, message.chat.id) as data:
    #     print(data['target_word'])  # удалить из БД

    user_words = query_to_bd(f"select rus_word "
                             f"from tab_russian_words "
                             f"join tab_users on tab_russian_words.id_user = tab_users.id_user "
                             f"where user_name='{message.from_user.id}'")
    # print(user_words)
    text = ""
    list_user_words.clear()
    for word in user_words:
        text += word[0] + "\n"
        list_user_words.append(word[0])
    chat_id = message.chat.id
    msg = bot.send_message(chat_id,f'Ваши слова в БД:\n{text}Напишите слово для удаления:')
    bot.register_next_step_handler(msg, del_word_to_bd)


def del_word_to_bd(message):
    if message.text in list_user_words:
        target = message.text
        result = query_to_bd(f"DELETE FROM tab_russian_words "
                             f"WHERE rus_word='{target}' "
                             f"and id_user='{query_to_bd(f"SELECT id_user "
                                                         f"FROM tab_users "
                                                         f"WHERE user_name='{str(message.from_user.id)}'")[0][0]}' "
                             f"RETURNING *")[0][1]
        bot.send_message(message.chat.id,f'Из БД удалено слово: {result}.')
        print(f'Из БД удалено слово: {result}')
    else:
        msg = bot.send_message(message.chat.id,f"Можно удалить только эти слова: {"; ".join(list_user_words)}."
                                               f"\nНапишите слово для удаления:")
        bot.register_next_step_handler(msg, del_word_to_bd)

@bot.message_handler(func=lambda message: message.text == Command.ADD_WORD)
def add_word(message):
    # cid = message.chat.id
    # userStep[cid] = 1
    # print(message.text)  # сохранить в БД

    chat_id = message.chat.id
    msg = bot.send_message(chat_id, 'Введите слово на русском и после двоеточия его перевод по шаблону:\n язык:language')
    bot.register_next_step_handler(msg, add_word_to_bd)

def add_word_to_bd(message):
    if ':' in message.text:
        source = message.text[: message.text.find(':')]
        print(source)
        target = message.text[message.text.rfind(':') + 1 :]
        print(target)

        print(f'В БД добавлено слово: "{query_to_bd(f"INSERT INTO tab_russian_words (rus_word, id_user) "
                             f"VALUES ('{source}', (SELECT id_user FROM tab_users WHERE user_name='{message.from_user.id}')"
                             f") RETURNING rus_word")[0][0]}"')

        print(f'В БД добавлено слово: "{query_to_bd(f"INSERT INTO tab_english_words (eng_word, id_rus_word) "
                                                    f"VALUES ('{target}', (SELECT id_rus_word FROM tab_russian_words WHERE rus_word='{source}')"
                                                    f") RETURNING eng_word")[0][0]}"')
        bot.send_message(message.chat.id,
                               f'Пара слов: {source} и {target} добавлена в БД.')
    else:
        chat_id = message.chat.id
        msg = bot.send_message(chat_id,
                               'Введите слово на русском и после двоеточия его перевод по шаблону:\n язык:language')
        bot.register_next_step_handler(msg, add_word_to_bd)

    # headers = {'Authorization': 'OAuth %s' % YANDEX_TOKEN}
    # request_url = HOST_YANDEX_DISK + '/v1/disk/resources?path=%s' % path
    # response = requests.put(url=request_url, headers=headers)
    # if response.status_code == 201:
    #     bot.reply_to(message, "Я создал папку %s" % path)
    # else:
    #     bot.reply_to(message, '\n'.join(["Произошла ошибка. Текст ошибки", response.text]))


@bot.message_handler(func=lambda message: True, content_types=['text'])
def message_reply(message):
    text = message.text

    markup = types.ReplyKeyboardMarkup(row_width=2)
    with bot.retrieve_data(message.from_user.id, message.chat.id) as data:
        target_word = data['target_word']
        if text == target_word:
            print(f'В БД записано правильно переведенное слово: "{text}" c id_rus_word: '
                  f'{query_to_bd(f"INSERT INTO tab_user_step (id_user, id_rus_word) "
                                 f"VALUES ("
                                 f"(SELECT id_user FROM tab_users WHERE user_name='{message.from_user.id}'), "
                                 f"(SELECT id_rus_word FROM tab_english_words WHERE eng_word='{text}')"
                                 f") RETURNING id_rus_word")[0][0]}')

            hint = show_target(data)

            count_step = query_to_bd(f"select user_name, count(*) "
                                     f"from tab_users "
                                     f"join tab_user_step on tab_users.id_user = tab_user_step.id_user "
                                     f"where user_name='{message.from_user.id}' "
                                     f"group by user_name")[0][1]

            print(f'Обновлен рейтинг пользователя до: '
                  f'{query_to_bd(f"UPDATE tab_users "
                                 f"SET user_step='{count_step}' "
                                 f"WHERE user_name='{message.from_user.id}' "
                                 f"RETURNING user_step")[0][0]}')

            hint_text = ["Отлично!❤", hint, f"Ваш рейтинг: {count_step}"]
            buttons.clear()
            next_btn = types.KeyboardButton(Command.NEXT)
            add_word_btn = types.KeyboardButton(Command.ADD_WORD)
            delete_word_btn = types.KeyboardButton(Command.DELETE_WORD)
            clear_rating_btn = types.KeyboardButton(Command.CLEAR)
            buttons.extend([next_btn, add_word_btn, delete_word_btn, clear_rating_btn])

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


