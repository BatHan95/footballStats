import fotmobData
import rdsConnector
import datetime
import pandas as pd
import generateBets

def refresh():
    try:
        dateYesterday = datetime.date.today() - datetime.timedelta(days=1)
        matchesDf = pd.DataFrame(fotmobData.getMatchesInDateRange(dateYesterday, dateYesterday), columns = fotmobData.matchesCols).drop_duplicates()
        rdsConnector.rdsInsert(matchesDf, 'matches')
        statsDf = pd.DataFrame(fotmobData.getAllStats(matchesDf), columns=fotmobData.statsCols).drop_duplicates()
        rdsConnector.rdsInsert(statsDf, 'stats')
        return (f'Success', True)
    except Exception as e:
        print(f'Error - { str(e) }')
        return (f'Error', False)

def updateTeams():
    teamsDf = fotmobData.getTeamNamesForLeagues(fotmobData.leagues)
    rdsConnector.rdsInsert(teamsDf, 'teams')

def getBetsForTomorrow():
    try:
        matchesDf = pd.DataFrame(fotmobData.getMatchesTomorrow(), columns = fotmobData.matchesCols).drop_duplicates()
        bets = []
        for index, row in matchesDf.iterrows():
            bets.append(generateBets.generateBets(row))
        return ({"matches": bets}, True)
    except Exception as e:
        print(f'Error - { str(e) }')
        return (f'Error', False)


def getBetsForDateRange(dateFrom, dateTo):
    try: 
        dateFrom = datetime.datetime.strptime(dateFrom, '%Y-%m-%d').date()
        dateTo = datetime.datetime.strptime(dateTo, '%Y-%m-%d').date()
        matchesDf = matchesDf = pd.DataFrame(fotmobData.getFutureMatchesInDateRange(dateFrom, dateTo), columns = fotmobData.matchesCols).drop_duplicates()
        bets = []
        for index, row in matchesDf.iterrows():
            bets.append(generateBets.generateBets(row))
        return ({"matches": bets}, True)
    except Exception as e:
        print(f'Error - { str(e) }')
        return (f'Error', False)