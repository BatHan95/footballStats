from fotmobData import matchesCols, statsCols, teamsCols


typeDict = {
    'matches': {
        'cols': matchesCols,
        'indices': matchesCols[0:2]},
    'stats': {
        'cols': statsCols,
        'indices': statsCols[0:3]},
    'teams': {
        'cols': teamsCols,
        'indices': teamsCols[0:2]}
}

def generateInsertQuery(type, row):
    typeCols = ", ".join(typeDict[type]['cols'])
    indices = ", ".join(typeDict[type]['indices'])
    insertQuery = f"""
    INSERT INTO {type}Data({typeCols})
    VALUES ( {', '.join(repr(e) for e in row)} )
    ON CONFLICT ({indices}) DO NOTHING
    """
    return insertQuery

def generateHomeSelectQuery(row, stats):
    statString = ''
    for stat in stats:
        statString = statString + f"insert into check_stats values ('{stat}');\n"
    selectQuery = f"""
    
    drop table if exists check_stats;
    create temporary table check_stats (statName text);

    {statString}

    drop table if exists temp_home_matches;
    drop table if exists temp_away_conceded_matches;
    drop table if exists temp_final_stats;
    
    select s.matchId, t2.teamName, s.statName, s.stat, s.homeOrAway
    into temporary table temp_away_conceded_matches
    from matchesData as m
    join statsData as s
    on m.matchId = s.matchId
    join teamsData as t2
    on t2.teamId = m.hometeamid
    where m.awayTeamId = {row['awayTeamId']}
    and s.statName in (select * from check_stats)
    and s.homeOrAway = 'home';

    select s.matchId, t.teamName, s.statName, s.stat, s.homeOrAway
    into temporary table temp_home_matches
    from statsData as s
    join teamsData as t
    on s.teamId = t.teamId
    where s.teamId = {row['homeTeamId']}
    and s.statName in (select * from check_stats)
    and s.homeOrAway = 'home';

    select {row['matchId']} as matchId, {row['competitionId']} as competitionId, '{row['matchDate']}' as matchDate, home.statName, (select teamName from teamsData where teamId = {row['homeTeamId']}), 'home' as homeOrAway, home.homeMin, home.homeMax, home.homeAvg, awayConcededMin, awayConcededMax, awayConcededAvg 
    into TEMPORARY table temp_final_stats
    from(
    select
    statName
    , min(left(stat, case when POSITION(' (' in stat) = 0 then length(stat) else POSITION(' (' in stat)-1 end) :: float) as homeMin
    , max(left(stat, case when POSITION(' (' in stat) = 0 then length(stat) else POSITION(' (' in stat)-1 end) :: float) as homeMax
    , avg(left(stat, case when POSITION(' (' in stat) = 0 then length(stat) else POSITION(' (' in stat)-1 end) :: float) as homeAvg
    from temp_home_matches
    group by statName) as home
    join (
    select
    statName
    , min(left(stat, case when POSITION(' (' in stat) = 0 then length(stat) else POSITION(' (' in stat)-1 end) :: float) as awayConcededMin
    , max(left(stat, case when POSITION(' (' in stat) = 0 then length(stat) else POSITION(' (' in stat)-1 end) :: float) as awayConcededMax
    , avg(left(stat, case when POSITION(' (' in stat) = 0 then length(stat) else POSITION(' (' in stat)-1 end) :: float) as awayConcededAvg
    from
    temp_away_conceded_matches
    group by statName) as awayConceded
    on home.statName = awayConceded.statName;

    select 
    matchId
    , competitionId
    , matchDate
    , teamName
    , homeOrAway
    , statName
    , least(homeMin, awayConcededMin) as homeMin
    , greatest(homeMax, awayConcededMax) as homeMax
    , (homeAvg*4 + awayConcededAvg*2)/6 as homeAvg

    from temp_final_stats
    order by statName;

    """
    return selectQuery

def generateAwaySelectQuery(row, stats):
    statString = ''
    for stat in stats:
        statString = statString + f"insert into check_stats values ('{stat}');\n"
    selectQuery = f"""
    
    drop table if exists check_stats;
    create temporary table check_stats (statName text);

    {statString}

    drop table if exists temp_away_matches;
    drop table if exists temp_home_conceded_matches;
    drop table if exists temp_final_stats;
    
    select s.matchId, t2.teamName, s.statName, s.stat, s.homeOrAway
    into temporary table temp_home_conceded_matches
    from matchesData as m
    join statsData as s
    on m.matchId = s.matchId
    join teamsData as t2
    on t2.teamId = m.awayteamid
    where m.homeTeamId = {row['homeTeamId']}
    and s.statName in (select * from check_stats)
    and s.homeOrAway = 'away';

    select s.matchId, t.teamName, s.statName, s.stat, s.homeOrAway
    into temporary table temp_away_matches
    from statsData as s
    join teamsData as t
    on s.teamId = t.teamId
    where s.teamId = {row['awayTeamId']}
    and s.statName in (select * from check_stats)
    and s.homeOrAway = 'away';

    select {row['matchId']} as matchId, {row['competitionId']} as competitionId, '{row['matchDate']}' as matchDate, away.statName, (select teamName from teamsData where teamId = {row['awayTeamId']}), 'away' as homeOrAway, awayMin, awayMax, awayAvg, homeConcededMin, homeConcededMax, homeConcededAvg 
    into TEMPORARY table temp_final_stats
    from(
    select
    statName
    , min(left(stat, case when POSITION(' (' in stat) = 0 then length(stat) else POSITION(' (' in stat)-1 end) :: float) as awayMin
    , max(left(stat, case when POSITION(' (' in stat) = 0 then length(stat) else POSITION(' (' in stat)-1 end) :: float) as awayMax
    , avg(left(stat, case when POSITION(' (' in stat) = 0 then length(stat) else POSITION(' (' in stat)-1 end) :: float) as awayAvg
    from temp_away_matches
    group by statName) as away
    join (
    select
    statName
    , min(left(stat, case when POSITION(' (' in stat) = 0 then length(stat) else POSITION(' (' in stat)-1 end) :: float) as homeConcededMin
    , max(left(stat, case when POSITION(' (' in stat) = 0 then length(stat) else POSITION(' (' in stat)-1 end) :: float) as homeConcededMax
    , avg(left(stat, case when POSITION(' (' in stat) = 0 then length(stat) else POSITION(' (' in stat)-1 end) :: float) as homeConcededAvg
    from
    temp_home_conceded_matches
    group by statName) as homeConceded
    on away.statName = homeConceded.statName;

    select
    matchId
    , competitionId
    , matchDate
    , teamName
    , homeOrAway
    , statName
    , least(awayMin, homeConcededMin) as awayMin
    , greatest(awayMax, homeConcededMax) as awayMax
    , (awayAvg*4 + homeConcededAvg*2)/6 as awayAvg

    from temp_final_stats
    order by statName;

    """
    return selectQuery

