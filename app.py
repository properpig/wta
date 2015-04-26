import os, os.path
import random
import string
import sqlite3
import json
import math
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
    def add_place(self, place, num_counters, is_pooled):
        visit_date = datetime.now()
        with sqlite3.connect(DB_STRING) as c:
            cursor = c.cursor();
            cursor.execute("INSERT INTO places (Name, VisitDate, NumCounters, IsPooled) VALUES (?, ?, ?, ?)",
                            [place, visit_date, num_counters, 1 if is_pooled == "true" else 0])
            cursor.close()
            c.commit()
            return json.dumps({'status': 'success'})

    @cherrypy.expose
    def retrieve_queue_info(self, place):
        with sqlite3.connect(DB_STRING) as c:
            cursor = c.cursor();
            cursor.execute("SELECT NumCounters, IsPooled FROM places WHERE Name=?",
                        [place])
            result = cursor.fetchone()
            output = {'place': place, 'num_counters': result[0], 'is_pooled': result[1]}
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
    def process_person(self, person_id, queue_id):
        served_time = datetime.now()

        with sqlite3.connect(DB_STRING) as c:
            cursor = c.cursor();
            cursor.execute("UPDATE people SET TimeServed=?, Queue=? WHERE RowID=?",
                [served_time, queue_id, person_id])
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

    @cherrypy.expose
    def get_analysis(self, place):

        with sqlite3.connect(DB_STRING, detect_types=sqlite3.PARSE_DECLTYPES) as c:
            cursor = c.cursor();

            ## start by getting the interarrival times
            cursor.execute("SELECT RowID, Queue, TimeArrived, TimeServed, TimeLeft, WaitingTime, ProcessingTime FROM people WHERE place=? ORDER BY TimeArrived",
                        [place])
            # store them because we'll be going through the list again later
            people_list = []
            row = cursor.fetchone()
            people_list.append(row)

            prev_time_arrived = row[2] #initialise first value
            print(prev_time_arrived)
            all_rows = cursor.fetchall()

            output = {}
            interarrival_times = []
            corresponding_queues = [] # stores the list of queue ids that the people arrived at

            for row in all_rows:
                interarrival_time = (row[2] - prev_time_arrived).total_seconds()
                interarrival_times.append(interarrival_time)
                corresponding_queues.append(row[1].encode('ascii','ignore'))

                #update the previous time arrived
                prev_time_arrived = row[2]
                people_list.append(row)

            output['interarrival'] = getSeriesAndLabelsScatter(interarrival_times, corresponding_queues)

            ## compute the waiting time and processing time for each person
            # and store the times
            waiting_times = []
            processing_times = []
            corresponding_queues = []

            for person in people_list:
                # RowID, Queue, TimeArrived, TimeServed, TimeLeft, WaitingTime, ProcessingTime

                # we only want to analyse the people that have been served
                # or those who left
                if not person[3] or not person[4] or person[5] == -1:
                    continue # skip

                if not person[5]: # means WaitingTime hasnt been computed before
                    waiting_time = (person[3] - person[2]).total_seconds()
                    processing_time = (person[4] - person[3]).total_seconds()
                else:
                    waiting_time = person[5]
                    processing_time = person[6]

                waiting_times.append(waiting_time)
                processing_times.append(processing_time)
                corresponding_queues.append(person[1].encode('ascii','ignore'))

                # update the row in the database
                cursor.execute("UPDATE people SET WaitingTime=?, ProcessingTime=? WHERE RowID=?",
                    [waiting_time, processing_time, person[0]])

            output['waiting'] = getSeriesAndLabelsScatter(waiting_times, corresponding_queues)
            output['processing'] = getSeriesAndLabelsHistogram(processing_times, corresponding_queues)

            cursor.close()
            c.commit()
            return json.dumps(output)

def getSeriesAndLabelsScatter(list_of_times, corresponding_queues):
    time_range = max(list_of_times)
    # divide this up into 100 - this will be our precision on the chart
    precision = 100
    time_slice = math.ceil(time_range / precision)

    # get the list of unique queue ids. we'll have to create one series for each
    unique_queue_ids = list(set(corresponding_queues))
    unique_queue_ids.sort()
    series_dict = {}
    for queue_id in unique_queue_ids:
        series_dict[queue_id] = []
        # initialise the null values. this will later hold our y-values
        for i in range(0, precision):
            series_dict[queue_id].append(None)

    # initialise a list to store the x-labels of our chart
    labels = []
    for i in range(0, precision):
        labels.append(int(time_slice * i))

    # then we store the y-values at the appropriate 'slot'
    num_points = len(list_of_times)
    list_of_times.sort()
    for i in range(0, num_points):
        interarrival_time = list_of_times[i]
        queue_id = corresponding_queues[i]
        bin = int(math.floor(interarrival_time / time_slice))
        series_dict[queue_id][bin] = round(i / float(num_points), 3)

    # convert the series dict back to a list (required by chartist)
    series = []
    for key in series_dict:
        series.append(series_dict[key])

    return {'series': series, 'labels': labels}

def getSeriesAndLabelsHistogram(list_of_times, corresponding_queues):
    time_range = max(list_of_times)
    number_of_bars = 10 # the number of bars we want to have on the histogram
    time_slice = math.ceil(time_range / number_of_bars)

    # get the list of unique queue ids. we'll have to create one series for each
    unique_queue_ids = list(set(corresponding_queues))
    unique_queue_ids.sort()
    series_dict = {}
    for queue_id in unique_queue_ids:
        series_dict[queue_id] = []
        # initialise the null values. this will later hold our y-values
        for i in range(0, number_of_bars):
            series_dict[queue_id].append(0)

    # initialise a list to store the x-labels of our chart
    labels = []
    for i in range(0, number_of_bars):
        labels.append(int(time_slice * i))

    # then we store the y-values at the appropriate 'slot'
    num_points = len(list_of_times)
    for i in range(0, num_points):
        interarrival_time = list_of_times[i]
        queue_id = corresponding_queues[i]
        bin = int(math.floor(interarrival_time / time_slice))
        series_dict[queue_id][bin] += 1

    # convert the series dict back to a list (required by chartist)
    series = []
    for key in series_dict:
        series.append(series_dict[key])

    return {'series': series, 'labels': labels}

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