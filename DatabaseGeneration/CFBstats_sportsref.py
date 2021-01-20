import urllib.request # static url reading

# xml parsing
from lxml import etree
from lxml import html
import lxml.cssselect
from http.cookiejar import CookieJar

import pymysql # sql queries

# system libs
import datetime
import sys
import time

# connects to my JCS DB with my super secure username and password
db = pymysql.connect(host="localhost", user="jcsuser", passwd="jcspassword", db="JCS")
cursor = db.cursor()

# Loads team aliases from CSV file - allows us to recognize team names that are stylized differently
teamAliases = {}
file = open("/var/www/html/JCSrankings/DatabaseGeneration/TeamAliases.csv")
for line in file:
	names = str(line.strip("\n").split(",")).strip("[]")
	cursor.execute("SELECT * from Teams where name in (" + names + ")")
	team = cursor.fetchall()
	if len(team) == 0:
		print("Team not found: " + names)
		quit()
	elif len(team) > 1:
		print("Multiple teams found: " + names)
		quit()
	else:
		for n in names.split(","):
			teamAliases[n.strip("' ").strip('"').lower()] = int(team[0][0])

# Log file for games that aren't handled properly
logfile = open("/var/www/html/JCSrankings/DatabaseGeneration/missing_games.txt", "w+")

class Team:
        id = -1

        name = "None"
        opp = None
        site = "N"
        score = -1

        passYds = -1
        passAtt = -1
        passComp = -1

        rushYds = -1
        rushAtt = -1

        ints = -1
        fumbs = -1

        firstDowns = -1

        pens = -1
        penYds = -1

        # placeholders for future ideas
        punts = -1
        puntYds = -1
        FGMade = -1
        FGAtt = -1

        def printSelf(self):
                print(self.name, "(" + str(self.id) + ", " + str(self.site) + ")", self.score)
                print("\tRushing: " + str(self.rushAtt) + ", " + str(self.rushYds))
                print("\tPassing: " + str(self.passComp) + "-" + str(self.passAtt) + ", " + str(self.passYds))
                print("\tFumbles: " + str(self.fumbs) + ", Interceptions: " + str(self.ints))

def printHtml(root, depth):
        for n in range(0, depth):
                print(" ", end='')
        print(depth, end='')
        print(root.tag, root.get("class"), root.text)
        for child in root:
                printHtml(child, depth+1)

def insertGameRow(date, awayTeam, homeTeam, legacy = False):
        cursor.execute("SELECT * from Games where date='" + date + "' and awayTeamID=" + str(awayTeam.id) + " and homeTeamID=" + str(homeTeam.id))
        games = cursor.fetchall()
        if len(games) > 0:
                print("Already handled " + awayTeam.name + "-" + homeTeam.name)
                return # game has already been handled

        print(date)
        awayTeam.printSelf()
        homeTeam.printSelf()

        site = 0
        if awayTeam.site == "N":
                site = 1

        if legacy:
#		print(\
                cursor.execute(\
                "INSERT into Games (date, awayTeamID, awayScore, homeTeamID, homeScore) values ('" + \
                date + "', " + str(awayTeam.id) + ", " + str(awayTeam.score) + ", " + str(homeTeam.id) + \
                ", " + str(homeTeam.score) + ")")
                return

#	print(\
        cursor.execute(\
        "INSERT into Games values (" + str(site) + ", '" + date + "', " + \
        str(awayTeam.id) + ", " + str(awayTeam.score) + ", " + str(awayTeam.passYds) + ", " + str(awayTeam.passAtt) + ", " + \
        str(awayTeam.passComp) + ", " + str(awayTeam.rushYds) + ", " + str(awayTeam.rushAtt) + ", " + str(awayTeam.ints) + ", " + \
        str(awayTeam.fumbs) + ", " + str(awayTeam.firstDowns) + ", " + str(awayTeam.pens) + ", " + str(awayTeam.penYds) + ", " + \
	str(homeTeam.id) + ", " + str(homeTeam.score) + ", " + str(homeTeam.passYds) + ", " + str(homeTeam.passAtt) + ", " + \
	str(homeTeam.passComp) + ", " + str(homeTeam.rushYds) + ", " + str(homeTeam.rushAtt) + ", " + str(homeTeam.ints) + ", " + \
	str(homeTeam.fumbs) + ", " + str(homeTeam.firstDowns) + ", " + str(homeTeam.pens) + ", " + str(homeTeam.penYds) + ", NULL, NULL, 0, 0)")

def getTeamIdFromName(name):
	name = name.lower()
	if name in teamAliases:
		return teamAliases[name]
	else:
		print("ID for " + name + " not found.")
		return -1

def parseBoxScore(link):
	response = urllib.request.urlopen(link)
	page = response.read()
	boxscore = html.document_fromstring(page)
	response.close()

