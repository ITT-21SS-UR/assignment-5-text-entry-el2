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


class ExtendedTextEdit(QtWidgets.QTextEdit):

    key_pressed_signal = QtCore.pyqtSignal(QtGui.QKeyEvent)

    def __init__(self, parent=None):
        super(ExtendedTextEdit, self).__init__(parent)

    def keyPressEvent(self, event):
        self.key_pressed_signal.emit(event)

        if event.key() != QtCore.Qt.Key_Return:
            super().keyPressEvent(event)


class SuperText(QtWidgets.QTextEdit):

    sentence_list = []
    original_text = ""
    user_id = 0

    def __init__(self):
        super(SuperText, self).__init__()
        self.ui = uic.loadUi('text_entry_ui.ui')
        self.user_input_layout = self.ui.userInputLayout
        self.text_changed_by_user = True
        self.text_edit = ExtendedTextEdit(self)
        self.current_sentence_index = 0
        self.parse_setup()
        self.original_text = self.sentence_list[0]
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

        self.ui.userInputLayout.addWidget(self.text_edit)
        self.text_edit.key_pressed_signal.connect(self.handle_key_pressed)
        self.text_edit.textChanged.connect(self.handle_text_changed)
        self.ui.show()

    def parse_setup(self):

        if len(sys.argv) is not 3:
            print("Please pass a .txt file with sentences and a user ID as arguments!")

        else:
            file = open(sys.argv[1], 'r')
            lines = file.readlines()

            for line in lines:
                self.sentence_list.append(line.strip())

            try:
                self.user_id = int(sys.argv[2])
            except ValueError:
                print("Please provide a valid ID as second argument! Using fallback ID (0) instead.")
                self.user_id = 0

    def handle_text_changed(self):
        if not self.text_changed_by_user:
            return

        if not self.sentence_timer_running:
            self.sentence_timer_running = True
            self.sentence_timer.start()
            self.word_timer.start()
            self.key_timer.start()

        if len(self.last_text_state) > len(self.text_edit.toPlainText()):
            self.last_character_entered = "backspace"
            self.num_backspace += 1
            self.add_log_entry(EventType.LETTER)
            self.key_timer.restart()

        elif len(self.text_edit.toPlainText()) > 0:
            self.last_character_entered = self.text_edit.toPlainText()[-1]
            self.add_log_entry(EventType.LETTER)
            self.key_timer.restart()

        if self.last_character_entered == " ":
            time_for_word = self.word_timer.elapsed()
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

    def handle_sentence_finished(self):
        self.text_changed_by_user = False
        if self.text_edit.toPlainText().strip() == self.original_text.strip():
            self.add_log_entry(EventType.SENTENCE)
            self.sentence_timer_running = False
            self.show_new_sentence()

            if self.current_sentence_index == len(self.sentence_list) - 1:
                self.df.to_csv(sys.stdout, index=False)
                self.ui.close()
            else:
                self.show_new_sentence()

        else:
            self.highlight_errors()

    def handle_key_pressed(self, event):
        self.text_changed_by_user = True

        if event.key() == QtCore.Qt.Key_Return:
            self.handle_sentence_finished()

    def highlight_errors(self):
        self.text_changed_by_user = False
        text_format = QtGui.QTextCharFormat()
        text_format.setBackground(QtGui.QBrush(QtGui.QColor("white")))
        cursor = self.text_edit.textCursor()

        user_text = self.text_edit.toPlainText()
        original_text = self.original_text
        cursor.setPosition(0)
        cursor.movePosition(QtGui.QTextCursor.EndOfBlock, 1)
        cursor.mergeCharFormat(text_format)

        text_format.setBackground(QtGui.QBrush(QtGui.QColor("red")))

        error_index_list = []
        index = 0
        while index < len(user_text):
            if index >= len(original_text):
                error_index_list.append(index)
                index += 1
                continue

            if user_text[index] != original_text[index]:
                error_index_list.append(index)

            index += 1

        for error_index in error_index_list:
            cursor.setPosition(error_index)
            cursor.movePosition(QtGui.QTextCursor.NextCharacter, 1)
            cursor.mergeCharFormat(text_format)

    def show_new_sentence(self):
        self.current_sentence_index += 1
        self.original_text = self.sentence_list[self.current_sentence_index]
        self.ui.originalText.setText(self.original_text)
        self.last_text_state = ""
        self.last_character_entered = ""
        self.text_edit.setText("")
        self.word_count = 0



def main():
    app = QtWidgets.QApplication(sys.argv)
    super_text = SuperText()
    sys.exit(app.exec_())


if __name__ == '__main__':
    main()
