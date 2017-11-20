#!/usr/bin/bash
prefix() {
	time=$(date "+[%Y-%m-%d %H:%M:%S] ")
	sed -u "s/^/${time}/"
}

echo "************** Start formating commute log file **************" | prefix
bench="/home/ladygrey/Documents/commute_log_store"
cd ${bench}

glist=$(gdrive list)
iftttId=$(echo "$glist" | grep 'commute_log_IFTTT' | cut -d' ' -f 1)
echo "detected ${iftttId}" | prefix
echo "============== Start downloading commute log file ==============" | prefix
gdrive export -f --mime text/csv "$iftttId" | prefix
if [[ $? -eq 0 ]]; then
	echo "finished downloading commute_log_IFTTT successfully" | prefix
else
	echo "Can't download commute_log_IFTTT file" | prefix
	echo "Abort formatting process..." | prefix
	exit 1
fi
mv commute_log_IFTTT.csv commute_log_raw.csv

if [[ ! -e commute_log_raw.csv ]]; then
	echo "Can't find commute_log_raw.csv in commute_log_store directory" | prefix
	echo "Abort formatting process..." | prefix
	exit 1
fi
#Pre edit. delete noise character
sed -e 's/Arrived at location/A/g' -e 's/Left location/L/g' -e 's/"//g' -e 's/ at /,/' -e 's/, /,/g' commute_log_raw.csv > /tmp/pre_formatted.csv
echo -e '\n' >> /tmp/pre_formatted.csv

echo "============== Start formatting commute log ==============" | prefix
addNum=0
#formatting
while read line; do
	logtype=$(echo ${line} | cut -d, -f 1)
	year=$(echo ${line} | cut -d, -f 3)
	logday=$(echo ${line} | cut -d, -f 2 | cut -d' ' -f 2)

	#change chara to num for Month
	#A,April 03,2017,08:42AM
	month=$(echo ${line} | cut -d, -f 2 | cut -d' ' -f 1)
	case ${month} in
		"January")   num_month="01";;
		"February")  num_month="02";;
		"March")     num_month="03";;
		"April")     num_month="04";;
		"May")       num_month="05";;
		"June")      num_month="06";;
		"July")      num_month="07";;
		"August")    num_month="08";;
		"September") num_month="09";;
		"October")   num_month="10";;
		"November")  num_month="11";;
		"December")  num_month="12";;
	esac
	#line=$(echo $line | sed -e "s/${month}/${num_month}/g" -e 's% %/%g')

	#hour time change to military system from AM/PM
	ampm=$(echo $line | cut -d, -f 4 | cut -c 6-7)
	loghour=$(echo $line | cut -d, -f 4 | cut -c 1-2)
	logminute=$(echo $line | cut -d, -f 4 | cut -c 4-5)

	#formatting hour section. change AM/PM to military time
	if [[ $logtype = "L" ]]; then
		if [[ $ampm = "PM" ]]; then
			loghour=$((10#$loghour + 12))
		fi

		#rounding minute
		if [ "$logminute" -lt 30 ]; then
			logminute=30
		else
			logminute=00
			loghour=$((10#$loghour + 1))
		fi
	fi

	#Output to file formatted line
	yesterday=$(date --date '1 day ago' +%Y/%m/%d)
	if [[ "${year}/${num_month}/${logday}" = ${yesterday} || $1 == "-f" ]]; then
		if [[ ${logtype} = 'A' ]]; then
			echo "${year}/${num_month}/${logday},${loghour}:${logminute}" >> commute_log_${year}-${num_month}.csv
			echo "Added arrived time ${year}/${num_month}/${logday},${loghour}:${logminute}" | prefix
			addNum=$((${addNum} + 1))
		else
			if [[ "$(grep "${year}/${num_month}/${logday}" commute_log_${year}-${num_month}.csv)" = "" ]]; then
				echo "${year}/${num_month}/${logday}" >> commute_log_${year}-${num_month}.csv
				echo "No log arrived time today. Add date" | prefix
			fi
			sed -i -e "/${year}\/${num_month}\/${logday}/s/$/,${loghour}:${logminute}/g" commute_log_${year}-${num_month}.csv
			echo "Add leave time ${loghour}:${logminute}" | prefix
			addNum=$((${addNum} + 1))
		fi
	fi
done < /tmp/pre_formatted.csv

echo "added ${addNum} element" | prefix
echo "finished formatting commute log" | prefix

#insert split line if the day was Monday
if [[ $(date +%s) = "Mon" ]]; then
	echo "-------------------------" >> commute_log_${year}-${num_month}.csv
fi

# if first day of month, current file change to past file and archive before 2 month file
if [[ "$(date +%d)" = "01" ]]; then
    echo "============== Start arrange commute log store files ==============" | prefix
	lastMonth=$(data -d 'last month' +%Y%m)
	archiveMonth=$(data -d '2 month ago' +%Y%m)

	#last month file archive
	mv commute_log_raw.csv commute_log_raw_${lastmonth}.csv
	echo "Renamed raw file to commute_log_raw_${lastmonth}.csv" | prefix

	#2 month ago file upload at csv file
	tar rf commute_log_raw.tar commute_log_raw_${archiveMonth}.csv
	echo "Archived commute_log_raw_${archiveMonth}.csv" | prefix

	#delete and commute_log_IFTTT
	gdrive delete --no-progress ${iftttId} | prefix
	echo "Deleted commute_log_IFTTT from gdrive" | prefix

fi

echo "============== Start sync to gdrive ==============" | prefix
dirId=$(echo "$glist" | grep commute_log_store | awk '{print $1}')
gdrive sync upload --no-progress ${bench} ${dirId} | prefix
echo "finished format commute log" | prefix



