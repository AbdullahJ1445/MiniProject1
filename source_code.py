import sqlite3
import time
import hashlib
import getpass
from bdb import effective
from random import randint
#import imp
import re
#from database import connect

#connect to database
connection = None
cursor = None

def connect(path):
    global connection, cursor
    
    connection = sqlite3.connect(path)
    cursor = connection.cursor()
    cursor.execute(' PRAGMA foreign_keys = ON; ')
    connection.commit()
    return

def login():

    '''The first screen of your system should provide options for both 
    users and artists to login. Both class of users should be able to 
    login using a valid id (respectively denoted as uid and aid for users
    and artists) and a password, denoted with pwd.  After a successful
    login, the system should detect whether it is a user or an artist 
    and provide the proper menus as discussed next. If the entered id 
    is a valid id in both users and artists tables, then the user will 
    be asked if they want to login as a user or as an artist.'''

    global connection, cursor, user_id, artist_id

    valid = False
    special_characters = "!@#$%^&*'""()-+?_=,<>/"
    user_type = "" 
    user_id = ""
    artist_id = ""
    pwd = ""
    choices = ""

    while valid == False:
        user_type = input("Enter your user type: (uid for user, aid for artists,reg for registration for user): ")
        user_type = user_type.lower()

        if user_type == "uid" or user_type == "aid":
            user_id = input("Enter your id: ").lower()
            pwd = getpass.getpass("Enter your password: ")

            if any(c in special_characters for c in user_id):
                print("Invalid user id")
                continue

            data = (pwd, user_id)
            cursor.execute("""
            SELECT LOWER(uid) AS a
            FROM users
            WHERE pwd = ? and uid = ? and uid LIKE a;
            """, (pwd, user_id))
            result1 = cursor.fetchone()
            connection.commit()

            cursor.execute("""
            SELECT LOWER(aid) AS a
            FROM artists
            WHERE pwd = ? and aid = ? and aid LIKE a;
            """, (pwd, user_id))
            result2 = cursor.fetchone()
            connection.commit()

            if result1 == None and result2 == None:
                print("Invalid user id or password")
                continue

            elif result1 != None:
                print("Welcome user", user_id)
                valid = True
                return 1

            elif result2 != None:
                print("Welcome artist", user_id)
                valid = True
                return 2

        elif user_type == "reg":
            while valid == False:
                user_id = input("Create your unqiue uid: ")

                if any(c in special_characters for c in user_id):
                    print("Invalid user id")
                    continue

                print(user_id)

                cursor.execute("""
                select LOWER(uid) AS a from users where uid = ? and a LIKE uid;
                """,(user_id,))
                result = cursor.fetchone()
                connection.commit()

                if result:
                    print("This uid is taken, please try another one")
                    continue
                else:
                    valid = True

            pwd = getpass.getpass("Enter your password: ")
            cursor.execute("""
            INSERT INTO users(uid, pwd)
            VALUES(?, ?);
            """, (user_id, pwd))
            connection.commit()
            
            print("Registration successful")
            # login()
            return 1

        else:
            print("Invalid user type")

def logout(choice):
    if choice == "exit":
        print("Thank you for using our system")
        end_session()
        exit()
    elif choice == "logout":
        print("You have logged out")
        login()
        return

def start_session():
    global connection, cursor

    #insert into sessions table
    query = '''
            INSERT INTO sessions(uid, sno, start, end)
            VALUES(?, ?, CURRENT_TIMESTAMP, NULL);
            '''
    #get session number if none then start at 1
    cursor.execute("SELECT MAX(sno) FROM sessions WHERE uid = ?", (user_id,))
    result = cursor.fetchone()
    connection.commit()
    if result[0] == None:
        session_number = 1
    else:
        session_number = result[0] + 1
    #insert into sessions table
    cursor.execute(query, (user_id, session_number))
    connection.commit()
    print("Session started")
    print("Session number:", session_number)

    return

