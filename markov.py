# -*- coding: utf-8 -*-
"""
Created on Thu Sep 13 09:12:15 2012

@author: FL232714
"""
import codecs
import random
import xml.etree.ElementTree as ET
import sys
from PyQt4 import QtGui, QtCore

class Markov(object):
    def __init__(self, filename):
        self.database = {}
        self.letter_tree = ET.Element("root")
        self.filename = filename
        self.words = self.file_to_words()
        self.generate_database()
        self.generate_nested_dict()
        
    def file_to_words(self):
        source_file = codecs.open(self.filename, 'r', 'utf-8')
        data = source_file.read()
        words = data.split()
        return words
    
    def doubles(self):
        if len(self.words) < 2:
            return
        for i in xrange(len(self.words) - 2):
            yield(self.words[i], self.words[i + 1])
    
    def generate_database(self):
        for word1, word2 in self.doubles():
            if word1 in self.database:
                self.database[word1].append(word2)
            else:
                self.database[word1] = [word2]
            
    def generate_markov_text(self, size=25):
        seed = random.randint(0, len(self.words) - 1)
        seed_word = self.words[seed]
        generated_text = [seed_word]
        for i in xrange(size):
            next_word = random.choice(self.database[seed_word])
            generated_text.append(next_word)
            seed_word = next_word
        return ' '.join(generated_text)

    def generate_nested_dict(self):
        for word in self.words:
            word = word + " "
            current_elem = self.letter_tree
            for letter in word:
                found = False
                for child in current_elem.findall("letter"):
                    if child.text == letter:
                        found = True
                        child.set("freq", child.get("freq") + 1)
                        current_elem = child
                        break
                if not found:
                    new_elem = ET.Element("letter")
                    new_elem.set("freq", 1)
                    new_elem.text = letter                    
                    current_elem.append(new_elem)
                    current_elem = new_elem

                
    def get_next_letters(self, word):
        current_elem = self.letter_tree        
        for letter in word:
            found = False
            for elem in current_elem.getchildren():
                if elem.text == letter:
                    found = True
                    current_elem = elem
                    break
            if not found:
                # la chaîne n'existe pas
                return []
        if found:
            # on va afficher les possibilités
            freq_dict = sorted(zip([x.text for x in current_elem.getchildren()],
                             [x.get("freq") for x in current_elem.getchildren()]),
                              key=lambda entry: entry[1])
                              
            #return freq_dict[-5:][::-1]
            return freq_dict[::-1]

    def build_tree(self, word):
        next_letters = self.get_next_letters(word)
        if next_letters == []:
            return [word]
        else: 
            output = []
            for letter in next_letters:
                tree = self.build_tree(word + letter[0])
                for element in tree:
                    output.append(element)
            
        return output
        
    def build_weighted_tree(self, word, weight):
        next_letters = self.get_next_letters(word)
        if next_letters == []:
            return [(word, weight)]
        else:
            output = []
            for elem in next_letters:
                tree = self.build_weighted_tree(word + elem[0], weight + elem[1])
                for node in tree:
                    output.append(node)
        return output
    
    def autocomplete(self, word):
        tree = self.build_weighted_tree(word, 0)
        sorted_tree = sorted(tree,
                              key=lambda entry: entry[1])
        return sorted_tree[::-1][:5]
            
class FlowLayout(QtGui.QLayout):
    def __init__(self, parent=None, margin=0, spacing=-1):
        super(FlowLayout, self).__init__(parent)

        if parent is not None:
            self.setMargin(margin)

        self.setSpacing(spacing)

        self.itemList = []

    def __del__(self):
        item = self.takeAt(0)
        while item:
            item = self.takeAt(0)

    def addItem(self, item):
        self.itemList.append(item)

    def count(self):
        return len(self.itemList)

    def itemAt(self, index):
        if index >= 0 and index < len(self.itemList):
            return self.itemList[index]

        return None

    def takeAt(self, index):
        if index >= 0 and index < len(self.itemList):
            return self.itemList.pop(index)

        return None

    def expandingDirections(self):
        return QtCore.Qt.Orientations(QtCore.Qt.Orientation(0))

    def hasHeightForWidth(self):
        return True

    def heightForWidth(self, width):
        height = self.doLayout(QtCore.QRect(0, 0, width, 0), True)
        return height

    def setGeometry(self, rect):
        super(FlowLayout, self).setGeometry(rect)
        self.doLayout(rect, False)

    def sizeHint(self):
        return self.minimumSize()

    def minimumSize(self):
        size = QtCore.QSize()

        for item in self.itemList:
            size = size.expandedTo(item.minimumSize())

        size += QtCore.QSize(2 * self.margin(), 2 * self.margin())
        return size

    def doLayout(self, rect, testOnly):
        x = rect.x()
        y = rect.y()
        lineHeight = 0

        for item in self.itemList:
            wid = item.widget()
            spaceX = self.spacing() + wid.style().layoutSpacing(QtGui.QSizePolicy.PushButton, QtGui.QSizePolicy.PushButton, QtCore.Qt.Horizontal)
            spaceY = self.spacing() + wid.style().layoutSpacing(QtGui.QSizePolicy.PushButton, QtGui.QSizePolicy.PushButton, QtCore.Qt.Vertical)
            nextX = x + item.sizeHint().width() + spaceX
            if nextX - spaceX > rect.right() and lineHeight > 0:
                x = rect.x()
                y = y + lineHeight + spaceY
                nextX = x + item.sizeHint().width() + spaceX
                lineHeight = 0

            if not testOnly:
                item.setGeometry(QtCore.QRect(QtCore.QPoint(x, y), item.sizeHint()))

            x = nextX
            lineHeight = max(lineHeight, item.sizeHint().height())

        return y + lineHeight - rect.y()
 
