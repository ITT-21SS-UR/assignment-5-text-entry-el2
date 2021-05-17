#!/usr/bin/python
# -*- coding: utf-8 -*-

import sys

import PyQt5.QtWidgets
from PyQt5 import uic, QtGui
import sys
from PyQt5 import QtWidgets, QtCore
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QTextCursor, QFont
from PyQt5.QtWidgets import QVBoxLayout, QCompleter
from enum import Enum
import pandas as pd
from datetime import datetime
from PyQt5.QtWidgets import QTextEdit, QCompleter

CSV_HEADER = ["event", "user_id", "timestamp", "time_taken_in_ms", "auto_completed", "auto_completion_count",
              "wpm", "numBksp"]


class EventType(Enum):
    LETTER = 1
    WORD = 2
    SENTENCE = 3
    FINISHED = 4


class TextEdit(QTextEdit):
    """
    Custom TextEdit widget with auto-complete functionality.
    Code taken from: https://github.com/baoboa/pyqt5/blob/master/examples/tools/customcompleter/customcompleter.py
    Slightly adjusted to our needs
    """

    key_pressed_signal = QtCore.pyqtSignal(QtGui.QKeyEvent)

    def __init__(self, parent=None):
        super(TextEdit, self).__init__(parent)

        self._completer = None
        self.auto_completed = False
        self.auto_completion_count = 0

    def setCompleter(self, c):
        if self._completer is not None:
            self._completer.activated.disconnect()

        self._completer = c

        c.setWidget(self)
        c.setCompletionMode(QCompleter.PopupCompletion)
        c.setCaseSensitivity(Qt.CaseInsensitive)
        c.activated.connect(self.insertCompletion)

    def completer(self):
        return self._completer

    def insertCompletion(self, completion):
        if self._completer.widget() is not self:
            return

        tc = self.textCursor()
        extra = len(completion) - len(self._completer.completionPrefix())
        tc.movePosition(QTextCursor.Left)
        tc.movePosition(QTextCursor.EndOfWord)
        if extra > 0:
            tc.insertText(completion[-extra:])
        # tc.insertText(" ") TODO intelligent space inserting
        self.setTextCursor(tc)
        self.auto_completed = True
        self.auto_completion_count += 1

    def textUnderCursor(self):
        tc = self.textCursor()
        tc.select(QTextCursor.WordUnderCursor)

        return tc.selectedText()

    def focusInEvent(self, e):
        if self._completer is not None:
            self._completer.setWidget(self)

        super(TextEdit, self).focusInEvent(e)

    def keyPressEvent(self, e):
        self.key_pressed_signal.emit(e)
        if e.key() == Qt.Key_Return:
            return

        if self._completer is not None and self._completer.popup().isVisible():
            # The following keys are forwarded by the completer to the widget.
            if e.key() in (Qt.Key_Enter, Qt.Key_Return, Qt.Key_Escape, Qt.Key_Tab, Qt.Key_Backtab):
                e.ignore()
                # Let the completer do default behavior.
                return

        isShortcut = ((e.modifiers() & Qt.ControlModifier) and e.key() == Qt.Key_E)
        if self._completer is None or not isShortcut:
            # Do not process the shortcut when we have a completer.
            super(TextEdit, self).keyPressEvent(e)

        ctrlOrShift = e.modifiers() & (Qt.ControlModifier | Qt.ShiftModifier)
        if self._completer is None or (ctrlOrShift and len(e.text()) == 0):
            return

        eow = "~!@#$%^&*()_+{}|:\"<>?,./;'[]\\-="
        hasModifier = (e.modifiers() != Qt.NoModifier) and not ctrlOrShift
        completionPrefix = self.textUnderCursor()

        if not isShortcut and (
                hasModifier or len(e.text()) == 0 or len(completionPrefix) < 3 or e.text()[-1] in eow):
            self._completer.popup().hide()
            return

        if completionPrefix != self._completer.completionPrefix():
            self._completer.setCompletionPrefix(completionPrefix)
            self._completer.popup().setCurrentIndex(
                self._completer.completionModel().index(0, 0))

        cr = self.cursorRect()
        cr.setWidth(self._completer.popup().sizeHintForColumn(
            0) + self._completer.popup().verticalScrollBar().sizeHint().width())
        self._completer.complete(cr)

    def reset_auto_completion_stats(self):
        self.auto_completion_count = 0
        self.auto_completed = False


