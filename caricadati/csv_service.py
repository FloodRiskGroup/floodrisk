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
import csv
import sys
import locale
from csv_exception import *

def set_csv_separator():
    locale.setlocale(locale.LC_ALL, '') # set to user's locale, not "C"
    dec_pt_chr = locale.localeconv()['decimal_point']
    if dec_pt_chr == ",":
        list_delimiter = ";"
    else:
        list_delimiter = ","
    return list_delimiter,dec_pt_chr

class CsvFileCheck:

    def __init__(self, pathToCsvFile):
        self._initWithPath(pathToCsvFile)

    def _initWithPath(self, pathToCsvFile):
        self.HeaderCount=0
        self.ok = False
        self.dec_pt_comma=False
        if not os.path.isfile(pathToCsvFile):
            raise FileNotFoundException()
        self.rootPath, fileExtension = os.path.splitext(pathToCsvFile)
        if fileExtension == '.csv':
            self.pathToCsvFile = pathToCsvFile
            self.firstText=''
            self.sep, self.dec_pt_chr=set_csv_separator()
            if self.dec_pt_chr==',':
                self.dec_pt_comma=True
            check1 = self.CheckNumFields()
            if not check1:
                if self.sep==',':
                    self.sep=';'
                elif self.sep==';':
                    self.sep=','
                    self.dec_pt_chr='.'
                    self.dec_pt_comma=False
                check2 = self.CheckNumFields()
                if check2:
                    self.ok=True
                    text=''
                    for txt in self.fields:
                        text+='%s | ' % txt
                    text=text[:-3]
                    text+='\n'
                    for txt in self.firstRows:
                        text+='%s | ' % txt
                    text=text[:-3]

                    self.firstText=text
                else:
                    raise UnknownFileFormatException()
            else:
                self.ok=True

        else:
            raise InvalidFileExtension()

    def ReadHeaders(self,sep):
        # Reading csv file
        finp = open(self.pathToCsvFile)
        csv_reader = csv.reader(finp, delimiter=sep, quotechar='"')
        headers = csv_reader.next()
        self.fields=[]
        for p in headers:
            self.fields.append(p)
        finp.close()
        self.HeaderCount=len(headers)

    def getSampleRowsFromCSV(self, maxRows=3):
        try :
            with open(self.pathToCsvFile, 'rb') as csvfile:
                reader = csv.reader(csvfile, delimiter=self.sep, quotechar='"')
                if self._csvHasHeader:
                    reader.next()
                rowCounter = 0
                rows = []
                row = reader.next()
                while row and rowCounter < maxRows:
                    rows.append(row)
                    rowCounter += 1
                    try:
                        row = reader.next()
                    except StopIteration:
                        pass
                return rows
        except:
            raise FileIOException()

    def CheckNumFields(self):
        self.ReadHeaders(self.sep)
        check1=False
        if self.HeaderCount>1:
            self._csvHasHeader=True
            self.firstRows = self.getSampleRowsFromCSV(1)
            if len(self.firstRows)>0:
                check1=True
                for row in self.firstRows:
                    if self.HeaderCount!=len(row):
                        check1=False
        return check1

    def float_comma(self,string):
        numstr=string.replace(',','.')
        num=float(numstr)
        return num

def main():

    pathToCsvFile='Tab1.csv'
    f1=CsvFileCheck(pathToCsvFile)

    print 'Check %s Done sep=%s' % (f1.pathToCsvFile, f1.sep)

    pathToCsvFile='Tab2.csv'
    f1=CsvFileCheck(pathToCsvFile)

    print 'Check %s Done sep=%s' % (f1.pathToCsvFile, f1.sep)

if __name__ == '__main__':
    main()