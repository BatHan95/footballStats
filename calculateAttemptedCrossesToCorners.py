import math
import rdsConnector
import pandas as pd
import datetime
import fotmobData

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

queryTypes = ['home', 'away']
statTypes = ['Accurate crosses']

def accurateCrossesToAttemptedCrosses(rawStat):
    accurateCrosses = float(rawStat[0:rawStat.find(' (')])
    crossAccuracy = float(rawStat[rawStat.find(' (')+2:rawStat.find('%)')])/100
    if crossAccuracy == 0:
        attemptedCrosses = 0
    else:
        attemptedCrosses = math.floor(accurateCrosses/crossAccuracy)
    return([accurateCrosses, crossAccuracy, attemptedCrosses])


def calculateValuesToUpdateOutput(row):
    attemptedCornersToCrosses = int(row['stat_y'])/row['stat_x'] if row['stat_x'] > 0 else 0
    statHomeAwayType = row['type'].split('_')[0]
    statWonConcededType = row['type'].split('_')[1]
    return statHomeAwayType + statWonConcededType.title(), attemptedCornersToCrosses



def calculateAttemptedCornersToCrossesMultiplier(inputRow):
    output = {
        "homeConceded": [],
        "awayWon": [],
        "homeWon": [],
        "awayConceded": []
        }
    accurateCrosses = [rdsConnector.rdsSelectStats(inputRow, 'Accurate crosses', queryType) for queryType in queryTypes]
    accurateCrosses = [item for sublist in accurateCrosses for item in sublist]
    corners = [rdsConnector.rdsSelectStats(inputRow, 'Corners', queryType) for queryType in queryTypes]
    corners = [item for sublist in corners for item in sublist]
    attemptedCrosses = [(item[0], 'Attempted crosses', accurateCrossesToAttemptedCrosses(item[4])[2], item[5], item[6], item[7])
    for item in accurateCrosses]
    attemptedCrossesDf = pd.DataFrame(attemptedCrosses, columns=['matchId', 'statName', 'stat', 'homeOrAway', 'season', 'type'])
    cornersDf = pd.DataFrame(corners, columns=['matchId', 'matchDate', 'teamName', 'statName', 'stat', 'homeOrAway', 'season', 'type', 'homeTeamWeight', 'awayTeamWeight'])
    combinedDf = attemptedCrossesDf.merge(cornersDf,how='inner',left_on=['matchId', 'homeOrAway', 'season', 'type'],right_on=['matchId', 'homeOrAway', 'season', 'type'])
    def updateOutput(keyValuePair):
        key, value = keyValuePair
        output[key].append(value)
    combinedDf.apply(calculateValuesToUpdateOutput, axis=1).apply(updateOutput)
    predictedHomeMultiplier = ((sum(output["homeWon"])/len(output["homeWon"]) * 0.5) + (sum(output["awayConceded"])/len(output["awayConceded"]) * 0.5))
    predictedAwayMultiplier = ((sum(output["awayWon"])/len(output["awayWon"]) * 0.5) + (sum(output["homeConceded"])/len(output["homeConceded"]) * 0.5))
    return([predictedHomeMultiplier, predictedAwayMultiplier])

def run(dateFrom, dateTo):
    datetime.datetime.strptime(dateFrom, '%Y-%m-%d').date()
    datetime.datetime.strptime(dateTo, '%Y-%m-%d').date()
    testMatchesData = []
    leagueId = 47
    testMatchesData = [[item for item in sublist] for leagueId in fotmobData.leagueIdList for sublist in rdsConnector.rdsSelectMatches(dateFrom, dateFrom, leagueId)]
    df = pd.DataFrame(testMatchesData, columns = fotmobData.matchesCols).drop_duplicates()
    df.apply(calculateAttemptedCornersToCrossesMultiplier, axis=1)
# run('2022-11-12', '2022-11-12')
