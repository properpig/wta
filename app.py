import os, os.path
import random
import string
import sqlite3
import json
from datetime import datetime

import cherrypy

DB_STRING = "matcha.db"

class StringGenerator(object):
    @cherrypy.expose
    def index(self):
        return "Hello world!"

    @cherrypy.expose
    def retrieve_places(self):
        with sqlite3.connect(DB_STRING) as c:
            cursor = c.cursor();
            cursor.execute("SELECT Name FROM places")
            result = cursor.fetchall()
            output = []
            for row in result:
                output.append(row[0])
            cursor.close()
            c.commit()
            return json.dumps(output)

    @cherrypy.expose
    def add_place(self, place, num_counters):
        visit_date = datetime.now()
        with sqlite3.connect(DB_STRING) as c:
            cursor = c.cursor();
            cursor.execute("INSERT INTO places (Name, VisitDate, NumCounters) VALUES (?, ?, ?)",
                            [place, visit_date, num_counters])
            cursor.close()
            c.commit()
            return json.dumps({'status': 'success'})

    @cherrypy.expose
    def retrieve_queue_info(self, place):
        with sqlite3.connect(DB_STRING) as c:
            cursor = c.cursor();
            cursor.execute("SELECT NumCounters FROM places WHERE Name=?",
                        [place])
            result = cursor.fetchone()
            output = {'place': place, 'num_counters': result[0]}
            cursor.close()
            c.commit()
            return json.dumps(output)

    @cherrypy.expose
    def retrieve_queues(self, place):

        with sqlite3.connect(DB_STRING) as c:
            cursor = c.cursor();
            cursor.execute("SELECT RowID, Queue, TimeServed FROM people WHERE place=? AND TimeLeft IS NULL ORDER BY TimeArrived",
                        [place])
            all_rows = cursor.fetchall()

            # save all the information in this variable
            output = []
            for row in all_rows:
                is_being_served = row[2] is not None
                output.append({'person_id': row[0], 'queue': row[1], 'is_being_served': is_being_served})

            cursor.close()
            c.commit()
            return json.dumps(output)

    @cherrypy.expose
    def add_person(self, queue_id, place):
        arrival_time = datetime.now()

        with sqlite3.connect(DB_STRING) as c:
            cursor = c.cursor();
            cursor.execute("INSERT INTO people (Queue, Place, TimeArrived) VALUES (?, ?, ?)",
                        [queue_id, place, arrival_time])
            message = json.dumps({"pid": cursor.lastrowid})
            cursor.close()
            c.commit()
            return message

    @cherrypy.expose
    def process_person(self, person_id):
        served_time = datetime.now()

        with sqlite3.connect(DB_STRING) as c:
            cursor = c.cursor();
            cursor.execute("UPDATE people SET TimeServed=? WHERE RowID=?",
                [served_time, person_id])
            cursor.close()
            c.commit()
            return json.dumps({"status": "success"})

    @cherrypy.expose
    def process_complete(self, person_id):
        left_time = datetime.now()

        with sqlite3.connect(DB_STRING) as c:
            cursor = c.cursor();
            cursor.execute("UPDATE people SET TimeLeft=? WHERE RowID=?",
                [left_time, person_id])
            cursor.close()
            c.commit()
            return json.dumps({"status": "success"})

    @cherrypy.expose
    def delete_person(self, person_id):
        left_time = datetime.now() # we'll just record the time they left for fun

        with sqlite3.connect(DB_STRING) as c:
            cursor = c.cursor();
            cursor.execute("UPDATE people SET WaitingTime=?, TimeLeft=? WHERE RowID=?",
                [-1, left_time, person_id])
            cursor.close()
            c.commit()
            return json.dumps({"status": "success"})

def CORS():
    cherrypy.response.headers["Access-Control-Allow-Origin"] = "*"

if __name__ == '__main__':
    conf = {
        '/': {
            'tools.sessions.on': True,
            'tools.response_headers.on': True,
            'tools.response_headers.headers': [('Content-Type', 'application/json')],
            'tools.CORS.on': True,
            'tools.staticdir.root': os.path.abspath(os.getcwd())
        },
        '/static': {
            'tools.staticdir.on': True,
            'tools.staticdir.dir': './dist'
        }
    }

    cherrypy.server.socket_host = '0.0.0.0'
    cherrypy.tools.CORS = cherrypy.Tool('before_handler', CORS)
    cherrypy.quickstart(StringGenerator(), '/', conf)