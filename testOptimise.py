import testBets
from sqlalchemy import null
import fotmobData
import rdsConnector
import datetime
import pandas as pd
import tqdm
from itertools import repeat
from concurrent.futures import ProcessPoolExecutor
import math
import scipy.optimize as optimize
from scipy.optimize import minimize, LinearConstraint, minimize_scalar


def test_predictions(nonTeamWeighted, dateFrom = '2022-11-01', dateTo = '2022-12-12'):
    teamWeightingsEffect = [nonTeamWeighted, 1 - nonTeamWeighted]
    datetime.datetime.strptime(dateFrom, '%Y-%m-%d').date()
    datetime.datetime.strptime(dateTo, '%Y-%m-%d').date()
    testMatchesData = []
    for leagueId in fotmobData.leagueIdList:
        testMatchesData.append(rdsConnector.rdsSelectMatches(dateFrom, dateTo, leagueId))

    df = [item for sublist in testMatchesData for item in sublist]
    # df = df.loc[df['matchId'] == 3916094]

    checkResults = []

    with ProcessPoolExecutor(max_workers=24) as executor:
        for r in executor.map(testBets.newCombinedAlgorithm, (df), repeat(teamWeightingsEffect, len(df))):
            checkResults.append(r)
    checkResults = [item for sublist in checkResults for item in [item for sub_sublist in sublist for item in sub_sublist]]
    checkResultsDf = pd.DataFrame(checkResults, columns=['matchId', 'match', 'stat', 'overallWin', 'predictedHomeStat',
    # 'predictedMaxHomeStat',
    'predictedAwayStat',
    # 'predictedMaxAwayStat',
    'homeWin', 'awayWin'])
    lostBets = checkResultsDf.loc[checkResultsDf['overallWin'] == False, ['matchId']].drop_duplicates().values.tolist()
    lostBets = [item for sublist in lostBets for item in sublist]
    totallyWonBets = checkResultsDf.loc[~(checkResultsDf['matchId'].isin(lostBets))].reset_index()
    # print(checkResultsDf)
    print(f"Would have won {math.ceil(totallyWonBets['matchId'].nunique()/(totallyWonBets['matchId'].nunique() + len(lostBets))*1000.0)/10}% with nonTeamWeighted as {nonTeamWeighted}")
    return -(totallyWonBets['matchId'].nunique()/(totallyWonBets['matchId'].nunique() + len(lostBets))*100.0)


if __name__ == '__main__':
    res = minimize_scalar(test_predictions,  method='bounded', bounds=(0.5, 1.0))
    print(f"The optimal nonTeamWeighted config is {res.x}")