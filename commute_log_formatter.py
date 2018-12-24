import os
import csv
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

Logger("************** Start formating commute log file **************")

bench = "/home/ladygrey/Documents/commute_log_store"

fileDec = get_file_dec()

print(fileDec)
