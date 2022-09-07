import numpy as np
import pandas as pd
import requests

from constants import DOTA_DIR
from dota.dota.calcs import calc_teamfight_stats, calc_gold_adv_rate, calc_gold_adv_std, calc_min_in_lead, \
    calc_max_gold_swing, calc_game_is_close, get_team_names, get_date_stuff, create_title, calc_game_num
from dota.dota.score import linear_map
from dota.dota.utils import create_highlights_df


def get_interesting_games():
    url = 'https://api.opendota.com/api/proMatches'

    # what makes a game interesting?
    # big gold swings - check
    # lots of kills - check
    # close game (gold dif close to 0 for a long time)
    #     not quite the same as min_in_lead
    #  min_in_lead - can add in caveat, check for how long they've been in the lead < 5K gold
    #      if they are only in the lead by a little bit, could still be interesting
    url = """https://api.opendota.com/api/explorer?sql=SELECT
    matches.match_id,
    matches.start_time,
    ((player_matches.player_slot < 128) = matches.radiant_win) win,
    player_matches.hero_id,
    player_matches.account_id,
    leagues.name leaguename
    FROM matches
    JOIN match_patch using(match_id)
    JOIN leagues using(leagueid)
    JOIN player_matches using(match_id)
    JOIN heroes on heroes.id = player_matches.hero_id
    LEFT JOIN notable_players ON notable_players.account_id = player_matches.account_id
    LEFT JOIN teams using(team_id)
    WHERE TRUE
    AND match_patch.patch >= '7.16'
    AND ((player_matches.purchase->>'rapier')::int > 0)
    AND matches.start_time >= extract(epoch from timestamp '2022-05-01T04:00:00.000Z')
    AND leagues.tier = 'premium'
    AND teams.team_id IN (15, 36, 39, 2163, 111474, 350190, 543897, 726228, 1838315, 1883502, 2108395, 2586976, 2626685, 2672298, 6209804, 6214538, 6214973, 7203342)
    AND ((matches.barracks_status_radiant = 0 AND matches.radiant_win) OR (matches.barracks_status_dire = 0 AND NOT matches.radiant_win))
    AND @ matches.radiant_gold_adv[array_upper(matches.radiant_gold_adv, 1)] >= 0
    ORDER BY matches.match_id NULLS LAST
    LIMIT 100"""
    limit = '500'
    # limit = '50'
    # premium is pro matches
    # professional = ???
    # ti9_teams = teams.team_id IN (15, 36, 39, 2163, 111474, 350190, 543897, 726228, 1838315, 1883502, 2108395, 2586976,2626685, 2672298, 6209804, 6214538, 6214973, 7203342)
    # JOIN leagues using(leagueid)
    url = f"""https://api.opendota.com/api/explorer?sql=SELECT * 
    FROM matches
    JOIN leagues using(leagueid)
    WHERE leagues.tier = 'premium'
    AND name not like '%Division II%'
    ORDER BY matches.start_time DESC
    LIMIT {limit}"""
    # JOIN match_patch using(match_id)
    # LEFT JOIN teams on teams.team_id = dire_team_id or teams.team_id = radiant_team_id
    # WHERE matches.start_time >= extract(epoch from timestamp '{oldest_date}T0:00:00.000Z')
    r = requests.get(url, timeout=45)
    if r.status_code != 200:
        print(r.text)
    matches = r.json()['rows']
    df_raw = pd.DataFrame(matches)
    df_raw['start_time'] = df_raw['start_time'].fillna(0)
    df_raw['date'] = pd.to_datetime(df_raw['start_time'], unit='s')
    df = df_raw
    # Remove div 2 games for now. Just give them a weight at some point and keep them in
    # Or give weights to average mmr of the team or something
    # Or specific teams give higher weights
    # For example I like watching Nigma, Tundra
    df['name'] = df['name'].fillna('')
    df = df[~df['name'].str.contains('Division II')]
    # df['div_1'] = ~df['name'].str.contains('Division II')
    # df['div_score'] = df.loc[df['div_1'] == True, 'div_1_score'] = 1
    # df['div_score'] = df.loc[df['div_1'] == False, 'div_1_score'] = 0

    # Remove games I've already watched, manually updated?
    # Easier, is to make myself a GUI, then click a button to say I watched that game already
    # try:
    df_watched = pd.read_csv(DOTA_DIR + 'text/already_watched.txt', header=0)
    # except FileNotFoundError:
    #     open('../text/already_watched.txt', 'a').close()
    df_watched = pd.DataFrame(columns=['match_id', 'last_watched_on', 'times_watched'])
    df = df[~df['match_id'].isin(df_watched['match_id'])]

    df['total_kills'] = df['radiant_score'] + df['dire_score']
    df['duration_min'] = (df['duration'] / 60).round()
    df['kills_per_min'] = df['total_kills'] / df['duration_min']
    df = get_team_names(df)
    df = get_date_stuff(df)
    df = calc_game_num(df)
    df = create_title(df)
    df[['gold_adv_rate', 'radiant_gold_adv_std', 'swing', 'fight_%_of_game', 'lead_is_small']] = None
    # df = linear_map(df, 'cci', 'rel cci', min_cci, max_cci, -1, 1)
    for i, row in df.iterrows():
        # radiant_gold_adv = df.loc[i, 'radiant_gold_adv']
        teamfights = df.loc[i, 'teamfights']
        if teamfights is None:
            df.loc[i, 'first_fight_at'] = 10000
            df.loc[i, 'fight_%_of_game'] = 0
        else:
            df = calc_teamfight_stats(df, i)
        radiant_gold_adv = df.loc[i, 'radiant_gold_adv']
        if radiant_gold_adv is None:
            df.loc[i, 'radiant_gold_adv_std'] = np.nan
            df.loc[i, 'gold_adv_rate'] = 100
            df.loc[i, 'min_in_lead'] = 100
            df.loc[i, 'swing'] = 0
            df.loc[i, 'lead_is_small'] = 0

        else:
            df = calc_gold_adv_rate(df, i)
            df = calc_gold_adv_std(df, i)
            df = calc_min_in_lead(df, i)
            df = calc_max_gold_swing(df, i)
            df = calc_game_is_close(df, i)
    df['swing'] = df['swing'].astype(int)
    df['lead_is_small'] = df['lead_is_small'].astype(float)

    col = 'min_in_lead'
    df = linear_map(df, col, f'{col}_score', 5, 10, 1, 0)
    df.loc[df[col] > 10, f'{col}_score'] = 0
    df.loc[df[col] < 5, f'{col}_score'] = 1

    col = 'duration_min'
    df = linear_map(df, col, f'{col}_score', 45, 65, 0, 1)
    df.loc[df[col] < 45, f'{col}_score'] = 0
    df.loc[df[col] > 65, f'{col}_score'] = 1

    col = 'kills_per_min'
    df = linear_map(df, col, f'{col}_score', 0.5, 2, 0, 1)
    df.loc[df[col] < 0.5, f'{col}_score'] = 0
    df.loc[df[col] > 2, f'{col}_score'] = 1

    col = 'lead_is_small'
    df.loc[df[col] == 1, col] = 0
    df = linear_map(df, col, f'{col}_score', 0.5, 1, 0, 1)
    df.loc[df[col] < 0.5, f'{col}_score'] = 0

    col = 'swing'
    df = linear_map(df, col, f'{col}_score', 7000, 12000, 0, 1)
    df.loc[df[col] < 7000, f'{col}_score'] = 0
    df.loc[df[col] > 12000, f'{col}_score'] = 1
    df['win_team_barracks_lost'] = 63 - np.where(df['radiant_win'] == True, df['barracks_status_radiant'],
                                                 df['barracks_status_dire'])
    df['win_team_barracks_dif'] = np.where(df['radiant_win'] == True,
                                           df['barracks_status_radiant'] - df['barracks_status_dire'],
                                           df['barracks_status_dire'] - df['barracks_status_radiant'])
    score_col = 'barracks_comeback_score'
    df = linear_map(df, 'win_team_barracks_dif', score_col, -36, 63, 0.8, 0)
    df.loc[df['win_team_barracks_dif'] < -36, score_col] = 1
    df.loc[df['win_team_barracks_lost'] == 63, score_col] = 1  # megacreeps comeback

    df['boring'] = (df['lead_is_small'] < 0.7) & (df['swing'] < 5000)
    # df = df[~df['boring']]

    highlights_score = ['lead_is_small_score', 'min_in_lead_score', 'duration_min_score', 'swing_score',
                        'barracks_comeback_score']
    whole_game_score = ['kills_per_min_score', 'swing_score', 'fight_%_of_game']
    # df['highlights_score'] = df[highlights_score].max(axis=1).round(2)
    df['highlights_score'] = df[highlights_score].sum(axis=1).round(2)
    df['whole_game_score'] = df[whole_game_score].max(axis=1).round(2)
    df.loc[
        (df[['radiant_team_name', 'dire_team_name']] == '???').any(axis=1), ['highlights_score', 'whole_game_score']] = \
        df[['highlights_score', 'whole_game_score']] / 2
    whole_game_cols = ['whole_game_score', 'kills_per_min_score', 'fight_%_of_game', 'first_fight_at']
    highlight_cols = ['highlights_score', 'lead_is_small_score', 'min_in_lead', 'min_in_lead_score', 'duration_min',
                      'duration_min_score', 'swing',
                      'swing_score', 'win_team_barracks_dif',
                      'barracks_comeback_score']
    df = df.sort_values('highlights_score')
    df_highlights = create_highlights_df(df, highlight_cols)
    # print_highlights_df(df, highlight_cols)
    # df2 = df.sort_values('highlights_score')
    # print_whole_game_df(df2, whole_game_cols)
    return df_highlights
