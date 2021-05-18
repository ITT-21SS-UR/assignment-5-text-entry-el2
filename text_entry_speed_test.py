#!/usr/bin/python
# -*- coding: utf-8 -*-

"""
This file expects three arguments:
- A .txt file containing the sentences that should be displayed (separated by new line)
- A user ID (Integer)
- Either 0 or 1, depending on if the helper should be disabled or enabled (0 = disabled, 1 = enabled)

Opens a Widget that implements a typing speed test. Upon completion the logged data is printed on stdout.
The workload was evenly distributed between the two team members.

Authors: ev, lj
"""

import sys
from PyQt5 import QtGui, QtCore, QtWidgets, uic
from enum import Enum
import pandas as pd
from datetime import datetime
from text_input_technique import TextEdit

CSV_HEADER = ["event", "user_id", "timestamp", "helper_enabled", "time_taken_in_ms", "auto_completed", "auto_completion_count",
              "wpm", "numBksp"]


class EventType(Enum):
    """
    Enum used to differentiate between the different input events for logging.
    """
    LETTER = 1
    WORD = 2
    SENTENCE = 3
    FINISHED = 4


class ExtendedTextEdit(QtWidgets.QTextEdit):
    """
    Class that extends QTextEdit.
    Adds a new signal and intercepts keypresses of the "Return" key.
    """

    key_pressed_signal = QtCore.pyqtSignal(QtGui.QKeyEvent)

    def __init__(self, parent=None):
        super(ExtendedTextEdit, self).__init__(parent)

    def keyPressEvent(self, event):
        self.key_pressed_signal.emit(event)

        if event.key() != QtCore.Qt.Key_Return:
            super().keyPressEvent(event)


