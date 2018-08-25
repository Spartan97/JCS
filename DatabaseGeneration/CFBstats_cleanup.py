import MySQLdb

# connects to my JCS DB with my super secure username and password
db = MySQLdb.connect(host="localhost", user="root", passwd="12345", db="JCS")
cursor = db.cursor()

cursor.execute("Select * from Games")

handled = []

games = cursor.fetchall()
for game in games:
	if (game[1], game[14], game[2]) in handled:
		continue
	cursor.execute("select * from Games where date='" + str(game[1]) + "' and homeTeamID=" + str(game[2]) + " and awayTeamID=" + str(game[14]))
	dupes = cursor.fetchall()
	if len(dupes) > 0:
		cursor.execute("select name from Teams where id=" + str(game[2]))
		name1 = cursor.fetchall()[0][0]
		cursor.execute("select name from Teams where id=" + str(game[14]))
		name2 = cursor.fetchall()[0][0]
#		print game[1], name1, name2

		if dupes[0][13] == None and game[13] == None:
			print "Both games are bad for " + name1 + "-" + name2 + " on " + str(game[1])
		elif dupes[0][13] == None:
			pass # remove this game
		elif game[13] == None:
			pass # remove this game

	handled.append((game[1], game[2], game[14]))

