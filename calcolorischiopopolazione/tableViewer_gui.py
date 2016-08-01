# -*- coding: utf-8 -*-
#-----------------------------------------------------------
#
# Table Manager
# Copyright (C) 2008-2011 Borys Jurgiel
#
#-----------------------------------------------------------
#
# licensed under the terms of GNU GPL 2
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License along
# with this program; if not, print to the Free Software Foundation, Inc.,
# 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301 USA.
#
#---------------------------------------------------------------------

from PyQt4.QtCore import *
from PyQt4.QtGui import *
from qgis.core import *
from qgis.gui import *
from ui_tableViewer import Ui_Dialog
#from tableManagerUiRename import Ui_Rename
#from tableManagerUiClone import Ui_Clone
#from tableManagerUiInsert import Ui_Insert
import sys
import os
# to reading cvs file
import csv
import locale

def checkNumRowsFromCSV(pathToCsvFile,sep):
    ok=False
    try :
        with open(pathToCsvFile, 'rb') as csvfile:
            reader = csv.reader(csvfile, delimiter=sep, quotechar='"')
            headers = reader.next()
            numheaders=len(headers)
            if numheaders>1:
                row = reader.next()
                numrow=len(row)
                if numheaders==numrow:
                    ok=True
    except:
        pass
    return ok

def check_csv_separator(pathToCsvFile):

    locale.setlocale(locale.LC_ALL, '') # set to user's locale, not "C"
    dec_pt_chr = locale.localeconv()['decimal_point']
    if dec_pt_chr == ",":
        list_delimiter = ";"
    else:
        list_delimiter = ","

    check1=checkNumRowsFromCSV(pathToCsvFile,list_delimiter)

    if not check1:
        if list_delimiter==',':
            list_delimiter=';'
        elif list_delimiter==';':
            list_delimiter=','
        check2 = checkNumRowsFromCSV(pathToCsvFile,list_delimiter)
        if not check2:
            list_delimiter=' '

    return list_delimiter

########## CLASS TableManager ##############################

class TableViewer(QDialog, Ui_Dialog):

  def __init__(self, iface, NomeFile):
    QDialog.__init__(self)
    self.iface = iface
    self.setupUi(self)
    # nome del file
    self.NomeFile = NomeFile
    #self.layer = self.iface.activeLayer()
    #self.provider = self.layer.dataProvider()
    #self.fields = self.readFields( self.provider.fields() )
    #self.isUnsaved = False  # No unsaved changes yet
    #if self.provider.storageType() == 'ESRI Shapefile': # Is provider saveable?
    #  self.isSaveable = True
    #else:
    #  self.isSaveable = False

    self.needsRedraw = True # Preview table is redrawed only on demand. This is for initial drawing.
    self.lastFilter = None
    self.selection = -1     # Don't highlight any field on startup
    self.selection_list = [] #Update: Santiago Banchero 09-06-2009

    #QObject.connect(self.butUp, SIGNAL('clicked()'), self.doMoveUp)
    #QObject.connect(self.butDown, SIGNAL('clicked()'), self.doMoveDown)
    #QObject.connect(self.butDel, SIGNAL('clicked()'), self.doDelete)
    #QObject.connect(self.butIns, SIGNAL('clicked()'), self.doInsert)
    #QObject.connect(self.butClone, SIGNAL('clicked()'), self.doClone)
    #QObject.connect(self.butRename, SIGNAL('clicked()'), self.doRename)
    #QObject.connect(self.butSave, SIGNAL('clicked()'), self.doSave)
    #QObject.connect(self.butSaveAs, SIGNAL('clicked()'), self.doSaveAs)
    #QObject.connect(self.buttonBox, SIGNAL('rejected()'), self.doDone)
    #QObject.connect(self.fieldsTable, SIGNAL('itemSelectionChanged ()'), self.selectionChanged)
    QObject.connect(self.tabWidget, SIGNAL('currentChanged (int)'), self.drawDataTable)

    msg='Table Viewer:'+self.NomeFile
    self.setWindowTitle(self.tr(msg))
    #self.setWindowTitle(self.tr('Table Viewer: %1').arg(self.NomeFile))
    #self.setWindowTitle(self.tr('Table Manager: %1').arg(self.layer.name()))
    #self.progressBar.setValue(0)
    #self.restoreCfg()
    #self.drawFieldsTable()
    ok=self.readData(NomeFile)
    if ok:
        self.drawDataTable(1)


  def readData(self,NomeFile): # Reads data from file into the 'data' list [[column1] [column2] [column3]...]

    self.NomeFile=NomeFile
    abil=bool()

    if os.path.exists(self.NomeFile):

        # field separator
        sep=check_csv_separator(self.NomeFile)

        # count the number of records
        filcsv=open(self.NomeFile,'r')
        riga=filcsv.readline()
        steps=0
        progress = unicode('Reading data ') # As a progress bar is used the main window's status bar, because the own one is not initialized yet
        for rec in filcsv:
            if len(rec)>0:
                steps=steps+1
        stepp = steps / 10
        if stepp == 0:
          stepp = 1
        filcsv.close()

        # Reading csv file
        finp = open(self.NomeFile)
        csv_reader = csv.reader(finp, delimiter=sep, quotechar='"')
        headers = csv_reader.next()
        self.fields=[]
        for p in headers:
            self.fields.append(p)

        self.data = []
        numfields=len(self.fields)
        for i in range(numfields):
          self.data += [[]]

        n = 0
        self.numRows=0
        for kk in range(steps):
            record=csv_reader.next()
            nn=min(numfields,len(record))
            for i in range(nn):
                self.data[i] += [record[i]]

            n += 1
            self.numRows+=1
            if n % stepp == 0:
                progress +=unicode("|")
                self.iface.mainWindow().statusBar().showMessage(progress)
        abil=bool("true")
        finp.close()

    else:
        txt1=self.tr('Warning the file')
        txt2=self.tr('does not exists')
        msg='%s\n\n %s\n\n %s' % (txt1,self.NomeFile,txt2)
        QMessageBox.information(None, "Fine input", msg)


    self.iface.mainWindow().statusBar().showMessage('')
    return abil


