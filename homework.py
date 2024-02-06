import logging
import os
import requests
import time
from http import HTTPStatus
from sys import exit, stdout

import telegram
from dotenv import load_dotenv

from exceptions import UnknownHomeWorkStatus, HomeWorkNameError

load_dotenv()
# Объявляем глобальные переменные:
PRACTICUM_TOKEN: str = os.getenv('PRACTICUM_TOKEN')
TELEGRAM_TOKEN: str = os.getenv('TELEGRAM_TOKEN')
TELEGRAM_CHAT_ID: str = os.getenv('TELEGRAM_CHAT_ID')
RETRY_PERIOD: int = 600
ENDPOINT: str = 'https://practicum.yandex.ru/api/user_api/homework_statuses/'
HEADERS: dict = {'Authorization': f'OAuth {PRACTICUM_TOKEN}'}
HOMEWORK_VERDICTS: dict = {
    'approved': 'Работа проверена: ревьюеру всё понравилось. Ура!',
    'reviewing': 'Работа взята на проверку ревьюером.',
    'rejected': 'Работа проверена: у ревьюера есть замечания.'
}
logger = logging.getLogger(__name__)


def check_tokens() -> bool:
    """Проверка токенов."""
    return all([PRACTICUM_TOKEN, TELEGRAM_TOKEN, TELEGRAM_CHAT_ID])


def send_message(bot: telegram.bot.Bot, message: str) -> None:
    """Отправка сообщения в чат пользователю."""
    logger.debug('Запущена функция отправки сообщения в телеграм...')
    try:
        bot.send_message(TELEGRAM_CHAT_ID, message)
        logger.debug('Сообщение успешно отправлено в чат.')
    except telegram.error.TelegramError:
        logger.error('Ошибка отправки сообщения.')
        raise telegram.error.TelegramError


def get_api_answer(timestamp: int) -> dict:
    """Проверка ответа API практикума."""
    logger.debug('Запущена функция запроса к API практикума...')
    payload: dict = {'from_date': timestamp}
    try:
        response = requests.get(ENDPOINT, headers=HEADERS, params=payload)
    except requests.RequestException as ex:
        logger.error(f'запрос к API сервера завершен с ошибкой: {ex}')
    if response.status_code == HTTPStatus.OK:
        logger.debug('Запрос к API завершен успешно')
        return response.json()
    elif response.status_code == HTTPStatus.INTERNAL_SERVER_ERROR:
        logger.error('Внутренняя ошибка сервера')
    elif response.status_code == HTTPStatus.NOT_FOUND:
        logger.error('Запрашиваемые данные не найдены на сервере')
    else:
        logger.debug(
            f'Неожиданный код состояния HTTP запроса: {response.status_code}'
        )
    raise requests.RequestException


def check_response(response: dict) -> None:
    """Проверка корректности данных в ответе от сервера."""
    if not isinstance(response, dict):
        logger.error('Неверный тип данных в ответе API.')
        raise TypeError
    if (
        isinstance(response.get('homeworks'), list)
    ) and (
        'homeworks' in response
    ):
        logger.debug('валидация файла json прошла успешно.')
    elif 'error' in response:
        error_desc = response.get('error')
        logger.debug(
            f'Данные файла json не валидны. Ошибка {error_desc}.'
        )
    else:
        logger.error('Неверная структура файла json')
        raise TypeError


def parse_status(homework: dict) -> str:
    """Проверка статуса домашней работы."""
    current_hw_status: str = homework.get('status')
    if current_hw_status not in HOMEWORK_VERDICTS:
        raise UnknownHomeWorkStatus('Недопустимое значение ключа статуса')
    homework_name: str = homework.get('homework_name')
    if not homework_name:
        raise HomeWorkNameError('Ошибка в значении ключа названия работы')
    verdict: str = HOMEWORK_VERDICTS.get(current_hw_status)
    return f'Изменился статус проверки работы "{homework_name}". {verdict}'


def main() -> None:
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
    last_message = ''
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
    # Настраиваем логгер:
    formatter = logging.Formatter('%(asctime)s [%(levelname)s] %(message)s')
    handler = logging.StreamHandler(stream=stdout)
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    logger.setLevel(logging.DEBUG)
    main()
