import urllib2 # url reading
from lxml import etree
from lxml import html # xml parsing
import MySQLdb # sql queries

db = MySQLdb.connect(host="localhost", user="root", passwd="12345", db="JCS")
cursor = db.cursor()

class Team:
	id = None

	name = None
	opp = None
	site = None
	score = None
	
	passYds = None
	passAtt = None
	passComp = None

	rushYds = None
	rushAtt = None

	ints = None
	fumbs = None

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

def getGameStats(gameID):
	gameURL = "http://scores.espn.go.com/ncf/boxscore?gameId=" + str(gameID)
	response = urllib2.urlopen(gameURL)
	page = response.read()
	root = html.document_fromstring(page)

	awayTeam = Team()
	homeTeam = Team()

	summary = root.find_class("matchup")[0]

	awayRegex = ".//*[contains(concat(' ', @class, ' '), ' away ') or contains(concat(' ', @class, ' '), ' visitor ')]"
	homeRegex = ".//*[contains(concat(' ', @class, ' '), ' home ')]"

	try:
		awayTeam.name = summary.xpath(awayRegex)[0].find(".//a").text_content()
		awayTeam.id = summary.xpath(awayRegex)[0].find(".//a").get("href").split("/")[-2]
	except:
		raise Exception("D2/D3 opponent. Game skipped")
	awayTeam.score = summary.xpath(awayRegex)[0].findall(".//span")[-1].text_content()
	try:
		homeTeam.name = summary.xpath(homeRegex)[0].find(".//a").text_content()
		homeTeam.id = summary.xpath(homeRegex)[0].find(".//a").get("href").split("/")[-2]
	except:
		raise Exception("D2/D3 opponent. Game skipped")
	homeTeam.score = summary.xpath(homeRegex)[0].findall(".//span")[-1].text_content()

	awayTeam.opp = homeTeam
	awayTeam.site = "V"
	homeTeam.opp = awayTeam
	homeTeam.site = "H"

	stats = root.find_class("gp-body")[0].find_class("clearfix")[0].findall(".//table")[-1]
	awayTeam.rushAtt = stats.findall("tr")[9].findall("td")[1].text_content()
	awayTeam.rushYds = stats.findall("tr")[8].findall("td")[1].text_content()
	homeTeam.rushAtt = stats.findall("tr")[9].findall("td")[2].text_content()
	homeTeam.rushYds = stats.findall("tr")[8].findall("td")[2].text_content()

	awayTeam.passComp = stats.findall("tr")[6].findall("td")[1].text_content().split("-")[0]
	awayTeam.passAtt = stats.findall("tr")[6].findall("td")[1].text_content().split("-")[1]
	awayTeam.passYds = stats.findall("tr")[5].findall("td")[1].text_content()

	homeTeam.passComp = stats.findall("tr")[6].findall("td")[2].text_content().split("-")[0]
	homeTeam.passAtt = stats.findall("tr")[6].findall("td")[2].text_content().split("-")[1]
	homeTeam.passYds = stats.findall("tr")[5].findall("td")[2].text_content()

	awayTeam.ints = stats.findall("tr")[14].findall("td")[1].text_content()
	awayTeam.fumbs = stats.findall("tr")[13].findall("td")[1].text_content()

	homeTeam.ints = stats.findall("tr")[14].findall("td")[2].text_content()
	homeTeam.fumbs = stats.findall("tr")[13].findall("td")[2].text_content()

	# could include penalties to formula too
	# need to determine line for the game

	return awayTeam, homeTeam

def verifyTeamExistsElseCreate(team):
	cursor.execute("SELECT * from Teams where id = " + str(team.id))
	teams = cursor.fetchall()
	assert (len(teams) < 2), "Error: More than one team matches id " + str(team.id)
	if len(teams) == 0:
		team.name = team.name.replace("'", "''")
		cursor.execute("INSERT into Teams values (" + str(team.id) + ", '" + team.name + "')")

