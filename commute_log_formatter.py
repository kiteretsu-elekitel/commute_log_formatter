#!/bin/python3
import os
import pandas
import datetime
import subprocess
import re
import sys
import gspread
import oauth2client
from oauth2client.service_account import ServiceAccountCredentials
from pydrive.auth import GoogleAuth
from pydrive.drive import GoogleDrive

def getCredential():
    scope = ['https://spreadsheets.google.com/feeds',
         'https://www.googleapis.com/auth/drive']
    return ServiceAccountCredentials.from_json_keyfile_name('/home/ladygrey/script/commute_log_formatter/cliant_secret.json', scope)


def Logger(message):
    currentTime = datetime.datetime.now()
    print("[" + currentTime.strftime("%Y-%m-%d %H:%M:%S") + "] " + message)


def get_file_dec():
    #command = ["gdrive", "list", "-q", "'name contains \"commute_log_store\" or name contains \"commute_log_IFTTT\"'"]
    glist = subprocess.run("gdrive list -q 'name contains \"commute_log_store\" or name contains \"commute_log_IFTTT\"'", shell=True,capture_output=True)

    strlist = str(glist.stdout)
    splitted = strlist.split('\\n')
    fileDec = {}

    for row in splitted:
        row2 = re.sub(' +', ' ', row).split(' ')
        if len(row2) >= 2:
            key = row2[1]
            val = row2[0]
            fileDec[key] = val

    return fileDec

def gen_raw_csv(fileId):
    command = "gdrive export -f --mime text/csv " + fileId
    result = subprocess.run(command, shell=True)

    if result.returncode == 0:
        Logger("finished downloading commute_log_IFTTT successfully")
    else:
        Logger("[ERROR] Failed Download commute_log_IFTTT")
        Logger("Abort Process")
        exit(1)

    Logger("Rename commute_log_IFTTT to commute_log_raw.csv")
    os.rename('commute_log_IFTTT.csv', bench + '/commute_log_raw.csv')

    return pandas.read_csv(bench + '/commute_log_raw.csv', header=None)

def get_commute_log(credentials):
    #get authorize
    gc = gspread.authorize(credentials)
    wks = gc.open('commute_log_IFTTT').sheet1
    # get all value of sheet1
    allList = wks.get_all_values()
    Logger(pandas.DataFrame(allList))

    # retuen all sheet values exchanged pandas DataFrame
    return pandas.DataFrame(allList)

def format_CSV(rawCsv):
    rawCsv = rawCsv.replace('Arrived at location', 'A')
    rawCsv = rawCsv.replace('Left location', 'L')

    #change words of month to number
    rawCsv[1] = rawCsv[1].str.replace('January','01')
    rawCsv[1] = rawCsv[1].str.replace("February", "02")
    rawCsv[1] = rawCsv[1].str.replace("March", "03")
    rawCsv[1] = rawCsv[1].str.replace("April", "04")
    rawCsv[1] = rawCsv[1].str.replace("May", "05")
    rawCsv[1] = rawCsv[1].str.replace("June", "06")
    rawCsv[1] = rawCsv[1].str.replace("July", "07")
    rawCsv[1] = rawCsv[1].str.replace("August", "08")
    rawCsv[1] = rawCsv[1].str.replace("September", "09")
    rawCsv[1] = rawCsv[1].str.replace("October", "10")
    rawCsv[1] = rawCsv[1].str.replace("November", "11")
    rawCsv[1] = rawCsv[1].str.replace("December", "12")

    #formatting date to yyyy/mm/dd HH:MMPM
    rawCsv[1] = rawCsv[1].replace('^ *([0-9]+) ([0-9]+), ([0-9]+) at (..:....)', r'\3/\1/\2 \4', regex=True)

    #formatting time AM/PM to Millitary time
    for i in range(len(rawCsv)):
        bTime = rawCsv[1][i]
        dt = datetime.datetime.strptime(bTime, '%Y/%m/%d %I:%M%p')
        aTime = dt.strftime('%Y/%m/%d %H:%M')
        rawCsv[1][i] = aTime

    Logger('formatted CSV data')
    Logger(rawCsv)
    return rawCsv

