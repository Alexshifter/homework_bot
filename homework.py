import logging
import os
import requests
import time
from sys import exit

import telegram
from dotenv import load_dotenv

from exceptions import UnknownHomeWorkStatus, HomeWorkNameError

load_dotenv()
# Настраиваем логгер:
logger = logging.getLogger(__name__)
formatter = logging.Formatter('%(asctime)s [%(levelname)s] %(message)s')
handler = logging.StreamHandler()
handler.setFormatter(formatter)
logger.addHandler(handler)
logger.setLevel(logging.DEBUG)

# Объявляем глобальные переменные:
PRACTICUM_TOKEN = os.getenv('PRACTICUM_TOKEN')
TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')
TELEGRAM_CHAT_ID = os.getenv('TELEGRAM_CHAT_ID')
RETRY_PERIOD = 600
ENDPOINT = 'https://practicum.yandex.ru/api/user_api/homework_statuses/'
HEADERS = {'Authorization': f'OAuth {PRACTICUM_TOKEN}'}
HOMEWORK_VERDICTS = {
    'approved': 'Работа проверена: ревьюеру всё понравилось. Ура!',
    'reviewing': 'Работа взята на проверку ревьюером.',
    'rejected': 'Работа проверена: у ревьюера есть замечания.'
}


def check_tokens():
    """Проверка токенов."""
    if PRACTICUM_TOKEN and TELEGRAM_TOKEN and TELEGRAM_CHAT_ID:
        return True


def send_message(bot, message):
    """Отправка сообщения в чат пользователю."""
    try:
        bot.send_message(TELEGRAM_CHAT_ID, message)
        logger.debug('Сообщение успешно отправлено в чат.')
    except telegram.error.TelegramError:
        logger.error('Ошибка отправки сообщения.')
        raise telegram.error.TelegramError


def get_api_answer(timestamp):
    """Проверка ответа API практикума."""
    payload = {'from_date': timestamp}
    try:
        response = requests.get(ENDPOINT, headers=HEADERS, params=payload)
    except requests.exceptions.ConnectionError:
        logger.error('Сервер недоступен')
    except requests.RequestException as ex:
        logger.error(f'запрос к API сервера завершен с ошибкой: {ex}')
    if response.status_code == 200:
        return response.json()
    raise requests.RequestException


def check_response(response):
    """Проверка корректности данных в ответе от сервера."""
    check_structure = isinstance(response, dict)
    if not check_structure:
        logger.error('Неверный тип данных в ответе API.')
        raise TypeError

    check_content = (
        isinstance(response.get('homeworks'), list)
    ) and (
        'homeworks' in response.keys()
    ) or (
        'error' in response.keys()
    )
    if not check_content:
        logger.error('Неверная структура файла json()')
        raise TypeError
    if 'error' in response.keys():
        error = response.get('error')
        logger.debug(
            f'Не удалось получить валидные данные json(). Ошибка {error}'
        )


def parse_status(homework):
    """Проверка статуса домашней работы."""
    current_hw_status = homework.get('status')
    if current_hw_status not in HOMEWORK_VERDICTS:
        raise UnknownHomeWorkStatus('Недопустимое значение ключа статуса')
    homework_name = homework.get('homework_name')
    if not homework_name:
        raise HomeWorkNameError('Ошибка в значении ключа названия работы')
    verdict = HOMEWORK_VERDICTS.get(current_hw_status)
    return f'Изменился статус проверки работы "{homework_name}". {verdict}'


def main():
    """Основная логика работы бота."""
    if check_tokens():
        logger.debug('Проверка токенов успешно выполнена.')
    else:
        logger.critical(
            ('Одна или несколько переменных окружения недоступны. '
                'Программа остановлена.')
        )
        exit()
    bot = telegram.Bot(token=TELEGRAM_TOKEN)
    timestamp = int(time.time())
    last_message = None
    while True:
        try:
            response = get_api_answer(timestamp)
            check_response(response)
            if response.get('homeworks'):
                current_homework = response.get('homeworks')[0]
                if current_homework.get('status') != last_message:
                    message = parse_status(current_homework)
                    send_message(bot, message)
                    last_message = current_homework.get('status')
            else:
                logger.debug('В списке нет активных работ')
        except Exception as error:
            message = f'Сбой в работе программы: {error}'
            if message != last_message:
                send_message(bot, message)
                last_message = message
                logger.error(message)
        finally:
            time.sleep(RETRY_PERIOD)


if __name__ == '__main__':
    main()
