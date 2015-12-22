# coding=utf-8
"""
#-------------------------------------------------------------------------------
# Name:        FloodRiskExceptions
# Purpose:     Custom exception classes for the FloodRisk plug-in
#
# Created:     19/03/2015
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

class HelpFileMissingError(Exception):
    """Raised if a help file cannot be found."""
    pass
