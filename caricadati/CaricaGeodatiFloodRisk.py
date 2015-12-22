"""
#-------------------------------------------------------------------------------
# Name:        CaricaGeodatiFloodRisk
# Purpose:
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
import sys
import os

try:
    from osgeo import gdal
    from osgeo.gdalconst import *
    gdal.TermProgress = gdal.TermProgress_nocb
except ImportError:
    import gdal
    from gdalconst import *

try:
    from osgeo import ogr
    # import reference systems module
    from osgeo import osr
except:
    import ogr
    # import reference systems module
    import osr

import sqlite3
from pyspatialite import dbapi2 as db


# module for reading csv files
import csv


def NewGeom(raw_geom,typeTab,NumEPSG):

    pp=str.split(raw_geom,' ')
    typeCurr=pp[0]
    # forced the geodatabase to import MULTIPOLYGON and MULTILINESTRING
    if typeCurr!=typeTab:
        if typeCurr=='POLYGON' and typeTab=='MULTIPOLYGON':
            pp1=raw_geom.replace('((','(((')
            new_geom='%s%s)' % ('MULTI',pp1)
        elif typeCurr=='LINESTRING' and typeTab=='MULTILINESTRING':
            pp1=raw_geom.replace('(','((')
            new_geom='%s%s)' % ('MULTI',pp1)
        else:
            new_geom=raw_geom
    else:
        new_geom=raw_geom

    geom = "GeomFromText('%s', %s)" %(new_geom,NumEPSG)

    return geom

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

def GeomColumn(TipoCampo,NomeCampo):

    tipi = ['POINT', 'LINESTRING', 'POLYGON', 'MULTILINESTRING', 'MULTIPOLYGON']

    nn=len(TipoCampo)
    ColGeom='Null'
    tipoGeom='Null'
    if nn>0:
        for k in range(nn):
            i=nn-k-1
            tipo=TipoCampo[i]
            if tipo in tipi:
                tipoGeom=tipo
                ColGeom=NomeCampo[i]
                break
    return tipo, ColGeom

def UploadLayerInSQL(layer,TargetEPSG,GeomAreawkt,NomeTabella,NameField,TypeField,dic_fiels,CampiInsert,typeTab,ListaSql, bar):

    # load a layer in memory and write a SQL file
    # --------------------------------------------

    Err='ok'

    dic = {1:'POINT', 2:'LINESTRING', 3:'POLYGON', 5:'MULTILINESTRING', 6:'MULTIPOLYGON'}

    feat_defn = layer.GetLayerDefn()
    NumFieldsShp=feat_defn.GetFieldCount()
    NumFields=len(CampiInsert)
    NomeTabellaShp=layer.GetName()
    print NomeTabellaShp

    carmin=0

    try:
        spatialRef = layer.GetSpatialRef()
        # looking for the code of the reference system
        spatialRef.AutoIdentifyEPSG()
        NumEPSG= int(spatialRef.GetAuthorityCode(None))
    except:
        NumEPSG=32632 # WGS84 UTM 32


    numFeatures = layer.GetFeatureCount()

    ini = 10.0
    fin = 40.0

    if numFeatures>0:

        dx = (fin - ini) / float(numFeatures)
        if TargetEPSG!=NumEPSG:
            targetSR = osr.SpatialReference()
            targetSR.ImportFromEPSG(TargetEPSG)
            sourceSR = osr.SpatialReference()
            sourceSR.ImportFromEPSG(NumEPSG)
            coordTrans = osr.CoordinateTransformation(sourceSR,targetSR)
            trasformare=bool('True')
        else:
            trasformare=bool()

        if len(GeomAreawkt)>0:
            intersezione=bool('True')
            GeomStudy=ogr.CreateGeometryFromWkt(GeomAreawkt)
        else:
            intersezione=bool()

        # Reading data into memory
        #===========================================
        feat = layer.GetNextFeature()
        kk = 0
        while feat:

            geom_class = feat.GetGeometryRef()
            geom_type = geom_class.GetGeometryType()
            GeomType = dic[geom_type]

            # writing sql text
            sql = "INSERT INTO " + NomeTabella +" ("
            # insert the field names
            for i in range(NumFieldsShp):
                field_defn = feat_defn.GetFieldDefn(i)
                name=field_defn.GetName()
                try:
                    ind=CampiInsert.index(field_defn.GetName())
                    nome=dic_fiels[CampiInsert[ind]]
                    sql +=nome+','
                except:
                    pass
            if typeTab!='Null':
                sql +="geom) "
                try:
                    geometry = feat.GetGeometryRef()
                    if trasformare:
                        geometry.Transform(coordTrans)

                    Area=geometry.GetArea()

                    if intersezione:
                        inters=geometry.Intersection(GeomStudy)
                        raw_geom= inters.ExportToWkt()
                    else:
                        raw_geom= geometry.ExportToWkt()

                    geom=NewGeom(raw_geom,typeTab,TargetEPSG)

                except:
                    exceptionType, exceptionValue, exceptionTraceback = sys.exc_info()
                    errMsg= "Table %s  Error! ->%s" % (NomeTabella,exceptionValue)
                    NotErr=bool()
                    return NotErr, errMsg



            else:
                sql=sql[:-1]+") "
            sql += "VALUES ("
            # insert the field values
            for i in range(NumFieldsShp):
                field_defn = feat_defn.GetFieldDefn(i)
                name_field_shp=field_defn.GetName()
                try:
                    NomeCampoCur=dic_fiels[name_field_shp]
                    if NomeCampoCur=='Shape_Area':
                        valore= "%.3f" % (Area)
                        sql += valore
                    else:
                        kfield=NameField.index(NomeCampoCur)
                        tipo=TypeField[kfield]
                        if field_defn.GetType() == ogr.OFTInteger:
                            valore= "%d" % feat.GetFieldAsInteger(i)
                            sql += valore
                        elif field_defn.GetType() == ogr.OFTReal:
                            valore= "%.3f" % feat.GetFieldAsDouble(i)
                            sql += valore
                        elif field_defn.GetType() == ogr.OFTString:
                            stringa=feat.GetFieldAsString(i)
                            stringa=str(stringa).replace("'"," ")
                            valore= "%s" % stringa
                            if len(stringa)<1:
                                stringa='Null'
                            sql += "'%s" % stringa+"'"
                        else:
                            stringa=feat.GetFieldAsString(i)
                            stringa=str(stringa).replace("'"," ")
                            valore= "%s" % stringa
                            if len(stringa)<1:
                                stringa='Null'
                            sql += "'%s" % stringa+"'"
                    sql +=','

                except:
                    pass
            if typeTab!='Null':

                # enters the value of geometry
                sql += " %s)" % (geom)
                sql +=';'

            else:
                sql += ");"
            ListaSql.append(sql)
            feat.Destroy()
            kk = kk+1
            numCur = int(ini + dx * kk)
            bar.setValue(numCur)
            feat = layer.GetNextFeature()

    bar.setValue(40)

    return Err


def main(self,FilesList,UpLoad, bar):

    dic_type = {'POINT':1, 'LINESTRING':2, 'POLYGON':3, 'MULTILINESTRING':5, 'MULTIPOLYGON':6}

    mydb_path=FilesList[0]
    ShpAreaStudio=FilesList[1]
    ShpCensimentoISTAT=FilesList[2]
    cvsCensus=FilesList[3]
    ShpBeniAreali=FilesList[4]
    ShpBeniLineari=FilesList[5]

    NotErr=bool('True')
    errMsg='OK'

    # creating/connecting the test_db
    conn = db.connect(mydb_path)
    # creating a Cursor
    cur = conn.cursor()

    # ====================
    # Table AnalysisArea
    # ====================
    carico=UpLoad[1]

    if carico>0:

        bar.setValue(0)

        NomeTabella='AnalysisArea'
        sql="SELECT sql FROM sqlite_master WHERE type='table' AND name='%s';" % (NomeTabella)
        cur.execute(sql)
        Tabella=str(cur.fetchone()[0])

        NameField=[]
        TypeField=[]
        NameField, TypeField = CampiTabella(Tabella)
        # do not load OBJECTID field
        if 'OBJECTID' in NameField:
            indiceid=NameField.index('OBJECTID')
            NameField.remove('OBJECTID')
            TypeField.remove(TypeField[indiceid])

        NumFields=len(NameField)
        Null='Null'
        TipoGeom, ColGeom=GeomColumn(TypeField,NameField)
        try:
            CodTipoGeom=dic_type[TipoGeom]
        except:
            CodTipoGeom=0

        driver = ogr.GetDriverByName('ESRI Shapefile')

        # open input file
        fn=ShpAreaStudio
        inDS = driver.Open(fn, 0)
        if inDS is None:
            errMsg= 'Could not open ' + fn
            #exit with an error code
            NotErr=bool()
            return NotErr, errMsg

        # open layer
        Inlayer = inDS.GetLayer()
        numFeatures = Inlayer.GetFeatureCount()
        spatialRef = Inlayer.GetSpatialRef()
        spatialRef.AutoIdentifyEPSG()
        NumEPSG= spatialRef.GetAuthorityCode(None)
        feat = Inlayer.GetNextFeature()
        geom_class = feat.GetGeometryRef()
        layer_geom_type = geom_class.GetGeometryType()
        geomok=bool()
        # check the type of geometry
        if layer_geom_type==CodTipoGeom:
            geomok=bool('True')
        # include POLYGON as MULTIPOLYGON
        elif CodTipoGeom==6 and layer_geom_type==3:
            geomok=bool('True')

        if not geomok:
            txt1=self.tr('Geometry type must be')
            txt2=self.tr('error in file')
            errMsg= '%s - %s : %s\n\n %s  %s' % (NomeTabella,txt1,TipoGeom,txt2,fn)
            #exit with an error code
            NotErr=bool()
            return NotErr, errMsg

        #Empty table
        sql = "DELETE FROM %s;" % (NomeTabella)
        cur.execute(sql)
        conn.commit()


        NameFieldShp, TypeFieldShp =CampiSHP(Inlayer,feat)
        NumFieldsShp=len(NameFieldShp)
        # mapping shapefile fields to those of the geodatabase
        dic_fiels = {}
        dic_fiels_type = {}
        CampiInsert=[]
        for i in range(NumFields):
            for j in range(NumFieldsShp):
                if str.upper(NameField[i])==str.upper(NameFieldShp[j]):
                    # todo : check the type
                    dic_fiels[NameFieldShp[j]]=NameField[i]
                    dic_fiels_type[NameFieldShp[j]]=TypeField[i]
                    CampiInsert.append(NameFieldShp[j])
                    break

        #need if looping again
        Inlayer.ResetReading()

        # look for the TargetEPSG to reach
        sql="SELECT srid FROM geometry_columns WHERE f_table_name='analysisarea';"
        cur.execute(sql)
        listasrid=cur.fetchone()
        srid=str(listasrid[0])
        TargetEPSG=int(srid)

        ListaSql=[]
        GeomAreawkt=''
        bar.setValue(10)

        UploadLayer=UploadLayerInSQL(Inlayer,TargetEPSG,GeomAreawkt,NomeTabella,NameField,
        TypeField,dic_fiels,CampiInsert,TipoGeom,ListaSql, bar)
        bar.setValue(60)

        ini = 60.0
        fin = 99.0
        numRighe = len(ListaSql)
        dx = (fin - ini) / float(numRighe)
        kk = 0
        for sql in ListaSql:
            try:
                cur.execute(sql)
                kk = kk+1
                numCur = int(ini + dx * kk)
                bar.setValue(numCur)
            except:
                exceptionType, exceptionValue, exceptionTraceback = sys.exc_info()
                errMsg= "Table %s  Error! ->%s" % (NomeTabella,exceptionValue)
                #exit with an error code
                NotErr=bool()
                return NotErr, errMsg

        conn.commit()
        bar.setValue(100)

    # --------------------------------------------------
    # Load in memory AnalysisArea geometry
    # --------------------------------------------------
    NomeTabella='AnalysisArea'
    sql="SELECT AsText(geom) FROM %s;" % (NomeTabella)
    cur.execute(sql)
    GeomAreawkt=str(cur.fetchone()[0])
    GeomArea=ogr.CreateGeometryFromWkt(GeomAreawkt)
    aa=GeomArea.GetArea()
    if aa==0:
        nrig=geometry.GetGeometryCount()
        if nrig>0:
            GeomArea = geometry.GetGeometryRef(0)

    Envelope=GeomArea.GetEnvelope()
    Xmin=Envelope[0]
    Xmax=Envelope[1]
    Ymin=Envelope[2]
    Ymax=Envelope[3]
    sql="SELECT DISTINCT Srid(geom) FROM %s;" % (NomeTabella)
    cur.execute(sql)
    NumEPSGAreaStudio=cur.fetchone()[0]
    targetSR = osr.SpatialReference()
    targetSR.ImportFromEPSG(NumEPSGAreaStudio)
    SpatialFilter = ogr.Geometry(ogr.wkbPolygon)
    SpatialFilter=GeomArea
    aa=SpatialFilter.GetArea()

    #----------------------------------
    # Load Census
    #----------------------------------
    carico=UpLoad[2]
    if carico>0:

        bar.setValue(0)
        NomeTabella='CensusBlocks'
        sql="SELECT sql FROM sqlite_master WHERE type='table' AND name='%s';" % (NomeTabella)
        cur.execute(sql)
        Tabella=str(cur.fetchone()[0])

        NameField=[]
        TypeField=[]
        NameField, TypeField = CampiTabella(Tabella)
        # do not load OBJECTID field
        if 'OBJECTID' in NameField:
            indiceid=NameField.index('OBJECTID')
            NameField.remove('OBJECTID')
            TypeField.remove(TypeField[indiceid])

        NumFields=len(NameField)
        Null='Null'
        TipoGeom, ColGeom=GeomColumn(TypeField,NameField)
        try:
            CodTipoGeom=dic_type[TipoGeom]
        except:
            CodTipoGeom=0

        driver = ogr.GetDriverByName('ESRI Shapefile')

        # open input file
        fn=ShpCensimentoISTAT
        inDS = driver.Open(fn, 0)
        if inDS is None:
            errMsg= 'Could not open ' + fn
            #exit with an error code
            NotErr=bool()
            return NotErr, errMsg
        # open layer for reading
        Inlayer = inDS.GetLayer()
        numFeatures = Inlayer.GetFeatureCount()
        # looking for the code of the reference system
        spatialRef = Inlayer.GetSpatialRef()
        spatialRef.AutoIdentifyEPSG()
        NumEPSG= int(spatialRef.GetAuthorityCode(None))

        SpatialFilter=ogr.CreateGeometryFromWkt(GeomAreawkt)

        if NumEPSG!=NumEPSGAreaStudio:
            # creating the spatial filter in the origins coordinates of the shapefile
            sourceSR = osr.SpatialReference()
            sourceSR.ImportFromEPSG(NumEPSG)
            coordTrans = osr.CoordinateTransformation(sourceSR,targetSR)
            coordTransInv = osr.CoordinateTransformation(targetSR,sourceSR)
            SpatialFilter.Transform(coordTransInv)
            bb=SpatialFilter.GetArea()
            Envelopeb=SpatialFilter.GetEnvelope()

        Inlayer.SetSpatialFilter(SpatialFilter)
        numFeatures = Inlayer.GetFeatureCount()

        if numFeatures>0:

            # list of fields
            feat = Inlayer.GetNextFeature()
            geom_class = feat.GetGeometryRef()
            layer_geom_type = geom_class.GetGeometryType()
            geomok=bool()
            # check the type of geometry
            if layer_geom_type==CodTipoGeom:
                geomok=bool('True')
            # include POLYGON as MULTIPOLYGON
            elif CodTipoGeom==6 and layer_geom_type==3:
                geomok=bool('True')

            if not geomok:
                txt1=self.tr('Geometry type must be')
                txt2=self.tr('error in file')
                errMsg= '%s - %s : %s\n\n %s  %s' % (NomeTabella,txt1,TipoGeom,txt2,fn)
                #exit with an error code
                NotErr=bool()
                return NotErr, errMsg

            #Empty table
            sql = "DELETE FROM %s;" % (NomeTabella)
            cur.execute(sql)
            conn.commit()


            NameFieldShp, TypeFieldShp =CampiSHP(Inlayer,feat)
            NumFieldsShp=len(NameFieldShp)
            # mapping shapefile fields to those of the geodatabase
            dic_fiels = {}
            dic_fiels_type = {}
            CampiInsert=[]
            # pair with fields of the same name
            # does not consider the case sensitive
            for i in range(NumFields):
                for j in range(NumFieldsShp):
                    if str.upper(NameField[i])==str.upper(NameFieldShp[j]):
                        # todo : check the type
                        dic_fiels[NameFieldShp[j]]=NameField[i]
                        dic_fiels_type[NameFieldShp[j]]=TypeField[i]
                        CampiInsert.append(NameFieldShp[j])
                        break

            bar.setValue(10)

            #need if looping again
            Inlayer.ResetReading()

            ListaSql=[]

            layermem=UploadLayerInSQL(Inlayer,NumEPSGAreaStudio,GeomAreawkt,
            NomeTabella,NameField,TypeField,dic_fiels,CampiInsert,TipoGeom,
            ListaSql, bar)
            bar.setValue(60)

            inDS=None

            nn=len(ListaSql)
            if nn>0:
                n1=40.0/float(nn)
            else:
                n1=0.0
            kkk=0
            for sql in ListaSql:
                kkk=kkk+1
                try:
                    cur.execute(sql)
                    conn.commit()

                    nnn=60+int(float(kkk)*n1)
                    if nnn<100:
                        bar.setValue(nnn)

                except:
                    exceptionType, exceptionValue, exceptionTraceback = sys.exc_info()
                    errMsg= "Table %s  Error! ->%s" % (NomeTabella,exceptionValue)
                    errMsg=exceptionValue
                    NotErr=bool()
                    return NotErr, errMsg

            bar.setValue(100)

    # updade fields
    # ----------------
    carico=UpLoad[3]

    if carico>0:

        bar.setValue(0)

        finp = open(cvsCensus)

        # Reading csv file
        csv_reader = csv.reader(finp, delimiter=';')

        headers = csv_reader.next()

        num_cols=len(headers)

        numcol = {}
        k=-1
        TypeField=[]
        for name in headers:
            k+=1
            numcol[name]=k
            if name=='CensID':
                KeyCol=k
            if name=='Resident':
                ColPop=k

        # mapping shapefile fields to those of the geodatabase
        dic_fiels = {}
        CampoChiave='CensID'
        CampoAb_Altro='Seasonal'
        NomeTabella='CensusBlocks'

        sql="SELECT OBJECTID, %s, %s, AsText(geom) FROM %s;" % (CampoChiave,
        CampoAb_Altro,NomeTabella)

        cur.execute(sql)
        records=cur.fetchall()
        OBJECTID=[]
        SEZ_insert=[]
        ListaPesi=[]
        ListaAbAltro=[]
        ListArea=[]

        nn=len(records)
        if nn>0:
            n1=10.0/float(nn)
        else:
            n1=0.0
            txt1=self.tr('Warning the table is empty')
            txt2=self.tr('not loaded')
            errMsg= '%s - %s\n\n file: %s\n\n %s' % (NomeTabella,txt1,cvsCensus,txt2)
            #exit with an error code
            NotErr=bool()
            return NotErr, errMsg

        kkk=0
        for rec in records:
            kkk=kkk+1
            try:
                sez_cur_txt='%d' % (rec[1])
                SEZ_insert.append(sez_cur_txt)

                OBJECTID.append(rec[0])
                wkt= rec[3]
                curva_mem = ogr.CreateGeometryFromWkt(wkt)
                Area= curva_mem.GetArea()
                ListArea.append(Area)
                peso=float(1000000.0/Area)
                ListaPesi.append(peso)

                if rec[2]!=None:
                    abaltro=int(rec[2])
                    ListaAbAltro.append(abaltro)
                else:
                    ListaAbAltro.append(0)
            except:
                pass

            nnn=int(float(kkk)*n1)
            if nnn<100:
                bar.setValue(nnn)


        # reads all the csv file and loads data from population
        # -------------------------------------------------------
        Pop_csv={}
        for row in csv_reader:
            sez_cur=int(row[KeyCol])
            sez_cur_txt='%d' % (sez_cur)
            try:
                if sez_cur_txt in SEZ_insert:
                    pop_cur=float(row[ColPop])
                    Pop_csv[sez_cur_txt]=pop_cur
            except:
                pass

        # set val
        # --------
        fin=15
        # --------
        bar.setValue(fin)

        nn=len(SEZ_insert)
        if nn>0:
            n1=float(100-fin)/float(nn)
        else:
            n1=0.0
        kkk=0

        for i in range (len(SEZ_insert)):
            SEZ_insert_cur=SEZ_insert[i]
            id_cur=OBJECTID[i]
            try:
                numPop=Pop_csv[SEZ_insert_cur]
                abkmq=(numPop+ListaAbAltro[i])*ListaPesi[i]
                sql='UPDATE %s SET' %(NomeTabella)
                sql+=' Resident=%d' % (numPop)
                sql+=', Peop_kmq=%.5f' % (abkmq)
                sql+=', Shape_Area=%.2f' % (ListArea[i])
                sql+=' WHERE OBJECTID=%d;' % (id_cur)
                cur.execute(sql)
                conn.commit()
            except:
                pass

            nnn=fin+int(float(i)*n1)
            if nnn<100:
                bar.setValue(nnn)
        bar.setValue(100)

    #------------------------------------
    # Load data of assets type polygonal
    #------------------------------------
    carico=UpLoad[4]

    if carico>0:

        fn=ShpBeniAreali

        NomeTabella='StructurePoly'
        sql="SELECT sql FROM sqlite_master WHERE type='table' AND name='%s';" % (NomeTabella)
        cur.execute(sql)
        Tabella=str(cur.fetchone()[0])

        NameField=[]
        TypeField=[]
        NameField, TypeField = CampiTabella(Tabella)
        # do not load OBJECTID field
        if 'OBJECTID' in NameField:
            indiceid=NameField.index('OBJECTID')
            NameField.remove('OBJECTID')
            TypeField.remove(TypeField[indiceid])

        NumFields=len(NameField)
        Null='Null'
        TipoGeom, ColGeom=GeomColumn(TypeField,NameField)
        try:
            CodTipoGeom=dic_type[TipoGeom]
        except:
            CodTipoGeom=0

        driver = ogr.GetDriverByName('ESRI Shapefile')

        # open input file
        inDS = driver.Open(fn, 0)
        if inDS is None:
            errMsg='Could not open ' + fn
            NotErr=bool()
            return NotErr, errMsg

        # open layer for reading
        Inlayer = inDS.GetLayer()
        numFeatures = Inlayer.GetFeatureCount()
        # looking for the code of the reference system
        spatialRef = Inlayer.GetSpatialRef()
        spatialRef.AutoIdentifyEPSG()
        NumEPSG= int(spatialRef.GetAuthorityCode(None))

        SpatialFilter=ogr.CreateGeometryFromWkt(GeomAreawkt)

        if NumEPSG!=NumEPSGAreaStudio:

            # spatial filter & transformation
            sourceSR = osr.SpatialReference()
            sourceSR.ImportFromEPSG(NumEPSG)
            coordTrans = osr.CoordinateTransformation(sourceSR,targetSR)
            coordTransInv = osr.CoordinateTransformation(targetSR,sourceSR)
            SpatialFilter.Transform(coordTransInv)
            bb=SpatialFilter.GetArea()
            Envelopeb=SpatialFilter.GetEnvelope()

        Inlayer.SetSpatialFilter(SpatialFilter)

        numFeatures = Inlayer.GetFeatureCount()

        if numFeatures>0:

            # list of fields
            feat = Inlayer.GetNextFeature()
            geom_class = feat.GetGeometryRef()
            layer_geom_type = geom_class.GetGeometryType()
            geomok=bool()
            # check the type of geometry
            if layer_geom_type==CodTipoGeom:
                geomok=bool('True')
            # include POLYGON as MULTIPOLYGON
            elif CodTipoGeom==6 and layer_geom_type==3:
                geomok=bool('True')

            if not geomok:
                txt1=self.tr('Geometry type must be')
                txt2=self.tr('error in file')
                errMsg= '%s - %s : %s\n\n %s  %s' % (NomeTabella,txt1,TipoGeom,txt2,fn)
                #exit with an error code
                NotErr=bool()
                return NotErr, errMsg

            NameFieldShp, TypeFieldShp =CampiSHP(Inlayer,feat)
            NumFieldsShp=len(NameFieldShp)
            # mapping shapefile fields to those of the geodatabase
            dic_fiels = {}
            dic_fiels_type = {}
            CampiInsert=[]
            # pair with fields of the same name
            # does not consider the case sensitive
            NameOccuType=''
            NameOccuTypeShp=''
            for i in range(NumFields):
                for j in range(NumFieldsShp):
                    if str.upper(NameField[i])==str.upper(NameFieldShp[j]):
                        # todo : check the type
                        dic_fiels[NameFieldShp[j]]=NameField[i]
                        dic_fiels_type[NameFieldShp[j]]=TypeField[i]
                        CampiInsert.append(NameFieldShp[j])
                        if str.upper(NameField[i])=='OCCUTYPE':
                            NameOccuType=NameField[i]
                            NameOccuTypeShp=NameFieldShp[j]
                        break

            #need if looping again
            Inlayer.ResetReading()

            # checks the OccuType
            sql="SELECT DISTINCT %s FROM Vulnerability;" % NameOccuType
            cur.execute(sql)
            rows=cur.fetchall()
            if len(rows)==0:
                #exit with an error code
                errMsg=self.tr('Error Vulnerability table is empty')
                NotErr=bool()
                return NotErr, errMsg
            else:
                ListOccuTypeVuln=[]
                for row in rows:
                    ListOccuTypeVuln.append(row[0])

                NameLayer=os.path.basename(ShpBeniAreali)
                NameLayer=str(NameLayer.split('.')[0])

                sql="SELECT DISTINCT %s FROM %s" % (NameOccuTypeShp,NameLayer)
                result = inDS.ExecuteSQL(sql)
                if result!=None:
                    resultFeat = result.GetNextFeature()
                    ListOccuTypeInput=[]
                    while resultFeat:
                        ListOccuTypeInput.append(resultFeat.GetField(0))
                        resultFeat = result.GetNextFeature()
                    inDS.ReleaseResultSet(result)
                else:
                    #exit with an error code
                    txt1=self.tr('Error: no OccuType field in file')
                    errMsg='%s : %s' % (txt1,ShpBeniAreali)
                    NotErr=bool()
                    return NotErr, errMsg

                if len(ListOccuTypeInput)==0:
                    #exit with an error code
                    txt1=self.tr('Error: no OccuType field in file')
                    errMsg='%s : %s' % (txt1,ShpBeniAreali)
                    NotErr=bool()
                    return NotErr, errMsg
                else:
                    for OccuTypeInput in ListOccuTypeInput:
                        if not OccuTypeInput in ListOccuTypeVuln:
                            #exit with an error code
                            txt1=self.tr('error: this value does not exist in Vulnerability table')
                            errMsg='File %s\n\n OccuType=%s\n\n %s' % (ShpBeniAreali,OccuTypeInput,txt1)
                            NotErr=bool()
                            return NotErr, errMsg

            #Empty table
            sql = "DELETE FROM %s;" % (NomeTabella)
            cur.execute(sql)
            conn.commit()


            ListaSql=[]

            layermem=UploadLayerInSQL(Inlayer,NumEPSGAreaStudio,GeomAreawkt,
            NomeTabella,NameField,TypeField,dic_fiels,CampiInsert,TipoGeom,
            ListaSql, bar)

            inDS=None

            ini = 40.0
            fin = 99.0
            numRighe = len(ListaSql)
            dx = (fin - ini) / float(numRighe)
            kk = 0
            for sql in ListaSql:
                try:
                    cur.execute(sql)
                    kk = kk+1
                    numCur = int(ini + dx * kk)
                    bar.setValue(numCur)
                except:
                    exceptionType, exceptionValue, exceptionTraceback = sys.exc_info()
                    errMsg= "Table %s  Error! ->%s" % (NomeTabella,exceptionValue)
                    #exit with an error code
                    NotErr=bool()
                    return NotErr, errMsg

            conn.commit()
            bar.setValue(100)


    #----------------------------------
    # Load data of assets type linear
    #----------------------------------
    carico=UpLoad[5]

    if carico>0:

        fn=ShpBeniLineari

        NomeTabella='InfrastrLines'
        sql="SELECT sql FROM sqlite_master WHERE type='table' AND name='%s';" % (NomeTabella)
        cur.execute(sql)
        Tabella=str(cur.fetchone()[0])

        NameField=[]
        TypeField=[]
        NameField, TypeField = CampiTabella(Tabella)
        # do not load OBJECTID field
        if 'OBJECTID' in NameField:
            indiceid=NameField.index('OBJECTID')
            NameField.remove('OBJECTID')
            TypeField.remove(TypeField[indiceid])

        NumFields=len(NameField)
        Null='Null'
        TipoGeom, ColGeom=GeomColumn(TypeField,NameField)
        try:
            CodTipoGeom=dic_type[TipoGeom]
        except:
            CodTipoGeom=0

        driver = ogr.GetDriverByName('ESRI Shapefile')

        # open input file
        inDS = driver.Open(fn, 0)
        if inDS is None:
            errMsg= 'Could not open ' + fn
            #exit with an error code
            NotErr=bool()
            return NotErr, errMsg

        # open layer for reading
        Inlayer = inDS.GetLayer()
        numFeatures = Inlayer.GetFeatureCount()
        # looking for the code of the reference system
        spatialRef = Inlayer.GetSpatialRef()
        spatialRef.AutoIdentifyEPSG()
        NumEPSG= int(spatialRef.GetAuthorityCode(None))
        print NumEPSG

        SpatialFilter=ogr.CreateGeometryFromWkt(GeomAreawkt)

        if NumEPSG!=NumEPSGAreaStudio:
            testo='File: %s' %(fn)
            print testo
            testo='Necessaria trasformazione di coordinate da %d a %d' %(NumEPSG,NumEPSGAreaStudio)
            print testo
            # creating the spatial filter in the origins coordinates of the shapefile
            sourceSR = osr.SpatialReference()
            sourceSR.ImportFromEPSG(NumEPSG)
            coordTrans = osr.CoordinateTransformation(sourceSR,targetSR)
            coordTransInv = osr.CoordinateTransformation(targetSR,sourceSR)
            SpatialFilter.Transform(coordTransInv)
            bb=SpatialFilter.GetArea()
            Envelopeb=SpatialFilter.GetEnvelope()

        Inlayer.SetSpatialFilter(SpatialFilter)
        numFeatures = Inlayer.GetFeatureCount()

        if numFeatures>0:


            # list of fields
            feat = Inlayer.GetNextFeature()
            geom_class = feat.GetGeometryRef()
            layer_geom_type = geom_class.GetGeometryType()
            geomok=bool()
            # check the type of geometry
            if layer_geom_type==CodTipoGeom:
                geomok=bool('True')
            # include LINESTRING as MULTILINESTRING
            elif CodTipoGeom==5 and layer_geom_type==2:
                geomok=bool('True')

            if not geomok:
                txt1=self.tr('Geometry type must be')
                txt2=self.tr('error in file')
                errMsg= '%s - %s : %s\n\n %s  %s' % (NomeTabella,txt1,TipoGeom,txt2,fn)
                #exit with an error code
                NotErr=bool()
                return NotErr, errMsg


            NameFieldShp, TypeFieldShp =CampiSHP(Inlayer,feat)
            NumFieldsShp=len(NameFieldShp)
            # mapping shapefile fields to those of the geodatabase
            dic_fiels = {}
            dic_fiels_type = {}
            CampiInsert=[]
            # pair with fields of the same name
            # does not consider the case sensitive
            NameOccuType=''
            NameOccuTypeShp=''
            for i in range(NumFields):
                for j in range(NumFieldsShp):
                    if str.upper(NameField[i])==str.upper(NameFieldShp[j]):
                        # todo : controllare il tipo
                        dic_fiels[NameFieldShp[j]]=NameField[i]
                        dic_fiels_type[NameFieldShp[j]]=TypeField[i]
                        CampiInsert.append(NameFieldShp[j])
                        if str.upper(NameField[i])=='OCCUTYPE':
                            NameOccuType=NameField[i]
                            NameOccuTypeShp=NameFieldShp[j]
                        break


            #need if looping again
            Inlayer.ResetReading()

            # checks the OccuType
            sql="SELECT DISTINCT %s FROM Vulnerability;" % NameOccuType
            cur.execute(sql)
            rows=cur.fetchall()
            if len(rows)==0:
                #exit with an error code
                errMsg=self.tr('Error Vulnerability table is empty')
                NotErr=bool()
                return NotErr, errMsg
            else:
                ListOccuTypeVuln=[]
                for row in rows:
                    ListOccuTypeVuln.append(row[0])

                NameLayer=os.path.basename(ShpBeniLineari)
                NameLayer=str(NameLayer.split('.')[0])

                sql="SELECT DISTINCT %s FROM %s" % (NameOccuTypeShp,NameLayer)
                result = inDS.ExecuteSQL(sql)
                if result!=None:
                    resultFeat = result.GetNextFeature()
                    ListOccuTypeInput=[]
                    while resultFeat:
                        ListOccuTypeInput.append(resultFeat.GetField(0))
                        resultFeat = result.GetNextFeature()
                    inDS.ReleaseResultSet(result)
                else:
                    #exit with an error code
                    txt1=self.tr('Error: no OccuType field in file')
                    errMsg='%s : %s' % (txt1,ShpBeniLineari)
                    NotErr=bool()
                    return NotErr, errMsg

                if len(ListOccuTypeInput)==0:
                    #exit with an error code
                    txt1=self.tr('Error: no OccuType field in file')
                    errMsg='%s : %s' % (txt1,ShpBeniLineari)
                    NotErr=bool()
                    return NotErr, errMsg
                else:
                    for OccuTypeInput in ListOccuTypeInput:
                        if not OccuTypeInput in ListOccuTypeVuln:
                            #exit with an error code
                            txt1=self.tr('error: this value does not exist in Vulnerability table')
                            errMsg='File %s\n\n OccuType=%s\n\n %s' % (ShpBeniLineari,OccuTypeInput,txt1)
                            NotErr=bool()
                            return NotErr, errMsg


            #Empty table
            sql = "DELETE FROM %s;" % (NomeTabella)
            cur.execute(sql)
            conn.commit()

            ListaSql=[]

            layermem=UploadLayerInSQL(Inlayer,NumEPSGAreaStudio,GeomAreawkt,
            NomeTabella,NameField,TypeField,dic_fiels,CampiInsert,TipoGeom,
            ListaSql, bar)

            inDS=None


            ini = 40.0
            fin = 99.0
            numRighe = len(ListaSql)
            dx = (fin - ini) / float(numRighe)
            kk = 0
            for sql in ListaSql:
                try:
                    cur.execute(sql)
                    kk = kk+1
                    numCur = int(ini + dx * kk)
                    bar.setValue(numCur)
                except:
                    exceptionType, exceptionValue, exceptionTraceback = sys.exc_info()
                    errMsg= "Table %s  Error! ->%s" % (NomeTabella,exceptionValue)
                    #exit with an error code
                    NotErr=bool()
                    return NotErr, errMsg

            conn.commit()
            bar.setValue(100)


    cur=None
    conn.close()

    return NotErr, errMsg

