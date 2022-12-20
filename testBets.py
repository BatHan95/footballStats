from sqlalchemy import null
import fotmobData
import rdsConnector
import datetime
import pandas as pd
import tqdm
from concurrent.futures import ProcessPoolExecutor
import math

statWeightings = {
    'Corners': {
        'won': 0.4,
        'conceded': 0.4
    },
    'Total shots': {
        'won': 0.35,
        'conceded': 0.35
    },
    'Shots on target': {
        'won': 0.4,
        'conceded': 0.35
    },
    'Accurate crosses': {
        'won': 0.456,
        'conceded': 0.31
    },
    'Blocked shots': {
        'won': 0.4,
        'conceded': 0.35
    }
}

attemptedCrossesToCorners = 0.28
maxMutiplier = 2.4
teamWeightingsEffect = [0.65, 0.12]

queryTypes = ['home', 'away']
statTypes = ['Accurate crosses']
queryResults = []

def accurateCrossesToAttemptedCrosses(rawStat):
    accurateCrosses = float(rawStat[0:rawStat.find(' (')])
    crossAccuracy = float(rawStat[rawStat.find(' (')+2:rawStat.find('%)')])/100
    if crossAccuracy == 0:
        attemptedCrosses = 0
    else:
        attemptedCrosses = math.floor(accurateCrosses/crossAccuracy)
    return([accurateCrosses, crossAccuracy, attemptedCrosses])

def newTestAlgorithm(inputRow):
    checkResult = []
    matchId = inputRow[1]
    queryResults = []
    checkStats = []
    homeTeam = inputRow[2]
    awayTeam = inputRow[3]
    matchDate = inputRow[4]
    competitionId = inputRow[0]
    statWeightWon = statWeightings['Accurate crosses']['won']
    statWeightConceded = statWeightings['Accurate crosses']['conceded']
    homeConceded = []
    awayWon = []
    homeWon = []
    awayConceded = []
    homeTeamWeighting = inputRow[5]
    homeTeamName = rdsConnector.selectTeamName(homeTeam)
    awayTeamWeighting = inputRow[6]
    awayTeamName = rdsConnector.selectTeamName(awayTeam)
    for queryType in queryTypes:
        queryResults.append(rdsConnector.rdsSelectStats(inputRow, 'Accurate crosses', queryType))
        checkStats.append(rdsConnector.rdsSelectStats(inputRow, 'Corners', queryType))
    queryResults = [item for sublist in queryResults for item in sublist]
    queryResultsDf = pd.DataFrame(queryResults, columns=['matchId', 'matchDate', 'teamName', 'statName', 'stat', 'homeOrAway', 'season', 'type', 'homeTeamWeight', 'awayTeamWeight'])
    for index, row in queryResultsDf.iterrows():
        if row['matchId'] != matchId:# and row['matchDate'] < matchDate:
            stat = accurateCrossesToAttemptedCrosses(row['stat'])[2]
            statHomeAwayType = row['type'].split('_')[0]
            statWonConcededType = row['type'].split('_')[1]
            if statHomeAwayType == 'home':
                if statWonConcededType == 'won':
                    modifier = awayTeamWeighting/row['awayTeamWeight']
                if statWonConcededType == 'conceded':
                    modifier = row['awayTeamWeight']/awayTeamWeighting
            if statHomeAwayType == 'away':
                if statWonConcededType == 'won':
                    modifier = homeTeamWeighting/row['homeTeamWeight']
                if statWonConcededType == 'conceded':
                    modifier = row['homeTeamWeight']/homeTeamWeighting
            newStat = (stat * teamWeightingsEffect[0]) + (stat * modifier * teamWeightingsEffect[1])
            eval(statHomeAwayType + statWonConcededType.title()).append(newStat)
    homeConceded = list(filter(lambda conceded: conceded > 0, homeConceded))
    predictedHomeStat = math.floor(((sum(homeWon)/len(homeWon) * statWeightWon) + (sum(awayConceded)/len(awayConceded) * statWeightConceded))* attemptedCrossesToCorners)
    predictedAwayStat = math.floor(((sum(awayWon)/len(awayWon) * statWeightWon) + (sum(homeConceded)/len(homeConceded) * statWeightConceded))* attemptedCrossesToCorners)
    predictedMaxHomeStat = math.ceil(((max(homeWon)*maxMutiplier + max(awayConceded)*maxMutiplier + (sum(homeWon)/len(homeWon)) + (sum(awayConceded)/len(awayConceded)))/5) * attemptedCrossesToCorners)
    predictedMaxAwayStat = math.ceil(((max(awayWon)*maxMutiplier + max(homeConceded)*maxMutiplier + (sum(awayWon)/len(awayWon)) + (sum(homeConceded)/len(homeConceded)))/5) * attemptedCrossesToCorners)
    checkStats = [item for sublist in checkStats for item in sublist]
    checkStatsDf = pd.DataFrame(checkStats, columns=['matchId', 'matchDate', 'teamName', 'statName', 'stat', 'homeOrAway', 'season', 'type', 'homeTeamWeight', 'awayTeamWeight'])
    checkHomeStat = int(checkStatsDf.loc[checkStatsDf['matchId'] == matchId].loc[checkStatsDf['type'] =='home_won']['stat'].values[0])
    checkAwayStat = int(checkStatsDf.loc[checkStatsDf['matchId'] == matchId].loc[checkStatsDf['type'] =='away_won']['stat'].values[0])
    checkResult.append([matchId, f'{homeTeamName} v {awayTeamName}', 'Corners', checkHomeStat >= predictedHomeStat and checkAwayStat >= predictedAwayStat and checkAwayStat <= predictedMaxAwayStat and checkHomeStat <= predictedMaxHomeStat, predictedHomeStat, predictedMaxHomeStat, predictedAwayStat, predictedMaxAwayStat, checkHomeStat >= predictedHomeStat and checkHomeStat <= predictedMaxHomeStat, checkAwayStat >= predictedAwayStat and checkAwayStat <= predictedMaxAwayStat])
    return checkResult


