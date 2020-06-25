# © Copyright 2020 HP Development Company, L.P.
# SPDX-License-Identifier: MIT

from my_connect import my_connect
import requests
import psycopg2.sql as sql
import pandas
from datetime import datetime, timedelta
import pytz
import tempfile
import os

connection = my_connect()
cursor = connection.cursor()

TABLE = "nyt_us_covid19"
CSV_TEMP = os.path.join(os.getcwd(), "nyt_latest.csv")


def yesterday():
    tz = pytz.timezone("Etc/UTC")
    todays_date = tz.localize(datetime.today())
    yesterdays_date = todays_date - timedelta(days=1)
    p = "%Y-%m-%d"
    return yesterdays_date.strftime(p)


# Look for any records in the NYT table for yesterday and return True if there there are any
# Note the possibility of incomplete last-day data if the last CSV load only had partial day data in it for yesterday,
# but that does not appear to be the case for this data source.  CSV is updated once/day in whole
def up_to_date():
    q = sql.SQL("SELECT COUNT(*) FROM {} WHERE date = {};")
    cursor.execute(q.format(sql.Identifier(TABLE), sql.Literal(yesterday())))
    result = cursor.fetchone()
    yesterday_row_count = result[0]
    return (yesterday_row_count > 0)


def drop_nyt_table():
    print("Dropping table")
    q = sql.SQL("DROP TABLE IF EXISTS {};")
    cursor.execute(q.format(sql.Identifier(TABLE)))
    connection.commit()


def create_nyt_table():
    print("Creating table")
    q = sql.SQL("""
    CREATE TABLE IF NOT EXISTS {} (
                    id SERIAL PRIMARY KEY,
                    date DATE,
                    county VARCHAR(200),
                    state VARCHAR(100),
                    fips VARCHAR(5),
                    cases INTEGER,
                    deaths INTEGER,
                    iso3166_1 VARCHAR(10),
                    iso3166_2 VARCHAR(10),
                    cases_since_prev_day INTEGER,
                    deaths_since_prev_day INTEGER,
                    last_update_date TIMESTAMP,
                    last_reported_flag BOOLEAN
                   )
    """)
    cursor.execute(q.format(sql.Identifier(TABLE)))
    connection.commit()


def download_nyt_csv():
    print("Downloading CSV file")
    SOURCE = "https://s3-us-west-1.amazonaws.com/starschema.covid/NYT_US_COVID19.csv"
    r = requests.get(SOURCE)
    with open(CSV_TEMP, 'wb') as f:
        f.write(r.content)


def load_nyt_csv():
    print("Loading CSV file")
    connection = my_connect()
    cursor = connection.cursor()

    # Zero out the table first
    q = sql.SQL("DELETE FROM {};")
    cursor.execute(q.format(sql.Identifier(TABLE)))
    connection.commit()

    q2 = sql.SQL("""
    COPY nyt_us_covid19(date, county, state, fips, cases, deaths, iso3166_1, iso3166_2,cases_since_prev_day, 
    deaths_since_prev_day, last_update_date, last_reported_flag) FROM {} CSV HEADER;
    """)

    cursor.execute(q2.format(sql.Literal(CSV_TEMP)))
    connection.commit()
    os.unlink(CSV_TEMP)


def show_sample():
    df = pandas.io.sql.read_sql_query("SELECT * FROM nyt_us_covid19 ORDER BY date DESC LIMIT 5", connection)
    print(df.head())


def update_nyt_if_needed():
    if not up_to_date():
        print("Updating table %s." % TABLE)
        drop_nyt_table()
        create_nyt_table()
        download_nyt_csv()
        load_nyt_csv()
        show_sample()
    else:
        print("Table %s is up to date." % TABLE)


if __name__ == "__main__":
    update_nyt_if_needed()
