# Learning_English_Telegram_bot (ver.2 - устранение замечаний)

## Замечания:
1. Наличие файла с зависимостями это очень хорошо, но данный файл должен содержать только то, что необходимо установить 
для корректной работы. Стандартных пакетов, входящих в пакет python, а также лишних библиотек не должно быть.
### Исправление:
В файле зависимостей оставлены две библиотеки: psycopg2-binary~=2.9.10; pyTelegramBotAPI~=4.27.0.
#### Решение в [файле requirements.txt](https://github.com/nemoymoy/Learning_English_Telegram_bot/blob/main/requirements.txt)

2. Наличие скрипта создания таблиц это конечно же здорово, но к сожалению это больше история про локальные работы, 
но никак не про разработку. В реальной разработке скрипты не передают. Их интегрируют в код. Поэтому создание таблиц 
должно происходить автоматически при запуске бота. То же самое относит и к вставке данных. Обратите внимание, что 
перед вставкой данных необходимо проверить на наличие данных. Если их нет, только тогда производить вставку данных.
### Исправление:
В соответствии с предложенной новой архитектурой БД переписан код.
В начале проверяется существование БД и если ее нет, то создается новая БД.
Далее проверяется существование таблиц, если их нет, то новые таблицы создаются.
Далее проверяется наличие записей в таблице "words", если записей нет, то новые записи добавляются.

3. Архитектурное решение выбрано не совсем верно. Перевод слово должно быть его частью, а значит находиться в одной таблице.
### Исправление:
Спроектирована новая архитектура БД.
#### ![Схема БД в файле scheme_db_v2.png](https://github.com/nemoymoy/Learning_English_Telegram_bot/blob/main/scheme_db_v2.png?raw=true)

4. В вашем коде есть вот такая часть
```doctest
    # Загружаем из БД список зарегистрированных пользователей
    known_users = list()
    for row in query_to_bd("SELECT user_name FROM tab_users"):
        known_users.append(row[0])
    # print(known_users)
    
    # Загружаем из БД и формируем словарь с ключом имени пользователя и значением количества шагов (рейтингом)
    userStep = dict()
    for row in query_to_bd("SELECT user_name, user_step FROM tab_users"):
        userStep[row[0]] = row[1]
```
её необходимо убрать.
### Исправление:
Указанный блок удалён из кода.

5. Вот такое написание кода
```doctest
    possible_rus_words = query_to_bd(f"select rus_word "
                                            f"from tab_russian_words "
                                            f"where id_user='1' or id_user='{query_to_bd(f"select id_user from "
                                                                                         f"tab_users where user_name='{cid}'")[0][0]}'"
                                            f"except select rus_word "
                                            f"from tab_russian_words "
                                            f"join tab_user_step on tab_russian_words.id_rus_word = tab_user_step.id_rus_word "
                                            f"join tab_users on tab_user_step.id_user = tab_users.id_user "
                                            f"where user_name='{cid}'")
```
считается неприемлемым, а именно:
* Запросы можно писать используя многострочный ввод (тройные кавычки). При таком подходе код смотрится чище. -> **_Применено_**
* При написании запроса стоит придерживаться написания системных команд используя верхний регистр. 
Так запрос читается легче. -> **_Применено_**
* f строка при сырых запросах не используется, т.к. есть риск инъекции. На странице с документацией psycopg2 данный 
способ является неправильным. Там есть примеры как правильно передавать переменные в запрос. -> **_Применено_**
* Есть принцип “разделяй и властвуй”. Он подразумевает то, что не нужно делать одну большую строку. 
Лучше логику разделить. Например, в вашем случае запрос пользователя стоит вынести и выполнить отдельно, 
а потом результат передать дальше. Аналогичная у вас история с принтами. 
К большому сожалению, такое написание кода даже не пройдет первый этап собеседования на работу, где сочтут, 
что разработчик не умеет писать красиво и понятно, а также не придерживается правил хорошего тона. -> **_Применено_**

6. При получении карточек я насчитал как минимум три запроса к БД. На мой взгляд это очень плохо. 
Это связано с тем, что вы изначально выбрали не совсем верную архитектуру и подход. 
Во-первых, для простоты и начала я бы вам рекомендовал вот такую архитектуру...
![Рекомендованная структура БД в файле many-to-one.png](https://github.com/nemoymoy/Learning_English_Telegram_bot/blob/main/many-to-one.png?raw=true)
Это поможет исключить не только не нужное добавление пользователя, а также поможет построить правильный и один запрос. 
Во-вторых, запрос при таком простом задании должен быть один. 
Опираясь на схему выше, то за один запрос можно получить 4 рандомные пары, вот так:
```
SELECT ..., ...  --получаем слово и перевод
FROM (
    SELECT ..., ...  --получаем слово и перевод
    FROM ...  --из таблицы общих слов
    UNION
    SELECT ..., ...  --получаем слово и перевод
    FROM ...  --из таблицы персональных слов
    WHERE ...  --где айди пользователя равно искомому айди
)
ORDER BY ...  --сортируем по рандому
LIMIT ...  --берем 4 слова
```
Код чище, запрос понятнее, один запрос, нет лишнего кода на питоне, так как большую часть делает бд и немного данных, 
которые не нагружают память. -> **_Применено_**

# Learning_English_Telegram_bot (ver.1)

## Необходимо разработать программу-бота, которая должна выполнять следующие действия.
1. Заполнить базу данных общим набором слов для всех пользователей (цвета, местоимения и т.д.). Достаточно 10 слов. -> **_Реализовано_**
2. Спрашивать перевод слова, предлагая 4 варианта ответа на английском языке в виде кнопок. -> **_Реализовано_**
3. При правильном ответе подтверждать ответ, при неправильном - предлагать попробовать снова. -> **_Реализовано_**
4. Должна быть реализована функция добавления нового слова. -> **_Реализовано_**
5. Должна быть реализована функция удаления слова. Удаление должно быть реализовано персонально для пользователя. -> **_Реализовано_**
6. Новые слова не должны появляться у других пользователей. -> **_Реализовано_**
7. Работа с ботом после запуска должна начинаться с приветственного сообщения. -> **_Реализовано_**

## Дополнительные требования к проекту (необязательные для получения зачёта):
1. После добавления нового слова выводить количество слов, которые изучает пользователь. -> **_Реализовано_**

## Собственное дополнение:
1. Реализовать отчистку (обнуление) шагов пользователя (рейтинга) после изучения всех возможных слов. -> **_Реализовано_**

## Правила сдачи работы
## Спроектирована база данных для бота. Есть скрипты для её создания и заполнения.
### Выполнено:
#### Решение в [файле scheme_db.png](https://github.com/nemoymoy/Learning_English_Telegram_bot/blob/main/scheme_db.png)
#### Решение в [файле create_db.sql](https://github.com/nemoymoy/Learning_English_Telegram_bot/blob/main/create_db.sql)
#### Решение в [файле insert_db.sql](https://github.com/nemoymoy/Learning_English_Telegram_bot/blob/main/insert_db.sql)

## Разработан бот и все части кода объединены в главной ветке (master/main).
### Выполнено:
#### Решение в [файле main.py](https://github.com/nemoymoy/Learning_English_Telegram_bot/blob/main/main.py)

## Написана документация по использованию программы.
### Написаны комментарии в исполняемом файле программы и в файле README.md

## В личном кабинете отправлена ссылка на репозиторий с решением.
### Создан публичный репозиторий [Learning_English_Telegram_bot](https://github.com/nemoymoy/Learning_English_Telegram_bot)