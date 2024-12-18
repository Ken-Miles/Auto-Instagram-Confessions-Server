import random
import string
import textwrap

from PIL import Image, ImageDraw, ImageFont
from instagrapi import Client
from instagrapi.types import Usertag
import pandas as pd
import psycopg2

from config import password, sheet_url, username
from flask import (
	Flask,
	jsonify,
	request,
)

# encode to pass the string in database
def encodeString(str):
	ret = ""
	for i in range(0, len(str)):
		if(str[i] == '\''):
			ret += '\''
		ret += str[i]
	return ret

# decode String to readable format
def decodeString(str):
	return str

# postgresql database connect
connection = psycopg2.connect(
	host = "localhost",
	database = "autopost",
	user = "postgres",
	password = "postgres",
	port = 5432
)

connection.autocommit = True

cursor = connection.cursor()

# Initiate app
app = Flask(__name__)

#instagram login
# If instaCache.json is not already present, create an empty instaCache.json file and dump the configs
# Otherwise, load the config settings from instaCache.json file
bot = Client()
instaCache = open('instaCache.json', 'r')
if(instaCache.read() == ''):
	bot.login(username, password)
	bot.dump_settings('instaCache.json')
else:
	bot.load_settings('instaCache.json')
	bot.login(username, password)
	

# font, size and colour
fontSize = 30
myFont = ImageFont.truetype('OpenSans-SemiBold.ttf', fontSize, encoding='unic')
# myFont = ImageFont.truetype('OpenSansEmoji.ttf', fontSize, encoding='unic')
bodyColor = (255, 0, 0)
headingColor = (0, 0, 255)
instaHandleCorner = (250, 1030)

# Verifying the session id
def verifySid(sessionId):
	cursor.execute("""SELECT session_id from sessions;""")
	sessionsList = cursor.fetchall()
	if(sessionId in sessionsList):
		return True
	else:
		return False

#create post and post it on instagram
def createPost(id):
	print(id)
	cursor.execute("SELECT entry FROM entries WHERE id = $1;", (id,))
	l = cursor.fetchall()
	print(type(l))
	print(len(l))
	print(l)
	if(len(l) != 1):
		return "Something went wrong in createPost1"
	text = decodeString(l[0][0])
	paragraphs = text.splitlines()
	Lines = [textwrap.wrap(j, 50) for j in paragraphs]
	lines = []
	lines.append('#'+str(id))
	lines.append('')
	lines.append('')
	for l in Lines:
		if(len(l) == 0):
			lines.append('')
		else:
			lines.extend(l)
	while(lines[len(lines)-1] == ''):
		lines = lines[:-1]

	print(lines)
	#template open
	img = Image.open('template.jpg')
	I1 = ImageDraw.Draw(img)
	I1.text(instaHandleCorner, username, font=myFont, fill=(0, 0, 0))
	w,h = img.size


	#single photo post
	if(len(lines) <= 20):
		currHeight = 100+20*(20-len(lines))
		for line in lines:
			if(line == ''):
				currHeight += 30
				continue
			width,height = myFont.getsize(line)
			print(line)
			I1.text((200, currHeight+height), line, font=myFont, fill=bodyColor)
			currHeight += height
		filename="posts/"+id+".jpg" 
		img.save(filename)
		print(text)
		bot.photo_upload(path=filename,
			caption='#'+str(id)+"\n"+text
			# ,usertags=[Usertag(user=bot.user_info_by_username(username), x=1, y=1)]
			)


