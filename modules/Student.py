from random import shuffle


class Student:
    def __init__(self, user_telegram_id, database):
        self._telegram_id = user_telegram_id
        self._database = database

        self._state = None
        self._current_target = None
        self._current_set = None
        self._current_words = None

    def new_session(self, words_amnt=4):
        '''Creates new session for user with a shuffled banks of words
        and returns current words set (as english options) and 
        target word (as russian, english)'''
        self._current_words = list(
            self._database.get_user_words(self._telegram_id))
        shuffle(self._current_words)
        self.learning()

        return self.next_set(words_amnt=words_amnt)
    
    def next_set(self, words_amnt=4):
        '''Returns current words set (as english options) and 
        target word (as russian, english)'''
        self._current_set = self._current_words[:words_amnt]
        self._current_target = self._current_set[0]
        self._current_words = self._current_words[words_amnt:]

        if len(self._current_words) <= words_amnt:
            self._current_words = list(
            self._database.get_user_words(self._telegram_id))
            shuffle(self._current_words)
        
        shuffle(self._current_set)
        buttons = [word[1] for word in self._current_set]

        return buttons, self._current_target
    
    def remove_word(self, rus_word):
        return self._database.add_stop_word(
            self._telegram_id, rus_word)
    
    def add_word(self, raw_term, splitter='/'):
        '''Runs checks on given raw term and adds term to database
        if correct'''
        if '\n' in raw_term:
            return 'NewLineUsed'
        splitted_term = raw_term.split(splitter)
        if len(splitted_term) != 2:
            return 'InvalidSplitCondition'
        rus_word, translation = [part.strip() for part in splitted_term]

        if len(rus_word) == 0 or len(translation) == 0:
            return 'EmptyTerm'
        
        # other error feedback are comes from
        # database control module
        return self._database.add_extra_word(
            self._telegram_id, rus_word, translation)
    
    def end_session(self):
        self._state = False
        self._current_target = None
        self._current_set = None
        self._current_words = None
    
    def is_learning(self):
        '''Returns True if user is learning, False otherwise'''
        return self._state == 'learning'
    
    def learning(self):
        '''Sets student's (user's) state to learning'''
        self._state = 'learning'
    
    def is_adding_word(self):
        '''Returns True if user in adding word state, False otherwise'''
        return self._state == 'adding_word'

    def adding_word(self):
        '''Sets student's (user's) state to adding word'''
        self._state = 'adding_word'
    
    def reset_state(self):
        self._state = None