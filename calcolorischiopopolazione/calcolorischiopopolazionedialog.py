"""
/***************************************************************************
CalcoloRischioPopolazioneDialog
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
from PyQt4.QtCore import *
from PyQt4.QtGui import *
from PyQt4 import QtCore, QtGui
from qgis.core import *
import os.path
from xml.dom import minidom
from xml.dom.minidom import Document
import AssessConsequencesPopulation
from ui_calcolorischiopopolazione import Ui_FloodRisk
from tableViewer_gui import TableViewer
try:
    from pylab import *
except:
    pass
import sys
import os
import sqlite3

# to reading cvs file
import csv
import locale

try:
    from osgeo import ogr
except:
    import ogr

from help import show_context_help

try:
    _fromUtf8 = QtCore.QString.fromUtf8
except AttributeError:
    def _fromUtf8(s):
        return s


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
    nome = str.split(str(os.path.basename(NomeLayer)),'.')[0]
    layers = QgsMapLayerRegistry.instance().mapLayers().values()
    for l in layers:
        if l.name()==nome:
            ok=bool('True')
            break
    return ok

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

class calcolorischiopopolazioneDialog(QtGui.QDialog, Ui_FloodRisk):
    def __init__(self,iface):
        QtGui.QDialog.__init__(self)
        self.setupUi(self)
        self.iface=iface

        self.btnChooseShellFile_3.setIcon(QIcon(":/plugins/floodrisk/icons/folder_explore.png"))
        self.btnChooseShellFile_3.setIconSize(QSize(25,25))
        self.btnChooseShellFile_velocita.setIcon(QIcon(":/plugins/floodrisk/icons/folder_explore.png"))
        self.btnChooseShellFile_velocita.setIconSize(QSize(25,25))
        self.btnChooseShellFile_tempi.setIcon(QIcon(":/plugins/floodrisk/icons/folder_explore.png"))
        self.btnChooseShellFile_tempi.setIconSize(QSize(25,25))
        self.pushButtonView_2.setIcon(QIcon(":/plugins/floodrisk/icons/table_go.png"))
        self.pushButtonView_2.setIconSize(QSize(25,25))
        self.pushButtonIstogrammi.setIcon(QIcon(":/plugins/floodrisk/icons/chart_bar.png"))
        self.pushButtonIstogrammi.setIconSize(QSize(25,25))
        self.label_red_pop.setPixmap(QPixmap(":/plugins/floodrisk/icons/red20.png"))
        self.label_green_pop.setPixmap(QPixmap(":/plugins/floodrisk/icons/green20.png"))

        # initialize actions
        QObject.connect(self.btnChooseShellFile_3, SIGNAL("clicked()"), self.setFileMaxH)
        QObject.connect(self.btnChooseShellFile_velocita, SIGNAL("clicked()"), self.setFileMaxV)
        QObject.connect(self.btnChooseShellFile_tempi, SIGNAL("clicked()"), self.setFileTime)
        QObject.connect(self.toolButtonEsegui_2, SIGNAL("clicked()"), self.EseguiCalcoloPopolazione)
        QObject.connect(self.pushButtonView_2, SIGNAL("clicked()"), self.VediTabellaRischio)
        QObject.connect(self.pushButtonSalvaProgetto, SIGNAL("clicked()"), self.writexml)
        QObject.connect(self.pushButtonLoadLayer, SIGNAL("clicked()"), self.CaricaLayers)
        QObject.connect(self.pushButtonIstogrammi, SIGNAL("clicked()"), self.istogrammi)
        self.radioButton.toggled.connect(self.setUnderstandingDam)
        self.radioButton_2.toggled.connect(self.setUnderstandingSufri)

        # help
        QObject.connect(self.buttonBox, SIGNAL(_fromUtf8("helpRequested()")), self.show_help)

        self.paramMethod=''
        self.paramUnderstanding=''
        self.paramLOL_notRound=0.0

    #------------- Actions -----------------------

    def show_help(self):
        """Load the help text into the system browser."""
        show_context_help(context='include4')


    def setFileMaxV(self):
        message = QtGui.QMessageBox.question(self, self.tr('Attention'),self.tr("Warning you are editing the data input to the project: current data" \
        " of output will be deleted. Are you sure?"), QtGui.QMessageBox.Yes | QtGui.QMessageBox.No, QtGui.QMessageBox.No)
        if message == QtGui.QMessageBox.Yes:
            FileMaxVPath = QFileDialog.getOpenFileName(self, "Select file max water velocity", \
            '.', 'File tif (*.tif);;All files (*.*)')
            self.txtShellFilePath_velocita.setText(FileMaxVPath)
            #----Deleting output data-----
            self.txtShellFilePath_4.setText("")
            self.txtShellFilePath_7.setText("")

    def setFileTime(self):
        message = QtGui.QMessageBox.question(self, self.tr('Attention'),self.tr("Warning you are editing the data input to the project: current data" \
        " of output will be deleted. Are you sure?"), QtGui.QMessageBox.Yes | QtGui.QMessageBox.No, QtGui.QMessageBox.No)
        if message == QtGui.QMessageBox.Yes:
            FileTimePath = QFileDialog.getOpenFileName(self, self.tr("Select warning time shape file"), \
            '.', 'File shp (*.shp);;All files (*.*)')
            self.txtShellFilePath_tempi.setText(FileTimePath)
            #----Deleting output data-----
            self.txtShellFilePath_4.setText("")
            self.txtShellFilePath_7.setText("")

    def setFileMaxH(self):
        message = QtGui.QMessageBox.question(self, self.tr('Attention'),self.tr("Warning you are editing the data input to the project: current data" \
        " of output will be deleted. Are you sure?"), QtGui.QMessageBox.Yes | QtGui.QMessageBox.No, QtGui.QMessageBox.No)
        if message == QtGui.QMessageBox.Yes:
            FileMaxHPath = QFileDialog.getOpenFileName(self, self.tr('Select peak flow depth file'), \
            '.', 'File tif (*.tif);;All files (*.*)')
            self.txtShellFilePath_3.setText(FileMaxHPath)
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

            msg=str(self.txtShellFilePath_4.text())
            if msg=="":
                aa=str(FileMaxHPath)
                DirOut=os.path.dirname(aa)
                Name=os.path.basename(aa)
                pp=str.split(Name,'.')
                FileGridPopPath=DirOut+os.sep + pp[0]+'_pop.tif'
                self.txtShellFilePath_4.setText(FileGridPopPath)

            msg=str(self.txtShellFilePath_7.text())
            if msg=="":
                aa=str(FileMaxHPath)
                DirOut=os.path.dirname(aa)
                Name=os.path.basename(aa)
                pp=str.split(Name,'.')
                FileTab2DannoPath=DirOut+os.sep + pp[0]+'_pop.csv'
                self.txtShellFilePath_7.setText(FileTab2DannoPath)

            #----Deleting output data-----
            self.txtShellFilePath_4.setText("")
            self.txtShellFilePath_7.setText("")
            abil=bool("true")
            self.pushButtonSalvaProgetto.setEnabled(abil)
            #self.luci()

    def EseguiCalcoloPopolazione(self):

        # ------------------------------------------------------
        # performs the calculation of the risk to the population
        # ------------------------------------------------------
        self.Nome=[]
        self.listafiles=[]
        # FileDEM1
        self.Nome.append('File Max Water Depth')
        self.listafiles.append(str(self.txtShellFilePath_3.text()))
        # file Water Velocity
        self.Nome.append('File Water Velocity')
        self.listafiles.append(str(self.txtShellFilePath_velocita.text()))
        # file Warning Time
        self.Nome.append('File Warning Time')
        self.listafiles.append(str(self.txtShellFilePath_tempi.text()))
        # DBfile
        self.Nome.append('File Geodatabase')
        self.listafiles.append(str(self.txtShellFilePath_2.text()))
        # NameFileGridPop
        self.Nome.append('File Grid population at risk')
        self.listafiles.append(str(self.txtShellFilePath_4.text()))
        # NameFileTable2
        self.Nome.append('File Table 2')
        self.listafiles.append(str(self.txtShellFilePath_7.text()))

        parametroUnderstanding = self.comboBox.currentText()
        self.paramUnderstanding=parametroUnderstanding
        self.listafiles.append(parametroUnderstanding)

        abil=bool("true")
        for i in range(4):
            if not os.path.exists(self.listafiles[i]):
                msg1=self.tr('Error the file')
                msg2=self.tr('does not exist')
                msg='%s %s: %s ' % (msg1,self.Nome[i],msg2)
                QMessageBox.information(None, "Fine input", msg)
                abil=bool()
        for k in range(2):
            i=k+4
            if len(self.listafiles[i])==0:
                txt1=self.tr('Attention assign a name to file')
                msg='%s: %s ' % (txt1,self.Nome[i])
                QMessageBox.information(None, "Fine output", msg)
                abil=bool()
        if not self.CheckFloodSeverity():
            abil=bool()

        if not self.CheckFatalityRate():
            abil=bool()

        if abil:
            fileprogetto=str(self.txtShellFilePath.text())

            if self.CheckGeodatabase():

                # initializes progressbar
                self.progressBar.setFormat(self.tr('Population consequences assessment') +': %p%')

                self.progressBar.setValue(0)
                abil=bool()
                self.buttonBox.setEnabled(abil)

                NotErr, errMsg, NumLoss_notRound = AssessConsequencesPopulation.main(self.listafiles,self.progressBar)

                self.paramLOL_notRound=NumLoss_notRound

                self.luci()

                if NotErr:
                    msg=self.tr('End of Job')
                    QMessageBox.information(None, "FloodRisk", msg)
                    self.writexml()

                    abil=bool('True')
                    self.buttonBox.setEnabled(abil)
                    self.progressBar.setFormat(('%p%'))
                    self.progressBar.setValue(0)
                else:
                    msg=self.tr("Run not executed")
                    msg='%s : %s' % (errMsg,msg)
                    QMessageBox.information(None, "Run", msg)
                    self.luci()

            else:

                QMessageBox.information(None, "FloodRisk", self.tr("You must first create the Geodb.Sqlite"))

        else:
            msg=self.tr("Run not executed")
            QMessageBox.information(None, "Run", msg)
            self.luci()

    def VediTabellaRischio(self):
        self.NomeTabella=str(self.txtShellFilePath_7.text())
        self.TabView = TableViewer(self.iface,self.NomeTabella)
        self.TabView.show()# show the dialog
        result = self.TabView.exec_()

    def writexml (self):
        fileprogetto=str(self.txtShellFilePath.text())
        dicProgetto={}
        dicParameter={}
        if fileprogetto!="":
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

        ShellFilePath= str(self.txtShellFilePath_3.text())
        paragraph1 = doc.createElement("File")
        paragraph1.setAttribute("Button", 'FilePeakFloodDepth')
        paragraph1.setAttribute("name", ShellFilePath)
        #paragraph1.setAttribute("unit", '[m]')
        maincard.appendChild(paragraph1)

        # Create a <p> element
        ShellFilePath= str(self.txtShellFilePath_velocita.text())
        paragraph1 = doc.createElement("File")
        paragraph1.setAttribute("Button", 'FilePeakFloodVelocity')
        paragraph1.setAttribute("name", ShellFilePath)
        #paragraph1.setAttribute("unit", '[m]')
        maincard.appendChild(paragraph1)

        # Create a <p> element
        ShellFilePath= str(self.txtShellFilePath_tempi.text())
        paragraph1 = doc.createElement("File")
        paragraph1.setAttribute("Button", 'FileWarningTime')
        paragraph1.setAttribute("name", ShellFilePath)
        #paragraph1.setAttribute("unit", '[m]')
        maincard.appendChild(paragraph1)

        # Save input files
        for Button in dicProgetto.keys():
            nome = dicProgetto[Button]
            if Button == 'FileGridDamages':
                paragraph1 = doc.createElement("File")
                paragraph1.setAttribute("Button", Button)
                paragraph1.setAttribute("name", nome)
                #paragraph1.setAttribute("unit", '[m]')
                maincard.appendChild(paragraph1)
            if Button == 'FileGridVulnerability':
                paragraph1 = doc.createElement("File")
                paragraph1.setAttribute("Button", Button)
                paragraph1.setAttribute("name", nome)
                #paragraph1.setAttribute("unit", '[m]')
                maincard.appendChild(paragraph1)
            if Button == 'FileTable1':
                paragraph1 = doc.createElement("File")
                paragraph1.setAttribute("Button", Button)
                paragraph1.setAttribute("name", nome)
                #paragraph1.setAttribute("unit", '[m]')
                maincard.appendChild(paragraph1)

        # Create a <p> element
        ShellFilePath= str(self.txtShellFilePath_4.text())
        paragraph1 = doc.createElement("File")
        paragraph1.setAttribute("Button", 'FileGridPopRisk')
        paragraph1.setAttribute("name", ShellFilePath)
        maincard.appendChild(paragraph1)

        # Create a <p> element
        ShellFilePath= str(self.txtShellFilePath_7.text())
        paragraph1 = doc.createElement("File")
        paragraph1.setAttribute("Button", 'FileTable2')
        paragraph1.setAttribute("name", ShellFilePath)
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

        Param2 = doc.createElement("Parameter")
        Param2.setAttribute("Param", 'Method')
        Param2.setAttribute("Value", str(self.paramMethod))
        maincard2.appendChild(Param2)

        Param2 = doc.createElement("Parameter")
        Param2.setAttribute("Param", 'Understand')
        Param2.setAttribute("Value", self.paramUnderstanding)
        maincard2.appendChild(Param2)

        Param3 = doc.createElement("Parameter")
        Param3.setAttribute("Param", 'LOL')
        msg='%4f' % self.paramLOL_notRound
        Param3.setAttribute("Value", msg)
        maincard2.appendChild(Param3)


        if fileprogetto!="":
            fp = open(fileprogetto,"w")
            # writexml(self, writer, indent='', addindent='', newl='', encoding=None)
            doc.writexml(fp, "", "   ", "\n", "UTF-8")
            self.AutoLoad=fileprogetto
            QMessageBox.information(None, "Info", self.tr("Project Saved"))

    def CaricaLayers(self):
        filePath=str(self.txtShellFilePath_2.text())
        if os.path.exists(filePath):
            # case geodatabase
            tabelle=['StructurePoly','InfrastrLines','CensusBlocks']
            for nomelayer in tabelle:
                # checks if the layer is already loaded
                if not LayerCaricato(self,nomelayer):
                    openFile(self,filePath,nomelayer)

        filePath=str(self.txtShellFilePath_3.text())
        if os.path.exists(filePath):
            if not LayerCaricato(self,filePath):
                openFile(self,filePath,'')

        filePath=str(self.txtShellFilePath_velocita.text())
        if os.path.exists(filePath):
            if not LayerCaricato(self,filePath):
                openFile(self,filePath,'')

        filePath=str(self.txtShellFilePath_tempi.text())
        if os.path.exists(filePath):
            if not LayerCaricato(self,filePath):
                openFile(self,filePath,'')

        filePath=str(self.txtShellFilePath_4.text())
        if os.path.exists(filePath):
            if not LayerCaricato(self,filePath):
                openFile(self,filePath,'')

    def istogrammi(self):
        self.NomeFile=str(self.txtShellFilePath_7.text())
        if os.path.exists(self.NomeFile):
            try:
                import matplotlib

                self.sep=check_csv_separator(self.NomeFile)
               # Reading csv file
                finp = open(self.NomeFile)
                csv_reader = csv.reader(finp, delimiter=self.sep, quotechar='"')
                headers = csv_reader.next()

                self.fields=[]
                for p in headers:
                    self.fields.append(p)

                progress = unicode('Reading data ') # As a progress bar is used the main window's status bar, because the own one is not initialized yet

                yPopTotRischio=[]
                yPerViteUman=[]
                xTiranteIdrico=[]
                for record in csv_reader:
                    for i in range(len(record)):

                        if i == 0:
                            xTiranteIdrico += [record[i]]
                        if i == 4:
                            yPopTotRischio += [int(record[i])]
                        if i == 5:
                            yPerViteUman += [int(record[i])]

                finp.close()

                #---------------Draw Chart-----------------
                y1=yPerViteUman
                y2=yPopTotRischio
                x1=xTiranteIdrico
                width=0.3  # bar width
                i=arange(len(y1))
                r1=bar(i, y1,width, color='r',linewidth=1)
                r2=bar(i+width,y2,width,color='b',linewidth=1)
                xticks(i+width/2,x1)
                xlabel(self.tr('Range water depth (m)')); ylabel(self.tr('Number people')); title(self.tr('Consequences for the population'))
                try:
                    legend((r1[0],r2[0]),(self.tr('Loss of Life'), self.tr('Total Polpulation at Risk')),'best')
                except:
                    pass
                grid()
                show()
            except:
                QMessageBox.information(None, "Warning", "The current version of QGIS does not allow import matplotlib")

    def setUnderstandingDam(self, enabled):
        if enabled:
            self.paramMethod=0
            FileGDB = str(self.txtShellFilePath_2.text())
            if FileGDB != "":
                if self.CheckGeodatabase():
                    conn = sqlite3.connect(FileGDB)
                    cursor = conn.cursor()
                    testoQuery='SELECT Understanding FROM FatalityRate WHERE FRType=0 GROUP BY Understanding'
                    cursor.execute(testoQuery)
                    ListaDam = cursor.fetchall()
                    if len(ListaDam)>0:
                        Lista=[]
                        for i in range(len(ListaDam)):
                            Lista.append(str(ListaDam[i][0]))
                        self.comboBox.clear()
                        self.comboBox.addItems(Lista)
                    else:
                        self.comboBox.clear()
                        msg0='Geodatabse %s' % FileGDB
                        msg1=self.tr('error table FatalityRate is empty')
                        msg='%s : %s' % (msg0,msg1)
                        QMessageBox.information(None, "FloodRisk", msg)
                else:
                    msg0='Geodatabse %s' % FileGDB
                    msg1=self.tr('error in table FatalityRate')
                    msg='%s : %s' % (msg0,msg1)
                    QMessageBox.information(None, "FloodRisk", msg)
            else:
                QMessageBox.information(None, "FloodRisk", self.tr("You must first create the Geodb.Sqlite"))

    def setUnderstandingSufri(self, enabled):
        if enabled:
            self.paramMethod=1
            FileGDB = str(self.txtShellFilePath_2.text())
            if FileGDB != "":
                if self.CheckGeodatabase():
                    conn = sqlite3.connect(FileGDB)
                    cursor = conn.cursor()
                    testoQuery='SELECT Understanding FROM FatalityRate WHERE FRType=1 GROUP BY Understanding'
                    cursor.execute(testoQuery)
                    ListaDam = cursor.fetchall()
                    if len(ListaDam)>0:
                        Lista=[]
                        for i in range(len(ListaDam)):
                            Lista.append(str(ListaDam[i][0]))
                        self.comboBox.clear()
                        self.comboBox.addItems(Lista)
                    else:
                        self.comboBox.clear()
                        msg0='Geodatabse %s' % FileGDB
                        msg1=self.tr('error table FatalityRate is empty')
                        msg='%s : %s' % (msg0,msg1)
                        QMessageBox.information(None, "FloodRisk", msg)
                else:
                    msg0='Geodatabse %s' % FileGDB
                    msg1=self.tr('error in table FatalityRate')
                    msg='%s : %s' % (msg0,msg1)
                    QMessageBox.information(None, "FloodRisk", msg)
            else:
                QMessageBox.information(None, "FloodRisk", self.tr("You must first create the Geodb.Sqlite"))


    def setCurrentUnderstanding(self,ItemText):
        # set currentItem paramUnderstanding
        NumType=self.comboBox.count()
        AllItems = [self.comboBox.itemText(i) for i in range(NumType)]
        if NumType>0:
            index=-1
            for ii in range(NumType):
                if ItemText==AllItems[ii]:
                    index=ii
            if index>=0:
                self.comboBox.setCurrentIndex(index)
                self.paramUnderstanding=ItemText

    #------------------- Functions -------------------
    def luci(self):
        #FileGridPopRisk
        FilePath= str(self.txtShellFilePath_4.text())
        if os.path.exists(FilePath):
            self.label_red_pop.hide()
            self.label_green_pop.show()
        else:
            self.label_red_pop.show()
            self.label_green_pop.hide()

    def preSetUnderstandingDam(self):

            self.radioButton.toggle()
            FileGDB = str(self.txtShellFilePath_2.text())
            if FileGDB != "":
                if self.CheckGeodatabase():
                    conn = sqlite3.connect(FileGDB)
                    cursor = conn.cursor()
                    testoQuery='SELECT Understanding FROM FatalityRate WHERE FRType=0 GROUP BY Understanding'
                    cursor.execute(testoQuery)
                    ListaDam = cursor.fetchall()
                    Lista=[]
                    for i in range(len(ListaDam)):
                        Lista.append(str(ListaDam[i][0]))
                    self.comboBox.clear()
                    self.comboBox.addItems(Lista)
                    self.paramMethod=0
                else:
                    msg0='Geodatabse %s' % FileGDB
                    msg1=self.tr('error in table FatalityRate')
                    msg='%s : %s' % (msg0,msg1)
                    QMessageBox.information(None, "FloodRisk", msg)
            else:
                QMessageBox.information(None, "FloodRisk", self.tr("You must first create the Geodb.Sqlite"))

    def preSetUnderstandingSufri(self):
            self.radioButton_2.toggle()
            FileGDB = str(self.txtShellFilePath_2.text())
            if FileGDB != "":
                if self.CheckGeodatabase():
                    conn = sqlite3.connect(FileGDB)
                    cursor = conn.cursor()
                    testoQuery='SELECT Understanding FROM FatalityRate WHERE FRType=1 GROUP BY Understanding'
                    cursor.execute(testoQuery)
                    ListaDam = cursor.fetchall()
                    Lista=[]
                    for i in range(len(ListaDam)):
                        Lista.append(str(ListaDam[i][0]))
                    self.comboBox.clear()
                    self.comboBox.addItems(Lista)
                else:
                    msg0='Geodatabse %s' % FileGDB
                    msg1=self.tr('error in table FatalityRate')
                    msg='%s : %s' % (msg0,msg1)
                    QMessageBox.information(None, "FloodRisk", msg)
            else:
                QMessageBox.information(None, "FloodRisk", self.tr("You must first create the Geodb.Sqlite"))

    def CheckGeodatabase(self):
        res=bool()
        if os.path.exists(self.txtShellFilePath_2.text()):
            mydb_path=self.txtShellFilePath_2.text()
            try:
                # connecting the db
                conn = sqlite3.connect(mydb_path)
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

    def CheckFloodSeverity(self):
        res=bool()
        FileGDB = str(self.txtShellFilePath_2.text())
        if FileGDB != "":
            if self.CheckGeodatabase():
                try:
                    conn = sqlite3.connect(FileGDB)
                    cursor = conn.cursor()
                    fieldOrder='Num'
                    NomeTabella='FloodSeverity'
                    testoQuery=" SELECT * FROM %s ORDER BY %s;" %(NomeTabella,fieldOrder)
                    cursor.execute(testoQuery)
                    Lista = cursor.fetchall()
                    if len(Lista)>0:
                        res=bool('True')
                    else:
                        msg0='Geodatabse %s' % FileGDB
                        msg1=self.tr('error table FloodSeverity is empty')
                        msg='%s : %s' % (msg0,msg1)
                        QMessageBox.information(None, "FloodRisk", msg)

                except:
                    msg0='Geodatabse %s' % FileGDB
                    msg1=self.tr('error in table FloodSeverity')
                    msg='%s : %s' % (msg0,msg1)
                    QMessageBox.information(None, "FloodRisk", msg)

            else:
                QMessageBox.information(None, "FloodRisk", self.tr("You must first create the Geodb.Sqlite"))
        else:
            QMessageBox.information(None, "FloodRisk", self.tr("You must first create the Geodb.Sqlite"))

        return res

    def CheckFatalityRate(self):
        res=bool()
        FileGDB = str(self.txtShellFilePath_2.text())
        if FileGDB != "":
            if self.CheckGeodatabase():
                try:
                    conn = sqlite3.connect(FileGDB)
                    cursor = conn.cursor()
                    fieldOrder='Num'
                    NomeTabella='FatalityRate'
                    testoQuery=" SELECT * FROM %s ORDER BY %s;" %(NomeTabella,fieldOrder)
                    cursor.execute(testoQuery)
                    Lista = cursor.fetchall()
                    if len(Lista)>0:
                        res=bool('True')
                    else:
                        msg0='Geodatabse %s' % FileGDB
                        msg1=self.tr('error table FatalityRate is empty')
                        msg='%s : %s' % (msg0,msg1)
                        QMessageBox.information(None, "FloodRisk", msg)

                except:
                    msg0='Geodatabse %s' % FileGDB
                    msg1=self.tr('error in table FatalityRate')
                    msg='%s : %s' % (msg0,msg1)
                    QMessageBox.information(None, "FloodRisk", msg)

            else:
                QMessageBox.information(None, "FloodRisk", self.tr("You must first create the Geodb.Sqlite"))
        else:
            QMessageBox.information(None, "FloodRisk", self.tr("You must first create the Geodb.Sqlite"))

        return res

