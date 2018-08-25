import urllib2 # static url reading

# xml parsing
from lxml import etree
from lxml import html
import lxml.cssselect

import MySQLdb # sql queries

# system libs
import datetime
import sys
import time

# imports for browser (javascript loading)
#from selenium import webdriver
#from pyvirtualdisplay import Display

# connects to my JCS DB with my super secure username and password
db = MySQLdb.connect(host="localhost", user="jcsuser", passwd="jcspassword", db="JCS")
cursor = db.cursor()

# Loads team aliases from CSV file - allows us to recognize team names that are stylized differently
teamAliases = {}
file = open("/var/www/html/JCSrankings/DatabaseGeneration/TeamAliases.csv")
for line in file:
	names = str(line.strip("\n").split(",")).strip("[]")
	cursor.execute("SELECT * from Teams where name in (" + names + ")")
	team = cursor.fetchall()
	if len(team) == 0:
		print "Team not found: " + names
		quit()
	elif len(team) > 1:
		print "Multiple teams found: " + names
		quit()
	else:
		for n in names.split(","):
			teamAliases[n.strip("' ").strip('"')] = int(team[0][0])

# starts browser used for getting stats. Browser is needed because tables are loaded by javascript, so we can't just get the HTML
#print "starting browser"
#display = Display(visible=0, size=(800,600))
#display.start()
#browser = webdriver.Firefox(log_path="./geckodriver.log")
#browser.set_page_load_timeout(60)

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
                print self.name, "(" + str(self.id) + ", " + str(self.site) + ")", self.score
                print "\tRushing: " + str(self.rushAtt) + ", " + str(self.rushYds)
                print "\tPassing: " + str(self.passComp) + "-" + str(self.passAtt) + ", " + str(self.passYds)
                print "\tFumbles: " + str(self.fumbs) + ", Interceptions: " + str(self.ints)

def printHtml(root, depth):
        for n in range(0, depth):
                print " ",
        print depth,
        print root.tag, root.get("class"), root.text
        for child in root:
                printHtml(child, depth+1)

def fillPenaltyData(date, awayTeam, homeTeam):
	cursor.execute("UPDATE Games SET awayPens=" + str(awayTeam.pens) + ", awayPenYds=" + str(awayTeam.penYds) + ", awayFirstDowns=" + str(awayTeam.firstDowns) + \
		       ", homePens=" + str(homeTeam.pens) + ", homePenYds=" + str(homeTeam.penYds) + ", homeFirstDowns=" + str(homeTeam.firstDowns) + \
		       " WHERE date='" + date + "' and awayTeamID=" + str(awayTeam.id) + " and homeTeamID=" + str(homeTeam.id))

def insertGameRow(date, awayTeam, homeTeam, legacy = False):
        cursor.execute("SELECT * from Games where date='" + date + "' and awayTeamID=" + str(awayTeam.id) + " and homeTeamID=" + str(homeTeam.id))
        games = cursor.fetchall()
        if len(games) > 0:
		print "Already handled " + awayTeam.name + "-" + homeTeam.name
                return # game has already been handled

	print date
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
	str(homeTeam.fumbs) + ", " + str(homeTeam.firstDowns) + ", " + str(homeTeam.pens) + ", " + str(homeTeam.penYds) + ", NULL, NULL)")

def getTeamIdFromName(name):
	if name in teamAliases:
		return teamAliases[name]
	else:
		print "ID for " + name + " not found."
		return -1

def parseBoxScore(link):
#	browser.get(link)
#	time.sleep(5) # delay to let the javascript load
#	boxscore = html.document_fromstring(browser.page_source)

	response = urllib2.urlopen(link)
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
		print "Stats for " + awayTeam.name + " " + homeTeam.name + " not available." 

	return awayTeam, homeTeam, isNeutral

scoreboardBase = "http://www.sports-reference.com/cfb/boxscores/index.cgi?"
def getScoresForDate(month, day, year, full_week = True, legacy = False):
	scoreboardURL = scoreboardBase + "month=" + str(month) + "&day=" + str(day) + "&year=" + str(year)
	response = urllib2.urlopen(scoreboardURL)
	page = response.read()
	root = html.document_fromstring(page)
	response.close()
	for br in root.xpath("*//br"):
		br.tail = "\n" + br.tail if br.tail else "\n"

	if len(root.cssselect("div.game_summaries")) == 0:
		print "No game summaries found for week of " + str(month) + "-" + str(day) + "-" + str(year)
		return

	main_scores = root.cssselect("div.game_summaries")[0]
