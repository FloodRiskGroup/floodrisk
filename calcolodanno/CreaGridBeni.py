"""
#-------------------------------------------------------------------------------
# Name:        CreaGridBeni
# Purpose:     Create grids with the types of goods
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
#!/usr/bin/env python
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
    # import reference systems module
    import osr

try:
    import numpy
except ImportError:
    import Numeric as numpy

import os
import sys
import time


import sqlite3
from pyspatialite import dbapi2 as db

spatialRef = osr.SpatialReference()


def LoadParametro(testo):
    text=testo[:-1]
    pp=str(text).split('=')
    parametro=pp[1]
    # remove spaces before and after the text
    parametro=parametro.lstrip()
    parametro=parametro.rstrip()
    return parametro

def FeatureType(wkt):

    if wkt:
        dic = {'POINT':1, 'LINESTRING':2, 'POLYGON':3, 'MULTILINESTRING':5, 'MULTIPOLYGON':6}
        pp=str.split(wkt,'(')
        try:
            geom_type=dic[pp[0]]
        except:
            print ('unknown geometry')
            print (wkt)
            geom_type=0
    else:
            print ('geometry field empty')
            geom_type=0

    return geom_type


def CaricaInMemLaySqlite(NomeTabella,curs,ListaCodici,NomeCampoTipo,ListaCampi,dst_ds,app,ini,fin):


    layer_mem=None

    sql=" SELECT "
    # loads the field with the type of good
    sql += ' %s,' %(NomeCampoTipo)
    # loading additional fields
    numfields=len(ListaCampi)
    if numfields>0:
        for field in ListaCampi:
            sql += ' %s,' %(field)
    else:
        return layer_mem
    sql += ' AsText(geom) from %s' % (NomeTabella)

    curs.execute(sql)

    # reading of the type of layer from the first element
    primafeature=curs.fetchone()

    if primafeature!=None:

        wkt=str(primafeature[numfields+1])
        layer_geom_type=FeatureType(wkt)

        layer_mem = dst_ds.CreateLayer('layer_copia', geom_type=layer_geom_type)
        # creating fields
        # field type
        fieldDefn = ogr.FieldDefn('Tipo', ogr.OFTInteger)
        layer_mem.CreateField(fieldDefn)
        # creates additional required fields assuming that are of type Double
        for field in ListaCampi:
            fldDef = ogr.FieldDefn(field, ogr.OFTReal)
            layer_mem.CreateField(fldDef)
        # get the FeatureDefn for the output layer
        featureDefn = layer_mem.GetLayerDefn()

        start_time = time.time()
        # rerunnig the query to start from the first feature
        curs.execute(sql)
        tuttefeature=curs.fetchall()
        numrows=len(tuttefeature)
        elapsed_time = time.time() - start_time

        dcur=float((fin-ini))*0.95
        curr=int(ini+dcur)
        app.setValue(curr)

        kk=-1
        for row in tuttefeature:

            wkt = str(row[numfields+1])

            # performing only for features with geometry
            # -----------------------------------------
            if wkt!='None':

                geom_type=FeatureType(wkt)

                if geom_type>0:

                    # create a new feature
                    feature = ogr.Feature(featureDefn)
                    polyg = ogr.Geometry(geom_type)

                    polyg = ogr.CreateGeometryFromWkt(wkt)

                    # adding the numerical value of the type
                    # -----------------------------------
                    StrCodice=str(row[0])
                    try:
                        itipo=ListaCodici.index(StrCodice)+1
                    except:
                        itipo=0
                    feature.SetField('Tipo', itipo)
                    # adding the value of other fields
                    for i in range(numfields):
                        valore=row[i+1]
                        feature.SetField(ListaCampi[i], valore)

                    feature.SetGeometry(polyg)

                    # add the feature to the output layer
                    layer_mem.CreateFeature(feature)
                    # destroy the geometry and feature and close the data source
                    polyg.Destroy()
                    feature.Destroy()
                else:
                    print ('unknown geometry')
                    print (row)

            else:
                print ('geometry field empty')
                print (row)

        #return ds
        elapsed_time = time.time() - start_time
        testo='elapsed_time=%s final=%s'%(elapsed_time,fin)
        print (testo)
        app.setValue(fin)

    else:

        layer_mem=None


    return layer_mem



def CalcoloValori(FileDEM1,DBfile,app,ini,fin):

    # tolerance below which consider water depth nothing
    # --------------------------------------------------
    TOLL_H=0.000001

    NotErr=bool('True')
    errMsg='OK'

    ListaCodici=''
    matrice=''
    gridtipi=''
    GridValoreStr=''
    GridValoreCon=''
    inNoData=''
    AreaCella=''

    # update ProgressBar
    #---------------------
    curr=ini
    app.setValue(int(curr))

    # legge i dati delle altezze d'acqua
    #===================================
    indataset = gdal.Open( FileDEM1, GA_ReadOnly )
    if indataset is None:
        errMsg= 'Could not open ' + FileDEM1
        #exit with an error code
        NotErr=bool()
        return NotErr, errMsg, ListaCodici, matrice, gridtipi, GridValoreStr, GridValoreCon,inNoData, AreaCella

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
    mask_tiranti=numpy.greater(tiranti, TOLL_H)
    mask_NoTiranti=numpy.less_equal(tiranti, TOLL_H)

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
    curr=ini+(fin-ini)/20.0
    app.setValue(int(curr))

    # loading data from Geodatabase
    #==============================

    dic = {1:'POINT', 2:'LINESTRING', 3:'POLYGON', 6:'MULTIPOLYGON'}

    # creating the dictionary of the type of geometry
    tipoGeom = {'StructurePoly':'MULTIPOLYGON',
               'InfrastrLines':'MULTILINESTRING'}

    TabGeom=['StructurePoly','InfrastrLines']

    # connencting to the database
    conn = sqlite3.connect(DBfile, detect_types=sqlite3.PARSE_DECLTYPES|sqlite3.PARSE_COLNAMES)

    cursor = conn.cursor()
    # make code list of OccupancyType in vulnerability table
    sql='SELECT OccuType FROM Vulnerability GROUP BY OccuType;'
    cursor.execute(sql)
    lista=cursor.fetchall()
    if lista!= None:
        ncodici=len(lista)
        ListaCodici=[]
        for rec in lista:
            ListaCodici.append(rec[0])
    else:
        print ('File ' + DBfile)
        errMsg ='Vulnerability table is empty !!'
        NotErr=bool()
        return NotErr, errMsg, ListaCodici, matrice, gridtipi, GridValoreStr, GridValoreCon,inNoData, AreaCella


    # creating the list of codes in the table StructurePoly
    #------------------------------------------------------------
    sql='SELECT OccuType FROM StructurePoly GROUP BY OccuType;'
    cursor.execute(sql)
    lista=cursor.fetchall()
    if lista!= None:
        ncodici=len(lista)
        ListaCodiciAree=[]
        for rec in lista:
            ListaCodiciAree.append(rec[0])
    else:
        errMsg = 'StructurePoly table is Empty !!'
        NotErr=bool()
        return NotErr, errMsg, ListaCodici, matrice, gridtipi, GridValoreStr, GridValoreCon,inNoData, AreaCella

    # creating the list of codes in the table InfrastrLines
    #-------------------------------------------------------
    sql='SELECT OccuType FROM InfrastrLines GROUP BY OccuType;'
    cursor.execute(sql)
    lista=cursor.fetchall()
    if lista!= None:
        ncodici=len(lista)
        TipiLineari=[]
        for rec in lista:
            TipiLineari.append(rec[0])
    else:
        #print 'File ' + DBfile
        NotErr=bool()
        errMsg =  'InfrastrLines Table is Empty !!'
        #sys.exit(1)
        return NotErr, errMsg, ListaCodici, matrice, gridtipi, GridValoreStr, GridValoreCon,inNoData, AreaCella

    conn.close()

    # update ProgressBar
    #---------------------
    curr=int(ini+(fin-ini)/10.0)
    app.setValue(curr)

    # connecting to SQlite Geodatabase
    conn = db.connect(DBfile)
    curs = conn.cursor()


    listatabelle=[]

    # ======================================
    # load into memory all type StructurePoly
    # ======================================

    # Creating the layer
    # ---------------
    salva=0
    if salva==1:
        driver = ogr.GetDriverByName('ESRI Shapefile')
        nomeshpText='Test.shp'
        if os.path.exists(nomeshpText):
            driver.DeleteDataSource(nomeshpText)

        dst_ds = driver.CreateDataSource(nomeshpText)
        if dst_ds is None:
            NotErr=bool()
            errMsg =  'Could not create file %s' % nomeshpText
            return NotErr, errMsg, ListaCodici, matrice, gridtipi, GridValoreStr, GridValoreCon,inNoData, AreaCella
    else:
        drv = ogr.GetDriverByName( 'Memory' )
        dst_ds = drv.CreateDataSource( 'out' )


    ListaCampi=['Valstr','Valcon']
    NomeCampoTipo='OccuType'
    nnll=0
    iii=curr
    for NomeTabella in TabGeom:

        listatabelle.append(NomeTabella)

        if NomeTabella==TabGeom[0]:
            fff=iii+(fin-ini)/10.0*7.0
            layer_mem_0=CaricaInMemLaySqlite(NomeTabella,curs,ListaCodici,NomeCampoTipo,ListaCampi,dst_ds,app,iii,fff)
            iii=fff
            if layer_mem_0==None:
                NotErr=bool()
                errMsg =  '%s Table is Empty !!' % NomeTabella
                return NotErr, errMsg, ListaCodici, matrice, gridtipi, GridValoreStr, GridValoreCon,inNoData, AreaCella
        if NomeTabella==TabGeom[1]:
            fff=iii+(fin-ini)/10.0
            layer_mem_1=CaricaInMemLaySqlite(NomeTabella,curs,ListaCodici,NomeCampoTipo,ListaCampi,dst_ds,app,iii,fff)
            iii=fff
            if layer_mem_1==None and layer_mem_0==None:
                NotErr=bool()
                errMsg =  '%s Table is Empty !!' % NomeTabella
                return NotErr, errMsg, ListaCodici, matrice, gridtipi, GridValoreStr, GridValoreCon,inNoData, AreaCella

    # closing the database connection
    curs.close()
    conn.close()


    if layer_mem_1!=None:

        # Creating the mask type linear
        #==============================
        #format = 'GTiff'
        format = 'MEM'
        type = GDT_Int16

        driver2 = gdal.GetDriverByName(format)
        driver2.Register()
        gt=indataset.GetGeoTransform()

        ds = driver2.Create('tipilineari.tif', indataset.RasterXSize, indataset.RasterYSize, 1, type)
        if gt is not None and gt != (0.0, 1.0, 0.0, 0.0, 0.0, 1.0):
            ds.SetGeoTransform(gt)

        # sets the reference system equal to the depth map of water: if it lacks sets the default
        if prj is not None and len(prj) > 0:
            ds.SetProjection(prj)
        else:
            prj= spatialRef.ExportToWkt()
            ds.SetProjection(prj)

        # Rasterize
        iBand=1
        outband = ds.GetRasterBand(iBand)

        # Rasterize
        err = gdal.RasterizeLayer(ds, [1], layer_mem_1,
                burn_values=[0],
                options=["ATTRIBUTE=Tipo"])
        if err != 0:
            raise Exception("error rasterizing layer: %s" % err)

        gridtipi1 = outband.ReadAsArray()

        # insert value 1 to linear grid
        GridLineari=numpy.choose(numpy.greater(gridtipi1,0),(gridtipi1,1))
        # setting zero for areas outside the area flooded
        GridLineari=numpy.choose(mask_NoTiranti,(GridLineari,0))

        ds = None
        outband = None

    # update ProgressBar
    #---------------------
    curr=ini+(fin-ini)/10.0*9.1
    app.setValue(int(curr))


    # create the new file for type areal
    #===================================
    #format = 'GTiff'
    format = 'MEM'
    type = GDT_Int16

    driver2 = gdal.GetDriverByName(format)
    driver2.Register()
    gt=indataset.GetGeoTransform()

    FileDEM_out='TipoAree.tif'

    ds = driver2.Create(FileDEM_out, indataset.RasterXSize, indataset.RasterYSize, 1, type)
    if gt is not None and gt != (0.0, 1.0, 0.0, 0.0, 0.0, 1.0):
        ds.SetGeoTransform(gt)

    # sets the reference system equal to the depth map of water: if it lacks sets the default
    if prj is not None and len(prj) > 0:
        ds.SetProjection(prj)
    else:
        prj= spatialRef.ExportToWkt()
        ds.SetProjection(prj)

    # Rasterize
    iBand=1
    outband = ds.GetRasterBand(iBand)

    # Rasterize
    # creating the mask with NoData and 0 at the points that are not NoData
    mask_NoData1= numpy.choose(numpy.not_equal(tiranti,inNoData),(tiranti,0))
    outband.WriteArray(mask_NoData1, 0, 0)

    # rasterize type areal
    err = gdal.RasterizeLayer(ds, [1], layer_mem_0,
            burn_values=[0],
            options=["ATTRIBUTE=Tipo"])
    if err != 0:
        raise Exception("error rasterizing layer: %s" % err)

    if layer_mem_1!=None:
        # rasterize type linear
        err = gdal.RasterizeLayer(ds, [1], layer_mem_1,
                burn_values=[0],
                options=["ATTRIBUTE=Tipo"])
        if err != 0:
            raise Exception("error rasterizing layer: %s" % err)

    # applying NoData in the areas without water depth
    gridtipi1 = outband.ReadAsArray()
    gridtipi= numpy.choose(mask_NoTiranti,(gridtipi1,inNoData))

    # SAVE THE MAP OF THE TYPES OF AREA
    # =================================
    ds = None
    outband = None

    # CREATE THE GRID OF VALUES
    # =========================

    #format = 'GTiff'
    format = 'MEM'
    type = GDT_Float32

    driver2 = gdal.GetDriverByName(format)
    driver2.Register()
    gt=indataset.GetGeoTransform()

    ds = driver2.Create('valori.tif', indataset.RasterXSize, indataset.RasterYSize, 2, type)
    if gt is not None and gt != (0.0, 1.0, 0.0, 0.0, 0.0, 1.0):
        ds.SetGeoTransform(gt)

    # sets the reference system equal to the depth map of water: if it lacks sets the default
    if prj is not None and len(prj) > 0:
        ds.SetProjection(prj)
    else:
        prj= spatialRef.ExportToWkt()
        ds.SetProjection(prj)

    for k in range(2):
        iBand=k+1
        Grid=numpy.zeros((rows,cols),numpy.float32)
        if k==0:
            CampoValore=["ATTRIBUTE=Valstr"]
        else:
            CampoValore=["ATTRIBUTE=Valcon"]
        outband = ds.GetRasterBand(iBand)

        # Rasterize
        outband.WriteArray(Grid, 0, 0)

        # creating a map of the areal values per square meter
        # -------------------------------------------------
        err = gdal.RasterizeLayer(ds, [iBand], layer_mem_0,
                burn_values=[0],
                options=CampoValore)
        if err != 0:
            raise Exception("error rasterizing layer: %s" % err)


        if layer_mem_1!=None:
            # adding a map of values for linear meter
            # -------------------------------------------------
            err = gdal.RasterizeLayer(ds, [iBand], layer_mem_1,
                    burn_values=[0],
                    options=CampoValore)
            if err != 0:
                raise Exception("error rasterizing layer: %s" % err)

            # reading the values obtained
            Grid = outband.ReadAsArray()

            # transforming all the values per square meter
            conv=1.0/pixelWidth
            tmp=Grid*GridLineari
            tmp=tmp*conv
            Grid= numpy.choose(numpy.equal(GridLineari,1),(Grid,tmp))
        else:
            # Reading grid
            Grid = outband.ReadAsArray()

        # setting to zero the areas without water depth
        Grid= numpy.choose(mask_NoTiranti,(Grid,0))
        if k==0:
            # values of the structure
            # ----------------------
            GridValoreStr=Grid
        else:
            # content values
            # --------------------
            GridValoreCon=Grid
        outband = None
    ds = None

    # update ProgressBar
    #---------------------
    curr=ini+(fin-ini)/10.0*9.5
    app.setValue(int(curr))

    # CALCULATE THE VALUE OF PIXEL FOR TYPE
    # ====================================
    ValStrItipo=[]
    ValConItipo=[]
    CodTipo=[]

    # writes the txt file with the values
    # ------------------------------
    numtipi=len(ListaCodici)

    # the results are stored in the array and passed to the calling script
    matrice=[]
    for i in range(numtipi):
        itipo=i+1
        maskTipo=numpy.equal(gridtipi,itipo)

        TMP1=GridValoreStr*maskTipo
        valore1=TMP1.sum()*AreaCella
        valore1=round(valore1 / 100.0) * 100.0
        ValStrItipo.append(valore1)

        TMP1=GridValoreCon*maskTipo
        valore2=TMP1.sum()*AreaCella
        valore2=round(valore2 / 100.0) * 100.0
        ValConItipo.append(valore2)
        CodiceTipo=ListaCodici[i]
        CodTipo.append(CodiceTipo)

        riga=[]
        riga.append(CodiceTipo)
        riga.append(valore1)
        riga.append(valore2)
        matrice.append(riga)

    # update ProgressBar
    #---------------------
    curr=fin
    app.setValue(int(curr))


    return NotErr, errMsg, ListaCodici, matrice, gridtipi, GridValoreStr, GridValoreCon,inNoData, AreaCella


