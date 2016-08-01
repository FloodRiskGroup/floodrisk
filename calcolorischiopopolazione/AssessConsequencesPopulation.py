"""
#-------------------------------------------------------------------------------
# Name:        AssessConsequencesPopulatione
# Purpose:     Assess Consequences to Population
#
# Created:     23/01/2015
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

spatialRef = osr.SpatialReference()

import sqlite3
from pyspatialite import dbapi2 as db

# to writing cvs file
import locale

def set_csv_separator():
    locale.setlocale(locale.LC_ALL, '') # set to user's locale, not "C"
    dec_pt_chr = locale.localeconv()['decimal_point']
    if dec_pt_chr == ",":
        list_delimiter = ";"
    else:
        list_delimiter = ","
    return list_delimiter

def CampiSHP(layer,feat):

    feat_defn = layer.GetLayerDefn()
    NumFields=feat_defn.GetFieldCount()
    NameField=[]
    TypeField=[]
    NumFields=feat.GetFieldCount()
    for i in range(NumFields):
        field_defn = feat_defn.GetFieldDefn(i)
        NameField.append(field_defn.GetName())

        if field_defn.GetType() == ogr.OFTInteger:
            TypeField.append('INTEGER')
        elif field_defn.GetType() == ogr.OFTReal:
            TypeField.append('REAL')
        elif field_defn.GetType() == ogr.OFTString:
            width=field_defn.GetWidth()
            stringa='VARCHAR(%d)' % (width)
            TypeField.append(stringa)
        else:
            TypeField.append('VARCHAR(20)')

    return NameField,TypeField


def ControlloCongruenzaGRID(OriginData,indataset,gt):
    toll=0.5
    toll2=0.001
    ok=bool('True')
    # OriginData=[originX,originY,pixelWidth,pixelHeight,cols,rows]
    if abs(OriginData[0] - gt[0])>toll:
        print 'originX non congruente con OriginData'
        ok=bool()
    if abs(OriginData[1] - gt[3])>toll:
        print 'originY non congruente con OriginData'
        ok=bool()
    if abs(OriginData[2] - gt[1])>toll2:
        print 'pixelWidth non congruente con OriginData'
        ok=bool()
    if abs(OriginData[3] - gt[5])>toll2:
        print 'pixelHeight non congruente con OriginData'
        ok=bool()
    if OriginData[4] <> indataset.RasterXSize:
        print 'cols non congruente con OriginData'
        ok=bool()
    if OriginData[5]<>indataset.RasterYSize:
        print 'rows non congruente con OriginData'
        ok=bool()
    return ok


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
    # removes spaces before and after the text
    parametro=parametro.lstrip()
    parametro=parametro.rstrip()
    return parametro

def FeatureType(wkt):
    dic = {'POINT':1, 'LINESTRING':2, 'POLYGON':3, 'MULTILINESTRING':5, 'MULTIPOLYGON':6}
    pp=str.split(wkt,'(')
    geom_type=dic[pp[0]]
    return geom_type

def LoadSqliteLayer(TableName,curs,FieldList,dst_ds):

    # Load in a layer a Sqlite geotable

    sql=" SELECT "
    # list fields
    numfields=len(FieldList)
    if numfields>0:
        for field in FieldList:
            sql += ' %s,' %(field)
    else:
        return
    sql += ' AsText(geom) from %s' % (TableName)

    curs.execute(sql)

    # Read geomtype
    primafeature=curs.fetchone()
    wkt=str(primafeature[numfields])
    layer_geom_type=FeatureType(wkt)

    layer_mem = dst_ds.CreateLayer('layer_copy', geom_type=layer_geom_type)

    # make fiels
    # creates additional required fields taking of type Double
    for field in FieldList:
        fldDef = ogr.FieldDefn(field, ogr.OFTReal)
        layer_mem.CreateField(fldDef)
    # get the FeatureDefn for the output layer
    featureDefn = layer_mem.GetLayerDefn()

    # scan the features
    # redo the query to start from the first feature
    curs.execute(sql)

    k=-1
    for row in curs:

        wkt = str(row[numfields])

        # run only for features with geometry
        # -----------------------------------
        if wkt!=None:

            geom_type=FeatureType(wkt)

            # create a new feature
            feature = ogr.Feature(featureDefn)
            polyg = ogr.Geometry(geom_type)

            polyg = ogr.CreateGeometryFromWkt(wkt)

            # adds the value of the fields
            for i in range(numfields):
                valore=row[i]
                feature.SetField(FieldList[i], valore)

            feature.SetGeometry(polyg)

            # add the feature to the output layer
            layer_mem.CreateFeature(feature)
            # destroy the geometry and feature and close the data source
            polyg.Destroy()
            feature.Destroy()

    return layer_mem



def main(Lista,app):

    FileDEM1=Lista[0]
    NomeGridVelocita = Lista[1]
    NomeFileWornTime = Lista[2]
    DBfile=Lista[3]
    NomeFileGridPAR=Lista[4]
    NomeFileTabella2=Lista[5]
    TipoUnderstanding=Lista[6]

    NotErr=bool('True')
    errMsg='OK'
    NumLoss_notRound=0.0

    # field separator
    sep=set_csv_separator()

    Codici, Descrizione = CaricaCodedDomains(DBfile)

    dic = {}
    for i in range(len(Codici)):
        dic[Codici[i]]= Descrizione[i]

    ini=2
    fin=8
    curr=ini
    app.setValue(int(curr))

    # connecting Geodatabase Sqlite
    # ===========================
    conn = db.connect(DBfile)
    curs = conn.cursor()

    # read from the database the data of interest
    # --------------------------------------
    NomeTabella='FloodSeverity'
    sql='PRAGMA table_info (%s)' % (NomeTabella)
    curs.execute(sql)
    records = curs.fetchall()

    ListaCampi=['Num','DV','hrate']

    # reading the sequential number of the fields of interest
    numcol = {}
    for row in records:
        for name in ListaCampi:
            if name==row[1]:
                 numcol [name]=row[0]
                 break

    fieldOrder='Num'
    sql=" SELECT * FROM %s ORDER BY %s;" %(NomeTabella,fieldOrder)
    curs.execute(sql)
    records=curs.fetchall()

    ID_FloodSeverity=[]
    DvFlooSev=[]
    HrateFlooSev=[]
    for row in records:
        ID_FloodSeverity.append(int(row[numcol['Num']]))
        DvFlooSev.append(float(row[numcol['DV']]))
        HrateFlooSev.append(float(row[numcol['hrate']]))

    NumClassFloSev=len(DvFlooSev)

    NomeTabella='FatalityRate'
    sql='PRAGMA table_info (%s)' % (NomeTabella)
    curs.execute(sql)
    records = curs.fetchall()

    # reading fields name of FatalityRates
    numcol = {}
    Fields_F_Rate=[]
    for row in records:
        Fields_F_Rate.append(row[1])
        numcol [row[1]]=row[0]

    # Make lists for FatalityRates assessment
    ID_FatRate=[]
    NumClassSeverity=[]
    FromWarningTime=[]
    ToWarningTime=[]
    FatRate=[]

    # Load List Num Flood Severity
    sql=" SELECT Num FROM %s WHERE Understanding='%s' GROUP BY Num ORDER BY Num DESC;" %(NomeTabella,TipoUnderstanding)
    curs.execute(sql)
    records=curs.fetchall()
    if len(records)>0:
        ListaNumSev=[]
        for rec in records:
            ListaNumSev.append(rec[0])
    else:
        #exit with an error code
        NotErr=bool()
        errMsg="Understanding = '%s' non found in Table=%s" % (TipoUnderstanding,NomeTabella)
        return NotErr, errMsg

    k=-1
    fieldOrder='WarnTime'
    for num in ListaNumSev:
        WarnTimePrec=0.0
        sql=" SELECT WarnTime,FatRate FROM %s WHERE Num=%d AND Understanding='%s' ORDER BY %s;" %(NomeTabella,num,TipoUnderstanding,fieldOrder)
        curs.execute(sql)
        records=curs.fetchall()
        if len(records)>0:
            ListaNumSev=[]
            for rec in records:
                if float(rec[0])>0:
                    k=k+1
                    ID_FatRate.append(k)
                    NumClassSeverity.append(num)
                    FromWarningTime.append(WarnTimePrec)
                    ToWarningTime.append(float(rec[0]))
                    WarnTimePrec=float(rec[0])
                    FatRate.append(float(rec[1]))

    # update ProgressBar status
    #--------------------------
    curr=fin
    app.setValue(int(curr))

    format = 'MEM'
    driver1 = gdal.GetDriverByName(format)
    driver1.Register()

    # Loading Water Depth
    #===================================
    indataset = gdal.Open( FileDEM1, GA_ReadOnly )
    if indataset is None:
        errMsg= 'Could not open ' + FileDEM1
        #exit with an error code
        NotErr=bool()
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

    AreaPixel=abs(pixelWidth*pixelHeight)

    # Save grid property
    OriginData=[originX,originY,pixelWidth,pixelHeight,cols,rows]

    # Reading grid file
    tiranti = inband.ReadAsArray(0, 0, cols, rows).astype(numpy.float32)

    # creating the mask of water depth
    mask_tiranti=numpy.greater(tiranti, -10)
    numcell=numpy.sum(mask_tiranti)
    # creating a mask with NoData and zero in the points which are not NoData
    mask_NoData= numpy.choose(numpy.not_equal(tiranti,inNoData),(tiranti,0))

    mask_wet=numpy.greater(tiranti, 0.001)
    mask_not_wet=numpy.equal(tiranti,inNoData)

    AreaCella=-pixelWidth*pixelHeight
    numcel=numpy.zeros(8,numpy.int32)
    numceltot=numpy.sum(mask_tiranti)
    AreaBacinoTot=numceltot*AreaCella/1000000

    # update ProgressBar status
    #--------------------------
    curr=10
    app.setValue(int(curr))

    # Make Grid Population
    # =======================



    # Make a new memlayer
    # ---------------
    sql=" SELECT OBJECTID FROM CensusBlocks;"
    curs.execute(sql)
    records=curs.fetchall()
    if len(records)>0:

        drv = ogr.GetDriverByName( 'Memory' )
        dst_ds = drv.CreateDataSource( 'out' )

        FieldList=['Resident','Seasonal']
        source_layer=LoadSqliteLayer('CensusBlocks',curs,FieldList,dst_ds)

    else:
        #exit with an error code
        NotErr=bool()
        errMsg="CensusBlocks non found"
        return NotErr, errMsg


    # execution of calculation of the population density and save it in a memory layer
    outfile='file1.shp'
    if os.path.exists(outfile) :
        drv.DeleteDataSource(outfile)

    outDS = drv.CreateDataSource(outfile)
    dest_layer = outDS.CreateLayer('layer1',
                                srs = source_layer.GetSpatialRef(),
                                geom_type=source_layer.GetLayerDefn().GetGeomType())

    # analyzes source_layer to perform calculations
    # =============================================

    numFeatures = source_layer.GetFeatureCount()

    ini=curr+2
    fin=ini+5
    curr=ini
    app.setValue(int(curr))

    if numFeatures>0:

        dprogr=float(fin-ini)/float(numFeatures)

        # creating the field in the new layer
        fldDef = ogr.FieldDefn('Calc1', ogr.OFTReal)
        dest_layer.CreateField(fldDef)
        # creating the field in the new layer
        fldDef = ogr.FieldDefn('Calc2', ogr.OFTReal)
        dest_layer.CreateField(fldDef)

        OutfeatureDefn = dest_layer.GetLayerDefn()

        feat = source_layer.GetNextFeature()
        k=0
        while feat:
            k=k+1
            geometry = feat.GetGeometryRef()
            area=geometry.Area()
            num1=feat.GetFieldAsDouble(0)
            num2=feat.GetFieldAsDouble(1)
            # calculation of the population density in the pixel
            cc1=float(num1*AreaPixel/area)
            cc2=float(num2*AreaPixel/area)

            outFeature = ogr.Feature(OutfeatureDefn)
            outFeature.SetGeometry(geometry)
            outFeature.SetField(0,cc1)
            outFeature.SetField(1,cc2)
            dest_layer.CreateFeature(outFeature)
            # destroy the features
            feat.Destroy()
            outFeature.Destroy()
            feat = source_layer.GetNextFeature()

            curr=float(ini)+k*dprogr
            app.setValue(int(curr))


    # closing the source of input data
    dst_ds.Destroy()

    # save the file
    outfile='TotalPopulationatRisk.tif'

    tipo = GDT_Float32
    NodataOut=inNoData

    # creating the data source
    outDs = driver1.Create(outfile, cols, rows, 2, tipo)

    # assigning the georeferencing
    if geotransform is not None and geotransform != (0.0, 1.0, 0.0, 0.0, 0.0, 1.0):
        outDs.SetGeoTransform(geotransform)
    # assigning reference system
    if prj is not None and len(prj) > 0:
        outDs.SetProjection(prj)
    else:
        prj= spatialRef.ExportToWkt()
        outDs.SetProjection(prj)

    # loanding first band
    iBand=1
    outband = outDs.GetRasterBand(iBand)

    err = gdal.RasterizeLayer(outDs, [1], dest_layer,
            burn_values=[0],
            options=["ATTRIBUTE=Calc1"])
    if err != 0:
        raise Exception("error rasterizing layer: %s" % err)

    PAR1 = outband.ReadAsArray(0, 0, cols, rows).astype(numpy.float32)
    n1=PAR1.sum()

    # loanding second band
    iBand=2
    outband2 = outDs.GetRasterBand(iBand)

    err = gdal.RasterizeLayer(outDs, [2], dest_layer,
            burn_values=[0],
            options=["ATTRIBUTE=Calc2"])
    if err != 0:
        raise Exception("error rasterizing layer: %s" % err)

    # reading grid density of population
    PAR2 = outband2.ReadAsArray(0, 0, cols, rows).astype(numpy.float32)
    n2=PAR2.sum()
    # resetting the indices of the cells not affected
    TotalPopulationatRisk1= numpy.choose(mask_not_wet,(PAR1,0))  # residential pop
    TotalPopulationatRisk2= numpy.choose(mask_not_wet,(PAR2,0))  # seasonal pop
    POP=[]
    POP.append(TotalPopulationatRisk1)
    POP.append(TotalPopulationatRisk2)

    outDS.Destroy()

    # ================================
    # creates the map of warning Time
    # ================================

    driver = ogr.GetDriverByName('ESRI Shapefile')

    # file input
    fn=NomeFileWornTime
    inDS = driver.Open(fn, 0)
    if inDS is None:
        errMsg ='Could not open ' + fn
        #exit with an error code
        NotErr=bool()
        return NotErr, errMsg
    # open the layer for reading
    Inlayer = inDS.GetLayer()
    numFeatures = Inlayer.GetFeatureCount()
    # Get reference system
    spatialRef = Inlayer.GetSpatialRef()
    spatialRef.AutoIdentifyEPSG()
    NumEPSG= spatialRef.GetAuthorityCode(None)
    # get the list of fields
    feat = Inlayer.GetNextFeature()
    geom_class = feat.GetGeometryRef()
    layer_geom_type = geom_class.GetGeometryType()
    geomok=bool()
    # check the type of geometry
    # I agree to include POLIGON in MULTIPOLYGON
    if layer_geom_type==6 or layer_geom_type==3:
        geomok=bool('True')

    if geomok:
        NameFieldShp, TypeFieldShp =CampiSHP(Inlayer,feat)
        NumFieldsShp=len(NameFieldShp)
        # I am looking for the first field having the name TIMEHOURS
        CampoTime=''
        for j in range(NumFieldsShp):
            if 'TIMEHOURS' in str.upper(NameFieldShp[j]):
                CampoTime=NameFieldShp[j]
                break
        #need if looping again
        Inlayer.ResetReading()

        # Create the matrix of the codes WarningTime
        # ===========================================
        Fwat=numpy.zeros((rows,cols),numpy.int)
        format = 'MEM'
        type = GDT_Float32

        driver2 = gdal.GetDriverByName(format)
        driver2.Register()
        gt=indataset.GetGeoTransform()

        ds = driver2.Create('Wtime.tif', indataset.RasterXSize, indataset.RasterYSize, 1, type)
        if gt is not None and gt != (0.0, 1.0, 0.0, 0.0, 0.0, 1.0):
            ds.SetGeoTransform(gt)

        # sets the reference system equal to the model of the depth of water: if it lacks sets the default
        if prj is not None and len(prj) > 0:
            ds.SetProjection(prj)
        else:
            prj= spatialRef.ExportToWkt()
            ds.SetProjection(prj)

        iBand=1
        testo="ATTRIBUTE=%s"  % (CampoTime)
        CampoValore=[testo]
        # Rasterize
        outband = ds.GetRasterBand(iBand)

        # Rasterize
        outband.WriteArray(Fwat, 0, 0)

        # Create a map of the values
        # -------------------------------------------------
        err = gdal.RasterizeLayer(ds, [iBand], Inlayer,
                burn_values=[0],
                options=CampoValore)
        if err != 0:
            raise Exception("error rasterizing layer: %s" % err)

        # Reading WarningTime in hours
        FwatArray = outband.ReadAsArray().astype(numpy.float32)

        # Writing Nodata
        Fwat= numpy.choose(numpy.equal(tiranti,inNoData),(FwatArray,inNoData))

        outband.WriteArray(Fwat, 0, 0)
        outband.FlushCache()
        outband.SetNoDataValue(inNoData)
        outband.GetStatistics(0,1)
        outband = None
        ds = None


    else:
        # assume warning time 0
        pass

    curr=curr+5.0
    app.setValue(int(curr))

    # =========================
    # FloodSeverity computation
    # =========================

    # ------------------------------------------
    # Loading flow velocity
    # ------------------------------------------
    indataset = gdal.Open( NomeGridVelocita, GA_ReadOnly )
    if indataset is None:
        errMsg ='Could not open ' + NomeGridVelocita
        #exit with an error code
        NotErr=bool()
        return NotErr, errMsg

    gt = indataset.GetGeoTransform()

    ok=ControlloCongruenzaGRID(OriginData,indataset,gt)

    if not ok:
        errMsg = 'Grid %s do not match %s ' % (FileDEM1, NomeGridVelocita)
        #exit with an error code
        NotErr=bool()
        return NotErr, errMsg

    # reading all the file at once
    inband = indataset.GetRasterBand(1)
    Velocity = inband.ReadAsArray(0, 0, cols, rows).astype(numpy.float32)
    # Sets zero the NOdata
    Velocity= numpy.choose(numpy.equal(tiranti,inNoData),(Velocity,0))


    inband = None
    indataset = None

    # ===============================
    # calculate the maximum flow unit
    # ===============================
    DV=Velocity*tiranti

    curr=curr+5.0
    app.setValue(int(curr))

    # =================================================
    # calculates first version of Grid of FloodSeverity
    # only on the basis of PeakUnitFlowRate
    # =================================================
    FloodSeverityID=numpy.zeros((rows,cols),numpy.int)
    LimAlt=DvFlooSev
    numerolim=len(LimAlt)
    numcel=numpy.zeros(numerolim,numpy.int32)
    mask_alt=numpy.zeros((numerolim,rows,cols),numpy.bool)
    # in nodata points of Flow Rate insert the upper limit
    # to avoid being counted as less than the minimum
    MaxLim=LimAlt[numerolim-1]+1
    mask_tmp=numpy.choose(mask_not_wet,(DV,MaxLim))

    # [0] is the mask with values below the minimum flow rate
    mask_alt[0]=numpy.less(mask_tmp, LimAlt[0])
    FloodSeverityID=numpy.choose(numpy.equal(mask_alt[0],1),(FloodSeverityID,ID_FloodSeverity[0]))

    # count the number of cells
    numcel[0]=numpy.sum(mask_alt[0])
    for i in range (1,numerolim):
        # each mask indicates the cells that have a value lower than the limit
        mask_alt[i]=numpy.less(mask_tmp, LimAlt[i])
        mask_alt[i]=mask_alt[i]*1
        nn=numpy.sum(mask_alt[i])
        for j in range (i):
            mask_alt[i]=mask_alt[i]-mask_alt[j]
        numcel[i]=numpy.sum(mask_alt[i])
        FloodSeverityID=numpy.choose(numpy.equal(mask_alt[i],1),(FloodSeverityID,ID_FloodSeverity[i]))

    # insert NoData
    FloodSeverityID=numpy.choose(mask_not_wet,(FloodSeverityID,inNoData))

    curr=curr+5.0
    app.setValue(int(curr))

    # =============================
    # Make Array of  FatalityRates
    # =============================

    # creating an empty array of floating point numbers
    ArrayFatalityRates=numpy.zeros((rows,cols)).astype(numpy.float)

    # cycling combinations of Fseverity-WarningTime
    for i in range(len(ID_FatRate)):
        CoeffFatRate=FatRate[i]
        ID_Severity=NumClassSeverity[i]
        maskSeverity= numpy.equal(FloodSeverityID,ID_Severity)
        maskWarnTime=numpy.greater(FwatArray,FromWarningTime[i]) & numpy.less_equal(FwatArray,ToWarningTime[i])
        mask=maskSeverity & maskWarnTime

        ArrayFatalityRates= numpy.choose(mask,(ArrayFatalityRates,CoeffFatRate))

    curr=curr+5.0
    app.setValue(int(curr))

    # ---------------------------
    # population analysis
    # ---------------------------

    # parameters
    FieldTime=Fields_F_Rate[3]
    FileldUnderstanding=Fields_F_Rate[4]

    NumTipiPop=len(POP)
    TotPopRiskSum=numpy.zeros((NumTipiPop),numpy.int)
    TotLossSumType=numpy.zeros((NumTipiPop),numpy.int)

    Campi=['Range Water Depth (m)','Flooded Area (m2)','Resident Pop. at Risk','Seasonal Pop. at Risk',
    'Total Population at Risk','Loss of Life']
    DepthLimits=[]

    Num_dh=4
    delta_h=1.0
    for i in range(Num_dh):
        lim=(i+1)*delta_h
        DepthLimits.append(lim)
    DepthLimits.append(999)
    righe=[]
    testo='%0.1f-%0.1f' %(0,DepthLimits[0])
    righe.append(testo)
    for i in range(Num_dh-1):
        testo='%0.1f-%0.1f' %(DepthLimits[i],DepthLimits[i+1])
        righe.append(testo)
    testo='>%d' %(lim)
    righe.append(testo)
    righe.append('Total')
    numRighe=len(righe)

    # open file output table
    # --------------------------
    filepath=os.path.dirname(NomeFileTabella2)
    if not os.path.exists(filepath):
        os.mkdir(filepath)

    ftab=open(NomeFileTabella2,'w')

    # writing heading
    testo=''
    for campo in Campi:
        testo+=campo+sep
    testo=testo[:-1]+'\n'
    ftab.write(testo)

    nrec= len(DepthLimits)

    tollFlora2D=0.001
    DepthLimit_prec=tollFlora2D
    numCellDepth=0

    # beginning of the cycle
    numDep=len(DepthLimits)
    PopRiskSum=numpy.zeros((numDep,NumTipiPop),numpy.int)
    PopLossSum=numpy.zeros((numDep,NumTipiPop),numpy.int)
    TotPopRiskRighe=numpy.zeros((numDep),numpy.int)

    # update ProgressBar status
    #--------------------------
    ini=curr+5
    fin=98
    curr=ini
    app.setValue(int(curr))

    dcur=(fin-ini)/numDep
    ListAree=[]
    TotAreaSum=0
    ListaLoss=[]

    # assess lost of lives
    # ---------------------
    ListaLOL=[]
    for i in range(NumTipiPop):
        LOL=POP[i]*ArrayFatalityRates
        ListaLOL.append(LOL)


    # ------------------------------------
    # cycle for the bands of water depth
    # ------------------------------------
    TotLossSum=0
    for irec in range(numDep):

        DepthLimit=DepthLimits[irec]
        MaskDepth=numpy.zeros((rows,cols),numpy.float32)
        mask_dh=numpy.greater(tiranti,DepthLimit_prec) & numpy.less_equal(tiranti,DepthLimit)

        nn=mask_dh.sum()
        aa=round(nn*AreaCella,0)
        ListAree.append(aa)

        DepthLimit_prec=DepthLimit

        TotLoss_dh=0

        for i in range(NumTipiPop):
            PoP1Risk=POP[i]*mask_dh
            p=round(PoP1Risk.sum(),0)
            PopRiskSum[irec,i]=p
            TotPopRiskSum[i]=TotPopRiskSum[i]+p

            loss_dh=ListaLOL[i]*mask_dh
            p=round(loss_dh.sum(),0)
            PopLossSum[irec,i]=p
            TotLoss_dh=TotLoss_dh+p
            TotLossSumType[i]=TotLossSumType[i]+p
            TotLossSum=TotLossSum+p

        ListaLoss.append(TotLoss_dh)

        TotAreaSum=TotAreaSum+aa
        TotPopRiskRighe[irec]=PopRiskSum[irec].sum()

        # update ProgressBar status
        #--------------------------
        curr=ini+dcur*(irec+1)
        app.setValue(int(curr))


    # calculates PopRisk and Loss of Life
    # ==============================
    TotalPopulationatRisk= numpy.zeros((rows,cols),numpy.int)
    for i in range(NumTipiPop):
        TotalPopulationatRisk=TotalPopulationatRisk+POP[i]

    LOLGrid=TotalPopulationatRisk*ArrayFatalityRates
    # apply before the zeros
    LOLGrid= numpy.choose(numpy.equal(tiranti,inNoData),(LOLGrid,0))
    NumLoss_notRound=LOLGrid.sum()
    NumLoss=round(LOLGrid.sum(),0)


    # Save the grid
    #---------------
    outfile=NomeFileGridPAR
    filepath=os.path.dirname(outfile)
    if not os.path.exists(filepath):
        os.mkdir(filepath)

    format = 'GTiff'
    driver1 = gdal.GetDriverByName(format)
    driver1.Register()

    type = GDT_Float32

    ds = driver1.Create(outfile, cols, rows, 2, type)
    if gt is not None and gt != (0.0, 1.0, 0.0, 0.0, 0.0, 1.0):
        ds.SetGeoTransform(gt)

    if prj is not None and len(prj) > 0:
        ds.SetProjection(prj)
    else:
        prj= spatialRef.ExportToWkt()
        ds.SetProjection(prj)

    iBand=1
    outband = ds.GetRasterBand(iBand)
    # change into ab/kmq
    PopulationatRiskKmq=TotalPopulationatRisk/AreaCella*1000000.0
    # applying Nodata
    PopulationatRiskKmq= numpy.choose(numpy.equal(tiranti,inNoData),(PopulationatRiskKmq,inNoData))
    outband.WriteArray(PopulationatRiskKmq, 0, 0)

    outband.FlushCache()
    outband.SetNoDataValue(inNoData)
    outband.GetStatistics(0,1)
    outband = None

    iBand=2
    outband = ds.GetRasterBand(iBand)
    # change into ab/kmq
    LOLGridKmq=LOLGrid/AreaCella*1000000.0
    # applying Nodata
    LOLGridKmq= numpy.choose(numpy.equal(tiranti,inNoData),(LOLGridKmq,inNoData))
    outband.WriteArray(LOLGridKmq, 0, 0)

    outband.FlushCache()
    outband.SetNoDataValue(inNoData)
    outband.GetStatistics(0,1)
    outband = None

    ds = None

    # update ProgressBar status
    #--------------------------
    curr=99
    app.setValue(int(curr))

    # writing file table
    # -----------------
    for irec in range(len(DepthLimits)):

        testo=righe[irec]+sep
        testo+='%d%s' % (ListAree[irec],sep)
        for i in range(NumTipiPop):
            testo+='%d%s' % (PopRiskSum[irec,i],sep)
        testo+='%d%s' % (TotPopRiskRighe[irec],sep)
        testo+='%d%s' % (ListaLoss[irec],sep)
        testo=testo[:-1] +'\n'
        ftab.write(testo)

    testo=righe[numRighe-1]+sep
    testo+='%d%s' % (TotAreaSum,sep)
    for i in range(NumTipiPop):
        testo+='%d%s' % (TotPopRiskSum[i],sep)
    testo+='%d%s' % (TotPopRiskRighe.sum(),sep)
    testo+='%d%s' % (TotLossSum,sep)
    testo=testo[:-1] +'\n'
    ftab.write(testo)

    # closing file
    ftab.close()
    # closing the database connection
    curs = None
    conn.close()

    # update ProgressBar status
    #--------------------------
    curr=fin
    app.setValue(int(curr))

    curr=100
    app.setValue(int(curr))

    return NotErr, errMsg, NumLoss_notRound

if __name__ == '__main__':

    #================
    #test the script
    #================

    file_param=open('NomeFilePop.txt','r')
    if file_param is None:
        print 'Could not open ' + 'NomeFilePop.txt'
        sys.exit(1)

    # Reading parameters
    # ====================================
    ListaFiles=[]

    # INPUT =============================

    # name file grid water depth
    text= file_param.readline()
    FileDEM1 = LoadParametro(text)
    ListaFiles.append(FileDEM1)

    # name NomeGridVelocita
    text= file_param.readline()
    NomeGridVelocita = LoadParametro(text)
    ListaFiles.append(NomeGridVelocita)

    # name NomeFileWorningTime
    text= file_param.readline()
    NomeFileWornTime = LoadParametro(text)
    ListaFiles.append(NomeFileWornTime)

    # name of Geodatabase
    text= file_param.readline()
    DBfile = LoadParametro(text)
    ListaFiles.append(DBfile)

    # OUTPUT =============================

    # name of FileGridPopolazione at risk of Loss of Life
    text= file_param.readline()
    NomeFileGridPAR = LoadParametro(text)
    ListaFiles.append(NomeFileGridPAR)

    # name file Tabella2
    text= file_param.readline()
    NomeFileTabella2 = LoadParametro(text)
    ListaFiles.append(NomeFileTabella2)

    # type of Understanding
    # ------------------------------
    # assume type 1
    Understanding='Vague'
##    Understanding='Precise'
##    Understanding='C10'
##    Understanding='C1'
    ListaFiles.append(Understanding)


    app=progressBar()

    # run
    NotErr, errMsg = main(ListaFiles,app)

    if NotErr:
        print 'End of Job'
    else:
        print 'Run not executed'
        print errMsg

    curr=101
    app.setValue(int(curr))