def search_songs_and_playlists():
    global connection, cursor

    keywords = input("Enter keywords: ")
    keywords = keywords.split()
    print("keywords: ", keywords)
    print("Songs and Playlists that match the keywords:")
    print("sid/pid\tTitle\tDuration/Total Duration\tType")
    print("--------------------------------------------------")

    #retrieve songs and playlists that match the keywords
    combined = []
    for keyword in keywords:
        cursor.execute("SELECT sid, title, duration, 'song' FROM songs WHERE title LIKE '%"+keyword+"%'")
        songs = cursor.fetchall()
        cursor.execute("SELECT pid, title, (SELECT SUM(duration) FROM songs WHERE sid IN (SELECT sid FROM plinclude WHERE pid = playlists.pid)) AS total_duration, 'playlist' FROM playlists WHERE title LIKE '%"+keyword+"%'")
        playlists = cursor.fetchall()
        combined += songs
        combined += playlists
    #sort by number of matching keywords
    combined = sorted(combined, key=lambda x: x[1])
    #print top 5 matches
    for row in combined[:5]:
        print(row[0], "\t", row[1], "\t", row[2], "\t", row[3])
    print("--------------------------------------------------")

    #if more than 5 matches, ask user if they want to see more matches or select a match
    if len(combined) > 5:
        print("More than 5 matches.")
        print("Press 1 to select a match for more details.")
        print("Press 2 to see the rest of the matches in a paginated downward format.")
        print("Press 3 to go back to the main menu.")
        user_input = input("Enter your choice: ")
        if user_input == '1':
            choice = input("Enter the id of the match you want to select: ")
            #check if choice is a song or playlist
            if choice in [str(row[0]) for row in combined]:
                #if song
                if choice in [str(row[0]) for row in songs]:
                    print("Selected song: ", choice)
                    song_Actions(choice)
                else:
                    print("Selected playlist: ", choice)
                    print("sid\tTitle\tDuration")
                    print("--------------------------")
                    cursor.execute("SELECT sid, title, duration FROM songs WHERE sid IN (SELECT sid FROM plinclude WHERE pid = "+choice+")")
                    songs = cursor.fetchall()
                    for row in songs:
                        print(row[0], "\t", row[1], "\t", row[2])
                    #song_Actions(input("Enter the id of the song you want to select: "))
            else:
                print("Invalid id.")
        elif user_input == '2':
            print("Rest of the matches:")
            print("sid/pid\tTitle\tDuration/Total Duration\tType")
            print("--------------------------------------------------")
            for row in combined[5:]:
                print(row[0], "\t", row[1], "\t", row[2], "\t", row[3])
            #song_Actions(input("Enter the id of the song you want to select: "))

        elif user_input == '3':
            return

        else:
            print("Invalid choice.")

    song_Actions(input("Select a song to perform an action: "))

    return
   
def search_artists():
    global connection, cursor

    keywords = input("Enter keywords: ")
    keywords = keywords.split()
    print("keywords: ", keywords)

    print("Artists that match the keywords:")
    print("Name\tNationality\tNumber of Songs")
    print("-------------------------------------")

    #retrieve artists that match the keywords
    combined = []
    for keyword in keywords:
        cursor.execute("SELECT name, nationality, COUNT(sid) AS num_songs FROM artists NATURAL JOIN perform NATURAL JOIN songs WHERE name LIKE '%"+keywords[0]+"%' OR title LIKE '%"+keywords[0]+"%' GROUP BY aid")
        artists = cursor.fetchall()
        cursor.execute
        combined += artists
    #sort by number of matching keywords
    combined = sorted(combined, key=lambda x: x[1])
    #print top 5 matches
    for row in combined[:5]:
        print(row[0], "\t", row[1], "\t", row[2])

    print("-------------------------------------")

    #if more than 5 matches, ask user if they want to see more matches or select a match
    if len(artists) > 5:
        print("More than 5 matches.")
        print("Press 1 to select a match.")
        print("Press 2 to see the rest of the matches.")
        print("Press 3 to go back to the main menu.")
        choice = input("Enter your choice: ")
        if choice == "1":
            user_input = input("Enter the name of the artist you want to select: ")
            
            for row in artists:
                #if artist is found
                if row[0] == user_input:
                    print("Artist selected.")
                    print("Artist's name: ", row[0])

                    #list all songs performed by the artist
                    print("Songs performed by the artist:")
                    print("sid\tTitle\tDuration")
                    print("---------------------------")
                    cursor.execute("SELECT sid, title, duration FROM songs WHERE sid IN (SELECT sid FROM perform WHERE aid IN (SELECT aid FROM artists WHERE name = '"+row[0]+"'))")
                    songs = cursor.fetchall()
                    for song in songs:
                        print(song[0], "\t", song[1], "\t", song[2])
                    #select a song to perform a song action
                    print("Select a song to perform a song action.")
                    song_id = input("Enter the sid of the song: ")
                    song_Actions(song_id)

        elif choice == "2":
            print("Artists that match the keywords:")
            print("Name\tNationality\tNumber of Songs")
            print("-------------------------------------")
            for row in artists[5:]:
                print(row[0], "\t", row[1], "\t", row[2])


        elif choice == "3":
            return

    #song_Actions(input("Select a song to perform an action: "))

    return
        
