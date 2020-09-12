import numpy as np
from collections import defaultdict
from dialogs import dialogs
import json
import requests


class Responder:
    def __init__(self):
        self.user_states = defaultdict(lambda: 'CHITCHAT')
        self.user_questions = defaultdict(lambda: list(range(len(dialogs))))
        self.user_coins = defaultdict(lambda: 5)
        self.level_up = 30

    def __call__(self, text, user_id=0):
        while 1:
            state = self.user_states[user_id]

            print('state: {}, text: {}'.format(state, text))
            print('user: {}, state: {}'.format(user_id, state))
            if state in ['START_GAME', 'NEXT_QUESTION']:

                if self.user_questions[user_id]:
                    question_id = np.random.choice(self.user_questions[user_id])
                    self.user_questions[user_id].remove(question_id)

                    self.user_states[user_id] = 'QUEST_{}'.format(question_id)

                    if state == 'START_GAME':
                        return 'Ну давай поиграем... ' + dialogs[question_id]['question']

                    elif state == 'NEXT_QUESTION':
                        return 'Следующий вопрос:' + dialogs[question_id]['question']
                    else:
                        raise ValueError
                else:
                    self.user_states[user_id] = 'CHITCHAT'
                    return 'Вопросы на сегодня закончились('

            elif state == 'CONTINUE_GAME':
                answer = 'yes' if text.lower() in ['да', 'давай', 'продолж', 'дальше'] else 'no'
                if answer == 'yes':
                    self.user_states[user_id] = 'NEXT_QUESTION'
                    continue
                else:
                    self.user_states[user_id] = 'CHITCHAT'
                    return 'Ну и ладно'

            elif state.startswith('QUEST_'):
                question_id = int(state.split('_')[1])
                if dialogs[question_id]['type'] == 'bin':
                    if text.lower() in ['да', 'ага', 'конечно', 'верно', 'можно']:
                        answer = 'yes'
                    elif text.lower() in ['нет', 'не', 'нельзя', 'неправильно', 'не верно']:
                        answer = 'no'
                    else:
                        return 'Я жду ответа!'

                    bonus = ''
                    if answer == dialogs[question_id]['correct']:
                        self.user_coins[user_id] += 1
                        bonus = '\n⭐️У вас {} монеток!'.format(self.user_coins[user_id])

                    self.user_states[user_id] = 'CONTINUE_GAME'
                    return dialogs[question_id]['answer'][answer] + bonus + '\nПродолжаем?'

                elif dialogs[question_id]['type'] == 'num':
                    self.user_coins[user_id] += 1
                    bonus = '\n⭐️У вас {} монеток!'.format(self.user_coins[user_id])

                    self.user_states[user_id] = 'CONTINUE_GAME'
                    return dialogs[question_id]['answer'].format(np.random.randint(60, 95)) + bonus + '\nПродолжаем?'

                self.user_states[user_id] = 'START'

            if state == 'GET_STAT':
                n_coins = self.user_coins[user_id]
                stat = '{} У вас {} монеток. Текущий кровень - "Олеженька". До следующего уроня "Олег" осталось заработать {} монет'.format('⭐️'*n_coins, n_coins, self.level_up-n_coins)
                self.user_states[user_id] = 'CHITCHAT'
                return stat

            elif state == 'CHITCHAT':
                stat_keys = ['статист', 'уровен', 'монетк', 'бонус', 'баланс', 'уровен', 'статус']
                game_keys = ['игра', 'вопрос']

                if any([key in text.lower() for key in stat_keys]):
                    self.user_states[user_id] = 'GET_STAT'
                    continue

                if any([key in text.lower() for key in game_keys]):
                    self.user_states[user_id] = 'START_GAME'
                    continue

                else:
                    resp = requests.post(
                        'https://chitchat-vc.tinkoff.ru/?key=d812744d7bb10f374df9faa10a146ebf',
                        json={'text': text, 'user_id': user_id}
                    )
                    chitchat_reponse = json.loads(resp.text)
                    return chitchat_reponse['text']

            else:
                raise ValueError

            self.user_states[user_id] = 'CHITCHAT'
