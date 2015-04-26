import sqlite3
from datetime import datetime

DB_STRING = "matcha.db"

db = sqlite3.connect(DB_STRING)
cursor = db.cursor()
cursor.execute('''CREATE TABLE places (
        Name varchar(30) primary key,
        VisitDate timestamp,
        NumCounters integer,
        IsPooled integer
      );''')
cursor.execute('''CREATE TABLE people(
      ID int primary key,
      TimeArrived timestamp,
      TimeServed timestamp,
      TimeLeft timestamp,
      Queue varchar(1),
      WaitingTime integer,
      ProcessingTime integer,
      Place varchar(30)
    );''')

# add one record to the places table
visit_date = datetime.now()
cursor.execute('''INSERT INTO places(Name, VisitDate, NumCounters, IsPooled)
                  VALUES(?, ?, ?)''', ('matcha', visit_date, 4, 0))

db.commit()

db.close()

