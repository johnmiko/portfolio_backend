import statistics
from datetime import datetime

import numpy as np
import pandas as pd
import requests


def calc_gold_adv_rate(df, i):
    radiant_gold_adv = df.loc[i, 'radiant_gold_adv']
    if radiant_gold_adv is None:
        df.loc[i, 'gold_adv_rate'] = np.nan
    else:
        df.loc[i, 'gold_adv_rate'] = round(abs(radiant_gold_adv[-1]) / df.loc[i, 'duration'], 2)
    return df


# Not really useful this guy
def calc_gold_adv_std(df, i):
    df.loc[i, 'radiant_gold_adv_std'] = statistics.stdev(df.loc[i, 'radiant_gold_adv'][:-5])
    return df


def calc_min_in_lead(df, i):
    radiant_gold_adv = df.loc[i, 'radiant_gold_adv']
    sign_changes = list((np.diff(np.sign(radiant_gold_adv)) != 0) * 1)
    sign_changes.reverse()
    try:
        # The values of the list are at minute points, so can just get the index to know how many minutes
        df.loc[i, 'min_in_lead'] = sign_changes.index(1)
    except ValueError:
        radiant_always_winning = (df.loc[i, 'radiant_win'] & (df.loc[i, 'radiant_gold_adv'][-1] > 0))
        dire_always_winning = ((df.loc[i, 'radiant_win'] == False) & (df.loc[i, 'radiant_gold_adv'][-1] < 0))
        winning_entire_game = radiant_always_winning | dire_always_winning
        if winning_entire_game:
            df.loc[i, 'min_in_lead'] = len(sign_changes)
        else:
            df.loc[i, 'min_in_lead'] = 0
    return df


def calc_max_gold_swing(df, i):
    # want to find the largest change in values from max value to any value after that
    max_swing = 0
    for j in range(10, len(df.loc[i, 'radiant_gold_adv']) - 1):
        # Find max net worth change that has occured in the past 10 minutes
        # Set value to 11 instead of 10 because of indexing
        max_window = 11
        indices_left = len(df.loc[i, 'radiant_gold_adv'][j + 1:]) + 1
        window = indices_left if indices_left < max_window else max_window
        val = df.loc[i, 'radiant_gold_adv'][j]
        if abs(val) < 5000:
            continue
        if val > 0:
            min_val = min(df.loc[i, 'radiant_gold_adv'][j + 1:j + window])
            if min_val < 0:
                min_val = 0
            swing = val - min_val
            # dif = val - min(df.loc[i, 'radiant_gold_adv'][j + 1:j + max_window])
        else:
            try:
                max_val = max(df.loc[i, 'radiant_gold_adv'][j + 1:j + window])
            except:
                a = 1
            if max_val > 0:
                max_val = 0
            swing = val - max_val

        if abs(swing) > max_swing:
            max_swing = abs(swing)
    df.loc[i, 'swing'] = max_swing
    return df


def calc_game_num(df):
    df.sort_values('date').groupby('series_id')
    df['game_num'] = df.groupby('series_id')['date'].rank('min')
    return df


def calc_teamfight_stats(df, i):
    teamfights = df.loc[i, 'teamfights']
    # num_teamfights = len(teamfights)
    secs_of_fighting = 0
    first_fight_at_in_secs = 100000
    for fight in teamfights:
        secs_of_fighting += fight['end'] - fight['start']
        if fight['start'] < first_fight_at_in_secs:
            first_fight_at_in_secs = fight['start']
    df.loc[i, 'first_fight_at'] = str(first_fight_at_in_secs // 60) + ':' + str(first_fight_at_in_secs % 60)
    df.loc[i, 'fight_%_of_game'] = secs_of_fighting / (df.loc[i, 'duration'] - first_fight_at_in_secs)
    return df


def get_date_stuff(df):
    df['start_time'] = df['start_time'].fillna(0)
    df['date'] = pd.to_datetime(df['start_time'], unit='s')
    # Not accounting for UTC
    df2 = pd.DataFrame()
    df2['dif'] = datetime.now() - df['date']
    df2['time_ago'] = None
    df2.loc[df2['dif'].dt.days < 7, 'time_ago'] = df2['dif'].dt.days.astype(str) + ' days ago'
    df2.loc[df2['dif'].dt.days == 0, 'time_ago'] = \
        (df2['dif'].dt.seconds / 3600).astype(int).astype(str) + ' hours ago'
    df2.loc[df2['dif'].dt.days >= 7, 'time_ago'] = \
        (df2['dif'].dt.days / 7).astype(int).astype(str) + ' weeks ago'
    df2['months_ago'] = ((df2['dif']) / np.timedelta64(1, 'M')).astype(int)
    df2.loc[df2['months_ago'] > 0, 'time_ago'] = df2['months_ago'].astype(str) + ' months ago'
    df['time_ago'] = df2['time_ago']
    return df


def get_team_names(df):
    teams_url = 'https://api.opendota.com/api/teams'
    r = requests.get(teams_url)
    teams_raw = r.json()
    df_teams = pd.DataFrame(teams_raw)
    df = df.merge(df_teams[['team_id', 'name']], how='left', left_on='dire_team_id', right_on='team_id')
    df = df.merge(df_teams[['team_id', 'name']], how='left', left_on='radiant_team_id', right_on='team_id')
    df['dire_team_name'] = df['name']
    df['radiant_team_name'] = df['name_y']
    df['tournament'] = df['name_x']
    return df


def create_title(df):
    # Remove text after 'presented' and/or 'powered'
    df[['radiant_team_name', 'dire_team_name', 'game_num', 'tournament']] = \
        df[['radiant_team_name', 'dire_team_name', 'game_num', 'tournament']].fillna('???')
    df['tournament'] = df['tournament'].str.split('presented').str[0].str.split('powered').str[0].str.strip()
    df['title'] = df['radiant_team_name'] + ' vs ' + df['dire_team_name'] + ' game ' + df['game_num'].astype(
        int).astype(str) + ' ' + df['tournament']
    return df


def calc_game_is_close(df, i):
    radiant_gold_adv = df.loc[i, 'radiant_gold_adv']
    lead_is_small = sum(abs(i) < 5000 for i in radiant_gold_adv)
    pct_lead_small = lead_is_small / len(radiant_gold_adv)
    df.loc[i, 'lead_is_small'] = pct_lead_small
    return df
