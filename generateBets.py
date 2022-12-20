import rdsConnector
import math
import pandas as pd

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
        'won': 0.5,
        'conceded': 0.33
    },
    'Blocked shots': {
        'won': 0.4,
        'conceded': 0.35
    }
}

attemptedCrossesToCorners = 0.27
maxMutiplier = 2.35
teamWeightingsEffect = [0.67, 0.115]
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


def generateBets(inputRow):
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
    homeConceded = []
    awayWon = []
    homeWon = []
    awayConceded = []
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
    bets.append(f"{homeTeamName} to have {predictedHomeStat}+ corners and under {predictedMaxHomeStat + 1} corners")
    bets.append(f"{awayTeamName} to have {predictedAwayStat}+ corners and under {predictedMaxAwayStat + 1} corners")
    responseObject.update({matchId: {
    "teams": {
        "home": homeTeamName,
        "away": awayTeamName
    },
    "league": competitionId,
    "date": str(matchDate),
    "bets": bets
    }})
    return responseObject
