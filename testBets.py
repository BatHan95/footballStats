from sqlalchemy import null
import fotmobData
import rdsConnector
import datetime
import pandas as pd
import tqdm
from itertools import repeat
from concurrent.futures import ProcessPoolExecutor
import math
from calculateAttemptedCrossesToCorners import calculateAttemptedCornersToCrossesMultiplier
import scipy.optimize as optimize


statWeightings = {
    'Corners': {
        'won': 0.4,
        'conceded': 0.4
    },
    'Total shots': {
        'won': 0.35,
        'conceded': 0.3
    },
    'Shots on target': {
        'won': 0.35,
        'conceded': 0.3
    },
    'Accurate crosses': {
        'won': 0.35,
        'conceded': 0.34
    },
    'Blocked shots': {
        'won': 0.4,
        'conceded': 0.35
    }
}

# maxMultiplier = 5.1
# nonTeamWeighted = 0.9

queryTypes = ['home', 'away']

def accurateCrossesToAttemptedCrosses(rawStat):
    accurateCrosses = float(rawStat[0:rawStat.find(' (')])
    crossAccuracy = float(rawStat[rawStat.find(' (')+2:rawStat.find('%)')])/100
    if crossAccuracy == 0:
        attemptedCrosses = 0
    else:
        attemptedCrosses = math.floor(accurateCrosses/crossAccuracy)
    return([accurateCrosses, crossAccuracy, attemptedCrosses])

def newTestAlgorithmStatsExceptCorners(inputRow, teamWeightingsEffect, statName):
    checkResult = []
    matchId = inputRow[1]
    queryResults = []
    checkStats = []
    homeTeam = inputRow[2]
    awayTeam = inputRow[3]
    matchDate = inputRow[4]
    competitionId = inputRow[0]
    statWeightWon = statWeightings[statName]['won']
    statWeightConceded = statWeightings[statName]['conceded']
    outputs = {
        "homeConceded": [],
        "awayWon": [],
        "homeWon": [],
        "awayConceded": []
        }
    homeTeamWeighting = inputRow[5]
    homeTeamName = rdsConnector.selectTeamName(homeTeam)
    awayTeamWeighting = inputRow[6]
    awayTeamName = rdsConnector.selectTeamName(awayTeam)
    for queryType in queryTypes:
        queryResults.append(rdsConnector.rdsSelectStats(inputRow, statName, queryType))
        checkStats.append(rdsConnector.rdsSelectStats(inputRow, statName, queryType))
    queryResults = [item for sublist in queryResults for item in sublist]
    queryResultsDf = pd.DataFrame(queryResults, columns=['matchId', 'matchDate', 'teamName', 'statName', 'stat', 'homeOrAway', 'season', 'type', 'homeTeamWeight', 'awayTeamWeight'])
    for index, row in queryResultsDf.iterrows():
        if row['matchId'] != matchId and row['matchDate'] < matchDate:
            stat = int(row['stat'])*1.0
            statHomeAwayType = row['type'].split('_')[0]
            statWonConcededType = row['type'].split('_')[1]
            if statHomeAwayType == 'home':
                if statWonConcededType == 'won':
                    modifier = (75-(2*math.floor((awayTeamWeighting - 1) / 2)))/(75-(2*math.floor((row['awayTeamWeight'] - 1) / 2)))
                if statWonConcededType == 'conceded':
                    modifier = (75-(2*math.floor((row['awayTeamWeight'] - 1) / 2)))/(75-(2*math.floor((awayTeamWeighting - 1) / 2)))
            if statHomeAwayType == 'away':
                if statWonConcededType == 'won':
                    modifier = (75-(2*math.floor((homeTeamWeighting - 1) / 2)))/(75-(2*math.floor((row['homeTeamWeight'] - 1) / 2)))
                if statWonConcededType == 'conceded':
                    modifier = (75-(2*math.floor((row['homeTeamWeight'] - 1) / 2)))/(75-(2*math.floor((homeTeamWeighting - 1) / 2)))
            newStat = (stat * teamWeightingsEffect[0]) + (stat * modifier * teamWeightingsEffect[1])
            outputs[statHomeAwayType + statWonConcededType.title()].append(newStat)
    # homeConceded = list(filter(lambda conceded: conceded > 0, outputs["homeConceded"]))
    predictedHomeStat = math.floor(((sum(outputs["homeWon"])/len(outputs["homeWon"]) * statWeightWon) + (sum(outputs["awayConceded"])/len(outputs["awayConceded"]) * statWeightConceded)))
    predictedAwayStat = math.floor(((sum(outputs["awayWon"])/len(outputs["awayWon"]) * statWeightWon) + (sum(outputs["homeConceded"])/len(outputs["homeConceded"]) * statWeightConceded)))
    # predictedMaxHomeStat = math.ceil(((max(outputs["homeWon"]) + max(outputs["awayConceded"]) + (sum(outputs["homeWon"])*2/len(outputs["homeWon"])) + (sum(outputs["awayConceded"])*2/len(outputs["awayConceded"])))/maxDivisor))
    # predictedMaxAwayStat = math.ceil(((max(outputs["awayWon"])+ max(outputs["homeConceded"]) + (sum(outputs["awayWon"])*2/len(outputs["awayWon"])) + (sum(outputs["homeConceded"])*2/len(outputs["homeConceded"])))/maxDivisor))
    checkStats = [item for sublist in checkStats for item in sublist]
    checkStatsDf = pd.DataFrame(checkStats, columns=['matchId', 'matchDate', 'teamName', 'statName', 'stat', 'homeOrAway', 'season', 'type', 'homeTeamWeight', 'awayTeamWeight'])
    checkHomeStat = int(checkStatsDf.loc[checkStatsDf['matchId'] == matchId].loc[checkStatsDf['type'] =='home_won']['stat'].values[0])
    checkAwayStat = int(checkStatsDf.loc[checkStatsDf['matchId'] == matchId].loc[checkStatsDf['type'] =='away_won']['stat'].values[0])
        # you changed this, make sure to look at it and finish what you were doing!!
    # Max should be no more than 2x of the actual, now build that into the optimiser somehow
    # and checkAwayStat <= predictedMaxAwayStat and checkHomeStat <= predictedMaxHomeStat
    # and predictedMaxHomeStat/checkHomeStat <= 2 and predictedMaxAwayStat/checkAwayStat <= 2 
    # 
    checkResult.append([matchId, f'{homeTeamName} v {awayTeamName}', statName, checkHomeStat >= predictedHomeStat and checkAwayStat >= predictedAwayStat, predictedHomeStat,
    # predictedMaxHomeStat,
    predictedAwayStat,
    # predictedMaxAwayStat,
    checkHomeStat >= predictedHomeStat 
    # and checkHomeStat <= predictedMaxHomeStat
    , checkAwayStat >= predictedAwayStat 
    # and checkAwayStat <= predictedMaxAwayStat
    ])
    # you changed this, make sure to look at it and finish what you were doing!!
    # Max should be no more than 2x of the actual, now build that into the optimiser somehow
    # 
    return checkResult

