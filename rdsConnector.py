import psycopg2
import json
import pandas as pd
import postgresQueries

config = json.loads(open('config.json', 'r').read())

def rdsConnection():
    try:
        conn = psycopg2.connect(host=config["main_rds_host"], port=config["main_rds_port"], database=config["main_rds_stats_db_name"], user=config["main_rds_username"], password=config["main_rds_password"], sslrootcert="SSLCERTIFICATE")
        cur = conn.cursor()
        # print('RDS connection established')
    except Exception as e:
        print("Database connection failed due to {}".format(e)) 
    return cur, conn

def rdsInsert(df, type):
    cur, conn = rdsConnection()
    print(f'Inserting {len(df)} {type}')
    for line_number, (index, row) in enumerate(df.iterrows()):
        query = postgresQueries.generateInsertQuery(type, row)
        print(f'Inserting/Updating {type} {line_number+1} of {len(df)} - {round(100*(line_number + 1)/len(df),1)}% complete')
        cur.execute(query)
        conn.commit()
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