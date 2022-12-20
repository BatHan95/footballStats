
import requests
import pandas as pd
import datetime
import math

baseUrl = 'https://www.fotmob.com/api'

matchesCols = ['competitionId', 'matchId', 'homeTeamId', 'awayTeamId', 'matchDate', 'homeTeamPosition', 'awayTeamPosition', 'homeTeamName', 'awayTeamName']
statsCols = ['matchId', 'teamId', 'statName', 'stat', 'homeOrAway', 'season']
teamsCols = ['teamId', 'leagueId', 'teamName']
relevantStats = ['Accurate crosses', 'Corners']

leagues = [{'name': 'Premier League', 'id': '47'}]

leagueIdList = []
for league in leagues:
        leagueIdList.append(league['id'])

leagueNameList = []
for league in leagues:
        leagueNameList.append(league['name'])

otherLeagues = [{'name': 'Premier League', 'id': '47'}, {'name': 'LaLiga', 'id': '87'}, {'name': 'Serie A', 'id': '55'}, {'name': 'Bundesliga', 'id': '54'}, {'name': 'Ligue 1', 'id': '53'}, {'name': 'League 1', 'id': '108'}]

def getLeaguePosition(teamId, leagueId):
    url = baseUrl + '/leagues?type=league&id=' + str(leagueId)
    r = requests.get(url)
    data = r.json()
    leagueTable = data['table'][0]['data']['table']['all']
    for team in leagueTable:
        if team['id'] == teamId:
            teamPosition = team['idx']
            teamName = (team['name']).replace("'", "")
    return teamPosition, teamName


def getMatchesByLeague(leagueId):
    url = baseUrl + '/leagues?type=league&id=' + leagueId
    r = requests.get(url)
    data = r.json()
    matchData = []
    matchDataList = data['matches']['data']['allMatches']
    for match in matchDataList:
        if (match['status']['finished'] == True) & (match['status']['cancelled'] == False) :
            matchDate = str(datetime.datetime.strptime(match['monthKey'], '%A, %d %B %Y'))
            matchId = match['id']
            homeTeamId = match['home']['id']
            awayTeamId = match['away']['id']
            homeLeaguePosition, homeTeamName = getLeaguePosition(homeTeamId, leagueId)
            awayLeaguePosition, awayTeamName = getLeaguePosition(awayTeamId, leagueId)
            matchData.append([leagueId, matchId, homeTeamId, awayTeamId, matchDate, homeLeaguePosition, awayLeaguePosition])
    if matchData != []:
        return matchData


def getMatchesByDate(date):
    url = baseUrl + '/matches?date=' + date
    r = requests.get(url)
    data = r.json()
    matchData = []
    matchDataList = data['leagues']
    for competition in matchDataList:
        competitionId = competition['primaryId']
        for match in competition['matches']:
            if (match['status']['finished'] == True) & (match['status']['cancelled'] == False) & (str(competitionId) in leagueIdList):
                matchDate = str(datetime.datetime.strptime(match['time'], '%d.%m.%Y %H:%M').date())
                matchId = match['id']
                homeTeamId = match['home']['id']
                awayTeamId = match['away']['id']
                homeLeaguePosition, homeTeamName = getLeaguePosition(homeTeamId, competitionId)
                awayLeaguePosition, awayTeamName = getLeaguePosition(awayTeamId, competitionId)
                matchData.append([competitionId, matchId, homeTeamId, awayTeamId, matchDate, homeLeaguePosition, awayLeaguePosition, homeTeamName, awayTeamName])
    if matchData != []:
        return matchData


def getMatchStats(matchId, homeTeamId, awayTeamId):
    url = baseUrl + '/matchDetails?matchId=' + matchId
    r = requests.get(url)
    data = r.json()
    statsData = []
    season = data['general']['parentLeagueSeason']
    if 'content' in data.keys():
        try: 
            statsDataList = data['content']['stats']['stats']
            for stats in statsDataList:
                for stat in stats['stats']:
                    if stat['type'] != 'title':
                        statName = stat['title']
                        homeStat = stat['stats'][0]
                        awayStat = stat['stats'][1]
                        if statName in relevantStats:
                            statsData.append([matchId, homeTeamId, statName, homeStat, 'home', season])
                            statsData.append([matchId, awayTeamId, statName, awayStat, 'away', season])
        except:
            pass
        if statsData != []:
            return statsData