def insertGameRow(id, date, awayTeam, homeTeam):
	cursor.execute("SELECT * from Games where id=" + str(id))
	games = cursor.fetchall()
	if len(games) > 0:
		return # game has already been handled (appears in both FBS and FCS list)

	site = 0
	if awayTeam.site == "N":
		site = 1
	cursor.execute("INSERT into Games values (" + str(id) + ", " + str(site) + ", '" + date + "', " + \
	str(awayTeam.id) + ", " + str(awayTeam.score) + ", " + str(awayTeam.passYds) + ", " + str(awayTeam.passAtt) + ", " + \
	str(awayTeam.passComp) + ", " + str(awayTeam.rushYds) + ", " + str(awayTeam.rushAtt) + ", " + str(awayTeam.ints) + ", " + \
	str(awayTeam.fumbs) + ", " + str(homeTeam.id) + ", " + str(homeTeam.score) + ", " + str(homeTeam.passYds) + ", " + \
	str(homeTeam.passAtt) + ", " + str(homeTeam.passComp) + ", " + str(homeTeam.rushYds) + ", " + str(homeTeam.rushAtt) + ", " + \
	str(homeTeam.ints) + ", " + str(homeTeam.fumbs) + ", 0)")

def findGamesForWeek(year, week, conference):
	seasonType = 2
	if week == 17:
		seasonType = 3 # bowl season

	scoresURL = "http://scores.espn.go.com/college-football/scoreboard/_/group/" + str(conference) + "/year/" + str(year) + "/seasontype/" + str(seasonType) + "/week/" + str(week);
	response = urllib2.urlopen(scoresURL)
	page = response.read()
	root = html.document_fromstring(page)

#	for elem in scores:
#		print elem.text_content()
	
#	for elem in scores:
#		dates = elem.find_class("games-date")
#		games = elem.find_class("gameDay-Container")
#		assert (len(dates) == len(games)), "Error: Different number of date headers and gameday containers"
#
#		for n in range(len(dates)):
#			print dates[n].text_content()
#			for game in games[n].find_class("mod-container"):
#				status = game.find_class("game-status")[0].text_content()
#				if "Final" not in status:
#					visitor = game.find_class("visitor")[0].find_class("team-capsule")[0].text_content().strip()
#					home= game.find_class("home")[0].find_class("team-capsule")[0].text_content().strip()
#					print visitor, "vs", home, "is not final yet"
#					continue
#
#				gameID = game.get("id").split("-")[0]
#
#				try:
#					awayTeam, homeTeam = getGameStats(gameID)			
#				except Exception as e:
#					print "Game failed to parse:", e.message
#					continue
#
#				verifyTeamExistsElseCreate(awayTeam)
#				verifyTeamExistsElseCreate(homeTeam)
#
#				for br in game.findall(".//br"): # replaces <br> with \n
#					br.tail = "\n" + br.tail if br.tail else "\n"
#				notes = game.find_class("game-notes")[0].text_content()
#				for line in notes.split("\n"):
#					if line.startswith("AT "): # rudimentary check for ESPN's listing of a neutral site
#						awayTeam.site = "N"
#						homeTeam.site = "N"
#
#				print "------------- " + str(gameID) + " --------------"
#				awayTeam.printSelf()
#				homeTeam.printSelf()
#				print notes
#				print "--------------------------------------"	
#
#				months = {"January":"1", "February":"2", "March":"3", "April":"4", "May":"5", "June":"6", "July":"7", "August":"8", "September":"9", "October":"10", "November":"11", "December":"12"}
#				year = dates[n].text_content().split(" ")[-1]
#				day = dates[n].text_content().split(" ")[-2]
#				month = months[dates[n].text_content().split(" ")[-3]]
#				if len(month) < 2:
#					month = "0" + month
#				if len(day) < 2:
#					day = "0" + day
#				date = year + "-" + month + "-" + day
#				insertGameRow(gameID, date, awayTeam, homeTeam)
#			print ""

for y in range(2015, 2016):
	for w in range(1, 7):
		findGamesForWeek(y, w, 80) # 80 is FBS
		findGamesForWeek(y, w, 81) # 81 is FCS

#cursor.execute("SELECT * from Teams")
#all_teams = cursor.fetchall()
#for team in all_teams:
#	print team[0], team[1]
#print len(all_teams)

db.commit()