class InteractiveTextEdit(QtGui.QWidget):
    def __init__(self):
        super(InteractiveTextEdit, self).__init__()
        self.initUI()
        self.init_data()
        self.init_slots()

    def initUI(self):
        text_edit = QtGui.QTextEdit()
        self.text_edit = text_edit
        
        prediction_widget = FlowLayout()
        self.prediction_widget = prediction_widget
        prediction_widget.addWidget(QtGui.QPushButton("Short"))
        
        sub_layout = QtGui.QVBoxLayout()
        sub_layout.addWidget(text_edit)
        
        main_layout = QtGui.QVBoxLayout()
        main_layout.addLayout(sub_layout)
        main_layout.addLayout(prediction_widget)
        
        self.setLayout(main_layout)
        self.show()
    
    def init_data(self):
        self.markov = markov_load()
        self.last_word = QtCore.QString("")
        
    def init_slots(self):
        QtCore.QObject.connect(self.text_edit, QtCore.SIGNAL('textChanged()'), self.on_text_changed)
                
    def on_text_changed(self):
        for i in range(self.prediction_widget.count())[::-1]:
                item = self.prediction_widget.itemAt(i).widget()
                if isinstance(item, QtGui.QWidget):
                    self.prediction_widget.removeWidget(item)
                    item.hide()
                    item.close()
                    item.destroy()
        text = self.text_edit.toPlainText()
        regexp = QtCore.QRegExp("[ \n]")
        splits = text.split(regexp)
        current_word = splits[-1]
        
        if current_word == QtCore.QString("") and self.last_word.size() > 1:
            #autocomplete case
            suggestion = self.markov.autocomplete(self.last_word)[0]
            if suggestion != None:
                text.chop(self.last_word.size() + 1)
                text.append(suggestion[0].trimmed() + " ")
                self.last_word = QtCore.QString("")
                cursor = self.text_edit.textCursor()
                self.text_edit.setPlainText(text)
                self.text_edit.setTextCursor(cursor)
                
            #suggestion process after inserting word
            key = unicode(suggestion[0].trimmed())
            if key in self.markov.database.keys():
                for item in self.markov.database[key]:
                    self.prediction_widget.addWidget(QtGui.QLabel(item))
                    
        if current_word.size() > 1:
            #suggestion process after typing letter
            if self.markov != None:
                suggestions = self.markov.autocomplete(current_word)
                if suggestions != None:
                    for item in suggestions:
                        self.prediction_widget.addWidget(QtGui.QLabel(QtCore.QStringList([item[0], str(item[1])]).join(" ")))
            
        self.last_word = current_word
        
        
def markov_main():
    markov = Markov("mousquetaires_chapitre1.txt")
    #markov = Markov("mousquetaires.txt")
    keys = markov.database.keys()
    text = markov.generate_markov_text(30)
    print text
    word = u"au"
    print markov.build_tree(word)
    print markov.build_weighted_tree(word, 0)
    print markov.autocomplete(word)
    return markov
    
def markov_load():
    markov = Markov("mousquetaires_chapitre1.txt")
    return markov
    
def pyqt_main():    
    app = QtGui.QApplication(sys.argv)
    ex = InteractiveTextEdit()
    sys.exit(app.exec_())           
           
           
if __name__ == '__main__':
    #markov = markov_main()
    pyqt_main()