##    self.NomeFile=NomeFile
##    abil=bool()
##    if os.path.exists(self.NomeFile):
##        filcsv=open(self.NomeFile,'r')
##        riga=filcsv.readline()
##        testo=riga[:-1]
##        pp=str.split(testo,';')
##        self.fields=[]
##        for p in pp:
##            self.fields.append(p)
##        self.data = []
##        for i in range(len(self.fields)):
##          self.data += [[]]
##        steps=0
##        for rec in filcsv:
##            if len(rec)>0:
##                steps=steps+1
##        #steps = self.provider.featureCount()
##        stepp = steps / 10
##        if stepp == 0:
##          stepp = 1
##        #progress = self.tr('Reading data ') # As a progress bar is used the main window's status bar, because the own one is not initialized yet
##        progress = unicode('Reading data ') # As a progress bar is used the main window's status bar, because the own one is not initialized yet
##        filcsv.close()
##        filcsv=open(self.NomeFile,'r')
##        riga=filcsv.readline()
##        n = 0
##        self.numRows=0
##        for kk in range(steps):
##            riga=filcsv.readline()[:-1]
##            attrs=str.split(riga,';')
##            for i in range(len(attrs)):
##                self.data[i] += [attrs[i]]
##
##            n += 1
##            self.numRows+=1
##            if n % stepp == 0:
##                progress +=unicode("|")
##                self.iface.mainWindow().statusBar().showMessage(progress)
##        abil=bool("true")
##
##    else:
##        msg='Attenzione il file %s: non esiste ' % self.NomeFile
##        QMessageBox.information(None, "Fine input", msg)
##
##
##    self.iface.mainWindow().statusBar().showMessage('')
##    return abil


  def drawDataTable(self,tab): # Called when user switches tabWidget to the Table Preview
    #if tab != 1 or self.needsRedraw == False: return
    if self.needsRedraw == False: return
    fields = self.fields
    self.dataTable.clear()
    self.repaint()
    self.dataTable.setColumnCount(len(fields))
    self.dataTable.setRowCount(self.numRows)
    #msg=str(self.numRows)
    #QMessageBox.information(None, "Numero di righe", msg)

    #self.dataTable.setRowCount(self.provider.featureCount())
    #header = QStringList()
    header = []
    #for i in fields.values():
    #  header.append(i.name())
    for field in fields:
      header.append(field)
    self.dataTable.setHorizontalHeaderLabels(header)
    self.progressBar.setRange (0, len(self.data)+1)
    #self.progressBar.setFormat(QString(self.tr('Drawing table') +': %p%'))
    self.progressBar.setFormat(self.tr('Drawing table') +': %p%')
    formatting = True
    if formatting: # slower procedure, with formatting the table items
      for i in range(len(self.data)):
        self.progressBar.setValue(i+1)
        for j in range(len(self.data[i])):
          item = QTableWidgetItem(unicode(self.data[i][j] or 'NULL'))
          item.setFlags(Qt.ItemIsSelectable)
          #if fields[i].type() == 6 or fields[i].type() == 2:
          item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
          self.dataTable.setItem(j,i,item)
    else: # about 25% faster procedure, without formatting
      for i in range(len(self.data)):
        self.progressBar.setValue(i+1)
        for j in range(len(self.data[i])):
          self.dataTable.setItem(j,i,QTableWidgetItem(unicode(self.data[i][j] or 'NULL')))
    self.dataTable.resizeColumnsToContents()
    self.needsRedraw = False
    self.progressBar.reset()


