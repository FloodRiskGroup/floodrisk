"""
#-------------------------------------------------------------------------------
# Name:        CreaGeodatabase
# Purpose:	   creates a new sqlite geodatabase
#
# Created:     12/01/2015
# Copyright:   (c) RSE 2015
# email:       FloodRiskGroup@rse-web.it
#-------------------------------------------------------------------------------
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
import os, shutil
import sys
import sqlite3

def CampiTabella(sql):

    nn=str.find(sql,'(')+1
    pp1=sql[nn:-1]
    campi=str.split(pp1,',')
    numcampi=len(campi)
    NomeCampo=[]
    TipoCampo=[]
    for campo in campi:
        testo=campo
        if campo[-1]== ' ':
            testo=campo[:-1]
        nn=str.find(testo,' ')
        if nn==0:
            testo=campo[1:]
            nn=str.find(testo,' ')
        NomeCampo.append(testo[:nn])
        TipoCampo.append(testo[nn+1:])
    return NomeCampo,TipoCampo

def checkGeodatabaseToTemplate(NomeFileGDB):

    # integrity check of the geodatabase sqlite
    # =================================
    plugin_dir = os.path.dirname(__file__)
    NomeFileTemplate = plugin_dir + os.sep + 'Template.sqlite'

    ok=bool('True')
    errMsg='Ok'

    # check template
    if os.path.exists(NomeFileTemplate):
        # creating/connecting the test_db
        conn = sqlite3.connect(NomeFileTemplate, detect_types=sqlite3.PARSE_DECLTYPES|sqlite3.PARSE_COLNAMES)
        # creating a Cursor
        cur = conn.cursor()
        try:
            NomeTabella='geometry_columns'
            errMsg='Err no table %s in the geodatabase %s' % (NomeTabella,NomeFileTemplate)
            sql="SELECT sql FROM sqlite_master WHERE type='table' AND name='%s';" % (NomeTabella)
            cur.execute(sql)
            Tabella=str(cur.fetchone()[0])
            NameField=[]
            TypeField=[]
            NameField, TypeField = CampiTabella(Tabella)

            FirstField= NameField[0][1:]

            errMsg='Err no geometry features in the geodatabase %s' % (NomeFileTemplate)
            sql="SELECT %s FROM %s" % (FirstField,NomeTabella)
            cur.execute(sql)
            Features=cur.fetchall()

            sql="SELECT * FROM sqlite_master WHERE type='table';"
            cur.execute(sql)
            Lista=cur.fetchall()
            TablesNames=[]
            for rec in Lista:
                TablesNames.append(str(rec[1]).upper())

            for feature in  Features:
                Feat=str(feature[0]).upper()
                errMsg='Err no feature %s in the geodatabase %s' % (Feat,NomeFileTemplate)
                if  Feat in TablesNames:
                    pass
                else:
                    errMsg='Err no feature %s in the geodatabase %s' % (Feat,NomeFileTemplate)
                    ok=bool()
        except:
            ok=bool()

    cur=None
    conn.close()
    if ok:
        errMsg='Ok'
        # checkGeodatabase
        if os.path.exists(NomeFileGDB):
            # creating/connecting the test_db
            conn = sqlite3.connect(NomeFileGDB, detect_types=sqlite3.PARSE_DECLTYPES|sqlite3.PARSE_COLNAMES)
            # creating a Cursor
            cur = conn.cursor()
            try:
                errMsg='Err no geometry features in the geodatabase %s' % (NomeFileGDB)
                NomeTabella='geometry_columns'
                sql="SELECT %s FROM %s" % (FirstField,NomeTabella)
                cur.execute(sql)
                Features=cur.fetchall()
            except:
                ok=bool()
                return ok, errMsg

            sql="SELECT * FROM sqlite_master WHERE type='table';"
            cur.execute(sql)
            Lista=cur.fetchall()
            TablesNames=[]
            for rec in Lista:
                TablesNames.append(str(rec[1]).upper())

            for feature in  Features:
                Feat=str(feature[0]).upper()
                errMsg='Err no feature %s in the geodatabase %s\n Create a new geodatabase' % (Feat,NomeFileGDB)
                if  Feat in TablesNames:
                    try:
                        sql='SELECT * FROM %s' % Feat
                        cur.execute(sql)
                        Lista=cur.fetchall()
                    except:
                        ok=bool()
                        return ok, errMsg

                else:
                    errMsg='Err no feature %s in the geodatabase %s\n Create a new geodatabase' % (Feat,NomeFileGDB)
                    ok=bool()

        cur=None
        conn.close()
        if ok:
            errMsg='Ok'

    return ok, errMsg


def main(self,NomeFileGDB):

    # =================================
    # creating the geodatabase sqlite
    # =================================
    plugin_dir = os.path.dirname(__file__)
    NomeFileSQL = plugin_dir + os.sep + 'ScriptQSL.sql'
    NomeFileTemplate = plugin_dir + os.sep + 'Template.sqlite'

    ok=bool('True')

    if os.path.exists(NomeFileGDB):
        msg1=self.tr("Attention file")
        msg2=self.tr('already exists: execution stopped')
        msg="%s %s %s" % (msg1,NomeFileGDB,msg2)
        QMessageBox.information(None, self.tr("Make Database"), msg)
        ok=bool()
        return ok
    else:

        shutil.copy (NomeFileTemplate, NomeFileGDB)

        ok=bool('True')
        return ok

if __name__ == '__main__':

    NomeFileGDB=''
    ok, errMsg = checkGeodatabaseToTemplate(NomeFileGDB)
    print (ok,errMsg)
