import os
import pandas
import datetime
import subprocess
import re

def Logger(message):
    currentTime = datetime.datetime.now()
    print("[" + currentTime.strftime("%Y-%m-%d %H:%M:%S") + "]" + message)


def get_file_dec():
    command = ["gdrive", "list", "-q", "'name contains \"commute\"'"]
    glist = subprocess.run("gdrive list -q 'name contains \"commute\"'", shell=True,capture_output=True)

    strlist = str(glist.stdout)
    splitted = strlist.split('\\n')
    fileDec = {}

    for row in splitted:
        #print(row)
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
    os.rename('commute_log_IFTTT.csv', 'commute_log_raw.csv')

    return pandas.read_csv('commute_log_raw.csv', header=None)

def Format_CSV(rawCsv):
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
        bFormat = '%Y/%m/%d %I:%M%p'
        dt = datetime.datetime.strptime(bTime, bFormat)
        aTime = dt.strftime('%Y/%m/%d %H:%M')
        rawCsv[1][i] = aTime


    print(rawCsv)

Logger("************** Start formating commute log file **************")

bench = "/home/ladygrey/Documents/commute_log_store"

#get file list
fileDec = get_file_dec()

#check exist commute_log_IFTTT
if not ('commute_log_IFTTT' in fileDec):
    Logger("[ERROR]Can't find commute_log_IFTTT file.")
    exit(1)

Logger("============== Start downloading commute log file ==============")

#Download commute_log_IFTTT and rename to commute_log_raw.csv
rawCsv = gen_raw_csv(fileDec['commute_log_IFTTT'])

#Formatting CSV file
Format_CSV(rawCsv)