#	try:
#		other_scores = root.cssselect(".game_summaries")[1].cssselect("div.game_summary")
#	except:
#		print "No other scores for the week of " + str(year) + "-" + str(month) + "-" + str(day)
#		other_scores = []

	# skip games that weren't actually played on this day
	if "Other Games" in main_scores.cssselect("h2")[0].text_content():
		print "No games played on " + str(month) + "-" + str(day) + "-" + str(year)
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
				print "\nParsing " + link
				awayTeam, homeTeam, isNeutral = parseBoxScore(link)
			else:
				awayTeam = Team()
				awayTeam.name = score[firstTeam][0].cssselect("a")[0].text_content()
				awayTeam.id = getTeamIdFromName(awayTeam.name)

				homeTeam = Team()
				homeTeam.name = score[firstTeam+1][0].cssselect("a")[0].text_content()
				homeTeam.id = getTeamIdFromName(homeTeam.name)

				print "Skipping boxscore portion for legacy game on " + date + " for " + awayTeam.name + " vs " + homeTeam.name

			awayTeam.score = score[firstTeam][1].text_content()
			homeTeam.score = score[firstTeam+1][1].text_content()
#			print date
#			awayTeam.printSelf()
#			homeTeam.printSelf()
			tempLegacy = legacy
			if awayTeam.score == '' or homeTeam.score == "":
				print "No score availible for " + awayTeam.name + " at " + homeTeam.name + ". Was the game not played?"
			else:
				if awayTeam.rushAtt == -1 and homeTeam.rushAtt == -1:
					tempLegacy = True # legacy if we can't find the boxscore
#				if not tempLegacy:
#					fillPenaltyData(date, awayTeam, homeTeam)
				insertGameRow(date, awayTeam, homeTeam, tempLegacy)
		except Exception as e:
			print "Failed to get boxscore"
			print e, e.reason

########### Disabling this feature to simplify parsing. Now we only look for the actaul day's games

#	if not full_week:
#		return

#	for score in other_scores:
#		score = score.cssselect("tr")
#		date = score[0].text_content().split(" ")[1].split("/")
#		newday = int(date[-1])
#		newmonth = int(date[-2])
#		newyear = year
#		if newmonth == 12 and month == 1:
#			newyear = year-1
#		elif newmonth == 1 and month == 12:
#			newyear = year+1
#		date = str(newyear) + "-" + str(newmonth) + "-" + str(newday)

#		try:
#			if not legacy:
#				link = "http://www.sports-reference.com" + score[1][2][0].get("href")
#				print "\nParsing " + link
#				awayTeam, homeTeam, isNeutral = parseBoxScore(link)
#			else:
#				awayTeam.name = score[1][0].cssselect("a")[0].text_content()
#				awayTeam.name = score[2][0].cssselect("a")[0].text_content()
#				print "Skipping legacy boxscore on " + date + " for " + awayTeam.name + " vs " + homeTeam.name
#			awayTeam.score = score[1][1].text_content()
#			homeTeam.score = score[2][1].text_content()
##			print date
##			awayTeam.printSelf()
##			homeTeam.printSelf()
#			insertGameRow(date, awayTeam, homeTeam, legacy)
#		except Exception as e:
#			print "Failed to get boxscore"
#			print e

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