def getAllStats(matchesDf):
    allStatsData = []
    for line_number, (index, row) in enumerate(matchesDf.iterrows()):
        print('getting stats for match ', f'{line_number+1} of {len(matchesDf)} - {round(100*(line_number + 1)/len(matchesDf),1)}% complete')
        matchStatsData = getMatchStats(str(row['matchId']), row['homeTeamId'], row['awayTeamId'])
        if matchStatsData != None:
            allStatsData.append(matchStatsData)
    allStatsDf = pd.DataFrame([item for sublist in allStatsData for item in sublist], columns = statsCols).drop_duplicates()
    if allStatsData != []:
        return allStatsDf

# def getTeamNamesForMatches(matchesDf):
#     teamsList = []
#     homeTeams = matchesDf['homeTeamId'].unique()
#     awayTeams = matchesDf['awayTeamId'].unique()
#     teamsList.append(awayTeams)
#     teamsList.append(homeTeams)
#     teamsList = set([item for sublist in teamsList for item in sublist])
#     teamsNameList = []
#     for team in teamsList:
#         url = baseUrl + '/teams?type=team&id=' + str(team)
#         r = requests.get(url)
#         data = r.json()
#         teamName = data['details']['name']
#         teamsNameList.append([team, teamName])
#     if teamsNameList != []:
#         teamsNameDf = pd.DataFrame(teamsNameList, columns=teamsCols)
#         return(teamsNameDf)


def getLeaguesMatches(leagues):
    matchData = []
    for league in leagues:
        leagueMatches = getMatchesByLeague(league['id'])
        matchData.append(leagueMatches)
    matchData = [item for sublist in matchData for item in sublist]
    if matchData != []:
        return matchData


def getMatchesInDateRange(startDate, endDate):
    print('Getting matches between ' + str(startDate) + ' and ' + str(endDate) + ' for ' + ' & '.join(leagueNameList))
    start = startDate
    end = endDate
    matchDay = start
    matchData = []
    while matchDay <= end:
        c = matchDay.strftime('%Y%m%d')
        matchDay = matchDay + datetime.timedelta(days=1)
        matchList = getMatchesByDate(c)
        if matchList != None:
            matchData.append(matchList)
            print('Got ' + str(len(matchList)) + ' match(es) on ' + str(matchDay - datetime.timedelta(days=1)))
    if matchData != []:
        matchData = [item for sublist in matchData for item in sublist]
        print('Got a total of ' + str(len(matchData)) + ' matches between ' + str(startDate) + ' and ' + str(endDate) + ' for ' + ' & '.join(leagueNameList))
        return matchData


def getTeamNamesForLeagues(leagues):
    teamsList = []
    for league in leagues:
        leagueId = league['id']
        url = baseUrl + '/leagues?type=league&id=' + leagueId
        r = requests.get(url)
        data = r.json()
        teamsTable = data['table'][0]['data']['table']['all']
        for team in teamsTable:
            teamsList.append([team['id'], leagueId, (team['name']).replace("'", "")])
    if teamsList != []:
        teamsNameDf = pd.DataFrame(teamsList, columns=teamsCols)
        return(teamsNameDf)

def getFutureMatchesByDate(date):
    dateString = date.strftime('%Y%m%d')
    url = baseUrl + '/matches?date=' + dateString
    r = requests.get(url)
    data = r.json()
    matchData = []
    matchDataList = data['leagues']
    for competition in matchDataList:
        competitionId = competition['primaryId']
        for match in competition['matches']:
            if (match['status']['started'] == False) & (match['status']['cancelled'] == False) & (str(competitionId) in leagueIdList):
                matchDate = datetime.datetime.strptime(match['time'], '%d.%m.%Y %H:%M').date()
                matchId = match['id']
                homeTeamId = match['home']['id']
                awayTeamId = match['away']['id']
                homeLeaguePosition, homeTeamName = getLeaguePosition(homeTeamId, competitionId)
                awayLeaguePosition, awayTeamName = getLeaguePosition(awayTeamId, competitionId)
                matchData.append([competitionId, matchId, homeTeamId, awayTeamId, matchDate, homeLeaguePosition, awayLeaguePosition, homeTeamName, awayTeamName])
    if matchData != []:
        return matchData

