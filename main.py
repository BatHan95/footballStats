import fotmobData
import rdsConnector
import pandas as pd

# matchesDf = pd.DataFrame(fotmobData.getMatchesInDateRange('2022-11-09', '2022-11-09'), columns = fotmobData.matchesCols).drop_duplicates()
# rdsConnector.rdsInsert(matchesDf, 'matches')
# statsDf = pd.DataFrame(fotmobData.getAllStats(matchesDf), columns=fotmobData.statsCols).drop_duplicates()
# rdsConnector.rdsInsert(statsDf, 'stats')
# teamsDf = fotmobData.getTeamNamesForLeagues(fotmobData.leagues)
# rdsConnector.rdsInsert(teamsDf, 'teams')

matchesDf = pd.DataFrame(fotmobData.getMatchesTomorrow(), columns = fotmobData.matchesCols).drop_duplicates()

for index, row in matchesDf.iterrows():
    finalStatsDf = pd.DataFrame(rdsConnector.rdsSelect(row, ['Total shots', 'Corners', 'Yellow cards', 'Shots on target']), columns = ['matchId', 'teamName', 'homeOrAway', 'statName', 'min', 'max', 'avg'])
    fotmobData.generateBets(finalStatsDf)
