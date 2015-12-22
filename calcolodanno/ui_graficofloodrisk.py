# -*- coding: utf-8 -*-

# Form implementation generated from reading ui file 'ui_graficofloodrisk.ui'
#
# Created: Fri Mar 06 22:29:10 2015
#      by: PyQt4 UI code generator 4.11.3
#
# WARNING! All changes made in this file will be lost!

from PyQt4 import QtCore, QtGui

try:
    _fromUtf8 = QtCore.QString.fromUtf8
except AttributeError:
    def _fromUtf8(s):
        return s

try:
    _encoding = QtGui.QApplication.UnicodeUTF8
    def _translate(context, text, disambig):
        return QtGui.QApplication.translate(context, text, disambig, _encoding)
except AttributeError:
    def _translate(context, text, disambig):
        return QtGui.QApplication.translate(context, text, disambig)

class Ui_graficofloodrisk(object):
    def setupUi(self, graficofloodrisk):
        graficofloodrisk.setObjectName(_fromUtf8("graficofloodrisk"))
        graficofloodrisk.resize(646, 510)
        self.buttonBox = QtGui.QDialogButtonBox(graficofloodrisk)
        self.buttonBox.setGeometry(QtCore.QRect(230, 470, 161, 41))
        self.buttonBox.setOrientation(QtCore.Qt.Horizontal)
        self.buttonBox.setStandardButtons(QtGui.QDialogButtonBox.Cancel|QtGui.QDialogButtonBox.Ok)
        self.buttonBox.setObjectName(_fromUtf8("buttonBox"))
        self.pushButton = QtGui.QPushButton(graficofloodrisk)
        self.pushButton.setGeometry(QtCore.QRect(10, 450, 121, 31))
        self.pushButton.setObjectName(_fromUtf8("pushButton"))
        self.pushButton_2 = QtGui.QPushButton(graficofloodrisk)
        self.pushButton_2.setGeometry(QtCore.QRect(550, 30, 81, 23))
        self.pushButton_2.setObjectName(_fromUtf8("pushButton_2"))
        self.lineEdit = QtGui.QLineEdit(graficofloodrisk)
        self.lineEdit.setGeometry(QtCore.QRect(60, 30, 481, 20))
        self.lineEdit.setObjectName(_fromUtf8("lineEdit"))
        self.label = QtGui.QLabel(graficofloodrisk)
        self.label.setGeometry(QtCore.QRect(60, 10, 161, 16))
        self.label.setObjectName(_fromUtf8("label"))
        self.label_4 = QtGui.QLabel(graficofloodrisk)
        self.label_4.setGeometry(QtCore.QRect(10, 30, 51, 20))
        self.label_4.setObjectName(_fromUtf8("label_4"))
        self.tableView = QtGui.QTableView(graficofloodrisk)
        self.tableView.setGeometry(QtCore.QRect(10, 120, 621, 321))
        self.tableView.setObjectName(_fromUtf8("tableView"))
        self.label_5 = QtGui.QLabel(graficofloodrisk)
        self.label_5.setGeometry(QtCore.QRect(10, 100, 221, 16))
        self.label_5.setObjectName(_fromUtf8("label_5"))
        self.label_2 = QtGui.QLabel(graficofloodrisk)
        self.label_2.setGeometry(QtCore.QRect(10, 70, 531, 16))
        self.label_2.setObjectName(_fromUtf8("label_2"))

        self.retranslateUi(graficofloodrisk)
        QtCore.QObject.connect(self.buttonBox, QtCore.SIGNAL(_fromUtf8("accepted()")), graficofloodrisk.accept)
        QtCore.QObject.connect(self.buttonBox, QtCore.SIGNAL(_fromUtf8("rejected()")), graficofloodrisk.reject)
        QtCore.QMetaObject.connectSlotsByName(graficofloodrisk)

    def retranslateUi(self, graficofloodrisk):
        graficofloodrisk.setWindowTitle(_translate("graficofloodrisk", "graficofloodrisk", None))
        self.pushButton.setText(_translate("graficofloodrisk", "Draw the chart", None))
        self.pushButton_2.setText(_translate("graficofloodrisk", "Browse...", None))
        self.label.setText(_translate("graficofloodrisk", "SpatiaLite Geodatabase", None))
        self.label_4.setText(_translate("graficofloodrisk", "Directory:", None))
        self.label_5.setText(_translate("graficofloodrisk", "Select  Occupacy Type and Type of Damage", None))
        self.label_2.setText(_translate("graficofloodrisk", "Depth-Damage Curves Type:", None))

