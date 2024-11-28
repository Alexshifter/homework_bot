# Телеграм-бот для проверки статуса домашних заданий.
## Описание проекта
Телеграм-бот для отслеживания статуса проверки заданий.
Бот обращается к внешнему API, проходит аутентификацию и отправляет в чат статус проверки задания ревьювером.
## Возможности проекта
 - Опрос API каждые 10 минут. Если статус изменился, в чат отправляется сообщение с новым статусом;
 - Логирование событий с флагами ```DEBUG``` и ```ERROR```
 - Лог с флагом ```ERROR``` отправляется в чат пользователю.

## Запуск
Клонируйте репозиторий локально: 
```
git clone git@github.com:Alexshifter/homework_bot.git
```
Находясь в директории проекта разверните виртуальное окружение
```
python -m venv venv
```
Запустите виртуальное окружение
```
source venv/scripts/activate
```
Обновите pip
```
python -m pip install --upgrade pip
```
Установите зависимости
```
pip install -r requirements.txt
```
Создайте файл .env и укажите в нем значения переменных:
```
TELEGRAM_TOKEN='<YOUR_TELEGRAM_BOT_API_TOKEN>'
TELEGRAM_CHAT_ID='<YOUR_TELEGRAM_USER_ID>'
PRACTICUM_TOKEN='<YOUR_PRACTICUM_API_TOKEN>'
```
## Работа с ботом
Запустите бот
```
python homework.py
```
Бот доступен по адресу:<br>

<img src="https://github.com/user-attachments/assets/d190e521-e941-43c4-add9-c5f709c9ee7a" width="200" height="200">

## Основные технологии
Python 3.9.13, Scrapy 2.5.1
## Автор
[Alexey Pakaev](https://github.com/Alexshifter/)

