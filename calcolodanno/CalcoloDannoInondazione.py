"""
#-------------------------------------------------------------------------------
# Name:        CalcoloDannoInondazione
# Purpose:     Estimate of flood damage
#
# Created:     22/01/2015
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
import sys
try:
    from osgeo import gdal
    from osgeo.gdalconst import *
    gdal.TermProgress = gdal.TermProgress_nocb
    from osgeo import ogr
    from osgeo import osr
except ImportError:
    import gdal
    import ogr
    from gdalconst import *
    import osr

try:
    import numpy
except ImportError:
    import Numeric as numpy

import os, math
import sys


spatialRef = osr.SpatialReference()

import CreaGridBeni

import sqlite3

def CaricaCodedDomains(DBfile):

    consql = sqlite3.connect(DBfile, detect_types=sqlite3.PARSE_DECLTYPES|sqlite3.PARSE_COLNAMES)
    cursql = consql.cursor()
    NomeTabella='NomiDomains'
    sql='SELECT NumDomain FROM '+ NomeTabella
    sql+=" WHERE (NomeDomain='OccupancyType');"
    numDom=cursql.execute(sql).fetchone()[0]

    NomeTabella='Domains'
    sql='SELECT code,Description FROM '+ NomeTabella
    sql+=' WHERE (NumDomain=%d);' % (numDom)
    records=cursql.execute(sql).fetchall()
    Codici=[]
    Descrizione=[]
    if records!=None:
        for rec in records:
            Codici.append(rec[0])
            Descrizione.append(rec[1])

    cursql.close()
    consql.close()

    return Codici,Descrizione


def LoadParametro(testo):
    text=testo[:-1]
    pp=str(text).split('=')
    parametro=pp[1]
    # remove spaces before and after the text
    parametro=parametro.lstrip()
    parametro=parametro.rstrip()
    return parametro


def main(Lista,app):

    FileDEM1=Lista[0]
    DBfile=Lista[1]
    NomeFileGridVulnerato=Lista[2]
    NomeFileGridDanno=Lista[3]
    NomeFileTabella=Lista[4]
    # ID of vulnerability curve to be used
    IDTipiCurveScelto=Lista[5]

    NotErr=bool('True')
    errMsg='OK'
    TotalDamage=0.0

    max_lim=999.0

    Codici, Descrizione = CaricaCodedDomains(DBfile)

    dic = {}
    for i in range(len(Codici)):
        dic[Codici[i]]= Descrizione[i]

    ini=1
    fin=30
    curr=ini
    app.setValue(int(curr))

    NotErr, errMsg,ListaCodici, valori, TipiArray, GridValoreStr, GridValoreCon, Nodata, AreaCella = CreaGridBeni.CalcoloValori(FileDEM1,DBfile,app,ini,fin)

    if NotErr:

        # update ProgressBar
        #---------------------
        curr=fin
        app.setValue(int(curr))

        # reading data of the water depth
        #=================================
        indataset = gdal.Open( FileDEM1, GA_ReadOnly )
        if indataset is None:
            errMsg = 'Could not open ' + FileDEM1
            NotErr= bool()
            return NotErr, errMsg

        prj = indataset.GetProjectionRef()

        geotransform = indataset.GetGeoTransform()

        originX = geotransform[0]
        originY = geotransform[3]
        pixelWidth = geotransform[1]
        pixelHeight = geotransform[5]
        cols=indataset.RasterXSize
        rows=indataset.RasterYSize
        bands=indataset.RasterCount
        iBand = 1
        inband = indataset.GetRasterBand(iBand)
        inNoData= inband.GetNoDataValue()
        # reading the entire file at once
        tiranti = inband.ReadAsArray(0, 0, cols, rows).astype(numpy.float32)

        # creating the mask of water depth
        mask_tiranti=numpy.greater(tiranti, -10)
        numcell=numpy.sum(mask_tiranti)
        # creating the mask with NoData and zeros at the points that are not NoData
        mask_NoData= numpy.choose(numpy.not_equal(tiranti,inNoData),(tiranti,0))

        AreaCella=-pixelWidth*pixelHeight
        numcel=numpy.zeros(8,numpy.int32)
        numceltot=numpy.sum(mask_tiranti)
        AreaBacinoTot=numceltot*AreaCella/1000000

        # creating an array with values False at the points nodata
        maskarray=numpy.ma.masked_equal(tiranti,inNoData)
        # calculating statistics
        ValMax=numpy.max(maskarray)
        ValMed=numpy.mean(maskarray)
        ValMin=numpy.min(maskarray)

        # update ProgressBar
        #---------------------
        curr=31
        app.setValue(int(curr))


        # ===========================
        # CALCULATE THE VULNERABILITY
        # ===========================
        # calculating the vulnerability requires combining the data of water depth
        # with curves of vulnerability of each type

        # connencting to the database
        # connection with sqlite3
        conn = sqlite3.connect(DBfile, detect_types=sqlite3.PARSE_DECLTYPES|sqlite3.PARSE_COLNAMES)

        cursor = conn.cursor()

        numtipibeni=len(ListaCodici)

        # ===================================================
        # performing the calculation for the type of property
        # ===================================================

        NomeTabella='Vulnerability'
        NomeCampoTipo='OccuType'

        # dimension arrays of Vulnerability
        GridVulnStr=numpy.zeros((rows,cols),numpy.float32)
        GridVulnCon=numpy.zeros((rows,cols),numpy.float32)

        # Type damage 1: Structure, Type damage 2: Contents
        TipoDanno=[1,2]
        # Type Vulnerability 1: Water depth, Type Vulnerability 2: velocity
        TipoVuln=[1,2]


        # dimension arrays of damage
        # -------------------------------
        GridDannoStr=numpy.zeros((rows,cols),numpy.float32)
        GridDannoCon=numpy.zeros((rows,cols),numpy.float32)

        NumCelTipo=[]
        # Calculates the number of pixels by type
        for i in range(numtipibeni):
            itipo=i+1
            mask_tipo=numpy.equal(TipiArray,itipo)
            NumCelTipo.append (mask_tipo.sum())

        # update ProgressBar
        #---------------------
        ini=32
        fin=90
        curr=ini
        app.setValue(int(curr))

        dcur=float((fin-ini))/float (numtipibeni)

        # start cycle
        for kk in range(numtipibeni):

            if NumCelTipo[kk]>0:

                tipologia=kk+1
                mask_tipo=numpy.equal(TipiArray,tipologia)
                numerocelletipo=mask_tipo.sum()

                # creating masks for water depth
                CodiceTipo=ListaCodici[kk]

                # cycle for type of damage
                for tipdanno in range(2):

                    GridVuln=numpy.zeros((rows,cols),numpy.float32)

                    # select
                    testoSQL='SELECT HydroValue,Damage FROM '+ NomeTabella + " WHERE " + NomeCampoTipo + "='" + CodiceTipo +"'"
                    testoSQL= testoSQL+ " AND VulnID=%d" % (IDTipiCurveScelto)
                    testoSQL= testoSQL+ " AND DmgType=%d" % (TipoDanno[tipdanno])
                    testoSQL= testoSQL+ " AND VulnType=%d" % (TipoVuln[0])
                    testoSQL=testoSQL + " ORDER BY HydroValue;"
                    cursor.execute(testoSQL)
                    TabVuln=cursor.fetchall()
                    #if TabVuln!= None:
                    if len(TabVuln)> 0:
                        LimAlt=[]
                        Danno=[]
                        for rec in TabVuln:
                            LimAlt.append(rec[0])
                            Danno.append(rec[1])
                        if LimAlt[-1]<max_lim:
                            LimAlt.append(max_lim)
                            Danno.append(rec[1])
                        numerolim=len(LimAlt)

                        if numerolim>0:
                            numcel=numpy.zeros(numerolim,numpy.int32)
                            mask_alt=numpy.zeros((numerolim,rows,cols),numpy.bool)
                            # at the points nodata of water depth insert the upper limit value
                            # to avoid being counted as less than the minimum
                            mask_tmp=numpy.choose(numpy.equal(tiranti,inNoData),(tiranti,LimAlt[numerolim-1]) )
                            # the mask index 0, is the one that means values of depth of water below the minimum
                            mask_alt[0]=numpy.less(mask_tmp, LimAlt[0])
                            # calculating the percentage of damage
                            GridVuln= numpy.choose(numpy.equal(mask_alt[0],1),(GridVuln,Danno[0]))
                            # account the number of pixels
                            numcel[0]=numpy.sum(mask_alt[0])
                            for i in range (1,numerolim):
                                # each mask indicates the cells with a value lower than the limit
                                mask_alt[i]=numpy.less(mask_tmp, LimAlt[i])
                                for j in range (i):
                                    mask_alt[i]=mask_alt[i]-mask_alt[j]
                                numcel[i]=numpy.sum(mask_alt[i])
                                # calculating the percentage of damage
                                GridVuln= numpy.choose(numpy.equal(mask_alt[i],1),(GridVuln,Danno[i]))
                                somma=GridVuln.sum()

                            numverifica=numpy.sum(numcel)
                            if numverifica<>numceltot:
                                errMsg= 'Attention problem in value of water depth'
                                #exit with an error code
                                NotErr=bool()
                                return NotErr, errMsg

                            # calculating the percentage of damage
                            if tipdanno==0:
                                GridVulnStr=GridVulnStr + mask_tipo*GridVuln
                            else:
                                GridVulnCon=GridVulnCon +mask_tipo*GridVuln
                    # if missing the curve of damage
                    else:
                        GridVuln=numpy.zeros((rows,cols),numpy.float32)
                        if tipdanno==0:
                            GridVulnStr=GridVulnStr + mask_tipo*GridVuln
                        else:
                            GridVulnCon=GridVulnCon +mask_tipo*GridVuln

            # update ProgressBar
            #---------------------
            curr=ini+dcur*(kk+1)
            app.setValue(int(curr))

        # closing the database connection
        cursor= None
        conn = None

        # calculate the damage per square meter
        # -----------------------------------
        GridDannoStr=GridValoreStr*GridVulnStr
        GridDannoCon=GridValoreCon*GridVulnCon

        # Calculate TOTAL Damage
        # ----------------------
        # calculating the total value of the damage to structure
        danno_tipo=numpy.choose(numpy.equal(tiranti,inNoData),(GridDannoStr,0))
        valore1=danno_tipo.sum()*AreaCella
        valore1=round(valore1 / 100.0) * 100.0

        # calculating the total value of damage to the contents
        danno_tipo=numpy.choose(numpy.equal(tiranti,inNoData),(GridDannoCon,0))
        valore2=danno_tipo.sum()*AreaCella
        valore2=round(valore2 / 100.0) * 100.0

        TotalDamage=valore1+valore2

        # saves the partial data
        # writes the txt file with the values
        # ------------------------------
        filepath=os.path.dirname(NomeFileTabella)
        if not os.path.exists(filepath):
            os.mkdir(filepath)

        fildanno=open(NomeFileTabella,'w')
        text='Code;Description;Valstr_Euro;ValCon_Euro;DamageStr_Euro;DamageCon_Euro\n'
        fildanno.write(text)
        #print text
        for i in range(numtipibeni):

            CodiceTipo=ListaCodici[i]
            valore1=0.0
            valore2=0.0
            itipo=i+1

            if NumCelTipo[i]>0:

                danno_tipo=numpy.choose(numpy.not_equal(TipiArray,itipo),(GridDannoStr,0))
                # calculating the value of the damage to structure for each type of structure
                valore1=danno_tipo.sum()*AreaCella
                valore1=round(valore1 / 100.0) * 100.0

                danno_tipo=numpy.choose(numpy.not_equal(TipiArray,itipo),(GridDannoCon,0))
                # calculating the value of damage to the contents for each type of structure
                valore2=danno_tipo.sum()*AreaCella
                valore2=round(valore2 / 100.0) * 100.0

            text='%s;%s;%d;%d;%d;%d\n' %(CodiceTipo,dic[CodiceTipo],valori[i][1],valori[i][2],valore1,valore2)
            fildanno.write(text)
            #print text


        fildanno.close()

        # update ProgressBar
        #---------------------
        curr=fin+1
        app.setValue(int(curr))

        # saves the map of percentage of damage
        #--------------------------------------
        format = 'GTiff'
        driver = gdal.GetDriverByName(format)
        type = GDT_Float32
        gt=indataset.GetGeoTransform()

        FileDEM_out=NomeFileGridVulnerato
        filepath=os.path.dirname(FileDEM_out)
        if not os.path.exists(filepath):
            os.mkdir(filepath)

        ds = driver.Create(FileDEM_out, indataset.RasterXSize, indataset.RasterYSize, 2, type)
        if gt is not None and gt != (0.0, 1.0, 0.0, 0.0, 0.0, 1.0):
            ds.SetGeoTransform(gt)

        # sets the reference system equal to the depth map of water: if it lacks sets the default
        if prj is not None and len(prj) > 0:
            ds.SetProjection(prj)
        else:
            prj= spatialRef.ExportToWkt()
            ds.SetProjection(prj)

        # writing raster
        iBand=1
        outband = ds.GetRasterBand(iBand)
        GridVulnStr= numpy.choose(numpy.equal(tiranti,inNoData),(GridVulnStr,inNoData))
        outband.WriteArray(GridVulnStr, 0, 0)

        outband.FlushCache()
        outband.SetNoDataValue(inNoData)
        outband.GetStatistics(0,1)
        outband = None

        # writing raster
        iBand=2
        outband = ds.GetRasterBand(iBand)
        GridVulnCon= numpy.choose(numpy.equal(tiranti,inNoData),(GridVulnCon,inNoData))
        outband.WriteArray(GridVulnCon, 0, 0)

        outband.FlushCache()
        outband.SetNoDataValue(inNoData)
        outband.GetStatistics(0,1)
        outband = None

        ds = None

        # update ProgressBar
        #---------------------
        curr=fin+8
        app.setValue(int(curr))

        # make grid of damage
        #========================
        FileDEM_out=NomeFileGridDanno

        filepath=os.path.dirname(FileDEM_out)
        if not os.path.exists(filepath):
            os.mkdir(filepath)


        ds = driver.Create(FileDEM_out, indataset.RasterXSize, indataset.RasterYSize, 2, type)
        if gt is not None and gt != (0.0, 1.0, 0.0, 0.0, 0.0, 1.0):
            ds.SetGeoTransform(gt)

        # sets the reference system equal to the depth map of water: if it lacks sets the default
        if prj is not None and len(prj) > 0:
            ds.SetProjection(prj)
        else:
            prj= spatialRef.ExportToWkt()
            ds.SetProjection(prj)

        # writing raster
        iBand=1
        outband = ds.GetRasterBand(iBand)
        GridDannoStr= numpy.choose(numpy.equal(tiranti,inNoData),(GridDannoStr,inNoData))
        outband.WriteArray(GridDannoStr, 0, 0)

        outband.FlushCache()
        outband.SetNoDataValue(inNoData)
        outband.GetStatistics(0,1)
        outband = None

        # writing raster
        iBand=2
        outband = ds.GetRasterBand(iBand)
        GridDannoCon= numpy.choose(numpy.equal(tiranti,inNoData),(GridDannoCon,inNoData))
        outband.WriteArray(GridDannoCon, 0, 0)

        outband.FlushCache()
        outband.SetNoDataValue(inNoData)
        outband.GetStatistics(0,1)
        outband = None

        ds = None


        # update ProgressBar
        #---------------------
        curr=fin+10
        app.setValue(int(curr))


        return NotErr, errMsg,TotalDamage

    else:

        return NotErr, errMsg,TotalDamage


