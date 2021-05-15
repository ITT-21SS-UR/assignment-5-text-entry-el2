#!/usr/bin/python
# -*- coding: utf-8 -*-

import sys
from PyQt5 import QtGui, QtCore, QtWidgets, uic
import random
from enum import Enum
import pandas as pd
from datetime import datetime

TEMPLATE_TEXT_LIST = ["Yep",
                      "Here we have another wonderful sentence.",
                      "Wow this is so much fun!"]

CSV_HEADER = ["event", "user_id", "timestamp", "time_taken_in_ms", "wpm", "numBksp"]


class EventType(Enum):
    LETTER = 1
    WORD = 2
    SENTENCE = 3
    FINISHED = 4


class SuperText(QtWidgets.QTextEdit):

    def __init__(self):
        super(SuperText, self).__init__()
        self.ui = uic.loadUi('text_entry_ui.ui')
        self.current_sentence_index = 0
        self.original_text = TEMPLATE_TEXT_LIST[0]
        self.initUI()
        self.df = pd.DataFrame(columns=CSV_HEADER)
        self.sentence_timer = QtCore.QTime()
        self.word_timer = QtCore.QTime()
        self.key_timer = QtCore.QTime()
        self.sentence_timer_running = False
        self.last_text_state = ""
        self.last_character_entered = ""
        self.num_backspace = 0
        self.word_count = 0

    def initUI(self):
        self.setWindowTitle('SuperText')
        self.setFocusPolicy(QtCore.Qt.StrongFocus)
        self.setMouseTracking(True)
        self.ui.originalText.setText(self.original_text)
        self.ui.keyPressEvent = self.keyPressEvent
        self.ui.userText.textChanged.connect(self.handleTextChanged)
        self.ui.show()

    def handleTextChanged(self):
        if not self.sentence_timer_running:
            self.sentence_timer_running = True
            self.sentence_timer.start()
            self.word_timer.start()
            self.key_timer.start()

        if len(self.last_text_state) > len(self.ui.userText.toPlainText()):
            self.last_character_entered = "backspace"
            self.num_backspace += 1
            self.add_log_entry(EventType.LETTER)
            self.key_timer.restart()

        elif len(self.ui.userText.toPlainText()) > 0:
            self.last_character_entered = self.ui.userText.toPlainText()[-1]
            self.add_log_entry(EventType.LETTER)
            self.key_timer.restart()

        if self.last_character_entered == " ":
            time_for_word = self.word_timer.elapsed()
            print(time_for_word)
            self.word_timer.restart()
            self.add_log_entry(EventType.WORD)
            self.word_count += 1

        if self.last_character_entered == "\n":
            self.handleSentenceFinished()

    def add_log_entry(self, event_type):
        if event_type == EventType.LETTER:
            self.df = self.df.append({
                'event': "key_press",
                'user_id': 1,
                'timestamp': datetime.now(),
                'time_taken_in_ms': self.key_timer.elapsed(),
                'wpm': 0,
                'numBksp': self.num_backspace
            }, ignore_index=True)

        if event_type == EventType.WORD:
            self.df = self.df.append({
                'event': "word",
                'user_id': 1,
                'timestamp': datetime.now(),
                'time_taken_in_ms': self.word_timer.elapsed(),
                'wpm': 0,
                'numBksp': self.num_backspace
            }, ignore_index=True)

        if event_type == EventType.SENTENCE:
            print(self.sentence_timer.elapsed())
            self.df = self.df.append({
                'event': "sentence",
                'user_id': 1,
                'timestamp': datetime.now(),
                'time_taken_in_ms': self.sentence_timer.elapsed(),
                'wpm': self.word_count / (self.sentence_timer.elapsed() / 60000),
                'numBksp': self.num_backspace
            }, ignore_index=True)

    def handleSentenceFinished(self):
        if self.current_sentence_index == len(TEMPLATE_TEXT_LIST) - 1:
            self.df.to_csv(sys.stdout, index=False)
            self.ui.close()
            return

        if self.ui.userText.toPlainText().strip() == self.original_text.strip():
            self.add_log_entry(EventType.SENTENCE)
            self.sentence_timer_running = False
            self.show_new_sentence()

    def show_new_sentence(self):
        self.current_sentence_index += 1
        self.original_text = TEMPLATE_TEXT_LIST[self.current_sentence_index]
        self.ui.originalText.setText(self.original_text)
        self.last_text_state = ""
        self.last_character_entered = ""
        self.ui.userText.setText("")
        self.word_count = 0



def main():
    app = QtWidgets.QApplication(sys.argv)
    super_text = SuperText()
    sys.exit(app.exec_())


if __name__ == '__main__':
    main()
