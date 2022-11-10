import psycopg2
import json
import postgresQueries

ENDPOINT="database-1.cn2p5chwsam4.eu-west-2.rds.amazonaws.com"
PORT="5432"
USER="postgres"
REGION="eu-west-2c"
DBNAME="footballStats"
PASSWORD = json.loads(open('.env', 'r').read())['RDS_PASSWORD']

def rdsConnection():
    try:
        conn = psycopg2.connect(host=ENDPOINT, port=PORT, database=DBNAME, user=USER, password=PASSWORD, sslrootcert="SSLCERTIFICATE")
        cur = conn.cursor()
    except Exception as e:
        print("Database connection failed due to {}".format(e)) 
    # print('RDS connection established')
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

def rdsSelect(row, stats):
    queryResults = []
    cur, conn = rdsConnection()
    selectQuery = postgresQueries.generateHomeSelectQuery(row, stats)
    cur.execute(selectQuery)
    queryResult = cur.fetchall()
    queryResults.append(queryResult)

    selectQuery = postgresQueries.generateAwaySelectQuery(row, stats)
    cur.execute(selectQuery)
    queryResult = cur.fetchall()
    queryResults.append(queryResult)

    queryResults = [item for sublist in queryResults for item in sublist]
    cur.close()
    conn.close()
    return(queryResults)
