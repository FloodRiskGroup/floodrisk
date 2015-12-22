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
 This script initializes the plugin, making it known to QGIS.
"""

def classFactory(iface):
    # load Floodrisk class from file Floodrisk
    from floodrisk import Floodrisk
    return Floodrisk(iface)
