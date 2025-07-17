from telebot import TeleBot, custom_filters
from telebot.storage import StateMemoryStorage
from telebot.handler_backends import State, StatesGroup

from modules.Interface import Interface, clear_terminal
from modules.English_DB import *
from modules.Student import Student
from modules.program import get_info


# check or gather needed info
token_bot, db_username, db_password = get_info()
clear_terminal()

print('Bot is being initialized')
# Bot setup
state_storage = StateMemoryStorage()
bot = TeleBot(token_bot, state_storage=state_storage)
class MyStates(StatesGroup):
    target_word = State()

# database setup
db = English_DB(db_username, db_password)

# other
interface = Interface()
users_now = {} # "user id:" "user object"


def check_in_user(message):
    '''Checks if user is new to current session and adds to
    users_now dict if so.\n
    Returns True if user is new, False otherwise.'''
    user_id = message.from_user.id
    is_new = str(user_id) not in users_now
    if is_new:
        users_now[str(user_id)] = Student(str(user_id), db)
        print("> new user in session:", message.from_user.username)
        if not db.find_object(users, users.telegram_ID == str(user_id)):
            db.add_user(user_id)
            greeting(message)
            print(f"> user added to database", message.from_user.username)

    return is_new


@bot.message_handler(commands=['start'])
def menu(message):
    check_in_user(message)    
    bot.send_message(message.chat.id,
                     text='Choose action',
                     reply_markup=interface.menu())


@bot.message_handler(func=lambda message: message.text == interface.BEGIN)
def learning(message):
    check_in_user(message)

    user_id = message.from_user.id
    student = users_now[str(user_id)]

    if not student.is_learning():
        buttons, target_word = student.new_session(words_amnt=4)
        print(f'new set for {user_id} ({message.from_user.username})')
    else:
        buttons, target_word = student.next_set(words_amnt=4)
    
    bot.send_message(message.chat.id,
                     text=f'Choose meaning:\n> "{target_word[0]}"',
                     reply_markup=interface.learn(buttons))
    bot.set_state(user_id, MyStates.target_word, message.chat.id)
    with bot.retrieve_data(user_id, message.chat.id) as data:
        data['target_word'] = target_word


@bot.message_handler(func=lambda message: message.text == interface.NEXT)
def next(message):
    check_in_user(message)
    learning(message)
    
# Add word
@bot.message_handler(func=lambda message: message.text == interface.ADD_WORD)
def add_word(message):
    check_in_user(message)
    user_id = message.from_user.id
    student = users_now[str(user_id)]
    student.adding_word()
    bot.send_message(message.chat.id,
                        text='Для добавления используйте схему:\n'
                        ' "<i>[слово] / [значение]</i>"\n'
                        'Пример:\n "<i>привет / hi, hey</i>"\n\n'
                        'Слэш "/" обязателен',
                        reply_markup=interface.no_keyboard(),
                        parse_mode='html')


def check_added_word(message):
    text = message.text
    user_id = message.from_user.id
    student = users_now[str(user_id)]

    added_word = student.add_word(text)
    if added_word == True:
        reply = 'Успешно!\nWord was added to your dictionary'
    else:
        reply = interface.error_decode(added_word)

    student.reset_state()
    bot.send_message(message.chat.id, 
                        text=reply,
                         reply_markup=interface.menu())

# Remove word
@bot.message_handler(func=lambda message: message.text == interface.DELETE_WORD)
def remove_word(message):
    if not check_in_user(message):
        user_id = message.from_user.id
        student = users_now[str(user_id)]
        if student.is_learning():
            with bot.retrieve_data(message.from_user.id, message.chat.id) as data:
                rus_word = data['target_word'][0]
            student.remove_word(rus_word)
            bot.send_message(message.chat.id,
                             text='Word was removed from your dictionary',
                             reply_markup=interface.learn(
                                 remove_commands=[0]))
    pass

# End learning session
@bot.message_handler(func=lambda message: message.text == interface.END)
def end(message):
    check_in_user(message)
    user_id = message.from_user.id
    student = users_now[str(user_id)]
    student.end_session()
    menu(message)
    

def check_answer(message):
    text = message.text
    user_id = message.from_user.id
    with bot.retrieve_data(user_id, message.chat.id) as data:
        target_word = data['target_word'][1]
        if text == target_word:
            reply = "Correct!"
        else:
            reply = f'Oops! The correct answer is \n"{target_word}"' 
        bot.send_message(message.chat.id,
                            text=reply,
                            reply_markup=interface.learn())


@bot.message_handler(func=lambda message: True, content_types=['text'])
def message_reply(message):
    '''Directing user's message to appropriate function'''
    if not check_in_user(message):
        user_id = message.from_user.id
        student = users_now[str(user_id)]
        if student.is_adding_word():
            check_added_word(message)
        elif student.is_learning():
            check_answer(message)
    else:
        menu(message)
        

def greeting(message):
    bot.send_message(message.chat.id, interface.greeting)


bot.add_custom_filter(custom_filters.StateFilter(bot))
print('Bot is running')
bot.infinity_polling(skip_pending=True)