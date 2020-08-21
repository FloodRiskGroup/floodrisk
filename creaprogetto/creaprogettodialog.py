"""
/***************************************************************************
 graficofloodriskDialog
                                 A QGIS plugin
 Load GeoDatabase, query sql e graph
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
from PyQt4.QtCore import *
from PyQt4.QtGui import *
from PyQt4 import QtCore, QtGui
from qgis.core import *
# Import the code for the dialog
from ui_creaprogetto import Ui_FloodRisk
import os.path
import os, shutil, subprocess
from xml.dom import minidom
from xml.dom.minidom import Document
import string
import sys

from help import show_context_help

try:
    _fromUtf8 = QtCore.QString.fromUtf8
except AttributeError:
    def _fromUtf8(s):
        return s

try:
    from osgeo import ogr
except:
    import ogr


vectors = [
            'shp','mif', 'tab','000','dgn','vrt','bna','csv','gml',
            'gpx','kml','geojson','itf','xml','ili','gmt',
            'sqlite','mdb','e00','dxf','gxt','txt','xml'
            ]

rasters = [
          'ecw','sid','vrt','tiff',
          'tif','ntf','toc','img',
          'gff','asc','ddf','dt0',
          'dt1','dt2','png','jpg',
          'jpeg','mem','gif','n1',
          'xpm','bmp','pix','map',
          'mpr','mpl','rgb','hgt',
          'ter','nc','grb','hdr',
          'rda','bt','lcp','rik',
          'dem','gxf','hdf5','grd',
          'grc','gen','img','blx',
          'blx','sqlite','sdat','adf'
          ]

def openFile(self,filePath,table):

    #Get the extension without the .
    extn = os.path.splitext(filePath)[1][1:].lower()
    if extn == 'qgs':
        #If we are project file we can just open that.
        self.iface.addProject(filePath)
    elif extn in vectors:
        if extn=='mdb':
            uri = "DRIVER='Microsoft Access Driver (*.mdb)',Database=%s,host=localhost|layername=%s" % (filePath,'HydroArea')
            uri = "%s |layername=%s" % (filePath,'HydroArea')
            uri = "%s |layer=%s" % (filePath,0)
        elif extn=='sqlite':
            uri = QgsDataSourceURI()
            uri.setDatabase(filePath)
            schema = ''
            geom_column = 'geom'
            uri.setDataSource(schema, table, geom_column)
            display_name=table
            self.iface.addVectorLayer(uri.uri(),display_name,"spatialite")
        else:
            self.iface.addVectorLayer(filePath,"","ogr")

    elif extn in rasters:
        self.iface.addRasterLayer(filePath,"")
    else:
        #We should never really get here, but just in case.
        pass

def LayerCaricato(self,NomeLayer):
    ok=bool()
    lista= str.split(str(os.path.basename(NomeLayer)),'.')
    nome = str.split(str(os.path.basename(NomeLayer)),'.')[0]
    layers = QgsMapLayerRegistry.instance().mapLayers().values()
    for l in layers:
        if l.name()==nome:
            ok=bool('True')
            break
    return ok

class creaprogettoDialog(QtGui.QDialog, Ui_FloodRisk):
    def __init__(self,iface):
        QtGui.QDialog.__init__(self)
        self.setupUi(self)
        # Save reference to the QGIS interface
        self.iface = iface
        self.btnChooseShellFile_1.setIcon(QIcon(":/plugins/floodrisk/icons/folder_explore.png"))
        self.btnChooseShellFile_1.setIconSize(QSize(25,25))
        self.btnChooseShellFile_2.setIcon(QIcon(":/plugins/floodrisk/icons/folder_explore.png"))
        self.btnChooseShellFile_2.setIconSize(QSize(25,25))
        self.btnChooseShellFile_3.setIcon(QIcon(":/plugins/floodrisk/icons/folder_explore.png"))
        self.btnChooseShellFile_3.setIconSize(QSize(25,25))
        self.btnChooseShellFile_velocita.setIcon(QIcon(":/plugins/floodrisk/icons/folder_explore.png"))
        self.btnChooseShellFile_velocita.setIconSize(QSize(25,25))
        self.btnChooseShellFile_tempi.setIcon(QIcon(":/plugins/floodrisk/icons/folder_explore.png"))
        self.btnChooseShellFile_tempi.setIconSize(QSize(25,25))
        # initialize plugin directory
        self.plugin_dir = os.path.dirname(__file__)

        self.nomefilelista=self.plugin_dir + os.sep +'FilesRecenti.xml'
        ListaFilesRecenti=self.LeggeListaFileRecenti()

        self.comboBox.clear()
        self.comboBox.addItems(ListaFilesRecenti)

        self.directoryPath=""
        self.NomeFileTemplate = self.plugin_dir + os.sep+'..' + os.sep +"caricadati" + os.sep + 'Template.sqlite'

        self.AutoLoad=''
        if len(ListaFilesRecenti)>0:
            self.FilePath1=ListaFilesRecenti[0]
            self.file1_action = QAction(QIcon(":/plugins/floodrisk/icon.png"), self.FilePath1, self.iface.mainWindow())
            QObject.connect(self.file1_action, SIGNAL("triggered()"), self.caricaProgetto1)
        if len(ListaFilesRecenti)>1:
            self.FilePath2=ListaFilesRecenti[1]
            self.file2_action = QAction(QIcon(":/plugins/floodrisk/icon.png"), self.FilePath2, self.iface.mainWindow())
            QObject.connect(self.file2_action, SIGNAL("triggered()"), self.caricaProgetto2)
        if len(ListaFilesRecenti)>2:
            self.FilePath3=ListaFilesRecenti[2]
            self.file3_action = QAction(QIcon(":/plugins/floodrisk/icon.png"), self.FilePath3, self.iface.mainWindow())
            QObject.connect(self.file3_action, SIGNAL("triggered()"), self.caricaProgetto3)

        # initialize actions
        QObject.connect(self.btnChooseShellFile_1, SIGNAL("clicked()"), self.setToolsFile)
        #QObject.connect(self.btnChooseShellFile_2, SIGNAL("clicked()"), self.setFileGDB)
        QObject.connect(self.btnChooseShellFile_2, SIGNAL("clicked()"), self.contextMenuEvent)
        QObject.connect(self.btnChooseShellFile_3, SIGNAL("clicked()"), self.setFileMaxH)
        QObject.connect(self.btnChooseShellFile_velocita, SIGNAL("clicked()"), self.setFileMaxV)
        QObject.connect(self.btnChooseShellFile_tempi, SIGNAL("clicked()"), self.setFileTime)
        QObject.connect(self.pushButtonSalvaProgetto, SIGNAL("clicked()"), self.writexml)
        QObject.connect(self.pushButtonLoadLayer, SIGNAL("clicked()"), self.CaricaLayers)
        self.comboBox.activated.connect(self.changeProgettoRecente)
        self.comboBox_3.currentIndexChanged.connect(self.selectComboVelocitaAcqua)
        self.comboBox_4.currentIndexChanged.connect(self.selectComboTempiAvviso)

        # help
        QObject.connect(self.buttonBox, SIGNAL(_fromUtf8("helpRequested()")), self.show_help)

        QObject.connect(self.pushButtonSalvaProgettoAs, SIGNAL("clicked()"), self.writexmlas)

    #----------- Actions -----------------------

    def show_help(self):
        """Load the help text into the system browser."""
        show_context_help(context='include1')

    def setToolsFile(self):
        filename = QFileDialog.getOpenFileName(None, self.tr("FloodRisk: select the project file"), self.directoryPath, "FloodRisk File (*.dmg)");
        if filename!="":
            self.txtShellFilePath.setText(filename)
            self.directoryPath=os.path.dirname(filename)
            self.comboBox_2.clear()
            self.comboBox_3.clear()
            self.comboBox_4.clear()
            self.startxml()

    def contextMenuEvent(self):
        current = QCursor.pos()
        menu = QMenu(self)
        menu.addAction(self.tr("Open file"), self.setFileGDB)
        menu.addSeparator()
        menu.addAction(self.tr("New file"), self.setNewFileGDB)

        if not menu.isEmpty():
            menu.exec_(current)

        menu.deleteLater()


    def setNewFileGDB(self):

        FileGDBPath = QFileDialog.getSaveFileName(None, self.tr("Floodrisk: select new sqlite file"), self.directoryPath, "Floodrisk.sqlite File (*.sqlite)",QFileDialog.DontConfirmOverwrite);

        if FileGDBPath!="":
            self.txtShellFilePath_2.setText(FileGDBPath)
            self.directoryPath=os.path.dirname(FileGDBPath)

            if os.path.exists(FileGDBPath):
                msgBox = QMessageBox()
                msgBox.setIcon(QMessageBox.Information)
                msgBox.setWindowTitle('Floodrisk')
                msgBox.setText(self.tr("File already exists"))
                msgBox.setInformativeText(self.tr("Do you want to overwrite it?"));
                msgBox.setStandardButtons(QMessageBox.Ok | QMessageBox.Cancel)
                msgBox.setDefaultButton(QMessageBox.Ok)
                ret = msgBox.exec_()

                if ret == QMessageBox.Ok:
                    os.remove(FileGDBPath)
                    shutil.copy(self.NomeFileTemplate, FileGDBPath)
            else:
                shutil.copy(self.NomeFileTemplate, FileGDBPath)

    def setFileGDB(self):
        FileGDBPath = QFileDialog.getOpenFileName(self, self.tr("Select the geodatabase"), \
        self.directoryPath, "File sqlite (*.sqlite);;All files (*.*)")
        if FileGDBPath!="":
            self.txtShellFilePath_2.setText(FileGDBPath)
            self.directoryPath=os.path.dirname(FileGDBPath)

    def setFileMaxH(self):

        FileMaxHPath = QFileDialog.getOpenFileName(self, self.tr('Select maximum water depth grid'), \
        self.directoryPath, 'File tif (*.tif);;All files (*.*)')
        if FileMaxHPath !="":
            self.comboBox_2.setEditText(FileMaxHPath)
            self.directoryPath=os.path.dirname(FileMaxHPath)
            msg=FileMaxHPath
            QMessageBox.information(None, "FileMaxHPath", msg)
            msg=str(self.txtShellFilePath.text())
            if msg=="":
                aa=str(FileMaxHPath)
                DirOut=os.path.dirname(aa)
                Name=os.path.basename(aa)
                pp=str.split(Name,'.')
                FileProgettoPath=DirOut+os.sep + pp[0]+'.dmg'
                self.txtShellFilePath.setText(FileProgettoPath)

            abil=bool("true")
            self.pushButtonSalvaProgetto.setEnabled(abil)

    def selectComboAltezzeAcqua(self):
            FileMaxHPath = self.comboBox_2.currentText()

    def selectComboVelocitaAcqua(self):
        if self.comboBox_3.isEnabled() == True:
            FileMaxVPath = self.comboBox_3.currentText()

    def selectComboTempiAvviso(self):
        if self.comboBox_4.isEnabled() == True:
##            import imp
##            import fTools
##            path = os.path.dirname(fTools.__file__)
##            ftu = imp.load_source('ftools_utils', os.path.join(path,'tools','ftools_utils.py'))
##            FileTimePath = ftu.getMapLayerByName(self.comboBox_4.currentText())
            FileTimePath = self.comboBox_4.currentText()

    def setFileMaxV(self):
        FileMaxVPath = QFileDialog.getOpenFileName(self, self.tr("Select maximum water velocity grid"), \
        self.directoryPath, 'File tif (*.tif);;All files (*.*)')
        if FileMaxVPath != "" :
            self.comboBox_3.setEditText(FileMaxVPath)
            self.directoryPath=os.path.dirname(FileMaxVPath)
            #self.txtShellFilePath_velocita.setText(FileMaxVPath)

    def setFileTime(self):
        FileTimePath = QFileDialog.getOpenFileName(self, self.tr("Select warning time shape-file"), \
        self.directoryPath, 'File shp (*.shp);;All files (*.*)')
        if FileTimePath != "" :
            self.comboBox_4.setEditText(FileTimePath)

    def writexml (self):

        fileprogetto=str(self.txtShellFilePath.text())
        dicProgetto={}
        dicParameter={}
        if  os.path.exists(fileprogetto):
            xmlfile=open(fileprogetto)
            dom=minidom.parse(xmlfile)
            for node in dom.getElementsByTagName("General"):
                L = node.getElementsByTagName("File")
                for node2 in L:
                    Button = node2.getAttribute("Button")
                    nome = node2.getAttribute("name")
                    dicProgetto[Button] = nome
            for node in dom.getElementsByTagName("Parameters"):
                L = node.getElementsByTagName("Parameter")
                for node2 in L:
                    Param = node2.getAttribute("Param")
                    Value = node2.getAttribute("Value")
                    dicParameter[Param] = Value

            xmlfile.close()

        # Create the minidom document
        doc = Document()

        # Create the <wml> base element
        wml = doc.createElement("FloodRisk")
        doc.appendChild(wml)

        # Create the main <card> element
        maincard = doc.createElement("General")
        wml.appendChild(maincard)

        # Create a <p> element
        ShellFilePath= str(self.txtShellFilePath_2.text())
        paragraph1 = doc.createElement("File")
        paragraph1.setAttribute("Button", 'FileGeodatabase')
        paragraph1.setAttribute("name", ShellFilePath)
        maincard.appendChild(paragraph1)

        # Create a <p> element
        ShellFilePath = self.comboBox_2.currentText()
        paragraph1 = doc.createElement("File")
        paragraph1.setAttribute("Button", 'FilePeakFloodDepth')
        paragraph1.setAttribute("name", ShellFilePath)
        maincard.appendChild(paragraph1)

        # Create a <p> element
        ShellFilePath = self.comboBox_3.currentText()
        paragraph1 = doc.createElement("File")
        paragraph1.setAttribute("Button", 'FilePeakFloodVelocity')
        paragraph1.setAttribute("name", ShellFilePath)
        maincard.appendChild(paragraph1)

        # Create a <p> element
        ShellFilePath= self.comboBox_4.currentText()
        paragraph1 = doc.createElement("File")
        paragraph1.setAttribute("Button", 'FileWarningTime')
        paragraph1.setAttribute("name", ShellFilePath)
        maincard.appendChild(paragraph1)

        for Button in dicProgetto.keys():
            nome = dicProgetto[Button]
            if Button == 'FileGridDamages':
                paragraph1 = doc.createElement("File")
                paragraph1.setAttribute("Button", Button)
                paragraph1.setAttribute("name", nome)
                maincard.appendChild(paragraph1)
            if Button == 'FileGridVulnerability':
                paragraph1 = doc.createElement("File")
                paragraph1.setAttribute("Button", Button)
                paragraph1.setAttribute("name", nome)
                maincard.appendChild(paragraph1)
            if Button == 'FileTable1':
                paragraph1 = doc.createElement("File")
                paragraph1.setAttribute("Button", Button)
                paragraph1.setAttribute("name", nome)
                maincard.appendChild(paragraph1)
            if Button == 'FileGridPopRisk':
                paragraph1 = doc.createElement("File")
                paragraph1.setAttribute("Button", Button)
                paragraph1.setAttribute("name", nome)
                maincard.appendChild(paragraph1)
            if Button == 'FileTable2':
                paragraph1 = doc.createElement("File")
                paragraph1.setAttribute("Button", Button)
                paragraph1.setAttribute("name", nome)
                maincard.appendChild(paragraph1)

        # Create the main <card> element
        maincard2 = doc.createElement("Parameters")
        wml.appendChild(maincard2)

        for Param in dicParameter.keys():
            Value = dicParameter[Param]
            if Param == 'CurveType':
                Param2 = doc.createElement("Parameter")
                Param2.setAttribute("Param", 'CurveType')
                Param2.setAttribute("Value", Value)
                maincard2.appendChild(Param2)
            if Param == 'TotalDamage':
                Param2 = doc.createElement("Parameter")
                Param2.setAttribute("Param", 'TotalDamage')
                Param2.setAttribute("Value", Value)
                maincard2.appendChild(Param2)
            if Param == 'Method':
                Param2 = doc.createElement("Parameter")
                Param2.setAttribute("Param", 'Method')
                Param2.setAttribute("Value", Value)
                maincard2.appendChild(Param2)
            if Param == 'Understand':
                Param2 = doc.createElement("Parameter")
                Param2.setAttribute("Param", 'Understand')
                Param2.setAttribute("Value", Value)
                maincard2.appendChild(Param2)
            if Param == 'LOL':
                Param2 = doc.createElement("Parameter")
                Param2.setAttribute("Param", 'LOL')
                Param2.setAttribute("Value", Value)
                maincard2.appendChild(Param2)

        if fileprogetto!="":
            fp = open(fileprogetto,"w")
            doc.writexml(fp, "", "   ", "\n", "UTF-8")
            self.AutoLoad=fileprogetto
            self.AggiornaListaFileRecenti()

            QMessageBox.information(None, "Info",  self.tr("Project Saved"))

            ListaFilesRecenti=self.LeggeListaFileRecenti()

            fp.close()
            self.comboBox.clear()
            self.comboBox.addItems(ListaFilesRecenti)

    def caricaComboBox(self, FeatureType):
        listFiles = []
        listFiles = self.getLayerSourceByMe(FeatureType)
        return listFiles

    def CaricaLayers(self):
        filePath=str(self.txtShellFilePath_2.text())
        if os.path.exists(filePath):
            tabelle=['StructurePoly','InfrastrLines','CensusBlocks']
            for nomelayer in tabelle:
                # checks if the layer is already loaded
                if not LayerCaricato(self,nomelayer):
                    openFile(self,filePath,nomelayer)

        filePath = self.comboBox_2.currentText()
        if os.path.exists(filePath):
            if not LayerCaricato(self,filePath):
                openFile(self,filePath,'')

        filePath=self.comboBox_3.currentText()
        if os.path.exists(filePath):
            if not LayerCaricato(self,filePath):
                openFile(self,filePath,'')

        filePath=self.comboBox_4.currentText()
        if os.path.exists(filePath):
            if not LayerCaricato(self,filePath):
                openFile(self,filePath,'')

    def writexmlas (self):
        fileprogetto = QFileDialog.getSaveFileName(None, self.tr("FloodRisk | Input the name of the project file"), "", "FloodRisk File (*.dmg)")
        if fileprogetto!="":
            self.txtShellFilePath.setText(fileprogetto)

            # Create the minidom document
            doc = Document()

            # Create the <wml> base element
            wml = doc.createElement("FloodRisk")
            doc.appendChild(wml)

            # Create the main <card> element
            maincard = doc.createElement("General")
            wml.appendChild(maincard)

            # Create a <p> element
            ShellFilePath = self.comboBox_2.currentText()
            paragraph1 = doc.createElement("File")
            paragraph1.setAttribute("Button", 'FilePeakFloodDepth')
            paragraph1.setAttribute("name", ShellFilePath)
            maincard.appendChild(paragraph1)

            # Create a <p> element
            ShellFilePath= self.comboBox_3.currentText()
            paragraph1 = doc.createElement("File")
            paragraph1.setAttribute("Button", 'FilePeakFloodVelocity')
            paragraph1.setAttribute("name", ShellFilePath)
            maincard.appendChild(paragraph1)

            # Create a <p> element
            ShellFilePath= self.comboBox_4.currentText()
            paragraph1 = doc.createElement("File")
            paragraph1.setAttribute("Button", 'FileWarningTime')
            paragraph1.setAttribute("name", ShellFilePath)
            maincard.appendChild(paragraph1)

            # Create a <p> element
            ShellFilePath= str(self.txtShellFilePath_2.text())
            paragraph1 = doc.createElement("File")
            paragraph1.setAttribute("Button", 'FileGeodatabase')
            paragraph1.setAttribute("name", ShellFilePath)
            maincard.appendChild(paragraph1)

            if fileprogetto!="":
                fp = open(fileprogetto,"w")
                # writexml(self, writer, indent='', addindent='', newl='', encoding=None)
                doc.writexml(fp, "", "   ", "\n", "UTF-8")
                self.AutoLoad=fileprogetto
                self.AggiornaListaFileRecenti()

                QMessageBox.information(None, "Info", self.tr("Project Saved"))


    #------------------- Functions ---------------------------
    def startxml (self):
        #starting xml file reading
        fileprogetto=str(self.txtShellFilePath.text())
        if os.path.exists(fileprogetto):
            xmlfile=open(fileprogetto)
            dom=minidom.parse(xmlfile)
            for node in dom.getElementsByTagName("General"):
                L = node.getElementsByTagName("File")
                for node2 in L:
                    Button = node2.getAttribute("Button")
                    nome = node2.getAttribute("name")
                    if Button=='FileGeodatabase':
                        self.txtShellFilePath_2.setText(nome)
                    elif Button=='FilePeakFloodDepth':
                        self.comboBox_2.addItem( nome)
                    elif Button=='FilePeakFloodVelocity':
                        self.comboBox_3.addItem( nome)
                    elif Button=='FileWarningTime':
                        self.comboBox_4.addItem( nome)

            xmlfile.close()
            abil=bool("true")
            self.pushButtonSalvaProgetto.setEnabled(abil)

    def startxml2 (self):
        #starting xml file reading
        fileprogetto=str(self.txtShellFilePath.text())
        if os.path.exists(fileprogetto):
            xmlfile=open(fileprogetto)
            dom=minidom.parse(xmlfile)
            for node in dom.getElementsByTagName("General"):
                L = node.getElementsByTagName("File")
                for node2 in L:
                    Button = node2.getAttribute("Button")
                    nome = node2.getAttribute("name")
                    if Button=='FileGeodatabase':
                        self.txtShellFilePath_2.setText(nome)
                    elif Button=='FilePeakFloodDepth':
                        self.comboBox_2.insertItem(0, nome)
                    elif Button=='FilePeakFloodVelocity':
                        self.comboBox_3.insertItem(0, nome)
                    elif Button=='FileWarningTime':
                        self.comboBox_4.insertItem(0, nome)

            xmlfile.close()
            abil=bool("true")
            self.pushButtonSalvaProgetto.setEnabled(abil)

    def AggiornaListaFileRecenti(self):
        nomefilelista=self.nomefilelista

        ListaFilesRecenti=self.LeggeListaFileRecenti()

        nn=len(ListaFilesRecenti)
        fileprogetto=str(self.txtShellFilePath.text())
        fileprogetto=os.path.abspath(fileprogetto)

        if os.path.exists(fileprogetto):
            # Create the minidom document
            doc = Document()

            # Create the <wml> base element
            wml = doc.createElement("FloodRisk")
            doc.appendChild(wml)

            # Create the main <card> element
            maincard = doc.createElement("General")
            wml.appendChild(maincard)

            # Create a <p> element
            kf=0
            kfmax=5
            #ShellFilePath= str(self.txtShellFilePath_3.text())
            ShellFilePath=self.comboBox_2.currentText()
            paragraph1 = doc.createElement("File")
            paragraph1.setAttribute("Num", str(kf))
            paragraph1.setAttribute("name", fileprogetto)
            maincard.appendChild(paragraph1)
            if nn>0:
                for i in range(nn):
                    nome_cur=ListaFilesRecenti[i]
                    nome_cur=os.path.abspath(nome_cur)
                    if os.path.exists(nome_cur) and nome_cur!=fileprogetto:
                        kf=kf+1
                        if kf<kfmax:
                            paragraph1 = doc.createElement("File")
                            paragraph1.setAttribute("Num", str(kf))
                            paragraph1.setAttribute("name", nome_cur)
                            maincard.appendChild(paragraph1)
                        else:
                            break
            fp = open(nomefilelista,"w")
            # writexml(self, writer, indent='', addindent='', newl='', encoding=None)
            doc.writexml(fp, "", "   ", "\n", "UTF-8")

    def LeggeListaFileRecenti(self):
        # reading recent project files
        nomefilelista=self.nomefilelista
        nn=0
        ListaFilesRecenti=[]
        if os.path.exists(nomefilelista):
            xmlfile=open(nomefilelista)
            dom=minidom.parse(xmlfile)
            for node in dom.getElementsByTagName("General"):
                L = node.getElementsByTagName("File")
                Num=[]
                for node2 in L:
                    nfile = int(node2.getAttribute("Num"))
                    nomefile = node2.getAttribute("name")
                    nomefile=os.path.abspath(nomefile)
                    if os.path.exists(nomefile):
                        Num.append(nfile)
                        ListaFilesRecenti.append(nomefile)

            xmlfile.close()
            nn=len(Num)

        return ListaFilesRecenti

    def caricaProgetto1(self):
        self.AutoLoad=self.FilePath1
        self.run()
    def caricaProgetto2(self):
        self.AutoLoad=self.FilePath2
        self.run()
    def caricaProgetto3(self):
        self.AutoLoad=self.FilePath3
        self.run()

    def changeProgettoRecente(self):
        self.txtShellFilePath.setText(self.comboBox.currentText())
        self.comboBox_2.clear()
        self.comboBox_3.clear()
        self.comboBox_4.clear()
        self.startxml()


    def startXmlForShp (self):
        #starting xml file reading
        self.txtShellFilePath.setText(self.comboBox.currentText())
        fileprogetto=str(self.txtShellFilePath.text())
        if os.path.exists(fileprogetto):
            xmlfile=open(fileprogetto)
            dom=minidom.parse(xmlfile)
            for node in dom.getElementsByTagName("General"):
                L = node.getElementsByTagName("File")
                for node2 in L:
                    Button = node2.getAttribute("Button")
                    nome = node2.getAttribute("name")
                    if Button=='FileWarningTime':
                        self.comboBox_4.insertItem(0, nome)

            xmlfile.close()