#def getLines(year, month, day):
#	date = str(year) + str(month).zfill(2) + str(day).zfill(2)
#	link = "http://www.sportsbookreview.com/betting-odds/college-football/?date=" + date
#	print "Getting lines from " + link
#	browser.get(link)
#	time.sleep(3) # delay to let the javascript load
#	root = html.document_fromstring(browser.page_source)
#
#	try:
#		games = root.cssselect(".eventLines")
#		if len(games) == 0:
#			print "No lines for date " + date
#			return
#		games = games[0].cssselect(".event-holder")
#	except Exception as e:
#		print "Could not find lines for date: " + date
#		print e, e.reason
#
#	try:
#		for game in games:
#			away = game.cssselect(".team-name a")[0].text_content()
#			home = game.cssselect(".team-name a")[1].text_content()
#
#			awayId = getTeamIdFromName(away)
#			homeId = getTeamIdFromName(home)
#
##			print away, awayId
##			print home, homeId
#
#			if awayId == -1 or homeId == -1:
#				continue # skip if we're missing one of the teams
#
#			line = 0.0
#			count = 0
#			books = game.cssselect(".eventLine-book")
#			# find the spread for each book
#			for book in books:
#				value = book.cssselect(".eventLine-book-value")[1].text_content().split(unichr(160))[0].replace(unichr(189), ".5")
#				if value != "":
#					# if its a pickem line, the value is 0, but count still goes up
#					if not "PK" in value:
#						line += float(value)
#					count += 1
#			# aggregate the lines
#			if count != 0:
#				line /= count
#			line = round(line * 2) / 2 # round to nearest .5
##			print line
##			print
#
#			date = str(year) + "-" + str(month) + "-" + str(day)
#			result = cursor.execute("UPDATE Games SET line=" + str(line) + " where date='" + date + "' and awayTeamID=" + str(awayId) + " and homeTeamID=" + str(homeId))
#			if result == 0:
#				cursor.execute("UPDATE Games SET line=" + str(-1*line) + " where date='" + date + "' and awayTeamID=" + str(homeId) + " and homeTeamID=" + str(awayId))
#			# sometimes with neutral site the home/away stuff gets janky, so we need to check hte opposite scenario
#			db.commit()
#	except Exception as e:
#		print "Error parsing game lines."
#		print e, e.reason

# MAIN METHOD
try:
	print "Getting scores..."

	if len(sys.argv) == 2 and sys.argv[1] == "daily":
		yesterday = datetime.datetime.now() - datetime.timedelta(days=1)
		getScoresForDate(yesterday.month, yesterday.day, yesterday.year)	
		getLines(yesterday.year, yesterday.month, yesterday.day)
	else:
		print "Invalid arguments. Executing default code."

# VEGAS LINES BACKFILL
#		for n in range(1, 32):
#			getLines(2003, 8, n)
#			getLines(2003, 9, n)
#			getLines(2003, 10, n)
#			getLines(2003, 11, n)
#			getLines(2003, 12, n)
#			getLines(2004, 1, n)

# PENALTY DATA BACKFILL
#		links = ["http://www.sports-reference.com/cfb/boxscores/2000-08-27-penn-state.html"] # will need to load from file
#		for link in links:
#			firstNum = link.index('2')
#			date = link[firstNum:firstNum+10]
#			awayTeam, homeTeam, isNeutral = parseBoxScore(link)
#			print awayTeam.id, awayTeam.firstDowns, awayTeam.pens, awayTeam.penYds
#			print homeTeam.id, homeTeam.firstDowns, homeTeam.pens, homeTeam.penYds
#			fillPenaltyData(date, awayTeam, homeTeam)	

#		getScoresForDate( 8, 28, 2015) # should be no games this week
#		getScoresForDate( 9,  1, 2015) # should be no games this day
#		getScoresForDate( 9,  3, 2015) # should have games, but already in table

		getScoresForDate( 9, 15, 2012)
		getScoresForDate(10, 19, 2013)
		getScoresForDate(10, 26, 2013)
		getScoresForDate(11, 9, 2013)
		getScoresForDate(11, 16, 2013)
		getScoresForDate( 8, 30, 2014)
		getScoresForDate( 9, 6, 2014)
		getScoresForDate( 9, 25, 2014)
		getScoresForDate( 9, 10, 2016)
		getScoresForDate(10, 8, 2016)
		getScoresForDate(10, 29, 2016)
		getScoresForDate( 9, 2, 2017)
		getScoresForDate( 9, 9, 2017)
		getScoresForDate(11, 3, 2017)
		getScoresForDate( 11, 18, 2017)
		getScoresForDate( 11, 25, 2017)

#		getLines(2012, 9, 15)
#		getLines(2013, 10, 19)
#		getLines(2013, 10, 26)
#		getLines(2013, 11, 9)
#		getLines(2013, 11, 16)
#		getLines(2014, 8, 30)
#		getLines(2014, 9, 6)
#		getLines(2014, 9, 25)
#		getLines(2016, 9, 10)
#		getLines(2016, 10, 8)
#		getLines(2016, 10, 29)
#		getLines(2017, 9, 2)
#		getLines(2017, 9, 9)
#		getLines(2017, 11, 3)
#		getLines(2017, 11, 18)
#		getLines(2017, 11, 25)

except:
	print "Something failed in parsing. Quitting..."

#browser.quit()
#display.stop()
#print "closing browser"

db.commit()