#	 #multiple_pages album post
	elif(len(lines) > 20):
		swipePhoto = Image.open('swipe.png').convert("RGBA")
		totalPages = 1+(len(lines)-1)/20
		subCount = 1
		photos = []
		while(len(lines) > 20):
			currHeight = 100
			for j in range(0, 20):
				line = lines[j]
				if(line == ''):
					currHeight += 30
					continue
				width,height = myFont.getsize(line)
				I1.text((200, currHeight+height), line, font=myFont, fill=bodyColor)
				currHeight += height
			filename="posts/"+id+"-"+str(subCount)+".jpg" 
			photos.append(filename)
			img.paste(swipePhoto, (900, 900), swipePhoto)
			img.save(filename)
			img = Image.open('template.jpg')
			I1 = ImageDraw.Draw(img)
			I1.text(instaHandleCorner, username, font=myFont, fill=(0, 0, 0))
			subCount+=1
			lines = lines[20:]

		#last page
		currHeight = 100+20*(20-len(lines))
		for line in lines:
			if(line == ''):
				currHeight += 30
				continue
			width,height = myFont.getsize(line)
			I1.text((200, currHeight+height), line, font=myFont, fill=bodyColor)
			currHeight += height
		filename="posts/"+id+"-"+str(subCount)+".jpg" 
		photos.append(filename)
		img.save(filename)
		
		#upload album post
		bot.album_upload(paths=photos, 
			 caption='#'+str(id)+"\n"+text
			 ,usertags=[Usertag(user=bot.user_info_by_username(username), x=1, y=1)]
			 )

def insertQueue():
	print("calling insertQueue")
	url_1 = sheet_url.replace('/edit', '/export?format=csv&')
	p = pd.read_csv(url_1, usecols= ['Submit your ticket'])
	Entries = [i[0] for i in p.values]
	cursor.execute("SELECT MAX(id) from accepted;")
	idList = cursor.fetchall()
	id1 = 0
	if(len(idList) == 1):
		if(idList[0][0] is None):
			id1 = 0
		else:
			id1 = int(idList[0][0])

	cursor.execute("SELECT MAX(id) from declined;")
	idList = cursor.fetchall()
	id2 = 0
	if(len(idList) == 1):
		if(idList[0][0] is None):
			id2 = 0
		else:
			id2 = int(idList[0][0])

	cursor.execute("SELECT MAX(id) from skipped;")
	idList = cursor.fetchall()
	id3 = 0
	if(len(idList) == 1):
		if(idList[0][0] is None):
			id3 = 0
		else:
			id3 = int(idList[0][0])
	print("DONE ")
	maxId = max(id1, max(id2, id3))
	queue = []

	for i in range(maxId, len(Entries)):
		queue.append(Entries[i]);
	print("queue is : ")
	print(queue)
	for s in queue:
		st = encodeString(s)
		print(st)
		cursor.execute("INSERT INTO entries (entry) VALUES ($1);", (st,))
	# cursor.commit()

def createSessionId():
	cursor.execute("SELECT session_id from sessions")
	sessionsList = cursor.fetchall()
	sessionsList = [a[0] for a in sessionsList]
	while (True):
		sessionId = ''.join(random.choices(string.ascii_uppercase +
							string.digits, k = 26))
		if sessionId in sessionsList:
			continue
		return sessionId

@app.route('/login', methods=['GET', 'POST'])
def login():
	if(request.method == request.method):
		username = request.args.get('username')
		print(username)
		cursor.execute("SELECT password from accounts WHERE accounts.username = $1;", (username,))
		passList = cursor.fetchall()
		print(passList)
		if len(passList) != 1:
			return "0"
		else:
			if(passList[0][0] == request.args.get('password')):
				sessionId = createSessionId()
				cursor.execute("INSERT INTO sessions (session_id, username, login_time) VALUES ($1, $2, current_timestamp);", (sessionId, username))
				return sessionId
		return "0"
	return "0"

