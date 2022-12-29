import psycopg2
import json
import pandas as pd
import postgresQueries
import tqdm
from itertools import repeat
from concurrent.futures import ProcessPoolExecutor

config = json.loads(open('config.json', 'r').read())

def rdsConnection():
    try:
        conn = psycopg2.connect(host=config["main_rds_host"], port=config["main_rds_port"], database=config["main_rds_stats_db_name"], user=config["main_rds_username"], password=config["main_rds_password"], sslrootcert="SSLCERTIFICATE")
        cur = conn.cursor()
        # print('RDS connection established')
    except Exception as e:
        print("Database connection failed due to {}".format(e)) 
    return cur, conn

def rdsInsert(insertList, type):
    cur, conn = rdsConnection()
    with tqdm.tqdm(total=len(insertList)) as pbar:
        pbar.set_description(f"Inserting/Updating {len(insertList)} {type}", refresh=False)
        with ProcessPoolExecutor(max_workers=24) as executor:
            for r in executor.map(postgresQueries.generateInsertQuery, (insertList), repeat(type, len(insertList))):
                cur.execute(r)
                conn.commit()
                pbar.update(1)
    cur.close()
    conn.close()
    print(f'Inserted/Updated all {type}')

def rdsSelectStats(row, stat, queryType):
    cur, conn = rdsConnection()
    selectQuery = postgresQueries.generateStatQuery(row, stat, queryType)
    cur.execute(selectQuery)
    queryResults = cur.fetchall()
    cur.close()
    conn.close()
    return queryResults

def rdsSelectMatches(startDate, endDate, competitionId):
    cur, conn = rdsConnection()
    selectQuery = postgresQueries.generateSelectMatchesQuery(startDate, endDate, competitionId)
    cur.execute(selectQuery)
    queryResults = cur.fetchall()
    cur.close()
    conn.close()
    return queryResults

def selectTeamName(teamId):
    cur, conn = rdsConnection()
    selectQuery = postgresQueries.generateSelectTeamNameQuery(teamId)
    cur.execute(selectQuery)
    queryResults = cur.fetchone()
    cur.close()
    conn.close()
    results = pd.DataFrame(queryResults, columns=['teamName'])
    return results['teamName'][0]