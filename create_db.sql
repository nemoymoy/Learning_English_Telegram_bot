-- создаем таблицу Пользователей

CREATE TABLE IF NOT EXISTS tab_users (
	id_user SERIAL PRIMARY KEY,
	user_name VARCHAR(40) NOT NULL,
	user_step INTEGER
);

-- создаем таблицу Русских слов

CREATE TABLE IF NOT EXISTS tab_russian_words (
	id_rus_word SERIAL PRIMARY KEY,
	rus_word VARCHAR(100) NOT NULL,
	id_user INTEGER FOREIGN KEY (id_user) REFERENCES tab_users(id_user) ON UPDATE CASCADE ON DELETE CASCADE
);

-- создаем таблицу Английских слов

CREATE TABLE IF NOT EXISTS tab_english_words (
	id_eng_word SERIAL PRIMARY KEY,
	eng_word VARCHAR(100) NOT NULL,
	id_rus_word INTEGER FOREIGN KEY (id_rus_word) REFERENCES tab_russian_words(id_rus_words) ON UPDATE CASCADE ON DELETE CASCADE
);

-- создаем таблицу Шагов пользователя

CREATE TABLE IF NOT EXISTS tab_user_step (
	id_user INTEGER FOREIGN KEY (id_user) REFERENCES tab_users(id_user) ON UPDATE CASCADE ON DELETE CASCADE,
	id_rus_word INTEGER FOREIGN KEY (id_rus_word) REFERENCES tab_russian_words(id_rus_word) ON UPDATE CASCADE ON DELETE CASCADE
);
