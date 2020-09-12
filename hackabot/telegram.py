import collections
import logging
import threading
from pathlib import Path
from threading import Lock
from typing import Any, DefaultDict

import requests
from urllib.request import urlopen
import telebot
import granula
from text2speach import text2speach
from speach2text import speach2text
from brain import Responder


logger = logging.getLogger('telegram')


def run_bot(token: str):
    locks: DefaultDict[Any, Lock] = collections.defaultdict(threading.Lock)
    bot = telebot.TeleBot(token)
    responder = Responder()
    def _send(message: telebot.types.Message, response: str, type_: str='all'):
        if type_ == 'text' or 'all':
            bot.send_message(chat_id=message.chat.id, text=response, parse_mode='html')

            if type_ == 'all':
                # generate voice here
                fp = text2speach(response)
                bot.send_voice(chat_id=message.chat.id, voice=fp)

        elif type_ == 'voice':
            voice_file = urlopen(response)
            bot.send_voice(chat_id=message.chat.id, voice=voice_file)

        else:
            raise ValueError

    @bot.message_handler(commands=['start'])
    def _start(message: telebot.types.Message):

        # clear old data
        user_id = message.from_user.username
        if user_id in responder.user_coins:
            del responder.user_coins[user_id]

        if user_id in responder.user_states:
            del responder.user_states[user_id]

        if user_id in responder.user_questions:
            del responder.user_questions[user_id]


        with locks[message.chat.id]:
            _send(message, response='Привет, это ассистент Олег! У меня  появилась новая игра, которая помогает зарабатывать монетки '
                                    '⭐️Они начисляются в копилочку за каждый правильный ответ. Не стесняйтесь спрашивать у меня про ваш статус и баланс. Ну что, поиграем?')


    @bot.message_handler(content_types=['voice'])
    def handle_voice(message):
        try:
            _send_response(message)
        except Exception as e:
            logger.exception(e)

    @bot.message_handler()
    def handle_text(message: telebot.types.Message):  # pylint:disable=unused-variable
        try:
            _send_response(message)
        except Exception as e:
            logger.exception(e)

    def _send_response(message: telebot.types.Message):

        chat_id = message.chat.id
        user_id = message.from_user.username if message.from_user else 0
        # parse voice
        if message.content_type == 'voice':
            # parse voice
            file_info = bot.get_file(message.voice.file_id)
            voice_url = 'https://api.telegram.org/file/bot{0}/{1}'.format(token, file_info.file_path)
            print('voice_url: {}'.format(voice_url))

            text = speach2text(voice_url)
            #_send(message, text type_='text')
        elif message.content_type == 'text':
            text = message.text

        with locks[chat_id]:
            try:
                # response = _get_echo_response(message.text, user_id)
                response = responder(text, user_id)
            except Exception as e:
                logger.exception(e)
                response = 'Произошла ошибка'

            if response is None:
                response = 'Ответа нет'

            _send(message, response=response)

    logger.info('Telegram bot started')
    bot.polling(none_stop=True)


def main():
    config_path = Path(__file__).parent / 'config.yaml'
    config = granula.Config.from_path(config_path)
    run_bot(config.telegram.key)


if __name__ == '__main__':
    while True:
        try:
            main()
        except requests.RequestException as e:
            logger.exception(e)