#	printHtml(boxscore, 0)

	homeTeam = Team()
	awayTeam = Team()

	teams = boxscore.cssselect(".scorebox strong a")

	homeTeam.name = teams[1].text_content()
	homeTeam.id = getTeamIdFromName(homeTeam.name)

	homeTeam.opp = awayTeam
	homeTeam.site = "H"

	awayTeam.name = teams[0].text_content()
	awayTeam.id = getTeamIdFromName(awayTeam.name)

	awayTeam.opp = homeTeam
	awayTeam.site = "V"

	isNeutral = False
	# This neutral site data is no longer availible. Will investigate an alternative if we really want it. Probably could just manually tag.

	try:
		allTeamStats = boxscore.cssselect("div#all_team_stats")[0]
		statsString = lxml.etree.tostring(allTeamStats).replace("<!--", " ").replace("-->", " ")
		if "<tbody>" not in statsString:
			statsString = statsString.split("</thead>")[0] + "</thead><tbody>" + statsString.split("</thead>")[1]
		statsHtml = html.document_fromstring(statsString)
		stats = statsHtml.cssselect("table#team_stats tbody")[0]
#		printHtml(stats, 0)

		awayTeam.rushAtt = stats[1][1].text_content().split("-")[0]
		if "--" in stats[1][1].text_content():
			awayTeam.rushYds = "-" + stats[1][1].text_content().split("-")[2]
		else:
			awayTeam.rushYds = stats[1][1].text_content().split("-")[1]
		homeTeam.rushAtt = stats[1][2].text_content().split("-")[0]
		if "--" in stats[1][2].text_content():
			homeTeam.rushYds = "-" + stats[1][2].text_content().split("-")[2]
		else:
			homeTeam.rushYds = stats[1][2].text_content().split("-")[1]
		# can get rushTDs too

		awayTeam.passAtt = stats[2][1].text_content().split("-")[1]
		awayTeam.passComp = stats[2][1].text_content().split("-")[0]
		if "--" in stats[2][1].text_content():
			awayTeam.passYds = "-" + stats[2][1].text_content().split("-")[3]
			awayTeam.ints = stats[2][1].text_content().split("-")[5]
		else:
			awayTeam.passYds = stats[2][1].text_content().split("-")[2]
			awayTeam.ints = stats[2][1].text_content().split("-")[4]
		homeTeam.passAtt = stats[2][2].text_content().split("-")[1]
		homeTeam.passComp = stats[2][2].text_content().split("-")[0]
		if "--" in stats[2][2].text_content():
			homeTeam.passYds = "-" + stats[2][2].text_content().split("-")[3]
			homeTeam.ints = stats[2][2].text_content().split("-")[5]
		else:
			homeTeam.passYds = stats[2][2].text_content().split("-")[2]
			homeTeam.ints = stats[2][2].text_content().split("-")[4]
		# can get passTD too

		awayTeam.firstDowns = stats[0][1].text_content()
		homeTeam.firstDowns = stats[0][2].text_content()

		awayTeam.fumbs = stats[4][1].text_content().split("-")[1]
		homeTeam.fumbs = stats[4][2].text_content().split("-")[1]
		# can differentiate lost vs retained

		awayTeam.pens = stats[6][1].text_content().split("-")[0]
		awayTeam.penYds = stats[6][1].text_content().split("-")[1]
		homeTeam.pens = stats[6][2].text_content().split("-")[0]
		homeTeam.penYds = stats[6][2].text_content().split("-")[1]
	except:
		logfile.write(link + "\n")
		print("Stats for " + awayTeam.name + " " + homeTeam.name + " not available.")

	return awayTeam, homeTeam, isNeutral

scoreboardBase = "http://www.sports-reference.com/cfb/boxscores/index.cgi?"
def getScoresForDate(month, day, year, full_week = True, legacy = False):
	scoreboardURL = scoreboardBase + "month=" + str(month) + "&day=" + str(day) + "&year=" + str(year)
	response = urllib.request.urlopen(scoreboardURL)
	page = response.read()
	root = html.document_fromstring(page)
	response.close()
	for br in root.xpath("*//br"):
		br.tail = "\n" + br.tail if br.tail else "\n"

	if len(root.cssselect("div.game_summaries")) == 0:
		print("No game summaries found for week of " + str(month) + "-" + str(day) + "-" + str(year))
		return

	main_scores = root.cssselect("div.game_summaries")[0]

	# skip games that weren't actually played on this day
	if "Other Games" in main_scores.cssselect("h2")[0].text_content():
		print("No games played on " + str(month) + "-" + str(day) + "-" + str(year))
		return

	main_scores = main_scores.cssselect("div.game_summary") # array of games

	for score in main_scores:
		date = str(year) + "-" + str(month) + "-" + str(day)
		score = score.cssselect("tr")


		firstTeam = 0
		if score[0].get("class") == "date":
			firstTeam = 1

		try:
			if not legacy and len(score[firstTeam][2]) > 0:
				link = "http://www.sports-reference.com" + score[firstTeam][2][0].get("href")
				print("\nParsing " + link)
				awayTeam, homeTeam, isNeutral = parseBoxScore(link)
			else:
				awayTeam = Team()
				awayTeam.name = score[firstTeam][0].cssselect("a")[0].text_content()
				awayTeam.id = getTeamIdFromName(awayTeam.name)

				homeTeam = Team()
				homeTeam.name = score[firstTeam+1][0].cssselect("a")[0].text_content()
				homeTeam.id = getTeamIdFromName(homeTeam.name)

				print("Skipping boxscore portion for legacy game on " + date + " for " + awayTeam.name + " vs " + homeTeam.name)

			awayTeam.score = score[firstTeam][1].text_content()
			homeTeam.score = score[firstTeam+1][1].text_content()
			tempLegacy = legacy
			if awayTeam.score == '' or homeTeam.score == "":
				print("No score availible for " + awayTeam.name + " at " + homeTeam.name + ". Was the game not played?")
			else:
				if awayTeam.rushAtt == -1 and homeTeam.rushAtt == -1:
					tempLegacy = True # legacy if we can't find the boxscore
				insertGameRow(date, awayTeam, homeTeam, tempLegacy)
		except Exception as e:
			print("Failed to get boxscore:", e)

