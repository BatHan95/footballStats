
import requests
import pandas as pd
import datetime
import math

baseUrl = 'https://www.fotmob.com/api'

matchesCols = ['competitionId', 'matchId', 'homeTeamId', 'awayTeamId', 'matchDate']
statsCols = ['matchId', 'teamId', 'statName', 'stat', 'homeOrAway', 'season']
teamsCols = ['teamId', 'leagueId', 'teamName']

leagues = [{'name': 'Premier League', 'id': '47'}, {'name': 'LaLiga', 'id': '87'}, {'name': 'Serie A', 'id': '55'}, {'name': 'Bundesliga', 'id': '54'}, {'name': 'Ligue 1', 'id': '53'}]

leagueIdList = []
for league in leagues:
        leagueIdList.append(league['id'])

leagueNameList = []
for league in leagues:
        leagueNameList.append(league['name'])

otherLeagues = [{'name': 'LaLiga', 'id': '87'}, {'name': 'Serie A', 'id': '55'}, {'name': 'Bundesliga', 'id': '54'}, {'name': 'Ligue 1', 'id': '53'}]

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
            matchData.append([leagueId, matchId, homeTeamId, awayTeamId, matchDate])
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
                matchData.append([competitionId, matchId, homeTeamId, awayTeamId, matchDate])
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
    print('Getting matches between ' + startDate + ' and ' + endDate + ' for ' + ' & '.join(leagueNameList))
    start = datetime.datetime.strptime(startDate, "%Y-%m-%d")
    end = datetime.datetime.strptime(endDate, "%Y-%m-%d")
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
        print('Got a total of ' + str(len(matchData)) + ' matches between ' + startDate + ' and ' + endDate + ' for ' + ' & '.join(leagueNameList))
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
                matchData.append([competitionId, matchId, homeTeamId, awayTeamId, matchDate])
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
                matchData.append([competitionId, matchId, homeTeamId, awayTeamId, matchDate])
    if matchData != []:
        return matchData

def generateBets(df):
    betList = []
    for index, row in df.iterrows():
        if row['statName'] != 'Yellow cards':
            stat = round(row['avg']-0.65)
            max = math.ceil((row['max'] * 6 + row['avg'] * 2)/8)
            betList.append([row['matchId'], row['teamName'], row['homeOrAway'], row['statName'], stat, max])
        if row['statName'] == 'Yellow cards':
            bookingPoints = (row['min'] * 3 + row['avg'] * 7)/10 * 10
            bookingPoints = bookingPoints - (bookingPoints%10)
            betList.append([row['matchId'], row['teamName'], row['homeOrAway'], 'Booking points', bookingPoints, bookingPoints])
    betDf = pd.DataFrame(betList, columns= ['matchId', 'teamName', 'homeOrAway', 'statName', 'stat', 'max'])

    matchStats = {}
    print('\n')
    for index, row in betDf.iterrows():
        if row['matchId'] in matchStats:
            if row['homeOrAway'] =='home':
                matchStats[row['matchId']]['homeTeam'] = row['teamName']
            if row['homeOrAway'] =='away':
                matchStats[row['matchId']]['awayTeam'] = row['teamName']
            if row['statName'] in matchStats[row['matchId']]:
                matchStats[row['matchId']][row['statName']] += row['stat']
            else:
                matchStats[row['matchId']][row['statName']] = row['stat']
        else:
            if row['homeOrAway'] =='home':
                matchStats[row['matchId']] = {'homeTeam': row['teamName']}
            if row['homeOrAway'] =='away':
                matchStats[row['matchId']] = {'awayTeam': row['awayName']}
            matchStats[row['matchId']] = {row['statName']: row['stat']}
        if row['statName'] != 'Booking points':
            print(f"{row['teamName']} ({row['homeOrAway']}) to have {math.floor(row['stat'])}+ {row['statName']} and under {math.floor(row['max'])} {row['statName']}")
        if row['statName'] == 'Booking points':
            bookingPoints = row['stat']
            print(f"{row['teamName']} ({row['homeOrAway']}) to have {math.floor(bookingPoints)}+ booking points")
    for key, value in matchStats.items():
        print(f"{value['homeTeam']} vs {value['awayTeam']} to have {value['Total shots']}+ Total Shots, {value['Shots on target']}+ Total Shots on Target, {value['Corners']}+ Total Corners and {value['Booking points']}+ Total Booking Points\n")


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
