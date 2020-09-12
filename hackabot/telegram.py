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
import json
from collections import defaultdict
import numpy as np
from text2speach import text2speach
from speach2text import speach2text


logger = logging.getLogger('telegram')


class Responder:
    def __init__(self):
        self.user_states = defaultdict(lambda: 'START')
        self.user_questions = defaultdict(lambda: list(range(len(dialogs))))

    def __call__(self, text, user_id=0):
        state = self.user_states[user_id]
        print('user: {}, state: {}'.format(user_id, state))
        if state == 'START':
            if self.user_questions[user_id]:
                question_id = np.random.choice(self.user_questions[user_id])
                self.user_questions[user_id].remove(question_id)

                self.user_states[user_id] = 'QUEST_{}'.format(question_id)
                resp = dialogs[question_id]['question']
            else:
                resp = 'Вопросы на сегодня закончились('

        elif state.startswith('QUEST_'):
            question_id = int(state.split('_')[1])
            if dialogs[question_id]['type'] == 'bin':
                answer = 'yes' if text.lower() in ['да', 'ага', 'конечно', 'верно', 'можно'] else 'no'
                resp = dialogs[question_id]['answer'][answer]
            elif dialogs[question_id]['type'] == 'num':
                resp = dialogs[question_id]['answer'].format(np.random.randint(60, 95))

            self.user_states[user_id] = 'START'

        # elif state.startswith('QUEST_'):
        #     question_id = int(state.split('_')[1])
        #     self.user_states[user_id] = 'START'
        #     resp = dialogs[question_id]['answer'].format(np.random.randint(60, 95))

        else:
            raise ValueError


        return resp

        # resp = requests.post(
        #     'https://chitchat-vc.tinkoff.ru/?key=d812744d7bb10f374df9faa10a146ebf',
        #     json={'text': text, 'user_id': user_id}
        # )
        # chichat_reponse = json.loads(resp.text)
        # chichat_text = chichat_reponse['text']
        #
        # return 'Отвечаю на \"{}\"\nChitchat: {}'.format(text, chichat_text)


def run_bot(token: str):
    locks: DefaultDict[Any, Lock] = collections.defaultdict(threading.Lock)
    bot = telebot.TeleBot(token)
    responder = Responder()
    print('resp')
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
        with locks[message.chat.id]:
            _send(message, response='Давай сыграем с тобой в игру')

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
        user_id = str(message.from_user.id) if message.from_user else 0

        # parse voice

        if message.content_type == 'voice':
            # parse voice
            file_info = bot.get_file(message.voice.file_id)
            voice_url = 'https://api.telegram.org/file/bot{0}/{1}'.format(token, file_info.file_path)
            print('voice_url: {}'.format(voice_url))

            text = speach2text(voice_url)
            _send(message, text, type_='text')
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