class SuperText(QtWidgets.QTextEdit):

    sentence_list = []
    original_text = ""
    user_id = 0

    def __init__(self):
        super(SuperText, self).__init__()
        self.ui = uic.loadUi('text_entry_technique.ui')
        self.user_input_layout = self.ui.userInputLayout
        self.text_edit = TextEdit(self)
        self.text_edit.key_pressed_signal.connect(self.handle_key_pressed)
        self.current_sentence_index = 0
        self.parse_setup()
        self.original_text = self.sentence_list[0]
        self.df = pd.DataFrame(columns=CSV_HEADER)
        self.initUI()
        self.sentence_timer = QtCore.QTime()
        self.word_timer = QtCore.QTime()
        self.key_timer = QtCore.QTime()
        self.sentence_timer_running = False
        self.text_changed_by_user = True
        self.last_text_state = ""
        self.last_character_entered = ""
        self.num_backspace = 0
        self.word_count = 0
        self.completer = ()
        self.init_completer()

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

    def init_completer(self):
        word_list = []
        for sentence in self.sentence_list:
            words = sentence.split()
            for word in words:
                if word not in word_list:
                    word_list.append(word)

        self.completer = QtWidgets.QCompleter(word_list, self)
        self.completer.setCaseSensitivity(QtCore.Qt.CaseSensitive)
        self.completer.setCompletionMode(QtWidgets.QCompleter.PopupCompletion)
        self.completer.setModelSorting(QtWidgets.QCompleter.UnsortedModel)
        self.text_edit.setCompleter(self.completer)

    def initUI(self):
        self.setWindowTitle('SuperText')
        self.setFocusPolicy(QtCore.Qt.StrongFocus)
        self.setMouseTracking(True)
        self.ui.originalText.setText(self.original_text)
        self.ui.keyPressEvent = self.keyPressEvent
        self.ui.show()

        self.ui.userInputLayout.addWidget(self.text_edit)
        self.text_edit.textChanged.connect(self.handleTextChanged)

    def handleTextChanged(self):
        if not self.text_changed_by_user:
            return

        if not self.sentence_timer_running:
            self.sentence_timer_running = True
            self.sentence_timer.start()
            self.word_timer.start()
            self.key_timer.start()

        elif len(self.text_edit.toPlainText()) > 0:
            self.last_character_entered = self.text_edit.toPlainText()[-1]
            self.add_log_entry(EventType.LETTER)
            self.key_timer.restart()

        if self.last_character_entered == " ":
            self.add_log_entry(EventType.WORD)
            self.word_timer.restart()
            self.word_count += 1

        # if self.last_character_entered == "\n":
        #     self.handleSentenceFinished()

    def handle_key_pressed(self, event):
        self.text_changed_by_user = True

        if event.key() == QtCore.Qt.Key_Return:
            self.handle_sentence_finished()

        if event.key() == QtCore.Qt.Key_Backspace:
            self.num_backspace += 1
            self.last_character_entered = "backspace"
            self.add_log_entry(EventType.LETTER)
            self.key_timer.restart()

    def add_log_entry(self, event_type):
        if event_type == EventType.LETTER:
            self.df = self.df.append({
                'event': "key_press",
                'user_id': self.user_id,
                'timestamp': datetime.now(),
                'time_taken_in_ms': self.key_timer.elapsed(),
                'auto_completed': False,
                'auto_completion_count': self.text_edit.auto_completion_count,
                'wpm': None,
                'numBksp': self.num_backspace
            }, ignore_index=True)

        if event_type == EventType.WORD:
            self.df = self.df.append({
                'event': "word",
                'user_id': self.user_id,
                'timestamp': datetime.now(),
                'time_taken_in_ms': self.word_timer.elapsed(),
                'auto_completed': self.text_edit.auto_completed,
                'auto_completion_count': self.text_edit.auto_completion_count,
                'wpm': None,
                'numBksp': self.num_backspace
            }, ignore_index=True)

        if event_type == EventType.SENTENCE:
            self.df = self.df.append({
                'event': "sentence",
                'user_id': self.user_id,
                'timestamp': datetime.now(),
                'time_taken_in_ms': self.sentence_timer.elapsed(),
                'auto_completed': self.text_edit.auto_completed,
                'auto_completion_count': self.text_edit.auto_completion_count,
                'wpm': self.word_count / (self.sentence_timer.elapsed() / 60000),
                'numBksp': self.num_backspace
            }, ignore_index=True)

    def handle_sentence_finished(self):
        if self.text_edit.toPlainText().strip() == self.original_text.strip():
            self.add_log_entry(EventType.SENTENCE)
            self.sentence_timer_running = False
            self.text_edit.reset_auto_completion_stats()

            if self.current_sentence_index == len(self.sentence_list) - 1:
                self.df.to_csv(sys.stdout, index=False)
                self.ui.close()
            else:
                self.show_new_sentence()

        else:
            self.highlight_errors()

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
                print("yep")
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