def testBets(dateFrom, dateTo):
    datetime.datetime.strptime(dateFrom, '%Y-%m-%d').date()
    datetime.datetime.strptime(dateTo, '%Y-%m-%d').date()
    testMatchesData = []
    for leagueId in fotmobData.leagueIdList:
        testMatchesData.append(rdsConnector.rdsSelectMatches(dateFrom, dateTo, leagueId))

    df = [item for sublist in testMatchesData for item in sublist]
    # df = df.loc[df['matchId'] == 3916094]

    checkResults = []
    if __name__ == '__main__':
        with tqdm.tqdm(total=len(df)) as pbar:
            with ProcessPoolExecutor(max_workers=16) as executor:
                for r in executor.map(newTestAlgorithm, df):
                    checkResults.append(r)
                    pbar.update(1)
        checkResults = [item for sublist in checkResults for item in sublist]
        checkResultsDf = pd.DataFrame(checkResults, columns=['matchId', 'match', 'stat', 'overallWin', 'predictedHomeStat', 'predictedMaxHomeStat', 'predictedAwayStat', 'predictedMaxAwayStat', 'homeWin', 'awayWin'])
        lostBets = checkResultsDf.loc[checkResultsDf['overallWin'] == False, ['matchId']].drop_duplicates().values.tolist()
        lostBets = [item for sublist in lostBets for item in sublist]
        totallyWonBets = checkResultsDf.loc[~(checkResultsDf['matchId'].isin(lostBets))].reset_index()
        # print(checkResultsDf)
        print(f"Would have won {totallyWonBets['matchId'].nunique()} bets out of {totallyWonBets['matchId'].nunique() + len(lostBets)} ({math.ceil(totallyWonBets['matchId'].nunique()/(totallyWonBets['matchId'].nunique() + len(lostBets))*100.0)}%) between {str(dateFrom)} and {str(dateTo)} in {' & '.join(fotmobData.leagueNameList)}")


# testBets('2022-11-10', '2022-12-19')