"""
/***************************************************************************
 graficofloodriskDialog
                                 A QGIS plugin
 Caricamento GeoDatabase, query sql e grafico
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
from PyQt4.QtCore import *
from PyQt4.QtGui import *
from PyQt4.QtGui import QImage
from PyQt4 import QtCore, QtGui
from qgis.core import *
from ui_caricadati import Ui_FloodRisk
import CreaGeodatabase
import CaricaGeodatiFloodRisk
import CaricaCurve
from qgis.gui import QgsGenericProjectionSelector
from pyspatialite import dbapi2 as db
from time import sleep
import sys
import os

from help import show_context_help

try:
    _fromUtf8 = QtCore.QString.fromUtf8
except AttributeError:
    def _fromUtf8(s):
        return s


class caricadatiDialog(QtGui.QDialog, Ui_FloodRisk):
    def __init__(self,iface):
        QtGui.QDialog.__init__(self)
        self.setupUi(self)
        self.iface=iface
        self.numEPGS = 32633
        self.label_loading.hide()
        self.label_sr.hide()
        self.FilesListGeoDati = ['', '', '', '', '', '']
        self.UpLoadGeoDati = [0, 0, 0, 0, 0, 0]
        self.FilesListCsv = ['', '', '', '', '', '']
        self.UpLoadCsv = [0, 0, 0, 0, 0, 0]
        self.nomeFileSQlite = str(self.txtShellFilePath.text())
        self.directoryPath=""


        # initialize actions
        QObject.connect(self.txtShellFilePath, SIGNAL("textChanged(QString)"), self.setNameFileSQlite)
        QObject.connect(self.btnChooseShellFile_1, SIGNAL("clicked()"), self.setFileSql)
        QObject.connect(self.btnChooseShellFile_2, SIGNAL("clicked()"), self.openSystem)
        QObject.connect(self.btnChooseShellFile_3, SIGNAL("clicked()"), self.loadingDB)
        #Shp
        QObject.connect(self.btnChooseShellFile_4, SIGNAL("clicked()"), self.setAreaStudio)
        QObject.connect(self.btnChooseShellFile_5, SIGNAL("clicked()"), self.setCensimento)
        QObject.connect(self.btnChooseShellFile_9, SIGNAL("clicked()"), self.setCensimentoXls)
        QObject.connect(self.btnChooseShellFile_6, SIGNAL("clicked()"), self.setBeniAreali)
        QObject.connect(self.btnChooseShellFile_7, SIGNAL("clicked()"), self.setBeniLineari)
        QObject.connect(self.btnChooseShellFile_8, SIGNAL("clicked()"), self.caricaGeoDati)
        self.checkBox.stateChanged.connect(self.setCheckAreaStud)
        self.checkBox_2.stateChanged.connect(self.setCheckCensimento)
        self.checkBox_3.stateChanged.connect(self.setCheckBA)
        self.checkBox_4.stateChanged.connect(self.setCheckBL)
        self.checkBox_All.stateChanged.connect(self.setCheckAll)
        #Csv
        QObject.connect(self.btnChooseShellFile_16, SIGNAL("clicked()"), self.setFatalityR)
        QObject.connect(self.btnChooseShellFile_17, SIGNAL("clicked()"), self.setFloodS)
        QObject.connect(self.btnChooseShellFile_21, SIGNAL("clicked()"), self.setTipoV)
        QObject.connect(self.btnChooseShellFile_18, SIGNAL("clicked()"), self.setVulnerabilita)
        QObject.connect(self.btnChooseShellFile_22, SIGNAL("clicked()"), self.setTipoCategoriaBeni)
        self.checkBox_9.stateChanged.connect(self.setCheckFatalityR)
        self.checkBox_10.stateChanged.connect(self.setCheckFloodS)
        self.checkBox_12.stateChanged.connect(self.setCheckTipoV)
        self.checkBox_11.stateChanged.connect(self.setCheckTipoVulnerabilita)
        self.checkBox_13.stateChanged.connect(self.setCheckTipoCategoriaBeni)
        self.checkBox_All_3.stateChanged.connect(self.setCheckAllCsv)
        QObject.connect(self.btnChooseShellFile_20, SIGNAL("clicked()"), self.caricaCurve)

        # help
        QObject.connect(self.buttonBox, SIGNAL(_fromUtf8("helpRequested()")), self.show_help)


    #------------- Actions -----------------------

    def show_help(self):
        """Load the help text into the system browser."""
        show_context_help(context='include2')

    def setNameFileSQlite(self):
        self.nomeFileSQlite =  str(self.txtShellFilePath.text())

    def setFileSql(self):
        self.nomeFileSQlite = QFileDialog.getSaveFileName(None, self.tr("FloodRisk | Make new Geodatabase Sqlite"), "", "FloodRisk File (*.sqlite)")
        if self.nomeFileSQlite!="":
            self.txtShellFilePath.setText(self.nomeFileSQlite)
            self.btnChooseShellFile_2.setEnabled(True)
            self.FilesListGeoDati[0] = self.nomeFileSQlite
            self.FilesListCsv[0] = self.nomeFileSQlite
            self.UpLoadGeoDati[0] = 1
            self.UpLoadCsv[0] = 1

    def loadingDB(self):
        NomeFileGDB= str(self.txtShellFilePath.text())
        if NomeFileGDB !="":
            self.label_loading.show()
            msg=self.tr("Start making")
            if os.path.exists(NomeFileGDB):
                msg1=self.tr("Attention file")
                msg2=self.tr("already exists: execution stopped")
                msg="%s %s %s" % (msg1,NomeFileGDB,msg2)
                QMessageBox.information(None, self.tr("Make Database"), msg)
            else:
                ok = CreaGeodatabase.main(self,NomeFileGDB)
                if ok:
                    QMessageBox.information(None, self.tr("Message"), self.tr("Sqlite file created"))
                else:
                    QMessageBox.information(None, self.tr("Message"), self.tr("Sqlite file error"))

            self.label_loading.hide()
            # check Reference System
            res, srid=self.CheckReferenceSystem()
            if res:
                msg=self.tr("Current Reference System :  EPSG=") + str(srid)
                QMessageBox.information(None, self.tr("Message"), msg)

        else:
            QMessageBox.information(None,  self.tr("Warning"), self.tr("You must first choose the Geodb.Sqlite's name"))


    def openSystem(self):
        projSelector = QgsGenericProjectionSelector()
        projSelector.exec_()
        a = projSelector.selectedCrsId()
        b = projSelector.selectedAuthId()
        if b == '':
            QMessageBox.information(None,  self.tr("Warning"), self.tr("Attention no Reference System selected"))
        else:
            self.numEPGS = int(str(b).split(':')[1])
            self.setSistemaRiferimento()
            self.label_sr.setText(self.tr("Reference System Loaded:  ") + b)
            self.label_sr.show()

    def setSistemaRiferimento(self):
        try:
            conn = db.connect(self.nomeFileSQlite)
            cur = conn.cursor()
            testoSql = 'UPDATE geometry_columns SET srid=%d' % (self.numEPGS)
            cur.execute(testoSql)
            conn.commit()
            cur=None
            conn.close()
        except:
            msg=self.tr("Attention: error in the definition of the reference system of the file ")  + self.nomeFileSQlite
            QMessageBox.information(None, self.tr("Setting Reference System"), msg)

    def setAreaStudio(self):
        self.nomeFileAreaStud = QFileDialog.getOpenFileName(None, self.tr("FloodRisk: select Analysis Area shapefile"), self.directoryPath, "FloodRisk File (*.shp)")
        if self.nomeFileAreaStud !="":
            self.comboBox.setEditText(self.nomeFileAreaStud)
            self.FilesListGeoDati[1] = self.nomeFileAreaStud
            self.UpLoadGeoDati[1] = 1
            self.directoryPath=os.path.dirname(self.FilesListGeoDati[1])

    def setCensimento(self):
        self.nomeFileCensimento = QFileDialog.getOpenFileName(None, self.tr("FloodRisk: select Census shapefile"), self.directoryPath, "FloodRisk File (*.shp)")
        if self.nomeFileCensimento !="" and self.checkBox_2.isChecked():
            self.comboBox_2.setEditText(self.nomeFileCensimento)
            self.FilesListGeoDati[2] = self.nomeFileCensimento
            self.UpLoadGeoDati[2] = 1
            self.directoryPath=os.path.dirname(self.FilesListGeoDati[2])

    def setCensimentoXls(self):
        self.nomeFileCensimentoXls = QFileDialog.getOpenFileName(None, self.tr("FloodRisk: select Census Table Data"), self.directoryPath, "FloodRisk File (*.csv)")
        if self.nomeFileCensimentoXls !="":
            self.txtShellFilePath_6.setText(self.nomeFileCensimentoXls)
            self.FilesListGeoDati[3] = self.nomeFileCensimentoXls
            self.UpLoadGeoDati[3] = 1
            self.directoryPath=os.path.dirname(self.FilesListGeoDati[3])

    def setBeniAreali(self):
        self.nomeFileBA = QFileDialog.getOpenFileName(None, self.tr("FloodRisk: select Estate Polygon shapefile"), self.directoryPath, "FloodRisk File (*.shp)")
        if self.nomeFileBA !="":
            self.comboBox_4.setEditText(self.nomeFileBA)
            self.FilesListGeoDati[4] = self.nomeFileBA
            self.UpLoadGeoDati[4] = 1
            self.directoryPath=os.path.dirname(self.FilesListGeoDati[4])

    def setBeniLineari(self):
        self.nomeFileBL = QFileDialog.getOpenFileName(None, self.tr("FloodRisk: select Infrastructures Line shapefile"), self.directoryPath, "FloodRisk File (*.shp)")
        if self.nomeFileBL !="":
            self.comboBox_5.setEditText(self.nomeFileBL)
            self.FilesListGeoDati[5] = self.nomeFileBL
            self.UpLoadGeoDati[5] = 1
            self.directoryPath=os.path.dirname(self.FilesListGeoDati[5])

    #-----Managing Check
    def setCheckAreaStud(self, state):
        if state == QtCore.Qt.Checked:
            self.btnChooseShellFile_4.setEnabled(True)
            self.comboBox.setEnabled(True)
            listaFile = self.caricaComboBox([QGis.Polygon])
            if len(listaFile) != 0:
                self.comboBox.clear()
                self.comboBox.addItems(listaFile)
        else:
            self.btnChooseShellFile_4.setEnabled(False)
            self.comboBox.setEnabled(False)
            self.comboBox.clear()

    def setCheckCensimento(self, state2):
        if state2 == QtCore.Qt.Checked:
            if self.checkAnalysisArea():
                self.btnChooseShellFile_5.setEnabled(True)
                self.txtShellFilePath_6.setEnabled(True)
                self.btnChooseShellFile_9.setEnabled(True)
                self.comboBox_2.setEnabled(True)
                listaFile = self.caricaComboBox([QGis.Polygon])
                if len(listaFile) != 0:
                    self.comboBox_2.clear()
                    self.comboBox_2.addItems(listaFile)
            else:
                self.msgAnalysisArea()
        else:
            self.btnChooseShellFile_5.setEnabled(False)
            self.txtShellFilePath_6.setEnabled(False)
            self.btnChooseShellFile_9.setEnabled(False)
            self.comboBox_2.setEnabled(False)
            self.comboBox_2.clear()


    def setCheckBA(self, state3):
        if state3 == QtCore.Qt.Checked:
            if self.checkAnalysisArea():
                self.btnChooseShellFile_6.setEnabled(True)
                self.comboBox_4.setEnabled(True)
                listaFile = self.caricaComboBox([QGis.Polygon])
                if len(listaFile) != 0:
                    self.comboBox_4.clear()
                    self.comboBox_4.addItems(listaFile)
            else:
                self.msgAnalysisArea()
        else:
            self.btnChooseShellFile_6.setEnabled(False)
            self.comboBox_4.setEnabled(False)
            self.comboBox_4.clear()

    def setCheckBL(self, state4):
        if state4 == QtCore.Qt.Checked:
            if self.checkAnalysisArea():
                self.btnChooseShellFile_7.setEnabled(True)
                self.comboBox_5.setEnabled(True)
                listaFile = self.caricaComboBox([QGis.Line])
                if len(listaFile) != 0:
                    self.comboBox_5.clear()
                    self.comboBox_5.addItems(listaFile)
            else:
                self.msgAnalysisArea()
        else:
            self.btnChooseShellFile_7.setEnabled(False)
            self.comboBox_5.setEnabled(False)
            self.comboBox_5.clear()

    def setCheckAll(self, stateAll):
        if stateAll == QtCore.Qt.Checked:
            self.btnChooseShellFile_7.setEnabled(True)
            self.checkBox_4.setChecked(True)
            self.btnChooseShellFile_6.setEnabled(True)
            self.checkBox_3.setChecked(True)
            self.btnChooseShellFile_5.setEnabled(True)
            self.checkBox_2.setChecked(True)

            self.txtShellFilePath_6.setEnabled(True)
            self.btnChooseShellFile_9.setEnabled(True)
            listaFile = self.caricaComboBox([QGis.Polygon])
            listaFile2 = self.caricaComboBox([QGis.Line])
            self.comboBox_5.clear()
            self.comboBox_5.addItems(listaFile2)
            self.comboBox_4.clear()
            self.comboBox_4.addItems(listaFile)
            self.comboBox_2.clear()
            self.comboBox_2.addItems(listaFile)
            self.comboBox.clear()
            self.comboBox.addItems(listaFile)
        else:
            self.btnChooseShellFile_7.setEnabled(False)
            self.checkBox_4.setChecked(False)
            self.btnChooseShellFile_6.setEnabled(False)
            self.checkBox_3.setChecked(False)
            self.btnChooseShellFile_5.setEnabled(False)
            self.checkBox_2.setChecked(False)
            self.checkBox.setChecked(False)
            self.txtShellFilePath_6.setEnabled(False)
            self.btnChooseShellFile_9.setEnabled(False)
            self.comboBox_5.clear()
            self.comboBox_4.clear()
            self.comboBox_2.clear()

    def setFatalityR(self):
        self.nomeFileFatalityR = QFileDialog.getOpenFileName(None, self.tr("FloodRisk: select Fatality Rate file"), self.directoryPath, "FloodRisk File (*.csv)")
        if self.nomeFileFatalityR !="":
            self.txtShellFilePath_12.setText(self.nomeFileFatalityR)
            self.FilesListCsv[1] = self.nomeFileFatalityR
            self.UpLoadCsv[1] = 1
            self.directoryPath=os.path.dirname(self.FilesListCsv[1])

    def setFloodS(self):
        self.nomeFileFloodS= QFileDialog.getOpenFileName(None, self.tr("FloodRisk: select Flood Severity file"), self.directoryPath, "FloodRisk File (*.csv)")
        if self.nomeFileFloodS !="":
            self.txtShellFilePath_13.setText(self.nomeFileFloodS)
            self.FilesListCsv[2] = self.nomeFileFloodS
            self.UpLoadCsv[2] = 1
            self.directoryPath=os.path.dirname(self.FilesListCsv[2])

    def setTipoV(self):
        self.nomeFileTipoV= QFileDialog.getOpenFileName(None, self.tr("FloodRisk: select List of Depth-Damage Curves file"), self.directoryPath, "FloodRisk File (*.csv)")
        if self.nomeFileTipoV !="":
            self.txtShellFilePath_16.setText(self.nomeFileTipoV)
            self.FilesListCsv[3] = self.nomeFileTipoV
            self.UpLoadCsv[3] = 1
            self.directoryPath=os.path.dirname(self.FilesListCsv[3])

    def setVulnerabilita(self):
        self.nomeFileVulnerabilita= QFileDialog.getOpenFileName(None, self.tr("FloodRisk: select Depth-Damage Curves file"), self.directoryPath, "FloodRisk File (*.csv)")
        if self.nomeFileVulnerabilita !="":
            self.txtShellFilePath_14.setText(self.nomeFileVulnerabilita)
            self.FilesListCsv[4] = self.nomeFileVulnerabilita
            self.UpLoadCsv[4] = 1
            self.directoryPath=os.path.dirname(self.FilesListCsv[4])

    def setTipoCategoriaBeni(self):
        self.nomeFileCatBeni= QFileDialog.getOpenFileName(None, self.tr("FloodRisk: select Occupacy Type file"), self.directoryPath, "FloodRisk File (*.csv)")
        if self.nomeFileCatBeni !="":
            self.txtShellFilePath_17.setText(self.nomeFileCatBeni)
            self.FilesListCsv[5] = self.nomeFileCatBeni
            self.UpLoadCsv[5] = 1
            self.directoryPath=os.path.dirname(self.FilesListCsv[5])

    def setCheckFatalityR(self, state):
        if state == QtCore.Qt.Checked:
            self.txtShellFilePath_12.setEnabled(True)
            self.btnChooseShellFile_16.setEnabled(True)
        else:
            self.txtShellFilePath_12.setEnabled(False)
            self.btnChooseShellFile_16.setEnabled(False)

    def setCheckFloodS(self, state):
        if state == QtCore.Qt.Checked:
            self.txtShellFilePath_13.setEnabled(True)
            self.btnChooseShellFile_17.setEnabled(True)
        else:
            self.txtShellFilePath_13.setEnabled(False)
            self.btnChooseShellFile_17.setEnabled(False)

    def setCheckTipoV(self, state):
        if state == QtCore.Qt.Checked:
            self.txtShellFilePath_16.setEnabled(True)
            self.btnChooseShellFile_21.setEnabled(True)
        else:
            self.txtShellFilePath_16.setEnabled(False)
            self.btnChooseShellFile_21.setEnabled(False)

    def setCheckTipoVulnerabilita(self, state):
        if state == QtCore.Qt.Checked:
            self.txtShellFilePath_14.setEnabled(True)
            self.btnChooseShellFile_18.setEnabled(True)
        else:
            self.txtShellFilePath_14.setEnabled(False)
            self.btnChooseShellFile_18.setEnabled(False)

    def setCheckTipoCategoriaBeni(self, state):
        if state == QtCore.Qt.Checked:
            self.txtShellFilePath_17.setEnabled(True)
            self.btnChooseShellFile_22.setEnabled(True)
        else:
            self.txtShellFilePath_17.setEnabled(False)
            self.btnChooseShellFile_22.setEnabled(False)

    def setCheckAllCsv(self, stateAll):
        if stateAll == QtCore.Qt.Checked:
            self.txtShellFilePath_12.setEnabled(True)
            self.btnChooseShellFile_16.setEnabled(True)
            self.checkBox_9.setChecked(True)
            self.txtShellFilePath_13.setEnabled(True)
            self.btnChooseShellFile_17.setEnabled(True)
            self.checkBox_10.setChecked(True)
            self.txtShellFilePath_16.setEnabled(True)
            self.btnChooseShellFile_21.setEnabled(True)
            self.checkBox_12.setChecked(True)
            self.txtShellFilePath_14.setEnabled(True)
            self.btnChooseShellFile_18.setEnabled(True)
            self.checkBox_11.setChecked(True)
            self.txtShellFilePath_17.setEnabled(True)
            self.btnChooseShellFile_22.setEnabled(True)
            self.checkBox_13.setChecked(True)
        else:
            self.txtShellFilePath_12.setEnabled(False)
            self.btnChooseShellFile_16.setEnabled(False)
            self.checkBox_9.setChecked(False)
            self.txtShellFilePath_13.setEnabled(False)
            self.btnChooseShellFile_17.setEnabled(False)
            self.checkBox_10.setChecked(False)
            self.txtShellFilePath_16.setEnabled(False)
            self.btnChooseShellFile_21.setEnabled(False)
            self.checkBox_12.setChecked(False)
            self.txtShellFilePath_14.setEnabled(False)
            self.btnChooseShellFile_18.setEnabled(False)
            self.checkBox_11.setChecked(False)
            self.txtShellFilePath_17.setEnabled(False)
            self.btnChooseShellFile_22.setEnabled(False)
            self.checkBox_13.setChecked(False)

    def caricaGeoDati(self):

        if self.CheckGeodatabase():
            if not self.checkAnalysisArea():
                self.msgAnalysisArea()
            else:
                self.label_loading.show()
                self.udateGeoFileLists()
                NotErr, errMsg = CaricaGeodatiFloodRisk.main(self,self.FilesListGeoDati, self.UpLoadGeoDati, self.progressBarGeo)
                if NotErr:
                    QMessageBox.information(None, "FloodRisk", self.tr("Files have been uploaded"))
                else:
                    QMessageBox.information(None, "FloodRisk", errMsg)
                self.label_loading.hide()
                res=self.checkAnalysisAreaReferenceSystem()

        else:
            QMessageBox.information(None, "FloodRisk", self.tr("You must first create the Geodb.Sqlite"))

    def caricaCurve(self):
        FileSql= str(self.txtShellFilePath.text())
        if (FileSql == ""):
            QMessageBox.information(None, "FloodRisk", self.tr("First load the DataBase"))
        else:
            if self.CheckGeodatabase():
                self.label_loading.show()
                NotErr, errMsg = CaricaCurve.main(self.FilesListCsv, self.UpLoadCsv)
                if NotErr:
                    QMessageBox.information(None, "FloodRisk", self.tr("Files have been uploaded"))
                else:
                    QMessageBox.information(None, "FloodRisk", errMsg)
                self.label_loading.hide()
            else:
                QMessageBox.information(None, "FloodRisk", self.tr("You must first create the Geodb.Sqlite"))


    def caricaComboBox(self, FeatureType):
        listAreaStudio = []
        listAreaStudio = self.getLayerSourceByMe(FeatureType)
        return listAreaStudio


    def getLayerSourceByMe(self, vTypes):
        import locale
        layermap = QgsMapLayerRegistry.instance().mapLayers()
        layerlist = []
        if vTypes == "all":
            for name, layer in layermap.iteritems():
                layerlist.append( layer.source() )
        else:
            for name, layer in layermap.iteritems():
                if layer.type() == QgsMapLayer.VectorLayer:
                    if layer.geometryType() in vTypes:
                        if layer.source()[-3:] == 'shp' :
                            layerlist.append( layer.source() )
                elif layer.type() == QgsMapLayer.RasterLayer:
                    if "Raster" in vTypes:
                        layerlist.append( layer.source() )
        return sorted( layerlist, cmp=locale.strcoll )

    def checkAnalysisArea(self):
        nome = self.comboBox.currentText()
        if nome != "":
            if os.path.exists(nome):
                res = bool('True')
                return res
            else:
                res = bool()
                return res
        else:
            mydb_path = str(self.txtShellFilePath.text())
            if os.path.exists(mydb_path):
                # creating/connecting the test_db
                conn = db.connect(mydb_path)
                # creating a Cursor
                cur = conn.cursor()
                NomeTabella='AnalysisArea'
                sql="SELECT AsText(geom) FROM %s;" % (NomeTabella)
                cur.execute(sql)
                GeomAreawkt=cur.fetchone()
                if GeomAreawkt != None:
                    res = bool('True')
                else:
                    res = bool('')
            else:
                res = bool('')
            return res


    def msgAnalysisArea(self):
        msg=self.tr("Please, upload firstly Analysis Area")
        QMessageBox.information(None, "Warning", msg)

    def udateGeoFileLists(self):

        nomeFileAreaStud = self.comboBox.currentText()
        state=self.checkBox.checkState()
        if len(nomeFileAreaStud)>0 and state == QtCore.Qt.Checked:
            self.FilesListGeoDati[1] = nomeFileAreaStud
            self.UpLoadGeoDati[1] = 1
        else:
            self.UpLoadGeoDati[1] = 0

        nomeFileCensimento = self.comboBox_2.currentText()
        state=self.checkBox_2.checkState()
        if len(nomeFileCensimento)>0 and state == QtCore.Qt.Checked:
            self.FilesListGeoDati[2] = nomeFileCensimento
            self.UpLoadGeoDati[2] = 1
        else:
            self.UpLoadGeoDati[2] = 0

        nomeFileCensimentoXls = self.txtShellFilePath_6.text()
        if len(nomeFileCensimentoXls)>0 and self.checkBox_2.isChecked():
            self.FilesListGeoDati[3] = nomeFileCensimentoXls
            self.UpLoadGeoDati[3] = 1
        else:
            self.UpLoadGeoDati[3] = 0

        nomeFileBA = self.comboBox_4.currentText()
        if len(nomeFileBA)>0 and self.checkBox_3.isChecked():
            self.FilesListGeoDati[4] = nomeFileBA
            self.UpLoadGeoDati[4] = 1
        else:
            self.UpLoadGeoDati[4] = 0

        nomeFileBL = self.comboBox_5.currentText()
        if len(nomeFileBL)>0 and self.checkBox_4.isChecked():
            self.FilesListGeoDati[5] = nomeFileBL
            self.UpLoadGeoDati[5] = 1
        else:
            self.UpLoadGeoDati[5] = 0


    def CheckGeodatabase(self):

        res=bool()

        if os.path.exists(self.FilesListGeoDati[0]):
            mydb_path=self.FilesListGeoDati[0]
            try:
                # creating/connecting the test_db
                conn = db.connect(mydb_path)
                # creating a Cursor
                cur = conn.cursor()

                TablesList=['spatial_ref_sys','AnalysisArea','CensusBlocks','FatalityRate']
                TablesList.append('FatalityRate')
                TablesList.append('FloodSeverity')
                TablesList.append('InfrastrLines')
                TablesList.append('VulnType')
                TablesList.append('Vulnerability')
                TablesList.append('StructurePoly')

                for NomeTabella in TablesList:
                    sql="SELECT sql FROM sqlite_master WHERE type='table' AND name='%s';" % (NomeTabella)
                    cur.execute(sql)
                    Tabella=str(cur.fetchone()[0])

                res=bool('True')
            except:
                res=bool()
        else:
            res=bool()
        return res


    def CheckReferenceSystem(self):
        res=bool()
        srid=0
        if os.path.exists(self.FilesListGeoDati[0]):
            mydb_path=self.FilesListGeoDati[0]
            try:
                # connecting the db
                conn = db.connect(mydb_path)
                # creating a Cursor
                cur = conn.cursor()
                NomeTabella='analysisarea'
                sql="SELECT srid FROM geometry_columns WHERE f_table_name='%s';" % (NomeTabella)
                cur.execute(sql)
                listasrid=cur.fetchone()
                srid=str(listasrid[0])
                res=bool('True')

            except:
                res=bool()
        else:
            res=bool()
        return res, srid

    def checkAnalysisAreaReferenceSystem(self):
        res = bool('')
        try:
            mydb_path = str(self.txtShellFilePath.text())
            if os.path.exists(mydb_path):
                # creating/connecting the test_db
                conn = db.connect(mydb_path)
                # creating a Cursor
                cur = conn.cursor()
                NomeTabella='AnalysisArea'
                sql="SELECT AsText(geom) FROM %s;" % (NomeTabella)
                cur.execute(sql)
                GeomAreawkt=cur.fetchone()
                if GeomAreawkt != None:
                    res = bool('True')
                    self.btnChooseShellFile_2.setEnabled(False)
                    # check Reference System
                    res, srid=self.CheckReferenceSystem()
                    if res:
                        self.numEPGS = int(srid)
                        msg=self.tr("Current Reference System :  EPSG=") + str(srid)
                        self.label_sr.setText(msg)
                        self.label_sr.show()

            else:
                res = bool('')
                self.btnChooseShellFile_2.setEnabled(True)
            return res
        except:
            res = bool('')
            self.btnChooseShellFile_2.setEnabled(True)
            return res