def song_Actions(sid):
    global connection, cursor

    print("Select an action to perform on the song.")
    print("Press 1 to listen to the song.")
    print("Press 2 to see more information about the song.")
    print("Press 3 to add the song to a playlist.")

    #print("user_id: ", user_id)

    user_input = input("Enter your choice: ")
    if user_input == '1':
        #check if user is logged in
        if user_id == None:
            print("You are not logged in.")
            return 
        
        #check if user has a session
        cursor.execute("SELECT sno FROM sessions WHERE uid LIKE ? AND end IS NULL", (user_id,))
        session = cursor.fetchone()
        #if user has a session
        if session != None:
            #check if user has listened to song before
            cursor.execute("SELECT * FROM listen WHERE uid LIKE ? AND sid LIKE ?", (user_id, sid))
            listen = cursor.fetchone()
            #if user has listened to song before
            if listen != None:
                cursor.execute("UPDATE listen SET cnt = cnt + 1 WHERE uid LIKE ? AND sid LIKE ?", (user_id, sid))
                connection.commit()
            #if user has not listened to song before
            else:
                cursor.execute("INSERT INTO listen VALUES (?, ?, ?, ?)", (user_id, session[0], sid, 1))
                connection.commit()

        #if user does not have a session
        else:
            #start a new session
            start_session()
            #get the session number of the new session
            cursor.execute("SELECT sno FROM sessions WHERE uid LIKE ? AND end IS NULL", (user_id,))
            session = cursor.fetchone()
            #insert into listen table
            cursor.execute("INSERT INTO listen VALUES (?, ?, ?, ?)", (user_id, session[0], sid, 1))
            connection.commit()

        #play the song
        print("Playing song...")

    elif user_input == '2':
        cursor.execute("SELECT sid, title, duration FROM songs WHERE sid LIKE ?", (sid,))
        song = cursor.fetchone()
        print("sid\tTitle\tDuration")
        print("-----------------------")
        print(song[0], "\t", song[1], "\t", song[2])

        #get the names of artists who performed the song
        cursor.execute("SELECT name FROM artists WHERE aid IN (SELECT aid FROM perform WHERE sid LIKE ?)", (sid,))
        artists = cursor.fetchall()
        print("Artists who performed the song:")
        for artist in artists:
            print(artist[0])

        #get the names of playlists the song is in(if any)
        cursor.execute("SELECT title FROM playlists WHERE pid IN (SELECT pid FROM plinclude WHERE sid LIKE ?)", (sid,))
        playlists = cursor.fetchall()
        print("Playlists the song is in:")
        for playlist in playlists:
            print(playlist[0])


        

    elif user_input == '3':
        #check if user is logged in
        if user_id == None:
            print("You are not logged in.")
            return

        #get the names of playlists owned by the user
        cursor.execute("SELECT title FROM playlists WHERE uid LIKE ?", (user_id,))
        playlists = cursor.fetchall()
        print("Playlists owned by you:")
        for playlist in playlists:
            print(playlist[0])

        #get the name of the playlist the user wants to add the song to
        playlist_name = input("Enter the name of the playlist you want to add the song to: ")
        #check if playlist exists
        cursor.execute("SELECT * FROM playlists WHERE title LIKE ? AND uid LIKE ?", (playlist_name, user_id))
        playlist = cursor.fetchone()
        #if playlist exists
        if playlist != None:
            #get the number of songs in the playlist
            cursor.execute("SELECT COUNT(*) FROM plinclude WHERE pid LIKE ?", (playlist[0],))
            count = cursor.fetchone()
            #add song to playlist
            cursor.execute("INSERT INTO plinclude VALUES (?, ?, ?)", (playlist[0], sid, count[0]+1))
            connection.commit()
            print("Song added to playlist.")
        #if playlist does not exist
        else:
            #create a new playlist
            x = id_gen(3)
            cursor.execute("INSERT INTO playlists VALUES (?, ?, ?)", (x, playlist_name, user_id))
            connection.commit()
            #add song to playlist
            cursor.execute("INSERT INTO plinclude VALUES (?, ?, ?)", (x, sid, 1))
            connection.commit()
            print("Song added to playlist.")
          
    return

