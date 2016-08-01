"""
/***************************************************************************
CalcolodannoDialog
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
from ui_calcolodanno import Ui_FloodRisk
import CalcoloDannoInondazione
import os.path
from xml.dom import minidom
from xml.dom.minidom import Document
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

class calcolodannoDialog(QtGui.QDialog, Ui_FloodRisk):
    def __init__(self,iface):
        QtGui.QDialog.__init__(self)
        self.setupUi(self)
        self.iface=iface
        self.btnChooseShellFile_3.setIcon(QIcon(":/plugins/floodrisk/icons/folder_explore.png"))
        self.btnChooseShellFile_3.setIconSize(QSize(25,25))
        self.pushButtonView.setIcon(QIcon(":/plugins/floodrisk/icons/table_go.png"))
        self.pushButtonView.setIconSize(QSize(25,25))
        self.pushButton.setIcon(QIcon(":/plugins/floodrisk/icons/chart_bar.png"))
        self.pushButton.setIconSize(QSize(25,25))
        self.buttonGrafici.setIcon(QIcon(":/plugins/floodrisk/icons/images.jpg"))
        self.buttonGrafici.setIconSize(QSize(35,25))
        self.label_red_danno.setPixmap(QPixmap(":/plugins/floodrisk/icons/red20.png"))
        self.label_red_vuln.setPixmap(QPixmap(":/plugins/floodrisk/icons/red20.png"))
        self.label_green_danno.setPixmap(QPixmap(":/plugins/floodrisk/icons/green20.png"))
        self.label_green_vuln.setPixmap(QPixmap(":/plugins/floodrisk/icons/green20.png"))

        # initialize actions
        QObject.connect(self.btnChooseShellFile_3, SIGNAL("clicked()"), self.setFileMaxH)
        QObject.connect(self.buttonGrafici, SIGNAL("clicked()"), self.graficoCurve)
        QObject.connect(self.pushButtonView, SIGNAL("clicked()"), self.VediTabellaDanni)
        QObject.connect(self.toolButtonEsegui, SIGNAL("clicked()"), self.EseguiCalcoloDanni)
        QObject.connect(self.pushButtonSalvaProgetto, SIGNAL("clicked()"), self.writexml)
        QObject.connect(self.pushButtonLoadLayer, SIGNAL("clicked()"), self.CaricaLayers)
        QObject.connect(self.pushButton, SIGNAL("clicked()"), self.istogrammi)

        self.dic_TypeId={}
        self.CurveType=''
        self.TotalDamage=0.0
        #self.sep=set_csv_separator()

        # help
        QObject.connect(self.buttonBox, SIGNAL(_fromUtf8("helpRequested()")), self.show_help)


    #------------- Actions -----------------------

    def show_help(self):
        """Load the help text into the system browser."""
        show_context_help(context='include3')

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

            msg=str(self.txtShellFilePath_5.text())
            if msg=="":
                aa=str(FileMaxHPath)
                DirOut=os.path.dirname(aa)
                Name=os.path.basename(aa)
                pp=str.split(Name,'.')
                FileDannoPath=DirOut+os.sep + pp[0]+'_dmg.tif'
                self.txtShellFilePath_5.setText(FileDannoPath)

            msg=str(self.txtShellFilePath_6.text())
            if msg=="":
                aa=str(FileMaxHPath)
                DirOut=os.path.dirname(aa)
                Name=os.path.basename(aa)
                pp=str.split(Name,'.')
                FileTabDannoPath=DirOut+os.sep + pp[0]+'_dmg.csv'
                self.txtShellFilePath_6.setText(FileTabDannoPath)

            msg=str(self.txtShellFilePath_vulnerato.text())
            if msg=="":
                aa=str(FileMaxHPath)
                DirOut=os.path.dirname(aa)
                Name=os.path.basename(aa)
                pp=str.split(Name,'.')
                FileVulnPath=DirOut+os.sep + pp[0]+'_vuln.tif'
                self.txtShellFilePath_vulnerato.setText(FileVulnPath)

            #----Deleting output data -----
            self.txtShellFilePath_5.setText("")
            self.txtShellFilePath_vulnerato.setText("")
            self.txtShellFilePath_6.setText("")
            abil=bool("true")
            self.pushButtonSalvaProgetto.setEnabled(abil)

    def graficoCurve(self):
        tipo = self.comboBoxGrafici.currentText()
        try:
            self.idTipo = self.dic_TypeId[tipo]
            from graficofloodriskdialog import graficofloodriskDialog
            gfd=graficofloodriskDialog(self.iface, self.idTipo, tipo)
            geoDataBase=str(self.txtShellFilePath_2.text())
            if geoDataBase!="":
                gfd.lineEdit.setText(geoDataBase)
            gfd.run()
        except:
            txt0='Geodatabase: %s \n\n' % self.txtShellFilePath_2.text()
            txt1=self.tr("Error in table Vulnerability")
            msg='%s %s' % (txt0,txt1)
            QMessageBox.information(None, "Graph", msg)

    def EseguiCalcoloDanni(self):

        self.Nome=[]
        self.listafiles=[]
        # FileDEM1
        self.Nome.append('File Max Water Depth')
        self.listafiles.append(str(self.txtShellFilePath_3.text()))
        # DBfile
        self.Nome.append('File Geodatabase')
        self.listafiles.append(str(self.txtShellFilePath_2.text()))
        # NameFileGridVulnerability
        self.Nome.append('File Grid Vulnerability')
        self.listafiles.append(str(self.txtShellFilePath_vulnerato.text()))
        # NameFileGridDamages
        self.Nome.append('File Grid Damages')
        self.listafiles.append(str(self.txtShellFilePath_5.text()))
        # NameFileTable
        self.Nome.append('File Table 1')
        self.listafiles.append(str(self.txtShellFilePath_6.text()))

        tipo = self.comboBoxGrafici.currentText()
        self.CurveType=tipo

        abil0=bool("true")
        try:
            self.idTipo = self.dic_TypeId[tipo]
            self.listafiles.append(self.idTipo)
        except:
                txt0='Geodatabase: %s \n\n' % self.txtShellFilePath_2.text()
                txt1=self.tr('Warning the Depth-Damage Curves Type')
                txt2=self.tr('does not exists')
                msg='%s %s %s: %s' % (txt0,txt1,tipo,txt2)
                QMessageBox.information(None, "Input", msg)
                abil0=bool()
                errMsg='Input Error'

        if abil0:
            abil=bool("true")
            for i in range(2):
                if not os.path.exists(self.listafiles[i]):
                    txt1=self.tr('Warning the file')
                    txt2=self.tr('does not exists')
                    msg='%s %s: %s' % (txt1,self.Nome[i],txt2)
                    QMessageBox.information(None, "File input", msg)
                    abil=bool()
                    errMsg='Input Error'
            for k in range(3):
                i=k+2
                if len(self.listafiles[i])==0:
                    txt1=self.tr('Attention assign a name to file')
                    msg='%s: %s ' % (txt1,self.Nome[i])
                    QMessageBox.information(None, "File output", msg)
                    abil=bool()
                    errMsg='Input Error'
        else:
            abil=bool()

        if abil:
            fileprogetto=str(self.txtShellFilePath.text())

            # initializes progressbar
            self.progressBar.setFormat(self.tr('Damage assessment') +': %p%')

            self.progressBar.setValue(0)
            abil=bool()
            self.buttonBox.setEnabled(abil)

            NotErr, errMsg, TotalDamage = CalcoloDannoInondazione.main(self.listafiles,self.progressBar)

            self.TotalDamage=TotalDamage

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
                msg=errMsg + " - " + self.tr("Run not executed")
                QMessageBox.information(None, "Run", msg)
                self.luci()
        else:
            msg=errMsg + " - " + self.tr("Run not executed")
            QMessageBox.information(None, "Run", msg)
            self.luci()

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

        # Save input file
        for Button in dicProgetto.keys():
            nome = dicProgetto[Button]
            if Button == 'FilePeakFloodVelocity':
                paragraph1 = doc.createElement("File")
                paragraph1.setAttribute("Button", Button)
                paragraph1.setAttribute("name", nome)
                #paragraph1.setAttribute("unit", '[m]')
                maincard.appendChild(paragraph1)
            if Button == 'FileWarningTime':
                paragraph1 = doc.createElement("File")
                paragraph1.setAttribute("Button", Button)
                paragraph1.setAttribute("name", nome)
                #paragraph1.setAttribute("unit", '[m]')
                maincard.appendChild(paragraph1)

        # Create a <p> element
        ShellFilePath= str(self.txtShellFilePath_5.text())
        paragraph1 = doc.createElement("File")
        paragraph1.setAttribute("Button", 'FileGridDamages')
        paragraph1.setAttribute("name", ShellFilePath)
        #paragraph1.setAttribute("unit", '[kEuro]')
        maincard.appendChild(paragraph1)
#
        # Create a <p> element
        ShellFilePath= str(self.txtShellFilePath_vulnerato.text())
        paragraph1 = doc.createElement("File")
        paragraph1.setAttribute("Button", 'FileGridVulnerability')
        paragraph1.setAttribute("name", ShellFilePath)
        maincard.appendChild(paragraph1)
#
        # Create a <p> element
        ShellFilePath= str(self.txtShellFilePath_6.text())
        paragraph1 = doc.createElement("File")
        paragraph1.setAttribute("Button", 'FileTable1')
        paragraph1.setAttribute("name", ShellFilePath)
        maincard.appendChild(paragraph1)

        # Save input file
        for Button in dicProgetto.keys():
            nome = dicProgetto[Button]
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

        # Create a <p> element
        Param1 = doc.createElement("Parameter")
        Param1.setAttribute("Param", 'CurveType')
        Param1.setAttribute("Value", self.CurveType)
        maincard2.appendChild(Param1)

        Param1 = doc.createElement("Parameter")
        Param1.setAttribute("Param", 'TotalDamage')
        msg='%.1f' % self.TotalDamage
        Param1.setAttribute("Value", msg)
        maincard2.appendChild(Param1)


        for Param in dicParameter.keys():
            Value = dicParameter[Param]
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
          # writexml(self, writer, indent='', addindent='', newl='', encoding=None)
          doc.writexml(fp, "", "   ", "\n", "UTF-8")
          self.AutoLoad=fileprogetto
          QMessageBox.information(None, "Info", self.tr("Project Saved"))

    def VediTabellaDanni(self):
        self.NomeTabella=str(self.txtShellFilePath_6.text())
        self.TabView = TableViewer(self.iface,self.NomeTabella)
        self.TabView.show()# show the dialog
        result = self.TabView.exec_()

    def CaricaLayers(self):
        filePath=str(self.txtShellFilePath_2.text())
        if os.path.exists(filePath):
            # case geodatabase
            tabelle=['StructurePoly','InfrastrLines','CensusBlocks']
            for nomelayer in tabelle:
                if not LayerCaricato(self,nomelayer):
                    openFile(self,filePath,nomelayer)

        filePath=str(self.txtShellFilePath_3.text())
        if os.path.exists(filePath):
            if not LayerCaricato(self,filePath):
                openFile(self,filePath,'')

        filePath=str(self.txtShellFilePath_vulnerato.text())
        if os.path.exists(filePath):
            if not LayerCaricato(self,filePath):
                openFile(self,filePath,'')

        filePath=str(self.txtShellFilePath_5.text())
        if os.path.exists(filePath):
            if not LayerCaricato(self,filePath):
                openFile(self,filePath,'')

    def istogrammi(self):
        self.NomeFile=str(self.txtShellFilePath_6.text())
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

                yEuro1=[]
                yEuro2=[]
                xCodice=[]
                for record in csv_reader:
                    for i in range(len(record)):
                        if i == 0:
                            xCodice += [record[i]]
                        if i == 5:
                            yEuro2 += [float(record[i])]
                        if i == 6:
                            yEuro1 += [float(record[i])]

                finp.close()

                #---------------Draw Chart-----------------
                y1=yEuro1
                y2=yEuro2
                x1=xCodice
                width=0.3
                i=arange(len(y1))
                r1=bar(i, y1,width, color='r',linewidth=1)
                r2=bar(i+width,y2,width,color='b',linewidth=1)
                xticks(i+width/2,x1)
                xlabel('Code'); ylabel('Euro'); title(self.tr('Damage assessment results'))
                try:
                    legend((r1[0],r2[0]),(self.tr('Content Damage'), self.tr('Structure Damage')), 'best')
                except:
                    pass
                grid()
                show()
            except:
                QMessageBox.information(None, "Warning", "The current version of QGIS does not allow import matplotlib")

        else:
            txt1=self.tr('Warning the file')
            txt2=self.tr('does not exists')
            msg='%s\n\n %s\n\n %s' % (txt1,self.NomeFile,txt2)
            QMessageBox.information(None, "Input", msg)


    #------------------- Functions ---------------------------
    def startxml (self):
        fileprogetto=str(self.txtShellFilePath.text())
        if fileprogetto!="":
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
                        self.txtShellFilePath_3.setText(nome)
                    elif Button=='FileGridDamages':
                        self.txtShellFilePath_5.setText(nome)
                    elif Button=='FileGridVulnerability':
                        self.txtShellFilePath_vulnerato.setText(nome)
                    elif Button=='FileTable1':
                        self.txtShellFilePath_6.setText(nome)

            for node in dom.getElementsByTagName("Parameters"):
                L = node.getElementsByTagName("Parameter")
                for node2 in L:
                    Param = node2.getAttribute("Param")
                    try:
                        Value = node2.getAttribute("Value")
                    except:
                        Value = node2.getAttribute("name")
                    if Param=='CurveType':
                        self.CurveType=Value
                        self.setCurrentCurveType(Value)

            xmlfile.close()
            abil=bool("true")
            self.pushButtonSalvaProgetto.setEnabled(abil)

    def luci(self):

        FilePath= str(self.txtShellFilePath_6.text())
        #FileGridDamages
        FilePath= str(self.txtShellFilePath_5.text())
        if os.path.exists(FilePath):
            self.label_red_danno.hide()
            self.label_green_danno.show()
        else:
            self.label_red_danno.show()
            self.label_green_danno.hide()

        #FileGridVulnerability
        FilePath= str(self.txtShellFilePath_vulnerato.text())
        if os.path.exists(FilePath):
            self.label_red_vuln.hide()
            self.label_green_vuln.show()
        else:
            self.label_red_vuln.show()
            self.label_green_vuln.hide()

    def setListaTipoCurvaVuln(self):
        FileGDB = str(self.txtShellFilePath_2.text())
        if FileGDB != "":
            if self.CheckGeodatabase():
                conn = sqlite3.connect(FileGDB)
                cursor = conn.cursor()
                testoQuery='SELECT VulnID FROM Vulnerability GROUP BY VulnID'
                cursor.execute(testoQuery)
                ListaTipi1 = cursor.fetchall()
                ListaTipi = []
                for row in ListaTipi1:
                    ListaTipi.append(int(row[0]))
                dic_VulnType={}
                self.dic_TypeId={}
                testoQuery2='SELECT * FROM VulnType'
                cursor.execute(testoQuery2)
                ListaDescription = cursor.fetchall()
                if len(ListaDescription)>0:
                    for row in ListaDescription:
                        dic_VulnType[int(row[1])] = str(row[2])
                        self.dic_TypeId[str(row[2])] = int(row[1])
                    ListaDescrizione=[]
                    for num in ListaTipi:
                        ListaDescrizione.append(dic_VulnType[num])
                    self.comboBoxGrafici.clear()
                    self.comboBoxGrafici.addItems(ListaDescrizione)

            else:
                 QMessageBox.information(None, "FloodRisk", self.tr("You must first create the Geodb.Sqlite"))
        else:
             QMessageBox.information(None, "FloodRisk", self.tr("You must first create the Geodb.Sqlite"))

    def setCurrentCurveType(self,ItemText):
        # set currentItem CurveType
        self.CurveType=''
        NumType=self.comboBoxGrafici.count()
        AllItems = [self.comboBoxGrafici.itemText(i) for i in range(NumType)]
        if NumType>0:
            index=-1
            for ii in range(NumType):
                if ItemText==AllItems[ii]:
                    index=ii
            if index>=0:
                self.comboBoxGrafici.setCurrentIndex(index)
                self.CurveType=ItemText

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