class SuperText(QtWidgets.QTextEdit):
    """
    Central class for this experiment.
    """

    sentence_list = []
    original_text = ""
    user_id = 0
    helper_enabled = False
    text_edit = ()
    completer = ()

    def __init__(self):
        super(SuperText, self).__init__()
        self.ui = uic.loadUi('text_entry_ui.ui')
        self.user_input_layout = self.ui.userInputLayout
        self.text_changed_by_user = True
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
        """
        Initializes the UI elements and decides which user text input widget should be added,
        depending on whether or not the helper is enabled
        authors: ev, lj
        """
        self.setWindowTitle('Typing Speed Test')
        self.setFocusPolicy(QtCore.Qt.StrongFocus)
        self.setMouseTracking(True)
        self.ui.originalText.setFont(QtGui.QFont('Calterra', 20))
        self.ui.originalText.setText(self.original_text)
        self.ui.keyPressEvent = self.keyPressEvent

        if self.helper_enabled:
            self.text_edit = TextEdit(self)
            self.init_completer()
        else:
            self.text_edit = ExtendedTextEdit(self)

        self.text_edit.setFont(QtGui.QFont('Calterra', 20))

        self.ui.userInputLayout.addWidget(self.text_edit)
        self.text_edit.key_pressed_signal.connect(self.handle_key_pressed)
        self.text_edit.textChanged.connect(self.handle_text_changed)
        self.ui.show()

    def parse_setup(self):
        """
        Parses the passed arguments and assigns the values to the class variables
        author: ev
        """

        if len(sys.argv) is not 4:
            print("Please pass a .txt file with sentences, a user ID, and a number that designates whether or not the "
                  "helper should be enabled (0 = disabled, 1 = enabled)")

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

            try:
                helper_arg = int(sys.argv[3])

                if helper_arg == 1:
                    self.helper_enabled = True
                elif helper_arg == 0:
                    self.helper_enabled = False
                else:
                    print("Please pass either 0 or 1 as a third parameter for helper activation!")
            except ValueError:
                print("Please pass either 0 or 1 as a third parameter for helper activation!")

    def init_completer(self):
        """
        Initializes the QCompleter with the list of words from the passed sentence list, and attaches it to the TextEdit
        author: lj
        """
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

    def handle_text_changed(self):
        """
        Handle changes in the input TextEdit
        authors: ev, lj
        """
        if not self.text_changed_by_user:
            # prevent infinite loops caused by text changes in automatic error highlighting
            return

        if not self.sentence_timer_running:
            # start all timers
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

        self.highlight_errors()

    def add_log_entry(self, event_type):
        """
        Appends log entries to the dataframe
        :param event_type: the type of event that should be logged
        authors: ev, lj
        """
        if event_type == EventType.LETTER:
            self.df = self.df.append({
                'event': "key_press",
                'user_id': self.user_id,
                'timestamp': datetime.now(),
                'helper_enabled': self.helper_enabled,
                'time_taken_in_ms': self.key_timer.elapsed(),
                'auto_completed': self.text_edit.auto_completed if self.helper_enabled else False,
                'auto_completion_count': self.text_edit.auto_completion_count if self.helper_enabled else 0,
                'wpm': None,
                'numBksp': self.num_backspace
            }, ignore_index=True)

        if event_type == EventType.WORD:
            self.df = self.df.append({
                'event': "word",
                'user_id': self.user_id,
                'timestamp': datetime.now(),
                'helper_enabled': self.helper_enabled,
                'time_taken_in_ms': self.word_timer.elapsed(),
                'auto_completed': self.text_edit.auto_completed if self.helper_enabled else False,
                'auto_completion_count': self.text_edit.auto_completion_count if self.helper_enabled else 0,
                'wpm': self.word_count / (self.sentence_timer.elapsed() / 60000),
                'numBksp': self.num_backspace
            }, ignore_index=True)

        if event_type == EventType.SENTENCE:
            self.df = self.df.append({
                'event': "sentence",
                'user_id': self.user_id,
                'timestamp': datetime.now(),
                'helper_enabled': self.helper_enabled,
                'time_taken_in_ms': self.sentence_timer.elapsed(),
                'auto_completed': self.text_edit.auto_completed if self.helper_enabled else False,
                'auto_completion_count': self.text_edit.auto_completion_count if self.helper_enabled else 0,
                'wpm': self.word_count / (self.sentence_timer.elapsed() / 60000),
                'numBksp': self.num_backspace
            }, ignore_index=True)

    def handle_sentence_finished(self):
        """
        When the sentence is finished, check if it was entered correctly.
        If yes, show the next sentence or finish the experiment when all sentences were shown.
        author: lj
        """
        self.text_changed_by_user = False
        if self.text_edit.toPlainText().strip() == self.original_text.strip():
            self.add_log_entry(EventType.SENTENCE)
            self.sentence_timer_running = False

            if self.current_sentence_index == len(self.sentence_list) - 1:
                self.df.to_csv(sys.stdout, index=False)
                self.ui.close()
            else:
                self.show_new_sentence()

    def handle_key_pressed(self, event):
        self.text_changed_by_user = True

        if event.key() == QtCore.Qt.Key_Return:
            self.handle_sentence_finished()

        if event.key() == QtCore.Qt.Key_Backspace:
            self.num_backspace += 1
            self.last_character_entered = "backspace"
            self.add_log_entry(EventType.LETTER)
            self.key_timer.restart()

    def highlight_errors(self):
        """
        Highlight errors with a red background as the user is typing.
        This is done by matching the current user input against the current original sentence.
        The highlighting is case sensitive
        author: lj
        """
        self.text_changed_by_user = False      # set this to False in order to not trigger an infinite loop
        text_format = QtGui.QTextCharFormat()
        text_format.setBackground(QtGui.QBrush(QtGui.QColor("white")))
        cursor = self.text_edit.textCursor()

        user_text = self.text_edit.toPlainText()
        original_text = self.original_text

        # reset the highlighting
        cursor.setPosition(0)
        cursor.movePosition(QtGui.QTextCursor.EndOfBlock, 1)
        cursor.mergeCharFormat(text_format)

        # mark current errors
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
        """
        Update the current sentence and reset logging stats
        author: ev
        """
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