def newTestAlgorithmCorners(inputRow, teamWeightingsEffect):
    attemptedCrossesToCornersHome = calculateAttemptedCornersToCrossesMultiplier(inputRow)[0]
    attemptedCrossesToCornersAway = calculateAttemptedCornersToCrossesMultiplier(inputRow)[1]

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
    outputs = {
        "homeConceded": [],
        "awayWon": [],
        "homeWon": [],
        "awayConceded": []
        }
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
        if row['matchId'] != matchId and row['matchDate'] < matchDate:
            stat = accurateCrossesToAttemptedCrosses(row['stat'])[2]
            statHomeAwayType = row['type'].split('_')[0]
            statWonConcededType = row['type'].split('_')[1]
            if statHomeAwayType == 'home':
                if statWonConcededType == 'won':
                    modifier = (75-(2*math.floor((awayTeamWeighting - 1) / 2)))/(75-(2*math.floor((row['awayTeamWeight'] - 1) / 2)))
                if statWonConcededType == 'conceded':
                    modifier = (75-(2*math.floor((row['awayTeamWeight'] - 1) / 2)))/(75-(2*math.floor((awayTeamWeighting - 1) / 2)))
            if statHomeAwayType == 'away':
                if statWonConcededType == 'won':
                    modifier = (75-(2*math.floor((homeTeamWeighting - 1) / 2)))/(75-(2*math.floor((row['homeTeamWeight'] - 1) / 2)))
                if statWonConcededType == 'conceded':
                    modifier = (75-(2*math.floor((row['homeTeamWeight'] - 1) / 2)))/(75-(2*math.floor((homeTeamWeighting - 1) / 2)))
            newStat = (stat * teamWeightingsEffect[0]) + (stat * modifier * teamWeightingsEffect[1])
            outputs[statHomeAwayType + statWonConcededType.title()].append(newStat)
    # homeConceded = list(filter(lambda conceded: conceded > 0, outputs["homeConceded"]))
    predictedHomeStat = math.floor(((sum(outputs["homeWon"])/len(outputs["homeWon"]) * statWeightWon) + (sum(outputs["awayConceded"])/len(outputs["awayConceded"]) * statWeightConceded))* attemptedCrossesToCornersHome)
    predictedAwayStat = math.floor(((sum(outputs["awayWon"])/len(outputs["awayWon"]) * statWeightWon) + (sum(outputs["homeConceded"])/len(outputs["homeConceded"]) * statWeightConceded))* attemptedCrossesToCornersAway)
    # predictedMaxHomeStat = math.ceil(((max(outputs["homeWon"]) + max(outputs["awayConceded"]) + (sum(outputs["homeWon"])*2/len(outputs["homeWon"])) + (sum(outputs["awayConceded"])*2/len(outputs["awayConceded"])))/maxDivisor) * attemptedCrossesToCornersHome)
    # predictedMaxAwayStat = math.ceil(((max(outputs["awayWon"])+ max(outputs["homeConceded"]) + (sum(outputs["awayWon"])*2/len(outputs["awayWon"])) + (sum(outputs["homeConceded"])*2/len(outputs["homeConceded"])))/maxDivisor) * attemptedCrossesToCornersAway)
    checkStats = [item for sublist in checkStats for item in sublist]
    checkStatsDf = pd.DataFrame(checkStats, columns=['matchId', 'matchDate', 'teamName', 'statName', 'stat', 'homeOrAway', 'season', 'type', 'homeTeamWeight', 'awayTeamWeight'])
    checkHomeStat = int(checkStatsDf.loc[checkStatsDf['matchId'] == matchId].loc[checkStatsDf['type'] =='home_won']['stat'].values[0])
    checkAwayStat = int(checkStatsDf.loc[checkStatsDf['matchId'] == matchId].loc[checkStatsDf['type'] =='away_won']['stat'].values[0])
        # you changed this, make sure to look at it and finish what you were doing!!
    # Max should be no more than 2x of the actual, now build that into the optimiser somehow
    # and checkAwayStat <= predictedMaxAwayStat and checkHomeStat <= predictedMaxHomeStat
    # and predictedMaxHomeStat/checkHomeStat <= 2 and predictedMaxAwayStat/checkAwayStat <= 2 
    # 
    checkResult.append([matchId, f'{homeTeamName} v {awayTeamName}', 'Corners', checkHomeStat >= predictedHomeStat and checkAwayStat >= predictedAwayStat, predictedHomeStat,
    # predictedMaxHomeStat,
    predictedAwayStat,
    # predictedMaxAwayStat,
    checkHomeStat >= predictedHomeStat 
    # and checkHomeStat <= predictedMaxHomeStat
    , checkAwayStat >= predictedAwayStat 
    # and checkAwayStat <= predictedMaxAwayStat
    ])
    # you changed this, make sure to look at it and finish what you were doing!!
    # Max should be no more than 2x of the actual, now build that into the optimiser somehow
    # 
    return checkResult


