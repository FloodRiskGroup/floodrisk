#!/usr/bin/env python
"""
/***************************************************************************
 FingEPSG
                             -------------------
        begin                : 2018-01-19
        copyright            : (C) 2018 by RSE
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
import sys
import os

# module for reading csv files
import csv

def FindEPSG(prj_txt):

    """
    Find EPSG
    """
    # inizializza
    NumEPSG=None

    # Rean EPSG list
    # ------------------------------------------
    Lista_EPSG=[]
    Lista_EPSG_name=[]
    Lista_i=[]

    # Read from csv
    dir_script= os.path.dirname(os.path.realpath(__file__))
    file_csv= os.path.realpath(dir_script)+os.sep+'Lista_srid.csv'

    fin=open(file_csv,'r')
    reader = csv.reader(fin,delimiter=';')
    headers = reader.next()

    Lista_EPSG=[]
    Lista_EPSG_name=[]
    Lista_i=[]
    ii=-1
    for row in reader:
        ii+=1
        Lista_i.append(ii)
        Lista_EPSG.append(row[0])
        Lista_EPSG_name.append(row[1])

    fin.close()

    pp=prj_txt.split(',')[0]
    NameEPSG=pp.split('"')[1]
    List_NameEPSG=NameEPSG.split('_')

    for keyword in List_NameEPSG:
        ListRemove=[]
        txt='key=%s n=%d' % (keyword,len(Lista_i))
        print (txt)
        for ii in Lista_i:
            if keyword not in Lista_EPSG_name[ii]:
                ListRemove.append(ii)
        for ii in ListRemove:
            Lista_i.remove(ii)

    nn=len(Lista_i)
    if nn==1:
        NumEPSG=int(Lista_EPSG[Lista_i[0]])

    return NumEPSG,NameEPSG

