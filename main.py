import fotmobData
import rdsConnector
import datetime
import pandas as pd
import generateBets

def refresh():
    try:
        dateFrom = datetime.date.today() - datetime.timedelta(days=1)
        dateYesterday = datetime.date.today() - datetime.timedelta(days=1)
        matchesList = fotmobData.getMatchesInDateRange(dateFrom, dateYesterday)
        rdsConnector.rdsInsert(matchesList, 'matches')
        matchesList = []
        for leagueId in fotmobData.leagueIdList:
            matchesList.append(rdsConnector.rdsSelectMatches(dateFrom, dateYesterday, leagueId))

        matchesList = [item for sublist in matchesList for item in sublist]
        statsList = fotmobData.getAllStats(matchesList)
        rdsConnector.rdsInsert(statsList, 'stats')
        return (f'Success', True)
    except Exception as e:
        print(f'Error - { str(e) }')
        return (f'Error', False)

def updateTeams():
    teamsDf = fotmobData.getTeamNamesForLeagues(fotmobData.leagues)
    rdsConnector.rdsInsert(teamsDf, 'teams')

def getBetsForTomorrow():
    print('\n')
    matchesDf = pd.DataFrame(fotmobData.getMatchesTomorrow(), columns = fotmobData.matchesCols).drop_duplicates()
    bets = []
    for index, row in matchesDf.iterrows():
        bets.append(generateBets.generateResponseObject(row))
    print('\n')
    return ({"matches": bets}, True)

def getBetsForToday():
    print('\n')
    matchesDf = pd.DataFrame(fotmobData.getMatchesToday(), columns = fotmobData.matchesCols).drop_duplicates()
    bets = []
    for index, row in matchesDf.iterrows():
        bets.append(generateBets.generateResponseObject(row))
    print('\n')
    return ({"matches": bets}, True)

def addStatType():
    dateFrom = datetime.datetime.strptime('2022-08-05', '%Y-%m-%d').date()
    dateTo = datetime.date.today()
    matchesList = []
    for leagueId in fotmobData.leagueIdList:
        matchesList.append(rdsConnector.rdsSelectMatches(dateFrom, dateTo, leagueId))

    matchesList = [item for sublist in matchesList for item in sublist]
    statsList = fotmobData.getAllStats(matchesList)
    rdsConnector.rdsInsert(statsList, 'stats')

def getBetsForDateRange(dateFrom, dateTo):
    try: 
        dateFrom = datetime.datetime.strptime(dateFrom, '%Y-%m-%d').date()
        dateTo = datetime.datetime.strptime(dateTo, '%Y-%m-%d').date()
        matchesDf = matchesDf = pd.DataFrame(fotmobData.getFutureMatchesInDateRange(dateFrom, dateTo), columns = fotmobData.matchesCols).drop_duplicates()
        bets = []
        for index, row in matchesDf.iterrows():
            bets.append(generateBets.generateResponseObject(row))
        return ({"matches": bets}, True)
    except Exception as e:
        print(f'Error - { str(e) }')
        return (f'Error', False)


if __name__ == '__main__':
    # refresh()
    getBetsForToday()