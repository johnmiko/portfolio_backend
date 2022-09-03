from dota.ease_of_use import pdf

print_cols = ['title', 'time_ago']


def print_highlights_df(df, cols, rows=10):
    print()
    cols2 = print_cols
    cols2.extend(cols)
    df = df.sort_values('highlights_score', ascending=False)
    df = df.set_index('match_id')
    print('highlights df')
    pdf(df[cols2].head(rows))
    print()


def print_whole_game_df(df, cols, rows=5):
    print()
    cols2 = print_cols
    cols2.extend(cols)
    print('whole game df')
    df = df.sort_values('whole_game_score', ascending=False)
    df = df.set_index('match_id')
    pdf(df[cols2].head(rows))
    print()
