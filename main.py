import fotmobData
import rdsConnector
import datetime
import pandas as pd

def refresh():
    dateYesterday = datetime.date.today() - datetime.timedelta(days=1)
    matchesDf = pd.DataFrame(fotmobData.getMatchesInDateRange(dateYesterday, dateYesterday), columns = fotmobData.matchesCols).drop_duplicates()
    rdsConnector.rdsInsert(matchesDf, 'matches')
    statsDf = pd.DataFrame(fotmobData.getAllStats(matchesDf), columns=fotmobData.statsCols).drop_duplicates()
    rdsConnector.rdsInsert(statsDf, 'stats')

def updateTeams():
    teamsDf = fotmobData.getTeamNamesForLeagues(fotmobData.leagues)
    rdsConnector.rdsInsert(teamsDf, 'teams')

def getBetsForTomorrow():
    matchesDf = pd.DataFrame(fotmobData.getMatchesTomorrow(), columns = fotmobData.matchesCols).drop_duplicates()
    bets = []
    for index, row in matchesDf.iterrows():
        finalStatsDf = pd.DataFrame(rdsConnector.rdsSelect(row, ['Total shots', 'Corners', 'Yellow cards', 'Shots on target']), columns = ['matchId', 'competitionId', 'matchDate', 'teamName', 'homeOrAway', 'statName', 'min', 'max', 'avg'])
        bets.append(fotmobData.generateBets(finalStatsDf))
    return {"matches": bets}
