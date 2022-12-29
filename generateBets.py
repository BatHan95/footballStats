import rdsConnector
import math
import pandas as pd
from calculateAttemptedCrossesToCorners import calculateAttemptedCornersToCrossesMultiplier


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


nonTeamWeighted = 0.9

teamWeightingsEffect = [nonTeamWeighted, 1 - nonTeamWeighted]

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


def generateCornerBets(inputRow):
    responseObject = {}
    bets = []
    matchId = inputRow['matchId']
    queryResults = []
    checkStats = []
    homeTeam = inputRow['homeTeamId']
    awayTeam = inputRow['awayTeamId']
    matchDate = inputRow['matchDate']
    competitionId = inputRow['competitionId']
    statWeightWon = statWeightings['Accurate crosses']['won']
    statWeightConceded = statWeightings['Accurate crosses']['conceded']
    attemptedCrossesToCornersHome = calculateAttemptedCornersToCrossesMultiplier(inputRow)[0]
    attemptedCrossesToCornersAway = calculateAttemptedCornersToCrossesMultiplier(inputRow)[1]
    outputs = {
        "homeConceded": [],
        "awayWon": [],
        "homeWon": [],
        "awayConceded": []
        }
    homeTeamWeighting = inputRow['homeTeamPosition']
    homeTeamName = rdsConnector.selectTeamName(inputRow['homeTeamId'])
    awayTeamWeighting = inputRow['awayTeamPosition']
    awayTeamName = rdsConnector.selectTeamName(inputRow['awayTeamId'])
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
                    modifier = (75-(3*math.floor((awayTeamWeighting - 1) / 3)))/(75-(3*math.floor((row['awayTeamWeight'] - 1) / 3)))
                if statWonConcededType == 'conceded':
                    modifier = (75-(3*math.floor((row['awayTeamWeight'] - 1) / 3)))/(75-(3*math.floor((awayTeamWeighting - 1) / 3)))
            if statHomeAwayType == 'away':
                if statWonConcededType == 'won':
                    modifier = (75-(3*math.floor((homeTeamWeighting - 1) / 3)))/(75-(3*math.floor((row['homeTeamWeight'] - 1) / 3)))
                if statWonConcededType == 'conceded':
                    modifier = (75-(3*math.floor((row['homeTeamWeight'] - 1) / 3)))/(75-(3*math.floor((homeTeamWeighting - 1) / 3)))
            newStat = (stat * teamWeightingsEffect[0]) + (stat * modifier * teamWeightingsEffect[1])
            outputs[statHomeAwayType + statWonConcededType.title()].append(newStat)
    homeConceded = list(filter(lambda conceded: conceded > 0, outputs["homeConceded"]))
    predictedHomeStat = math.floor(((sum(outputs["homeWon"])/len(outputs["homeWon"]) * statWeightWon) + (sum(outputs["awayConceded"])/len(outputs["awayConceded"]) * statWeightConceded))* attemptedCrossesToCornersHome)
    predictedAwayStat = math.floor(((sum(outputs["awayWon"])/len(outputs["awayWon"]) * statWeightWon) + (sum(homeConceded)/len(homeConceded) * statWeightConceded))* attemptedCrossesToCornersAway)
    # predictedMaxHomeStat = math.ceil(((max(outputs["homeWon"]) + max(outputs["awayConceded"]) + (sum(outputs["homeWon"])*2/len(outputs["homeWon"])) + (sum(outputs["awayConceded"])*2/len(outputs["awayConceded"])))/maxDivisor) * attemptedCrossesToCornersHome)
    # predictedMaxAwayStat = math.ceil(((max(outputs["awayWon"])+ max(homeConceded) + (sum(outputs["awayWon"])*2/len(outputs["awayWon"])) + (sum(homeConceded)*2/len(homeConceded)))/maxDivisor) * attemptedCrossesToCornersAway)
    bets.append(f"{homeTeamName} to have {predictedHomeStat}+ corners")# and under {predictedMaxHomeStat + 1} corners")
    bets.append(f"{awayTeamName} to have {predictedAwayStat}+ corners")# and under {predictedMaxAwayStat + 1} corners")
    print(f"{homeTeamName} to have {predictedHomeStat}+ corners")# and under {predictedMaxHomeStat + 1} corners")
    print(f"{awayTeamName} to have {predictedAwayStat}+ corners")# and under {predictedMaxAwayStat + 1} corners")
    return matchId, homeTeamName, awayTeamName, competitionId, matchDate, bets

