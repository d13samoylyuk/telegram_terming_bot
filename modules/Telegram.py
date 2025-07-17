import telebot
from telebot import apihelper


def test_token(token):
    try:
        bot = telebot.TeleBot(token)
        bot.get_me()
        return True
    except apihelper.ApiException:
        return False