# receive a new entry from database
@app.route('/getEntry', methods=['GET', 'POST'])
def getEntry():
	if(request.method=='GET'):
		print("Get request in getEntry received")
		entries = []
		cursor.execute("SELECT MAX(id) from accepted;")
		idList = cursor.fetchall()
		id1 = 0
		if(len(idList) == 1):
			if(idList[0][0] is None):
				id1 = 0
			else:
				id1 = int(idList[0][0])

		cursor.execute("SELECT MAX(id) from declined;")
		idList = cursor.fetchall()
		id2 = 0
		if(len(idList) == 1):
			if(idList[0][0] is None):
				id2 = 0
			else:
				id2 = int(idList[0][0])

		cursor.execute("SELECT MAX(id) from skipped;")
		idList = cursor.fetchall()
		id3 = 0
		if(len(idList) == 1):
			if(idList[0][0] is None):
				id3 = 0
			else:
				id3 = int(idList[0][0])
		print("DONE ")
		maxId = max(id1, max(id2, id3))
		cursor.execute("SELECT id, entry from entries WHERE id > $1 ORDER BY id limit 1;", (maxId,))
		entries = cursor.fetchall()
		print(entries)
		if(len(entries) != 1):
			insertQueue()
			cursor.execute("SELECT id, entry from entries WHERE id > $1 ORDER BY id limit 1;", (maxId,))
			entries = cursor.fetchall()

		if(len(entries) != 1):
			return jsonify({
				"id" : "-1",
				"text" : "No new Entries! Please come back later",
				})
		return jsonify({
				 "id" : str(entries[0][0]),
				 "text" : decodeString(entries[0][1]),
				 })
	elif(request.method == 'POST'):
		print("post request in getEntry received")
		id = request.args.get('id')
		print(id)
		print(type(id))

		if(request.args.get('status') == 'approve'):
			print("approval")
			cursor.execute("INSERT INTO accepted (id) VALUES ($1);",(id,))
			createPost(id)
			return "Posted on Instagram"
		elif(request.args.get('status') == 'decline'):
			cursor.execute("INSERT INTO declined (id) VALUES ($1);",(id,))
			return "Declined"
		elif(request.args.get('status') == 'skip'):
			cursor.execute("INSERT INTO skipped (id) VALUES ($1);",(id,))
			return "Skipped"
		else:
			return "Something went wrong in getEntry POST"
	else:
		return "Invalid request type in getEntry"

# receive entries which were skipped earlier
@app.route('/getEntrySkipped', methods=['GET', 'POST'])
def getEntrySkipped():
	if(request.method=='GET'):
		print("Get request in getEntrySkipped received")
		entries = []
		cursor.execute("SELECT id from skipped limit 1;")
		entries = cursor.fetchall()

		if(len(entries) != 1):
			return jsonify({
				"id" : "-1",
				"text" : "No new Entries! Please come back later",
				})
		id = entries[0][0]
		cursor.execute("SELECT id, entry from entries WHERE id = $1;", (id,))
		entries = cursor.fetchall()
		return jsonify({
				 "id" : str(entries[0][0]),
				 "text" : decodeString(entries[0][1]),
				 })
	else:
		print("post request in getEntrySkipped received")
		id = request.args.get('id')
		print(id)
		print(type(id))

		cursor.execute("DELETE FROM skipped WHERE id = $1;", (id,))
		if(request.args.get('status') == 'approve'):
			cursor.execute("INSERT INTO accepted (id) VALUES ($1);", (id,))
			print(createPost(id))
			return "Posted on Instagram"
		elif(request.args.get('status') == 'decline'):
			cursor.execute("INSERT INTO declined (id) VALUES ($1);", (id,))
			return "Declined"
		elif(request.args.get('status') == 'skip'):
			cursor.execute("INSERT INTO skipped (id) VALUES ($1);",(id,))
			return "Skipped"
		else:
			return "Something went wrong in getEntrySkipped POST"

# Sample api for testing
@app.route('/', methods=['GET', 'POST'])
def index():
	return "Hello World"

# API to verify the session id everytime the user opens the app
@app.route('/verify', methods=['GET', 'POST'])
def verifySessionId():
	cursor.execute("SELECT session_id from sessions;")
	sessionsList = cursor.fetchall()
	sessionId = request.args.get('session_id')
	print(sessionsList)
	sessionsList = [a[0] for a in sessionsList]
	if(sessionId in sessionsList):
		cursor.execute("UPDATE sessions SET login_time = current_timestamp WHERE session_id = $1;", (sessionId,))
		return "1"
	else:
		return "0"

# API for logging out the account of auto instagram confessions app session
@app.route('/logout', methods=['GET', 'POST'])
def logout():
	sid = request.args.get('session_id')
	print("logging out ")
	print(sid)
	cursor.execute("DELETE FROM sessions where session_id = $1;", (sid,))
	# connection.commit()
	return "1"

# This initiates the server
if __name__ == "__main__":
	app.run(port=5000, debug=True)