def getLastData(csv):
    today = datetime.datetime.now()
    yesterday = today - datetime.timedelta(days=1)

    strYesterday = yesterday.strftime('%Y/%m/%d')
    lastData = csv[csv[1].str.contains(strYesterday)]
    Logger('num of lastData is ' + str(len(lastData)))

    # add yesterday date
    resultCSV = []
    resultCSV.append(strYesterday)

    if len(lastData != 0):
        lineA = lastData[lastData[0] == 'A']
        lineL = lastData[lastData[0] == 'L']
        # split colume 1 and get it
        lineADate = lineA[1].str.split(' ', expand=True)
        lineLDate = lineL[1].str.split(' ', expand=True)

        #Process arrived time
        listAtime = lineADate[1]
        sorttedA = sorted(listAtime)
        Logger("pickupped arrived time is " + str(sorttedA))
        resultCSV.append(sorttedA[0])

        #Process left time
        listLtime = lineLDate[1]
        sorttedL = sorted(listLtime)
        Logger("pickupped left time is " + str(sorttedL))
        for i in sorttedL:
            hour = int(str(i).split(':')[0])
            minute = int(str(i).split(':')[1])
            strhour = ''

            if minute > 29:
                strminute = '00'
                strhour = str(hour + 1)
            else:
                strminute = '30'
                strhour = str(hour)

            roundup = strhour + ':' + strminute
            resultCSV.append(roundup)

    Logger("last commute data is " + str(resultCSV))
    return resultCSV


def writeToCurrentCSV(lastData):
    # generate file name
    today = datetime.datetime.now()
    targetDate = today - datetime.timedelta(days=1)
    filedate = targetDate.strftime('%Y-%m')
    filename = 'commute_log_' + filedate + '_py.csv'
    #filename = 'commute_log_-.csv'
    Logger('Target CSV file name is ' + filename)

    num = len(lastData)
    #list2 = [[0]*num]*2
    list2 = [[0]*num]
    col = 0
    for i in lastData:
        list2[0][col] = i
        col = col + 1

    Logger('Write data is ' + str(list2))
    #export csv to pandas
    ps = pandas.DataFrame(list2)
    #ps.head(1).to_csv('~/Documents/commute_log_store/'+filename, mode='a', header=False, index=False)
    ps.to_csv('/home/ladygrey/Documents/commute_log_store/' + filename, mode='a', header=False, index=False)
    #ps.head(1).to_csv(sys.stdout, header=False, index=False)

    return filename


#
# main main main
#

Logger("************** Start formating commute log file **************")

bench = "/home/ladygrey/Documents/commute_log_store"

# get Google credentials
Logger("============== get google credentials ==============")
gauth = GoogleAuth()
drive = GoogleDrive(gauth)
credentials = getCredential()


#get file list
#fileDec = get_file_dec()

#check exist commute_log_IFTTT
#if not ('commute_log_IFTTT' in fileDec):
#    Logger("[ERROR]Can't find commute_log_IFTTT file.")
#    exit(1)

Logger("============== Start downloading commute log file ==============")

#Download commute_log_IFTTT and rename to commute_log_raw.csv
#rawCsv = gen_raw_csv(fileDec['commute_log_IFTTT'])
rawCsv = get_commute_log(credentials)

#Formatting CSV file
Logger("============== Start formatting commute log ==============")
formattedCSV = format_CSV(rawCsv)

#get last day data
lastData = getLastData(formattedCSV)
Logger(str(lastData))

#write to current csv file
Logger("============== Start write commute log ==============")
filename = writeToCurrentCSV(lastData)

Logger("============== Start sync to gdrive ==============")
#Logger('file id of commute_log_store is ' + fileDec['commute_log_store'])
#result = subprocess.run("gdrive sync upload --no-progress " + bench + " " + fileDec['commute_log_store'], shell=True,capture_output=True)
#result = subprocess.run("skicka upload ~/Documents/commute_log_store /commute_log_store", shell=True,capture_output=True)

Logger("============== get file id ==============")
file_list = drive.ListFile({'q': "title = '" + filename + "' and trashed=false"}).GetList()
Logger("target file id is " + file_list[0])
gdrivefile = file_list[0]

Logger("============== get file id ==============")
f = drive.CreateFile({'title':'test.csv', 'mimeType':'text/csv', 'id':gdrivefile['id'], 'parents': [{'id': '0B7_p81hYdRkzNnhhdlhUeHBJWXc'}]})
f.SetContentFile('/home/ladygrey/Documents/commute_log_store/' + filename)
f.Upload()

#Logger(str(result.stdout).replace('\\n', '\n'))
#Logger(str(result.stderr))
print()