def handleYear(year):
	# start in february to ignore previous season's bowls
	for month in range(8, 13): # aug-dec, assume no games until late-August
		max_date = 31
		if month == 2:
			max_date = 28
			if year % 4 == 0:
				max_date = 29
		elif month in [4, 6, 9, 11]:
			max_date = 30
		for date in range(1, max_date+1):
			getScoresForDate(month, date, year)
			db.commit()

	for date in range(1, 32): # jan of next year (bowls)
		getScoresForDate(1, date, year+1)
		db.commit()

def getLinesForYesterday(month, day, year):
	date = str(year) + str(month).zfill(2) + str(day).zfill(2)
#	link = "http://www.scoresandodds.com/index.html?sort=rot"
	link = "http://www.scoresandodds.com/yesterday.html?sort=rot"

	cj = CookieJar()
	opener = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(cj))
	response = opener.open(link)
	page = response.read()
	root = html.document_fromstring(page)
	response.close()

	lines = root.findall(".//div[@id='fbc']...")
	if len(lines) == 0:
		print("No lines found for " + str(month) + "-" + str(day) + "-" + str(year))
		return
	lines = lines[0]
	teams = lines.cssselect("tr.team")
	for n in range(0, len(teams), 2):
		away = teams[n]
		home = teams[n+1]

		awayteam = getTeamIdFromName(" ".join(away.cssselect("td.name")[0].text_content().split(" ")[1:]))
		awayline = away.cssselect("td.currentline")[0].text_content().split(" ")[0]
		awaymoney = away.cssselect("td.line")[2].text_content()
		hometeam = getTeamIdFromName(" ".join(home.cssselect("td.name")[0].text_content().split(" ")[1:]))
		homeline = home.cssselect("td.currentline")[0].text_content().split(" ")[0]
		homemoney = home.cssselect("td.line")[2].text_content()

		if "-" in awayline:
			homeline = awayline[1:]
		else:
			awayline = homeline[1:]

		if awaymoney == "":
			awaymoney = "0"
		if homemoney == "":
			homemoney = "0"

		cursor.execute("UPDATE Games set line=" + homeline + ", moneyLineAway=" + awaymoney + ", moneyLineHome=" + homemoney + 
			       " WHERE awayTeamID=" + str(awayteam) + " and homeTeamID=" + str(hometeam) + " and date=" + date)

# MAIN METHOD
try:
	print("Getting scores...")

	if len(sys.argv) == 2 and sys.argv[1] == "daily":
		yesterday = datetime.datetime.now() - datetime.timedelta(days=1)
		getScoresForDate(yesterday.month, yesterday.day, yesterday.year)
		db.commit()
#		getLinesForYesterday(yesterday.month, yesterday.day, yesterday.year)
	else:
		print("Invalid arguments. Executing default code.")

		getScoresForDate( 9, 2, 2018)
		getScoresForDate( 9, 3, 2018)
		getScoresForDate( 9, 4, 2018)
		getScoresForDate( 9, 5, 2018)
		getScoresForDate( 9, 6, 2018)
#		getLinesForYesterday(9, 1, 2018)

#		getScoresForDate( 8, 28, 2015) # should be no games this week
#		getScoresForDate( 9,  1, 2015) # should be no games this day
#		getScoresForDate( 9,  3, 2015) # should have games, but already in table

# Must switch user to root in order to delete from DB
#		for n in range(16, 32):
#			cursor.execute("DELETE from Games WHERE date='%s-%s-%s'", [2017, 12, n])
#			getScoresForDate(12, n, 2017)
#		for n in range(1, 9):
#			cursor.execute("DELETE from Games WHERE date='%s-%s-%s'", [2018, 1, n])
#			getScoresForDate(1, n, 2018)

#		getLinesForYesterday(8, 25, 2018) # test this function

except MySQLdb.Error as e:
	print(str(e))

db.commit()
logfile.close()
