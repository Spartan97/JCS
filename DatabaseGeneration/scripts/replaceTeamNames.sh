#!/bin/bash

function replaceName {
	if [[ $# -ne 2 ]]
		then
			echo "Must supply two arguments - a team name string and a new team name"
			exit 1
	fi

	old_name=','${1//"&"/"\&"}','
	new_name=','${2//"&"/"\&"}','

	sed -i.bak "s/$old_name/$new_name/g" ../stats00-13/*.csv
}

cat TeamNames.csv | while read line
do
	old_name=$(echo $line | cut -d "," -f1)
	new_name=$(echo $line | cut -d "," -f2)

	replaceName "$old_name" "$new_name"
done
