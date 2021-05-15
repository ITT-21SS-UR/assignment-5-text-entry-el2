% Interaction Technology and Techniques  
  Assignment 5: Text Input
% Summer semester 2021
% **Submission due: Wednesday, 19. May 2021, 23:55**

**Hand in in groups of max. two.**

Goals of this assignment
========================

* get an overview of the state of the art in pointing / text entry research
* learn more about QT signals and slots
* get some more experience with PyQt and graphical applications
* learn how to design a novel interaction technique
* perform a small experiment


5.1: Get an overview of current research in text entry / pointing
===================================================================

a) Read [MacKenzie, I. S., & Soukoreff, R. W. (2002). Text entry for mobile computing: Models and methods, theory and practice. Human-Computer Interaction, 17, 147-198.](http://www.yorku.ca/mack/hci3.html) and provide a short summary (1000-2000 characters) of the paper in your own words, focusing on practically relevant topics.

b) The CHI conference is the most important annual scientific conference in the area of human-computer interaction.
Watch the CHI 2021 showreel[^chi2021_reel] and find three examples of research on novel interfaces or interaction techniques for text entry or pointing.
Find the papers online and provide a short summary of each (max. 5 sentences) in your own words.

Hand in the following files:

**mobile-text-entry.txt**: a plain text file containing a summary of the MacKenzie & Soukoreff paper.

**chi-2021-research.txt**: a plain text file containing short summaries of three papers from CHI 2021.

[^chi2021_reel]: <https://www.youtube.com/playlist?list=PLqhXYFYmZ-Vc-oiiwfAcE46XlYVdHQkG_>

Points
------------

* **1** contains comments highlighting work distribution
* **3** good, interesting summary of the MacKenzie & Soukoreff paper.
* **3** good, concise summaries of the CHI papers



5.2: Design and implement a tool for measuring text entry speed
==============================================================

Implement a tool that allows for measuring and logging typing speed (i.e., a window with an editable textbox).

* download the example file textedit.py and adjust it.
* test data should be logged to stdout (not to a file) in CSV format (see <http://www.cse.yorku.ca/~stevenc/tema/> for best practices of logging such data). 
* the application should measure how long it takes to write a sentence (delimited at the end with a newline) and each individual word. Find out how to best define *beginning/end of word/sentence* (and when to start/stop measuring the time). 
* you do not need to log typing errors for this assignment
* log appropriate data for the following events (indicate which event you are logging as the first field in the log data):
    * key pressed 
    * word typed
    * sentence typed
    * test finished (all sentences typed) 
* informally test whether your tool works as expected

Hand in the following file:

**text_entry_speed_test.py**: a Python/PyQt script implementing a typing speed test.

Points
------------

* **1** Script conforms to PEP8, is well structured and includes comments
* **2** Script works as expected
* **2** Script outputs sensible and valid CSV data
* **1** Script contains comments highlighting work distribution


5.3: Design and implement a method for faster text input
======================================================

Extend the tool from assignment 5.2 to enable an efficient input method, either: 

* chord input: if the user simultaneously presses multiple keys, they act as a *chord* and produce a single word (or multiple) - e.g.,. by pressing 'a', 's', and 'd' simultaneously, the word "das" is entered.
* autocompletion: once the user has typed a few letters, an autocompletion hint is shown which the user may accept (hint: have a look at `QCompleter`).
* support placeholders that are automatically replaced with configurable text (e.g., `$DATE` gets replaced with `11. 1. 2021`, `$MFG` gets replaced with `Mit freundlichen Grüßen, NN`)
* another potentially efficient input method of your own choosing (please discuss your idea with us).


**Hints for chord input:**

- You want to intercept all key events and only emit (new) key events once the buttons are released again.
- You might want to have a look at `QObject.installEventFilter()`. 
- Furthermore, you might want to make sure to intercept only those key events coming from the keyboard, not the ones your filter emits later on. Check out the attributes of the `QKeyEvent` class. 
- You might need ` Qt.qApp.postEvent()` for emitting new key events.
- Be aware of auto-repeat.

Hand in the following file:

**text_input_technique.py**: a Python/PyQt script implementing the aforementioned input method.

Points
------------

* **1** Script contains comments highlighting work distribution
* **1** Script conforms to PEP8, is well structured and includes comments and does not print out errors
* **3** Sensible selection of input technique and implementation details
* **3** Robust and extensible integration of input technique in code



5.4: Evaluate and document your input method
=============================================

Conduct a user study comparing the performance of your novel input method to unenhanced keyboard input.
Create a report (max 4 pages) describing your input method and its evaluation.

Hand in the following files:

**text_input.pdf**: a report containing a thorough description of your input method, including design decisions and limitations, technical implementation, and results of your evaluation.

**demo.mp4**: a short video (max. 30 seconds) showcasing your novel input method

Points
-------

* **2** Good video
* **3** Study design includes sensible methodology
* **3** Sensible evaluation including statistical tests and thorough interpretation


Submission 
=========================================
Submit via GRIPS until the deadline

All files should use UTF-8 encoding and Unix line breaks.
Python files should use spaces instead of tabs.

                                                               Have Fun!
