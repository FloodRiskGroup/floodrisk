# -*- coding: utf-8 -*-
"""
/***************************************************************************
 graficofloodriskDialog
                                 A QGIS plugin

                             -------------------
        begin                : 2014-11-02
        copyright            : (C) 2014 by RSE
        email                : FloodRiskGroup@rse-web.it
 ***************************************************************************/

/***************************************************************************
 *                                                                         *
 *   This program is free software; you can redistribute it and/or modify  *
 *   it under the terms of the GNU General Public License as published by  *
 *   the Free Software Foundation; either version 2 of the License, or     *
 *   (at your option) any later version.                                   *
 *                                                                         *
 ***************************************************************************/
"""

from PyQt4 import QtCore, QtGui
from ui_graficofloodrisk import Ui_graficofloodrisk

from PyQt4.QtCore import *
from PyQt4.QtGui import *
from qgis.core import *
import os.path
import sqlite3
try:
    from pylab import *
    from matplotlib.font_manager import FontProperties
except:
    pass

from PyQt4.QtGui import QAction, QIcon, QApplication, QMessageBox
from qgis.gui import *


# create the dialog for zoom to point


class graficofloodriskDialog(QtGui.QDialog, Ui_graficofloodrisk):
    def __init__(self, iface, idTipo, tipo):
        QtGui.QDialog.__init__(self)
        self.iface=iface
        self.idTipo=idTipo
        self.tipo = tipo
        self.setupUi(self)
        self.mdl = QStandardItemModel(0, 5)

    def run(self):
        # Create the dialog (after translation) and keep reference
        self.showIt()
        # self.mdl = QStandardItemModel(0, 5)
        self.setFileGDB()
        # Run the dialog event loop
        QObject.connect(self.pushButton_2, SIGNAL("clicked()"), self.setFileGDB2)
        QObject.connect(self.pushButton, SIGNAL("clicked()"), self.querySql)
        QObject.connect(self.tableView,SIGNAL("clicked(QModelIndex)"), self.onClick)
        QObject.connect(self, SIGNAL( "closed(PyQt_PyObject)" ), self.cleaning2)

        self.show()
        result = self.exec_()
        # See if OK was pressed
        if result == 1:
            self.cleaning2()
            # do something useful (delete the line containing pass and
            # substitute with your code)
            pass

    def showIt(self):
        #TableWiew thing
        self.tableView.setModel(self.mdl)
        self.tableView.setColumnWidth(0, 35)
        self.tableView.setColumnWidth(1, 35)
        #self.tableView.setColumnWidth(2, 20)
        self.tableView.setColumnWidth(2, 100)
        self.tableView.setColumnWidth(3, 350)
        hh = self.tableView.horizontalHeader()
        hh.setStretchLastSection(True)
        self.tableView.setColumnHidden(4 , True)
        self.mdl.setHorizontalHeaderLabels(["ST","CN","Code","Description"])
        #self.checkBox.setEnabled(False)
        txt1=self.tr("Type Depth-Damage Curve: ")
        self.label_2.setText(txt1 + self.tipo)

    def cleaning2(self):        #used when Dock dialog is closed
                self.mdl = None

    def setFileGDB2(self):
        FileGDBPath = QFileDialog.getOpenFileName(self, "Select geodatabase", \
        ".", "File sqlite (*.sqlite);;All files (*.*)")
        #".", "File mdb (*.mdb);;All files (*.*)", "Filter list for selecting files from a dialog box")
        self.lineEdit.setText(FileGDBPath)
        conn = sqlite3.connect(FileGDBPath, detect_types=sqlite3.PARSE_DECLTYPES|sqlite3.PARSE_COLNAMES)
        cursor = conn.cursor()
        if self.lineEdit.displayText() == "":
            QMessageBox.information(None, "Info", "Load GeoDataBase")
        if self.lineEdit.displayText() != "":
            self.codDesk={}
            self.deskCod={}
            self.dannoNum={}
            self.numDanno={}
            self.codTipoDanno=[]

            NomeTabella='NomiDomains'
            sql='SELECT NumDomain FROM '+ NomeTabella
            sql+=" WHERE (NomeDomain='OccupancyType');"
            numDom=cursor.execute(sql).fetchone()[0]

            NomeTabella2='NomiDomains'
            sql='SELECT NumDomain FROM '+ NomeTabella2
            sql+=" WHERE (NomeDomain='DamageType');"
            numDom2=cursor.execute(sql).fetchone()[0]

            NomeTabella='Domains'
            sql='SELECT code,Description FROM '+ NomeTabella
            sql+=' WHERE (NumDomain=%d);' % (numDom)
            records=cursor.execute(sql).fetchall()

            NomeTabella2='Domains'
            sql='SELECT code,Description FROM '+ NomeTabella2
            sql+=' WHERE (NumDomain=%d);' % (numDom2)
            records2=cursor.execute(sql).fetchall()

            Codici=[]
            Descrizione=[]
            Codici2=[]
            Descrizione2=[]

            if records!=None:
                for rec in records:
                    Codici.append(rec[0])
                    Descrizione.append(rec[1])
                    self.codDesk[rec[0]]=rec[1]
                    self.deskCod[rec[1]]=rec[0]
            if records2 !=None:
                for rec in records2:
                    Codici2.append(rec[0])
                    self.codTipoDanno.append(rec[1])
                    Descrizione2.append(rec[1])
                    self.dannoNum[int(rec[0])]=rec[1]
                    self.numDanno[rec[1]]=int(rec[0])

            testoSQL = 'SELECT OccuType FROM Vulnerability'
            testoSQL += ' WHERE VulnID = %d' % self.idTipo
            testoSQL += ' GROUP BY OccuType;'
            cursor.execute(testoSQL)
            Lista=cursor.fetchall()
            if Lista != None:
                ListaBeni=[]
                for rec in Lista:
                    ListaBeni.append(self.codDesk[rec[0]])
                # Adding Occupacy type to tableView
                for bene in ListaBeni:
                    row = self.mdl.rowCount()
                    self.mdl.insertRow(row)
                    self.mdl.setData( self.mdl.index(row, 0, QModelIndex())  ,False, Qt.CheckStateRole)
                    self.mdl.item(row,0).setFlags(Qt.ItemIsSelectable)
                    self.mdl.setData( self.mdl.index(row, 1, QModelIndex())  ,False, Qt.CheckStateRole)
                    self.mdl.item(row,1).setFlags(Qt.ItemIsSelectable)
                    self.mdl.setData( self.mdl.index(row, 2, QModelIndex())  ,self.deskCod[bene])
                    self.mdl.item(row,2).setFlags(Qt.NoItemFlags)
                    self.mdl.setData( self.mdl.index(row, 3, QModelIndex())  ,bene)
                    self.mdl.item(row,3).setFlags(Qt.NoItemFlags)
                self.mdl.setHorizontalHeaderLabels(["ST","CN","Code","Description"])
                self.tableView.setModel(self.mdl)

            testoSQL2='SELECT DmgType FROM Vulnerability'
            testoSQL2 += ' WHERE VulnID = %d' % self.idTipo
            testoSQL2 += ' GROUP BY DmgType;'
            cursor.execute(testoSQL2)
            Lista2=cursor.fetchall()
            if Lista2 != None:
                ListaDanno=[]
                for rec in Lista2:
                    ListaDanno.append(self.dannoNum[rec[0]])

    def setFileGDB(self):
        if self.lineEdit.displayText() == "":
            null
        if self.lineEdit.displayText()!="":
            FileGDBPath=str(self.lineEdit.text())
        conn = sqlite3.connect(FileGDBPath, detect_types=sqlite3.PARSE_DECLTYPES|sqlite3.PARSE_COLNAMES)
        cursor = conn.cursor()
        if self.lineEdit.displayText() == "":
            QMessageBox.information(None, "Info", "Load GeoDataBase")
        if self.lineEdit.displayText() != "":
            self.codDesk={}
            self.deskCod={}
            self.dannoNum={}
            self.numDanno={}
            self.codTipoDanno=[]

            NomeTabella='NomiDomains'
            sql='SELECT NumDomain FROM '+ NomeTabella
            sql+=" WHERE (NomeDomain='OccupancyType');"
            numDom=cursor.execute(sql).fetchone()[0]

            NomeTabella2='NomiDomains'
            sql='SELECT NumDomain FROM '+ NomeTabella2
            sql+=" WHERE (NomeDomain='DamageType');"
            numDom2=cursor.execute(sql).fetchone()[0]

            NomeTabella='Domains'
            sql='SELECT code,Description FROM '+ NomeTabella
            sql+=' WHERE (NumDomain=%d);' % (numDom)
            records=cursor.execute(sql).fetchall()

            NomeTabella2='Domains'
            sql='SELECT code,Description FROM '+ NomeTabella2
            sql+=' WHERE (NumDomain=%d);' % (numDom2)
            records2=cursor.execute(sql).fetchall()

            Codici=[]
            Descrizione=[]
            Codici2=[]
            Descrizione2=[]

            if records!=None:
                for rec in records:
                    Codici.append(rec[0])
                    Descrizione.append(rec[1])
                    self.codDesk[rec[0]]=rec[1]
                    self.deskCod[rec[1]]=rec[0]
            if records2 !=None:
                for rec in records2:
                    # select only structure and content
                    if int(rec[0])>0:
                        Codici2.append(rec[0])
                        self.codTipoDanno.append(rec[1])
                        Descrizione2.append(rec[1])
                        self.dannoNum[int(rec[0])]=rec[1]
                        self.numDanno[rec[1]]=int(rec[0])

            testoSQL='SELECT OccuType FROM Vulnerability GROUP BY OccuType;'
            cursor.execute(testoSQL)
            Lista=cursor.fetchall()
            if Lista != None:
                ListaBeni=[]
                for rec in Lista:
                    ListaBeni.append(self.codDesk[rec[0]])
                for bene in ListaBeni:
                    row = self.mdl.rowCount()
                    self.mdl.insertRow(row)
                    self.mdl.setData( self.mdl.index(row, 0, QModelIndex())  ,False, Qt.CheckStateRole)
                    self.mdl.item(row,0).setFlags(Qt.ItemIsSelectable)
                    self.mdl.setData( self.mdl.index(row, 1, QModelIndex())  ,False, Qt.CheckStateRole)
                    self.mdl.item(row,1).setFlags(Qt.ItemIsSelectable)
                    self.mdl.setData( self.mdl.index(row, 2, QModelIndex())  ,self.deskCod[bene])
                    self.mdl.item(row,2).setFlags(Qt.NoItemFlags)
                    self.mdl.setData( self.mdl.index(row, 3, QModelIndex())  ,bene)
                    self.mdl.item(row,3).setFlags(Qt.NoItemFlags)
                self.mdl.setHorizontalHeaderLabels(["ST","CN","Code","Description"])
                self.tableView.setModel(self.mdl)

            testoSQL2='SELECT DmgType FROM Vulnerability GROUP BY DmgType;'
            cursor.execute(testoSQL2)
            Lista2=cursor.fetchall()
            if Lista2 != None:
                ListaDanno=[]
                for rec in Lista2:
                    ListaDanno.append(self.dannoNum[rec[0]])



    def onClick(self,index1):                 #action when clicking the tableview
        temp = self.mdl.itemFromIndex(index1)
        if index1.column()== 0:                #modifying checkbox
            booltemp = temp.data(Qt.CheckStateRole)
            if booltemp == True:
                booltemp = False
            else:
                booltemp = True
            self.mdl.setData( self.mdl.index(temp.row(), 0, QModelIndex())  ,booltemp, Qt.CheckStateRole)
        elif index1.column()== 1:                #modifying checkbox
            booltemp = temp.data(Qt.CheckStateRole)
            if booltemp == True:
                booltemp = False
            else:
                booltemp = True
            self.mdl.setData( self.mdl.index(temp.row(), 1, QModelIndex())  ,booltemp, Qt.CheckStateRole)

        else :
            return


    def querySql(self):
        if self.lineEdit.displayText() == "":
            QMessageBox.information(None, "Info", "Load GeoDataBase")
        try:
            fontp=FontProperties()
            if self.lineEdit.displayText() != "":
                DBFile=str(self.lineEdit.text())
                #connecting to sqlite
                conn = sqlite3.connect(DBFile, detect_types=sqlite3.PARSE_DECLTYPES|sqlite3.PARSE_COLNAMES)
                ListaTipiBeni = []
                fontp=FontProperties()
                fontp.set_size('small')
                txt=self.tr('Chart Depth-Damage Curve')
                txt1=self.tr("Type Curve : ") + self.tipo
                nomiLegenda=[]
                # Cycle on the damage to the structure curves
                if len(self.codTipoDanno) > 0:
                    TipoDanno=self.codTipoDanno[0]
                    # Manage multiselection
                    for i in range(0 , self.mdl.rowCount()):
                        if self.mdl.item(i,0).data(Qt.CheckStateRole):
                            TipoBene = self.mdl.item(i,3).text()
                            ListaTipiBeni.append(TipoBene)
                            nome='%s - damage to  %s' % (TipoBene, TipoDanno)
                            nomiLegenda.append(nome)

                    TipoDanno=self.numDanno[TipoDanno]
                    for TipoBene in ListaTipiBeni:
                        TipoBene=self.deskCod[TipoBene]

                        testoSQL="SELECT HydroValue,Damage FROM Vulnerability where"
                        testoSQL += " OccuType='%s'" % TipoBene
                        testoSQL += ' and DmgType=%s' %  TipoDanno
                        testoSQL += ' and VulnType=1'
                        testoSQL += ' and VulnID=%d' % self.idTipo
                        testoSQL += ' ORDER BY HydroValue;'
                        cursor = conn.cursor()
                        cursor.execute(testoSQL)
                        TabVuln=cursor.fetchall()
                        if TabVuln!= None:
                            LimAlt=[]
                            Danno=[]
                            for rec in TabVuln:
                                LimAlt.append(rec[0])
                                Danno.append(rec[1])
                                numerolim=len(LimAlt)

                    #--------------------------------------------------------------------------
                    #--------------Draw the Chart------------------------------------------------
                    #--------------------------------------------------------------------------
                        y=Danno
                        x=[]
                        x_prec=0
                        for z in LimAlt:
                            if z != 9999.0:
                                x_prec=z
                                x.append(z)
                            else:
                                x.append(x_prec * 1.1)

                        plot(x,y)
                        hold(True)

                # Cycle on the damage to the content curves
                if len(self.codTipoDanno) > 1:
                    TipoDanno=self.codTipoDanno[1]
                    ListaTipiBeni=[]
                    for i in range(0 , self.mdl.rowCount()):
                        if self.mdl.item(i,1).data(Qt.CheckStateRole):
                            TipoBene = self.mdl.item(i,3).text()
                            ListaTipiBeni.append(TipoBene)
                            nome='%s - damage to  %s' % (TipoBene, TipoDanno)
                            nomiLegenda.append(nome)

                    TipoDanno=self.numDanno[TipoDanno]
                    for TipoBene in ListaTipiBeni:
                        TipoBene=self.deskCod[TipoBene]

                        testoSQL="SELECT HydroValue,Damage FROM Vulnerability where"
                        testoSQL += " OccuType='%s'" % TipoBene
                        testoSQL += ' and DmgType=%s' %  TipoDanno
                        testoSQL += ' and VulnType=1'
                        testoSQL += ' and VulnID=%d' % self.idTipo
                        testoSQL += ' ORDER BY HydroValue;'
                        cursor = conn.cursor()
                        cursor.execute(testoSQL)
                        TabVuln=cursor.fetchall()
                        if TabVuln!= None:
                            LimAlt=[]
                            Danno=[]
                            for rec in TabVuln:
                                LimAlt.append(rec[0])
                                Danno.append(rec[1])
                                numerolim=len(LimAlt)
                        #--------------------------------------------------------------------------
                        #--------------Draw the Chart------------------------------------------------
                        #--------------------------------------------------------------------------
                        y=Danno
                        x=[]
                        x_prec=0
                        for z in LimAlt:
                            if z != 9999.0:
                                x_prec=z
                                x.append(z)
                            else:
                                x.append(x_prec * 1.1)

                        plot(x,y,'--')
                        hold(True)


                xlabel(self.tr("Water depth (m)"))
                ylabel(self.tr('Damage (%)'))
                posizioneLegend='best'
                legend(nomiLegenda, posizioneLegend, prop=fontp)
                suptitle(txt,fontsize=14)
                title(txt1,fontsize=12)
                limy=ylim()
                y1=limy[0]
                y2=limy[1] * 1.1
                lim=[y1,y2]
                ylim(lim)
                grid()
                show()
        except:
            QMessageBox.information(None, "Warning", "The current version of QGIS does not allow import matplotlib")

