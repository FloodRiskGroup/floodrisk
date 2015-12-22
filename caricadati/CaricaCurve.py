"""
#-------------------------------------------------------------------------------
# Name:        CaricaCurve
# Purpose:     Load alphanumeric data into geo-database
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
#!/usr/bin/env python
import sqlite3
import sys
import string

# to reading cvs file
import csv

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

def CaricaTabella(cur,NomeFile,NomeTabella,sql_delete):

    finp = open(NomeFile)

    # Reading csv file
    csv_reader = csv.reader(finp, delimiter=';')

    headers = csv_reader.next()
    # delete parts of names after the first space
    NameFieldCsv=[]
    for name0 in headers:
        name=str.split(name0,' ')[0]
        NameFieldCsv.append(name)

    print NameFieldCsv

    num_cols=len(NameFieldCsv)

    # creates the dictionary to associate the name to the number of the column
    numcol = {}
    k=-1
    for name in NameFieldCsv:
        k+=1
        numcol [name]=k

    # Loads data
    #--------------
    sql="SELECT sql FROM sqlite_master WHERE type='table' AND name='%s';" % (NomeTabella)
    cur.execute(sql)
    TipoTabella=str(cur.fetchone()[0])

    NameField=[]
    TypeField=[]
    NameField, TypeField = CampiTabella(TipoTabella)

    NumFields=len(NameField)

    dic_fiels = {}
    dic_fiels_type = {}
    CampiInsert=[]
    for i in range(NumFields):
        for NameCsv in NameFieldCsv:
            if str.upper(NameField[i])==str.upper(NameCsv):
                # todo : check the type
                dic_fiels[NameCsv]=NameField[i]
                dic_fiels_type[NameCsv]=TypeField[i]
                CampiInsert.append(NameCsv)
                break
    # discards the field OBJECTID
    if 'OBJECTID' in NameField:
        indiceid=NameField.index('OBJECTID')
        NameField.remove('OBJECTID')
        TypeField.remove(TypeField[indiceid])

    NumFields=len(CampiInsert)

    if NumFields>0:
        cur.execute(sql_delete)

    for row in csv_reader:
        # writing instruction sql
        sql = "INSERT INTO " + NomeTabella +" ("
        # adds the names of the fields
        for i in range(NumFields):
            if i<(NumFields-1):
                sql +="'"+dic_fiels[CampiInsert[i]]+"',"
            else:
                sql +="'"+dic_fiels[CampiInsert[i]]+"') VALUES ("
        for i in range(NumFields):
            col=numcol [CampiInsert[i]]
            if dic_fiels_type[CampiInsert[i]] == 'INTEGER':
                sql += "%d" % int(row[col])
            elif dic_fiels_type[CampiInsert[i]] == 'REAL':
                sql += "%.6f" % float(row[col])
            else:
                stringa=row[col]
                stringa=stringa.decode('unicode-escape')
                stringa=str(stringa).replace("'"," ")
                sql += "'%s" % stringa+"'"
            if i<(NumFields-1):
                sql +=' ,'
            else:
                sql +=' );'

        cur.execute(sql)
    finp.close()

def main(FilesList,UpLoad):

    # files
    mydb_path=FilesList[0]
    FileTabFloodFatalityRates=FilesList[1]
    FileTabFloodSeverity=FilesList[2]
    FileTabTypeCur=FilesList[3]
    FileTabDepthDamage=FilesList[4]
    FileCategorieBeni=FilesList[5]

    NotErr=bool('True')
    errMsg='OK'

    conn = sqlite3.connect(mydb_path, detect_types=sqlite3.PARSE_DECLTYPES|sqlite3.PARSE_COLNAMES)
    cur = conn.cursor()

    try:

        # Empty and load table of Flood Fatality
        # ==============================
        if  UpLoad[1] >0:
            tableName='FatalityRate'
            sql_delete='DELETE FROM %s' % tableName
            CaricaTabella(cur,FileTabFloodFatalityRates,tableName,sql_delete)
            conn.commit()

        # Empty and load table of FloodSeverity
        # =============================
        if  UpLoad[2] >0:
            tableName='FloodSeverity'
            sql_delete='DELETE FROM %s' % tableName
            CaricaTabella(cur,FileTabFloodSeverity,tableName,sql_delete)
            conn.commit()

        # Empty and load domains of OccupancyType
        # =======================================
        if  UpLoad[5] >0:
            NameDomain='OccupancyType'
            sql="SELECT NumDomain FROM NomiDomains WHERE NomeDomain='%s'" % (NameDomain)
            cur.execute(sql)
            NumDomain=int(cur.fetchone()[0])
            tableName='Domains'
            sql_delete='DELETE FROM %s WHERE NumDomain=%d' % (tableName,NumDomain)
            CaricaTabella(cur,FileCategorieBeni,tableName,sql_delete)
            conn.commit()

        # Empty and load  table of vulnerability type
        # ==========================================
        if  UpLoad[3] >0:
            tableName='VulnType'
            sql_delete='DELETE FROM %s' % tableName
            CaricaTabella(cur,FileTabTypeCur,tableName,sql_delete)
            conn.commit()


        # Load vulnerability type
        # ========================
        if  UpLoad[4] >0:

            # Reading ID
            finp = open(FileTabDepthDamage)
            # Reading from csv file
            csv_reader = csv.reader(finp, delimiter=';')
            headers = csv_reader.next()

            ListaVulnID=[]
            for row in csv_reader:
                VulnID=int(row[0])
                if VulnID not in ListaVulnID:
                    ListaVulnID.append(VulnID)

            # Empty and load Vulnerability table where new type is loading
            # ----------------------------------------------------
            tableName='Vulnerability'
            for VulnID in ListaVulnID:
                sql_delete='DELETE FROM %s WHERE VulnID=%d' % (tableName,VulnID)
                cur.execute(sql_delete)

            CaricaTabella(cur,FileTabDepthDamage,tableName,sql_delete)
            conn.commit()


    except:
        # Get the most recent exception
        exceptionType, exceptionValue, exceptionTraceback = sys.exc_info()
        # Exit the script and print an error telling what happened.
        errMsg= "Error %s" % (exceptionValue)
        NotErr=bool()
        return NotErr, errMsg



    cur=None
    conn.close()

    return NotErr, errMsg