def artist_Action(choice):
    
    global connection, cursor

    if choice == "Add song":
        title = input("Enter the title of the song: ")
        duration = input("Enter the duration of the song: ")
        
        # Check if the song already exists
        cursor.execute("""
            SELECT *
            FROM songs
            WHERE title = ? and duration = ?;
            """, (title, duration))
        connection.commit()
        result = cursor.fetchall()

        if len(result) > 0:
            print("Song already exists")
            return

        else:
            x = id_gen(3)
            print(x)
            x = str(x)
            print(type(x))
            #check if the song id already exists
            cursor.execute("""
                SELECT *
                FROM songs
                WHERE sid = ?;
                """, (x,))
            connection.commit()
            result4 = cursor.fetchall()

            if (len(result4)) > 0:
                print("Sid exists")
                return
        
            # Add the song
            cursor.execute("""
                INSERT INTO songs
                VALUES (?, ?, ?);
                """, (x, title, duration,))
            connection.commit()

            #add any additional artist who may have performed the song with their ids obtained from input.
            print("Enter additional artist ids (enter 0 to stop): ")
            y = input("")
            y = str(y)
            while y != "0":
                #check if the artist id exists
                cursor.execute("""
                    SELECT *
                    FROM artists
                    WHERE aid = ?;
                    """, (y,))
                connection.commit()
                result2 = cursor.fetchall()
                
                if len(result2) > 0:
                    cursor.execute("""
                        INSERT INTO perform
                        VALUES (?, ?);
                        """, (y, x,))
                    connection.commit()
                else:
                    print("Artist id does not exist")
                    return

            return

    elif choice == "Find top":
        aid = input("Enter your artist id: ")

        cursor.execute("""
            SELECT u.uid, u.name
            FROM users AS u, songs AS s, listen AS l, perform AS p
            WHERE u.uid = l.uid and l.sid = s.sid and s.sid = p.sid and p.aid = ?
            Order by l.cnt DESC
            LIMIT 3;
            """, (aid,))
        connection.commit()

        result1 = cursor.fetchall()
        #top 3 playlist that include the largest number of their songs
        cursor.execute("""
                SELECT p.pid, p.title, COUNT(p.pid)
                FROM playlists AS p, songs AS s, perform AS pe, plinclude AS pl
                WHERE p.pid = pl.pid and pl.sid = s.sid and s.sid = pe.sid and pe.aid = ?
                GROUP BY p.pid
                Order by count(s.sid) DESC
                LIMIT 3;
                """, (aid,))
        connection.commit()

        result2 = cursor.fetchall()

        print("Top 3 users who listen to your songs the longest time: ")
        print("User ID\t\tUser Name")
        for row in result1:
            print(row[0], "\t\t", row[1])

        print("Top 3 playlists that include the largest number of your songs: ")
        print("Playlist ID\t\tPlaylist Title\t\tTotal Songs")
        for row in result2:
            print(row[0], "\t\t", row[1], "\t\t", row[2])
        
        return
        
    else:
        print("Invalid choice")
        return

def id_gen(n):
	s = 10**(n-1) 
	e = (10**n)-1                   
	return randint(s,e)         
	
#End the session. The user should be able to end the current session. This should be recorded with the end date/time set to the current date/time. 
def end_session():
    global connection, cursor

    #end the session for the current user 
    cursor.execute("""
        UPDATE sessions
        SET end = CURRENT_TIMESTAMP
        WHERE uid = ? and end is NULL;
        """, (user_id,))
    connection.commit()
    print("Session ended")
    return

#test code
def main():
    global connection, cursor

    #ask user for database name
    db = input("Enter database name: ")

    #connect to database
    connect(db)

    #login

    #if login returns 1, print menu
    if login() == 1:
        print("Menu:")
        print("1. Start a new session")
        print("2. Search for songs and playlists")
        print("3. Search for artists")
        print("4. End a session")
        print("5. Exit")
        print("6. Logout")
        while True:
            choice = input("Select menu option: ")
            if choice == "1":
                start_session()
            elif choice == "2":
                search_songs_and_playlists()
            elif choice == "3":
                search_artists()
            elif choice == "4":
                end_session()
            elif choice == "5":
                logout("exit")
            elif choice == "6":
                logout("logout")
            else:
                print("Invalid choice")

    else:
        print("Menu:")
        print("1. Add a song")
        print("2. Find top fans and playlists")
        print("3. Exit")
        print("4. Logout")
        while True:
            choice = input("Select menu option: ")
            if choice == "1":
                artist_Action("Add song")
            elif choice == "2":
                artist_Action("Find top")
            elif choice == "3":
                logout("exit")
            elif choice == "4":
                logout("logout")
            else:
                print("Invalid choice")
    

    #close connection
    connection.close()

    return

if __name__ == "__main__":
    main()




        

 