def getFutureMatchesInDateRange(startDate, endDate):
    print('Getting matches between ' + str(startDate) + ' and ' + str(endDate) + ' for ' + ' & '.join(leagueNameList))
    start = startDate
    end = endDate
    matchDay = start
    matchData = []
    while matchDay <= end:
        matchList = getFutureMatchesByDate(matchDay)
        matchDay = matchDay + datetime.timedelta(days=1)
        if matchList != None:
            matchData.append(matchList)
            print('Got ' + str(len(matchList)) + ' match(es) on ' + str(matchDay - datetime.timedelta(days=1)))
    if matchData != []:
        matchData = [item for sublist in matchData for item in sublist]
        print('Got a total of ' + str(len(matchData)) + ' matches between ' + str(startDate) + ' and ' + str(endDate) + ' for ' + ' & '.join(leagueNameList))
        return matchData

def getMatchesTomorrow():
    dateToday = datetime.date.today()
    dateTomorrow = dateToday + datetime.timedelta(days=1)
    dateTomorrowString = dateTomorrow.strftime('%Y%m%d')
    url = baseUrl + '/matches?date=' + dateTomorrowString
    r = requests.get(url)
    data = r.json()
    matchData = []
    matchDataList = data['leagues']
    for competition in matchDataList:
        competitionId = competition['primaryId']
        for match in competition['matches']:
            if (match['status']['started'] == False) & (match['status']['cancelled'] == False) & (str(competitionId) in leagueIdList):
                matchDate = str(datetime.datetime.strptime(match['time'], '%d.%m.%Y %H:%M').date())
                matchId = match['id']
                homeTeamId = match['home']['id']
                awayTeamId = match['away']['id']
                homeLeaguePosition, homeTeamName = getLeaguePosition(homeTeamId, competitionId)
                awayLeaguePosition, awayTeamName = getLeaguePosition(awayTeamId, competitionId)
                matchData.append([competitionId, matchId, homeTeamId, awayTeamId, matchDate, homeLeaguePosition, awayLeaguePosition, homeTeamName, awayTeamName])
    if matchData != []:
        return matchData

def getMatchesToday():
    dateToday = datetime.date.today()
    dateTodayString = dateToday.strftime('%Y%m%d')
    url = baseUrl + '/matches?date=' + dateTodayString
    r = requests.get(url)
    data = r.json()
    matchData = []
    matchDataList = data['leagues']
    for competition in matchDataList:
        competitionId = competition['primaryId']
        for match in competition['matches']:
            if (match['status']['started'] == False) & (match['status']['cancelled'] == False) & (str(competitionId) in leagueIdList):
                matchDate = str(datetime.datetime.strptime(match['time'], '%d.%m.%Y %H:%M').date())
                matchId = match['id']
                homeTeamId = match['home']['id']
                awayTeamId = match['away']['id']
                homeLeaguePosition, homeTeamName = getLeaguePosition(homeTeamId, competitionId)
                awayLeaguePosition, awayTeamName = getLeaguePosition(awayTeamId, competitionId)
                matchData.append([competitionId, matchId, homeTeamId, awayTeamId, matchDate, homeLeaguePosition, awayLeaguePosition, homeTeamName, awayTeamName])
    if matchData != []:
        return matchData


# print(getMatchesTomorrow())

# print(getTeamNamesForMatches(pd.DataFrame(getMatchesInDateRange('2022-08-05', '2022-08-09'), columns = matchesCols).drop_duplicates()))
# matchesDf = pd.DataFrame(getMatchesInDateRange('2022-08-05', '2022-08-09'), columns=matchesCols)
# print(getAllStats(matchesDf))

# matchesDf = pd.DataFrame(getMatchesByDate('20221106'), columns=matchesCols)
# statsDf = pd.DataFrame(getAllStats(matchesDf), columns=statsCols)
# for row in matchesDf:

#     print(', '.join(repr(e) for e in row))
# # leaguesMatchesDf = pd.DataFrame(getLeaguesMatches(leagues), columns=matchesCols).drop_duplicates()
# # teamNamesDf = getTeamNamesForMatches(leaguesMatchesDf)
# # print(teamNamesDf)

# #teamNames.to_csv('teamNames.csv', index=False)

# leaguesMatchesDf = getLeaguesMatches(leagues)
# allLeagueMatchesStatsDf = getAllStats(leaguesMatchesDf)
# print(allLeagueMatchesStatsDf)
#allLeagueMatchesStatsDf.to_csv('output.csv', index=False)
