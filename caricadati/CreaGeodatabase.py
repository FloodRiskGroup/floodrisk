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

from pyspatialite import dbapi2 as db

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
