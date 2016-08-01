# -*- coding: utf-8 -*-
"""
/***************************************************************************
Reading CSV
A QGIS plugin
                              -------------------
begin                : 2016-04-08
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
import os
import sys

class FileNotFoundException(Exception):
    pass

class FileIOException(Exception):
    pass

class UnknownFileFormatException(Exception):
    pass

class InvalidFileExtension(Exception):
    pass