def generateStatsExceptCornersBets(inputRow, statName):
    responseObject = {}
    bets = []
    matchId = inputRow['matchId']
    queryResults = []
    checkStats = []
    homeTeam = inputRow['homeTeamId']
    awayTeam = inputRow['awayTeamId']
    matchDate = inputRow['matchDate']
    competitionId = inputRow['competitionId']
    statWeightWon = statWeightings[statName]['won']
    statWeightConceded = statWeightings[statName]['conceded']
    outputs = {
        "homeConceded": [],
        "awayWon": [],
        "homeWon": [],
        "awayConceded": []
        }
    homeTeamWeighting = inputRow['homeTeamPosition']
    homeTeamName = rdsConnector.selectTeamName(inputRow['homeTeamId'])
    awayTeamWeighting = inputRow['awayTeamPosition']
    awayTeamName = rdsConnector.selectTeamName(inputRow['awayTeamId'])
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
                    modifier = (75-(3*math.floor((awayTeamWeighting - 1) / 3)))/(75-(3*math.floor((row['awayTeamWeight'] - 1) / 3)))
                if statWonConcededType == 'conceded':
                    modifier = (75-(3*math.floor((row['awayTeamWeight'] - 1) / 3)))/(75-(3*math.floor((awayTeamWeighting - 1) / 3)))
            if statHomeAwayType == 'away':
                if statWonConcededType == 'won':
                    modifier = (75-(3*math.floor((homeTeamWeighting - 1) / 3)))/(75-(3*math.floor((row['homeTeamWeight'] - 1) / 3)))
                if statWonConcededType == 'conceded':
                    modifier = (75-(3*math.floor((row['homeTeamWeight'] - 1) / 3)))/(75-(3*math.floor((homeTeamWeighting - 1) / 3)))
            newStat = (stat * teamWeightingsEffect[0]) + (stat * modifier * teamWeightingsEffect[1])
            outputs[statHomeAwayType + statWonConcededType.title()].append(newStat)
    homeConceded = list(filter(lambda conceded: conceded > 0, outputs["homeConceded"]))
    predictedHomeStat = math.floor(((sum(outputs["homeWon"])/len(outputs["homeWon"]) * statWeightWon) + (sum(outputs["awayConceded"])/len(outputs["awayConceded"]) * statWeightConceded)))
    predictedAwayStat = math.floor(((sum(outputs["awayWon"])/len(outputs["awayWon"]) * statWeightWon) + (sum(homeConceded)/len(homeConceded) * statWeightConceded)))
    # predictedMaxHomeStat = math.ceil(((max(outputs["homeWon"]) + max(outputs["awayConceded"]) + (sum(outputs["homeWon"])*2/len(outputs["homeWon"])) + (sum(outputs["awayConceded"])*2/len(outputs["awayConceded"])))/maxDivisor) * attemptedCrossesToCornersHome)
    # predictedMaxAwayStat = math.ceil(((max(outputs["awayWon"])+ max(homeConceded) + (sum(outputs["awayWon"])*2/len(outputs["awayWon"])) + (sum(homeConceded)*2/len(homeConceded)))/maxDivisor) * attemptedCrossesToCornersAway)
    bets.append(f"{homeTeamName} to have {predictedHomeStat}+ {statName}")# and under {predictedMaxHomeStat + 1} corners")
    bets.append(f"{awayTeamName} to have {predictedAwayStat}+ {statName}")# and under {predictedMaxAwayStat + 1} corners")
    print(f"{homeTeamName} to have {predictedHomeStat}+ {statName}")# and under {predictedMaxHomeStat + 1} corners")
    print(f"{awayTeamName} to have {predictedAwayStat}+ {statName}")# and under {predictedMaxAwayStat + 1} corners")
    return matchId, homeTeamName, awayTeamName, competitionId, matchDate, bets


def generateResponseObject(inputRow):
    responseObject = {}
    cornerResults = generateCornerBets(inputRow)
    otherStatResults = generateStatsExceptCornersBets(inputRow, 'Total shots')
    results = [cornerResults[0], cornerResults[1], cornerResults[2], cornerResults[3], cornerResults[4], [cornerResults[5], otherStatResults[5]]]
    responseObject.update({results[0]: {
    "teams": {
        "home": results[1],
        "away": results[2]
    },
    "league": results[3],
    "date": str(results[4]),
    "bets": results[5]
    }})
    return responseObject
