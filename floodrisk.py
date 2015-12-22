# -*- coding: utf-8 -*-
"""
/***************************************************************************
 Floodrisk
                                 A QGIS plugin
 Floodrisk
                              -------------------
        begin                : 2014-11-28
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
# Import the PyQt and QGIS libraries
from PyQt4.QtCore import *
from PyQt4.QtGui import *
from qgis.core import *
# Initialize Qt resources from file resources.py
import resources
# Import the code for the dialog
from creaprogetto.creaprogettodialog import creaprogettoDialog
from calcolodanno.calcolodannodialog import calcolodannoDialog
from calcolorischiopopolazione.calcolorischiopopolazionedialog import calcolorischiopopolazioneDialog
from caricadati.caricadatidialog import caricadatiDialog
from help import show_context_help
from xml.dom import minidom
from xml.dom.minidom import Document

import os.path


class Floodrisk:

    def __init__(self, iface):
        # Save reference to the QGIS interface
        self.iface = iface
        # initialize plugin directory
        self.plugin_dir = os.path.dirname(__file__)
        # initialize locale
        locale = QSettings().value("locale/userLocale")[0:2]
        localePath = os.path.join(self.plugin_dir, 'i18n', 'floodrisk_{}.qm'.format(locale))

        if os.path.exists(localePath):
            self.translator = QTranslator()
            self.translator.load(localePath)

            if qVersion() > '4.3.3':
                QCoreApplication.installTranslator(self.translator)

        # Create the dialog (after translation) and keep reference
        self.dialog = creaprogettoDialog(self.iface)
        self.dialog2 = caricadatiDialog(self.iface)
        self.dialog3 = calcolodannoDialog(self.iface)
        self.dialog4 = calcolorischiopopolazioneDialog(self.iface)

        self.FileGridPopRisk=""
        self.FileTable1=""
        self.FileTable2=""
        self.FileGridDamages=""
        self.FileGridVulnerability=""

        # Parameters
        self.Param1=''
        self.Param2=''
        self.Param3=''
        self.Param4=''
        self.startxml()

    def initGui(self):

        #---Create Toolbar-------------------------------------------
        self.toolbar = self.iface.addToolBar('FloodRisk')
        self.toolbar.setObjectName('FloodRiskToolBar')
        # 1----------------------------------------------------------
        self.toolbarCreaProgetto = QAction(
            QIcon(':/plugins/floodrisk/icons/1fp.png'), \
            'Project', self.iface.mainWindow())
        self.toolbarCreaProgetto.setObjectName('ToolBarCreaProgetto')
        self.toolbarCreaProgetto.setCheckable(False)
        self.toolbarCreaProgetto.triggered.connect(self.showToolbarCreaProgetto)
        self.toolbar.addAction(self.toolbarCreaProgetto)
        # 2----------------------------------------------------------
        self.toolbarCaricaDati = QAction(
            QIcon(':/plugins/floodrisk/icons/2db.png'), \
            'Database Manager', self.iface.mainWindow())
        self.toolbarCaricaDati.setObjectName('ToolBarLoadData')
        self.toolbarCaricaDati.setCheckable(False)
        self.toolbarCaricaDati.triggered.connect(self.showToolbarCaricaDati)
        self.toolbar.addAction(self.toolbarCaricaDati)
        # 3-----------------------------------------------------------
        self.toolbarCalcoloDanno = QAction(
            QIcon(':/plugins/floodrisk/icons/3ei.png'), \
            'Damage Assessment', self.iface.mainWindow())
        self.toolbarCalcoloDanno.setObjectName('ToolBarDamage')
        self.toolbarCalcoloDanno.setCheckable(False)
        self.toolbarCalcoloDanno.triggered.connect(self.showToolbarCalcoloDanno)
        self.toolbar.addAction(self.toolbarCalcoloDanno)
        # 4-----------------------------------------------------------
        self.toolbarCalcoloPopolazione = QAction(
            QIcon(':/plugins/floodrisk/icons/4lol.png'), \
            'Population Consequences Assessment', self.iface.mainWindow())
        self.toolbarCalcoloPopolazione.setObjectName('ToolBarPopulation')
        self.toolbarCalcoloPopolazione.setCheckable(False)
        self.toolbarCalcoloPopolazione.triggered.connect(self.showToolbarCalcoloPopolazione)
        self.toolbar.addAction(self.toolbarCalcoloPopolazione)
        # 5-----------------------------------------------------------
        self.toolbar5 = QAction(
            QIcon(':/plugins/floodrisk/icons/5h.png'), \
            'Help', self.iface.mainWindow())
        self.toolbar5.setObjectName('Help')
        self.toolbar5.setCheckable(False)
        self.toolbar5.triggered.connect(self.show_help)
        self.toolbar.addAction(self.toolbar5)

        self.iface.addPluginToMenu("Floodrisk", self.toolbarCreaProgetto)
        self.iface.addPluginToMenu("Floodrisk", self.toolbarCaricaDati)
        self.iface.addPluginToMenu("Floodrisk", self.toolbarCalcoloDanno)
        self.iface.addPluginToMenu("Floodrisk", self.toolbarCalcoloPopolazione)
        self.iface.addPluginToMenu("Floodrisk", self.toolbar5)

    def unload(self):
        # Remove the plugin menu item and icon
        self.iface.removePluginMenu("Floodrisk", self.toolbarCreaProgetto)
        self.iface.removePluginMenu("Floodrisk", self.toolbarCaricaDati)
        self.iface.removePluginMenu("Floodrisk", self.toolbarCalcoloDanno)
        self.iface.removePluginMenu("Floodrisk", self.toolbarCalcoloPopolazione)
        self.iface.removePluginMenu("Floodrisk", self.toolbar5)


    def startxml (self):
        #starting xml file reading
        fileprogetto=str(self.dialog.txtShellFilePath.text())
        if fileprogetto!="":

            # Reset Output filenames
            self.FileGridDamages=''
            self.FileGridVulnerability=''
            self.FileTable1=''
            self.FileGridPopRisk=''
            self.FileTable2=''

            xmlfile=open(fileprogetto)
            dom=minidom.parse(xmlfile)
            for node in dom.getElementsByTagName("General"):
                L = node.getElementsByTagName("File")
                for node2 in L:
                    Button = node2.getAttribute("Button")
                    nome = node2.getAttribute("name")
                    if Button=='FileGeodatabase':
                        pass
                    elif Button=='FilePeakFloodDepth':
                        pass
                    elif Button=='FilePeakFloodVelocity':
                        pass
                    elif Button=='FileWarningTime':
                        pass
                    # output economic damage assessment
                    elif Button=='FileGridDamages':
                        self.FileGridDamages=nome
                    elif Button=='FileGridVulnerability':
                        self.FileGridVulnerability=nome
                    elif Button=='FileTable1':
                        self.FileTable1=nome
                    # output Damage to Population
                    elif Button=='FileGridPopRisk':
                        self.FileGridPopRisk=nome
                    elif Button=='FileTable2':
                        self.FileTable2=nome

            self.Param1=''
            self.Param2=''
            self.Param3=''
            self.Param4=''
            self.Param5=''

            for node in dom.getElementsByTagName("Parameters"):
                L = node.getElementsByTagName("Parameter")
                for node2 in L:
                    Param = node2.getAttribute("Param")
                    Value = node2.getAttribute("Value")
                    if Param=='CurveType':
                        self.Param1=Value
                    if Param=='Method':
                        self.Param2=Value
                    if Param=='Understand':
                        self.Param3=Value
                    if Param=='LOL':
                        self.Param4=Value
                    if Param=='TotalDamage':
                        self.Param5=Value

            xmlfile.close()


    def showToolbarCreaProgetto(self):
        #Populate comboBox del "Water depth and velocity" with raster
        fileprogetto=self.dialog.txtShellFilePath.text()
        self.dialog.comboBox_2.clear()
        self.dialog.comboBox_3.clear()
        self.dialog.comboBox_4.clear()
        self.dialog.startxml()
        indice = self.dialog.comboBox_2.count() + 1
        indice2 = self.dialog.comboBox_3.count() + 1
        layermap = QgsMapLayerRegistry.instance().mapLayers()
        for ( name, layer ) in layermap.iteritems():
            if layer.type() == QgsMapLayer.RasterLayer:
                self.dialog.comboBox_2.addItem( layer.source())
                self.dialog.comboBox_3.addItem( layer.source())
        #Populate comboBox del "Warning time" with vector
        import qgis.core as qgis
        if os.path.exists(fileprogetto):
            self.dialog.startXmlForShp()
            listTempiPreavviso = []
            listTempiPreavviso = self.getLayerSourceByMe([qgis.QGis.Polygon])
            self.dialog.comboBox_4.addItems(listTempiPreavviso)
            self.dialog.txtShellFilePath.setText(fileprogetto)


        #Run the window
        self.dialog.exec_()

    def showToolbarCaricaDati(self):
        geoDataBase=str(self.dialog.txtShellFilePath_2.text())
        if geoDataBase!="":
            self.dialog2.txtShellFilePath.setText(geoDataBase)
            self.dialog2.FilesListGeoDati[0] = geoDataBase
            self.dialog2.FilesListCsv[0] = geoDataBase
            self.dialog2.UpLoadGeoDati[0] = 1
            self.dialog2.UpLoadCsv[0] = 1
            res=self.dialog2.checkAnalysisAreaReferenceSystem()
        else:
            self.dialog2.txtShellFilePath.setText('')
            self.dialog2.FilesListGeoDati[0] = ''
            self.dialog2.FilesListCsv[0] = ''
            self.dialog2.UpLoadGeoDati[0] = 0
            self.dialog2.UpLoadCsv[0] = 0
        #Run the window
        self.dialog2.exec_()

    def showToolbarCalcoloDanno(self):

        # Load project file xml
        self.startxml()

        fileprogetto=str(self.dialog.txtShellFilePath.text())
        geoDataBase=str(self.dialog.txtShellFilePath_2.text())
        altezzAcqua=self.dialog.comboBox_2.currentText()
        if fileprogetto!="":
            self.dialog3.txtShellFilePath.setText(fileprogetto)
        if geoDataBase!="":
            self.dialog3.txtShellFilePath_2.setText(geoDataBase)
        if altezzAcqua!="":
            self.dialog3.txtShellFilePath_3.setText(altezzAcqua)

        # Reset Output file names
        self.dialog3.txtShellFilePath_5.setText('')
        self.dialog3.txtShellFilePath_vulnerato.setText('')
        self.dialog3.txtShellFilePath_6.setText('')

        # check output Economic Damage Layer
        msg=str(self.dialog3.txtShellFilePath_5.text())

        if msg=="":
            if self.FileGridDamages=="":
                aa=str(altezzAcqua)
                if os.path.exists(aa):
                    DirOut=os.path.dirname(aa)
                    Name=os.path.basename(aa)
                    pp=str.split(Name,'.')
                    FileDannoPath=DirOut+os.sep + pp[0]+'_dmg.tif'
                    self.dialog3.txtShellFilePath_5.setText(FileDannoPath)
            else:
                self.dialog3.txtShellFilePath_5.setText(self.FileGridDamages)

        msg=str(self.dialog3.txtShellFilePath_6.text())
        if msg=="":
            if self.FileTable1=="":
                aa=str(altezzAcqua)
                if os.path.exists(aa):
                    DirOut=os.path.dirname(aa)
                    Name=os.path.basename(aa)
                    pp=str.split(Name,'.')
                    FileTabDannoPath=DirOut+os.sep + pp[0]+'_dmg.csv'
                    self.dialog3.txtShellFilePath_6.setText(FileTabDannoPath)
            else:
                self.dialog3.txtShellFilePath_6.setText(self.FileTable1)

        msg=str(self.dialog3.txtShellFilePath_vulnerato.text())
        if msg=="":
            if self.FileGridVulnerability=="":
                aa=str(altezzAcqua)
                if os.path.exists(aa):
                    DirOut=os.path.dirname(aa)
                    Name=os.path.basename(aa)
                    pp=str.split(Name,'.')
                    FileVulnPath=DirOut+os.sep + pp[0]+'_vuln.tif'
                    self.dialog3.txtShellFilePath_vulnerato.setText(FileVulnPath)
            else:
                self.dialog3.txtShellFilePath_vulnerato.setText(self.FileGridVulnerability)

        #dialog.exec_()  Set for Modal
        self.dialog3.luci()

        self.dialog3.setListaTipoCurvaVuln()
        # set currentItem CurveType for dialog3
        self.dialog3.setCurrentCurveType(self.Param1)
        self.dialog3.show()
        result = self.dialog3.exec_()
        if result == 1:
            pass

    def showToolbarCalcoloPopolazione(self):

        # Load project file xml
        self.startxml()

        fileprogetto=str(self.dialog.txtShellFilePath.text())
        geoDataBase=str(self.dialog.txtShellFilePath_2.text())
        altezzAcqua=self.dialog.comboBox_2.currentText()
        velocitAcqua=self.dialog.comboBox_3.currentText()
        tempiPreavviso=self.dialog.comboBox_4.currentText()

        if fileprogetto!="":
            self.dialog4.txtShellFilePath.setText(fileprogetto)
        if geoDataBase!="":
            self.dialog4.txtShellFilePath_2.setText(geoDataBase)
        if altezzAcqua!="":
            self.dialog4.txtShellFilePath_3.setText(altezzAcqua)
        if velocitAcqua !="":
            self.dialog4.txtShellFilePath_velocita.setText(velocitAcqua)
        if tempiPreavviso !="":
            self.dialog4.txtShellFilePath_tempi.setText(tempiPreavviso)

        # Reset Output file names
        self.dialog4.txtShellFilePath_4.setText('')
        self.dialog4.txtShellFilePath_7.setText('')


        msg=str(self.dialog4.txtShellFilePath_4.text())
        if msg=="":
            if self.FileGridPopRisk=="":
                aa=str(altezzAcqua)
                DirOut=os.path.dirname(aa)
                Name=os.path.basename(aa)
                pp=str.split(Name,'.')
                FileGridPopPath=DirOut+os.sep + pp[0]+'_pop.tif'
                self.dialog4.txtShellFilePath_4.setText(FileGridPopPath)
            else:
                self.dialog4.txtShellFilePath_4.setText(self.FileGridPopRisk)

        msg=str(self.dialog4.txtShellFilePath_7.text())
        if msg=="":
            if self.FileTable2=="":
                aa=str(altezzAcqua)
                DirOut=os.path.dirname(aa)
                Name=os.path.basename(aa)
                pp=str.split(Name,'.')
                FileTab2DannoPath=DirOut+os.sep + pp[0]+'_pop.csv'
                self.dialog4.txtShellFilePath_7.setText(FileTab2DannoPath)
            else:
                self.dialog4.txtShellFilePath_7.setText(self.FileTable2)

        self.dialog4.luci()

        if self.Param2=='1':
            self.dialog4.preSetUnderstandingSufri()
        else:
            self.dialog4.preSetUnderstandingDam()
        self.dialog4.setCurrentUnderstanding(self.Param3)
        self.dialog4.show()
        result = self.dialog4.exec_()
        if result == 1:
            pass

    def show_help(self):
        """Load the help text into the system browser."""
        show_context_help(context='index')

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
                        layerlist.append( layer.source() )
                elif layer.type() == QgsMapLayer.RasterLayer:
                    if "Raster" in vTypes:
                        layerlist.append( layer.source() )
        return sorted( layerlist, cmp=locale.strcoll )





