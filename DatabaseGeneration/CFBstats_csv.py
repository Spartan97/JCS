import pymysql # sql queries

db = pymysql.connect(host="localhost", user="root", db="JCS")
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

def getGameStats(line):
	awayTeam = Team()
	homeTeam = Team()

	stats = line.split(",")

	# create the two teams, then assign them to home and away at the end
	Team1 = Team()
	Team2 = Team()

	Team1.name = stats[1]
	Team2.name = stats[10]	

	Team1.score = stats[2]
	Team2.score = stats[11]

	Team1.rushAtt = stats[3]
	Team2.rushAtt = stats[12]

	Team1.rushYds = stats[4]
	Team2.rushYds = stats[13]

	Team1.passAtt = stats[5]
	Team2.passAtt = stats[14]

	Team1.passComp = stats[6]
	Team2.passComp = stats[15]

	Team1.passYds = stats[7]
	Team2.passYds = stats[16]

	Team1.ints = stats[8]
	Team2.ints = stats[17]

	Team1.fumbs = stats[9]
	Team2.fumbs = stats[18]

	homeTeam = Team1
	awayTeam = Team2
	isNeutral = True
	bettingLine = 0
	# default assignments

	if len(stats) == 21: # later years have site and line (2000-2001 don't)
		bettingLine = -1*stats[20] # lines appear to be backwards...
		if stats[19]== "V":
			homeTeam = Team2
			awayTeam = Team1
			bettingLine *= -1
			isNeutral = False
		elif stats[19] == "H":
			isNeutral = False

	return isNeutral, awayTeam, homeTeam, bettingLine

foundTeams = []
notFoundTeams = []
def verifyTeamExistsElseCreate(team): # This method needs to reconcile CSV team names with ESPN names and give the appropriate ID
	cursor.execute("SELECT * from Teams where name='" + str(team.name) + "'")
	teams = cursor.fetchall()
	assert (len(teams) < 2), "Error: More than one team matches id " + str(team.id)
	if len(teams) == 1:
		if team.name not in foundTeams:
			foundTeams.append(team.name)
	else:
		if team.name not in notFoundTeams:
			notFoundTeams.append(team.name)
#	if len(teams) == 0:
#		team.name = team.name.replace("'", "''")
#		cursor.execute("INSERT into Teams values (" + str(team.id) + ", '" + team.name + "')")

def insertGameRow(id, date, awayTeam, homeTeam, bettingLine):
	cursor.execute("SELECT * from Games where id=" + str(id))
	games = cursor.fetchall()
	if len(games) > 0:
		return # game has already been handled (appears in both FBS and FCS list)

	site = 0
	if awayTeam.site == "N":
		site = 1
	if bettingLine == "":
		bettingLine = 0

	print "Inserting game", id

	cursor.execute("INSERT into Games values (" + str(id) + ", " + str(site) + ", '" + date + "', " + \
	str(awayTeam.id) + ", " + str(awayTeam.score) + ", " + str(awayTeam.passYds) + ", " + str(awayTeam.passAtt) + ", " + \
	str(awayTeam.passComp) + ", " + str(awayTeam.rushYds) + ", " + str(awayTeam.rushAtt) + ", " + str(awayTeam.ints) + ", " + \
	str(awayTeam.fumbs) + ", " + str(homeTeam.id) + ", " + str(homeTeam.score) + ", " + str(homeTeam.passYds) + ", " + \
	str(homeTeam.passAtt) + ", " + str(homeTeam.passComp) + ", " + str(homeTeam.rushYds) + ", " + str(homeTeam.rushAtt) + ", " + \
	str(homeTeam.ints) + ", " + str(homeTeam.fumbs) + ", " + str(bettingLine) + ")")

for year in range(2000, 2014): # 2000-2013
	statsfile = open("stats00-13/cfb" + str(year) + "stats.csv")

	this_day = ""
	teams_this_day = []

	firstline = False
	for line in statsfile:
		if not firstline:
			firstline = True
			continue
		date = line.strip().split(",")[0].split("/")
		if len(date[2]) != 4:
			date[2] = "20" + date[2]
		date = date[2] + "-" + date[0] + "-" + date[1]
		if this_day != date:
			this_day = date
			teams_this_day = []			

		if line.strip().split(",")[1] in teams_this_day:
			assert line.strip().split(",")[10] in teams_this_day, "ERROR: Mismatched teams on " + date + " for " + line.strip().split(",")[10]
		elif len(line.strip().split(",")[4]) == 0:
			print "Stats not found for", line.strip().split(",")[1], "vs", line.strip().split(",")[10], "on", line.strip().split(",")[0]
			continue
		else:
			teams_this_day.append(line.strip().split(",")[1])
			teams_this_day.append(line.strip().split(",")[10])

		isNeutral, awayTeam, homeTeam, bettingLine = getGameStats(line.strip())

		verifyTeamExistsElseCreate(awayTeam)
		verifyTeamExistsElseCreate(homeTeam)


		cursor.execute("SELECT id from Teams where name='" + str(awayTeam.name) + "'")
		id = cursor.fetchall()
		awayTeam.id = int(id[0][0])
		cursor.execute("SELECT id from Teams where name='" + str(homeTeam.name) + "'")
		id = cursor.fetchall()
		homeTeam.id = int(id[0][0])

		id = str(date.split("-")[0]) + str(date.split("-")[1]) + str(date.split("-")[2]) + str(awayTeam.id).zfill(4) + str(homeTeam.id).zfill(4)

		insertGameRow(id, date, awayTeam, homeTeam, bettingLine)

for team in notFoundTeams:
	print team

db.commit()