def newCombinedAlgorithm(inputRow, teamWeightingsEffect):
    checkResults = []
    checkResults.append(newTestAlgorithmCorners(inputRow, teamWeightingsEffect))
    checkResults.append(newTestAlgorithmStatsExceptCorners(inputRow, teamWeightingsEffect, 'Total shots'))
    return checkResults


def testBets(nonTeamWeighted, dateFrom, dateTo):
    teamWeightingsEffect = [nonTeamWeighted, 1 - nonTeamWeighted]
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
            with ProcessPoolExecutor(max_workers=24) as executor:
                for r in executor.map(newCombinedAlgorithm, (df), repeat(teamWeightingsEffect, len(df))):
                    checkResults.append(r)
                    pbar.update(1)
        checkResults = [item for sublist in checkResults for item in [item for sub_sublist in sublist for item in sub_sublist]]
        checkResultsDf = pd.DataFrame(checkResults, columns=['matchId', 'match', 'stat', 'overallWin', 'predictedHomeStat',
        # 'predictedMaxHomeStat',
        'predictedAwayStat',
        # 'predictedMaxAwayStat',
        'homeWin', 'awayWin'])
        lostBets = checkResultsDf.loc[checkResultsDf['overallWin'] == False, ['matchId']].drop_duplicates().values.tolist()
        lostBets = [item for sublist in lostBets for item in sublist]
        totallyWonBets = checkResultsDf.loc[~(checkResultsDf['matchId'].isin(lostBets))].reset_index()
        print(checkResultsDf)
        print(f"Would have won {totallyWonBets['matchId'].nunique()} bets out of {totallyWonBets['matchId'].nunique() + len(lostBets)} ({math.ceil(totallyWonBets['matchId'].nunique()/(totallyWonBets['matchId'].nunique() + len(lostBets))*1000.0)/10}%) between {str(dateFrom)} and {str(dateTo)} in {' & '.join(fotmobData.leagueNameList)}")
        return math.ceil(totallyWonBets['matchId'].nunique()/(totallyWonBets['matchId'].nunique() + len(lostBets))*100.0)

testBets(0.9, '2022-12-28', '2022-12-30')

