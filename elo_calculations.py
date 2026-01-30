import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import plotly.express as px


# Read in all CSV files and combine into a single DataFrame
months = ['march','april','may','june','july','aug','sep']
numbers = ['1','2','3','4','5','6']
combined_df = pd.DataFrame()
counter = 0 #should end up at 34
for month in months: 
    for number in numbers:
        try: 
            current_df = pd.read_csv(f'{month}{number}.csv')

            # remove any rows where 'events' column is null 
            current_df = current_df[current_df['events'].notnull()] 

            combined_df = pd.concat([combined_df, current_df], ignore_index=True)
            counter += 1
        except: 
            continue 

#read in park factors df
park_factors_df = pd.read_csv('park_factors.csv')
park_factors_df['Park Factor'] = park_factors_df['Park Factor'] / 100

#read in wRC+ and era+ df 

# read in 2025 zips projections df

# drop duplicates from combined_df
combined_df = combined_df.drop_duplicates() 

# remove unnecessary columns from combined_df 
cols = ['game_date', 'batter','pitcher','events','estimated_ba_using_speedangle',
        'estimated_woba_using_speedangle','woba_value','woba_denom','at_bat_number',
        'estimated_slg_using_speedangle', 'home_team']

#combined_df_big = combined_df.copy()
combined_df = combined_df[cols]

# order combined_df chronologically (date, at_bat_number) 
combined_df = combined_df.sort_values(by=['game_date','at_bat_number'], ascending=[True, True]).reset_index(drop=True)

# read in marels data 
#marcels_pitchers = pd.read_csv('pitchers_marcels_pre_2025.csv')
#marcels_batters = pd.read_csv('batters_marcels_pre_2025.csv')

# calculate weighted average leage era and ops dependend on ip and pa
#average_era = (marcels_pitchers['ERA'] * marcels_pitchers['IP']).sum() / marcels_pitchers['IP'].sum()
#average_ops = (marcels_batters['OPS'] * marcels_batters['PA']).sum() / marcels_batters['PA'].sum()

#marcels_pitchers['era-'] = (average_era - marcels_pitchers['ERA']) * (marcels_pitchers['IP'] / marcels_pitchers['IP'].sum())
#marcels_batters['ops+'] = (marcels_batters['OPS'] - average_ops) * (marcels_batters['PA'] / marcels_batters['PA'].sum())

# future idea: benchmark by using these instead of just assuming 1500 

# create pitcher_df and hitter_df with all unique player_ids, and standard starting ELOs
pitcher_df = pd.DataFrame({'player_id': combined_df['pitcher'].unique(), 'elo': 1500.00, 'count': 0})
batter_df = pd.DataFrame({'player_id': combined_df['batter'].unique(), 'elo': 1500.00, 'count': 0})

# Loop through all events, applying the ELO rating adjustments to the pitchers and the hitters
#Version 1: hit is a win, out is a loss (for the hitter) (like chess)
combined_df['woba_value'] = combined_df['woba_value'].fillna(0)
combined_df['binary_outcome'] = np.where(combined_df['woba_value'] > 0, 1, 0)

# if events = strikeout, make the woba_value -0.5 (worse than normal out)
combined_df.loc[combined_df['events'] == 'strikeout', 'woba_value'] = -0.7

# min/max scale woba by adding 0.5, then doing proper scaling 
combined_df['woba_add_0.5'] = combined_df['woba_value'] + 0.7
woba_min = combined_df['woba_add_0.5'].min()
woba_max = combined_df['woba_add_0.5'].max()
combined_df['woba_norm'] = (combined_df['woba_add_0.5'] - woba_min) / (woba_max - woba_min)

examples = combined_df[['events','woba_norm']].drop_duplicates().reset_index(drop=True).sort_values(by='woba_norm', ascending=False)
examples2 = combined_df[['events','woba_value']].drop_duplicates().reset_index(drop=True).sort_values(by='woba_value', ascending=False)

examples3 = examples.copy()
examples3['value'] = examples3['woba_norm'].round(2)

_progress_thresholds = [i/10 for i in range(1, 11)]
_progress_printed = set()
print("Starting loop!")
for index, row in combined_df.iterrows():

    #print statement (just once!) whenever we eclipse 10%, 20%, etc. 
    progress = (index + 1) / len(combined_df)

    # print once when crossing each threshold (10%, 20%, ..., 100%)
    for t in _progress_thresholds:
        if progress >= t and t not in _progress_printed:
            print(f"Progress: {int(t*100)}% reached ({index+1}/{len(combined_df)})")
            _progress_printed.add(t)
            break

    #Get home team 
    home_team = row['home_team']

    #get park factor from park_factors_df
    park_factor = park_factors_df.loc[park_factors_df['Team'] == home_team, 'Park Factor'].values[0]

    # Get the current batter and pitcher
    batter = row['batter']
    batter_elo = batter_df.loc[batter_df['player_id'] == batter, 'elo'].values[0]
    batter_count = batter_df.loc[batter_df['player_id'] == batter, 'count'].values[0]
    batter_k_factor = 0 

    # k factor based on sample size (consider adjusting!)
    # 30 games is considered the chess sample size, so 30*4 = 120 at bats
    # if a player has played 30 games, we just keep the k factor at 20 
    if batter_count <= 120:
        batter_k_factor = 40
    #elif batter_elo <= 2400:
    #    batter_k_factor = 20
    else:
        batter_k_factor = 20

    pitcher = row['pitcher']
    pitcher_elo = pitcher_df.loc[pitcher_df['player_id'] == pitcher, 'elo'].values[0]
    pitcher_count = pitcher_df.loc[pitcher_df['player_id'] == pitcher, 'count'].values[0]
    pitcher_k_factor = 0

    # k factor based on sample size (consider adjusting!)
    # 30 games is considered the chess sample size, so 30*4 = 120 at bats
    # we do 4 as well here for pitchers, even though this is not accurate for SP
    # if a player has played 30 games, we just keep the k factor at 20
    if pitcher_count <= 120:
        pitcher_k_factor = 40
    #elif pitcher_elo <= 2400:
    #    pitcher_k_factor = 20
    else:
        pitcher_k_factor = 20

    # Get the outcome of the event
    outcome_binary = row['binary_outcome']
    outcome_woba = row['woba_value']
    outcome_woba_norm = row['woba_norm']

    # Apply ELO adjustments based on the outcome and based on the ELO difference
    difference = pitcher_elo - batter_elo
    value1 = difference / 400
    value2 = (10**value1)+1
    expected_batter = 1 / value2
    expected_batter = expected_batter * park_factor  # adjust expectation by park factor
    if expected_batter > 1: 
        expected_batter = 1 
        print("HAD TO CLIP AN EXPECTATION")
    expected_pitcher = 1 - expected_batter

    batter_change = batter_k_factor * (outcome_woba_norm - expected_batter)
    pitcher_change = pitcher_k_factor * ((1-outcome_woba_norm)-expected_pitcher)

    batter_df.loc[batter_df['player_id'] == batter, 'elo'] += batter_change
    pitcher_df.loc[pitcher_df['player_id'] == pitcher, 'elo'] += pitcher_change

    batter_df.loc[batter_df['player_id'] == batter, 'count'] += 1
    pitcher_df.loc[pitcher_df['player_id'] == pitcher, 'count'] += 1

    # I think negative ELO is technically ok...
    #print warning if either ELO goes into the negative
    #if batter_df.loc[batter_df['player_id'] == batter, 'elo'].values[0] < 0:
        #print(f"Warning: Batter ELO for {batter} is negative!")
    #if pitcher_df.loc[pitcher_df['player_id'] == pitcher, 'elo'].values[0] < 0:
        #print(f"Warning: Pitcher ELO for {pitcher} is negative!")

# read in player names
id_map = pd.read_csv('playerid_map.csv')
id_map = id_map[['MLBID', 'MLBNAME', 'TEAM', 'FANGRAPHSNAME']]


# merge player names
batter_df = pd.merge(batter_df, id_map, left_on='player_id', right_on='MLBID', how='left')
pitcher_df = pd.merge(pitcher_df, id_map, left_on='player_id', right_on='MLBID', how='left')

wrc_df = pd.read_csv('wrc_plus.csv')
wrc_df = wrc_df.dropna()
wrc_df['is_qualified'] = wrc_df['PA'] >= 502

batter_df = pd.merge(batter_df, wrc_df, left_on='FANGRAPHSNAME', right_on='Name', how='inner')

era_df = pd.read_csv('era_minus.csv')
era_df = era_df.dropna()
era_df['is_qualified'] = era_df['IP'] >= 162

pitcher_df = pd.merge(pitcher_df, era_df, left_on='FANGRAPHSNAME', right_on='Name', how='inner')

#ELO plus column explanations
# elo is standard, based at 1500 like chess 
# elo_adjusted is used to bump negatives to zero (if necessary)
# elo+ standardizes elo using league averages
# elo_adjusted2 sets the minimums to zero (ASSUMING NO NEGATIVES)
# elo+2 standardizes using league averages after setting minimums to zero 
# elo+_wrc makes the necessary adjustments to set the qualified elo+_wrc min and max at the wrc+ min and max for comparision 


# first, get the mins 
batter_elo_min = batter_df['elo'].min()
pitcher_elo_min = pitcher_df['elo'].min()

if batter_elo_min >= 0: 
    batter_elo_min = 0 
else: 
    print("WARNING, NEGATIVE BATTER ELO")
if pitcher_elo_min >= 0: 
    pitcher_elo_min = 0 
else: 
    print("WARNING, NEGATIVE PITCHER ELO")

#elo_adjusted column to eliminate negatives
batter_df['elo_adjusted'] = batter_df['elo'] + abs(batter_elo_min)
pitcher_df['elo_adjusted'] = pitcher_df['elo'] + abs(pitcher_elo_min)

#weighted averages for batter and pitcher elos: 
average_batter_elo = (batter_df['elo_adjusted'] * batter_df['count']).sum() / batter_df['count'].sum()
average_pitcher_elo = (pitcher_df['elo_adjusted'] * pitcher_df['count']).sum() / pitcher_df['count'].sum()

batter_df['elo+'] = (batter_df['elo_adjusted'] / average_batter_elo) * 100
pitcher_df['elo+'] = (pitcher_df['elo_adjusted'] / average_pitcher_elo) * 100

#make the worst zero 
batter_df['elo_adjusted2'] = batter_df['elo'] - batter_df['elo'].min()
pitcher_df['elo_adjusted2'] = pitcher_df['elo'] - pitcher_df['elo'].min()

#now calculate the weighted averages 
batter_adjusted2_mean = (batter_df['elo_adjusted2'] * batter_df['count']).sum() / batter_df['count'].sum()
pitcher_adjusted2_mean = (pitcher_df['elo_adjusted2'] * pitcher_df['count']).sum() / pitcher_df['count'].sum()

#elo+2
batter_df['elo+2'] = (batter_df['elo_adjusted2'] / batter_adjusted2_mean) * 100
pitcher_df['elo+2'] = (pitcher_df['elo_adjusted2'] / pitcher_adjusted2_mean) * 100

# elo+_wrc makes the necessary adjustments to set the qualified elo+_wrc min and max at the wrc+ min and max for comparision 
qualified_batters = batter_df[batter_df['is_qualified'] == True]
min_wrc_plus = qualified_batters['WRC+'].min()
max_wrc_plus = qualified_batters['WRC+'].max()
min_elo = qualified_batters['elo'].min()
max_elo = qualified_batters['elo'].max()

batter_df['elo+_wrc'] = ((batter_df['elo'] - min_elo) / (max_elo - min_elo)) * (max_wrc_plus - min_wrc_plus) + min_wrc_plus

#do the same with pitchers and era-
qualified_pitchers = pitcher_df[pitcher_df['is_qualified'] == True]
min_era = qualified_pitchers['ERA-'].min()
max_era = qualified_pitchers['ERA-'].max()
min_elo = qualified_pitchers['elo'].min()
max_elo = qualified_pitchers['elo'].max()

pitcher_df['elo+_era'] = ((pitcher_df['elo'] - min_elo) / (max_elo - min_elo)) * (max_era - min_era) + min_era

#sort best to worst 
batter_df_sorted = batter_df.sort_values(by='elo', ascending=False).reset_index(drop=True)
pitcher_df_sorted = pitcher_df.sort_values(by='elo', ascending=False).reset_index(drop=True)

# check out how this stat treats tommy pham 
tommy_pham = batter_df_sorted[batter_df_sorted['MLBNAME'] == 'Tommy Pham']
print(f"Tommy Pham's ELO+ from 2025 is: {tommy_pham['elo+'].values[0]} or {tommy_pham['elo+2'].values[0]} or {tommy_pham['elo+_wrc'].values[0]}, compared to an OPS+ of 95, and a wRC+ of 94")

# plot wrc+ by elo+_wrc+ for qualified hitters
#make the plots so that if you hover over the point the name pops up 
qualified_batters = batter_df_sorted[batter_df_sorted['is_qualified'] == True]

try: 
    plt.scatter(qualified_batters['elo+_wrc'], qualified_batters['WRC+'])
    plt.xlabel("ELO+_WRC+")
    plt.ylabel("WRC+")
    plt.title("WRC+ by ELO+_WRC+ for Qualified Hitters")
    plt.show()

    # save figure
    plt.savefig("wrc_plus_by_elo_plus_wrc_plus.png")
except: 
    print("Couldn't plot hitters")

# do the same for pitchers 
qualified_pitchers = pitcher_df_sorted[pitcher_df_sorted['is_qualified'] == True]
try: 
    plt.scatter(qualified_pitchers['elo+_era'], qualified_pitchers['ERA-'])
    plt.xlabel("ELO+_ERA-")
    plt.ylabel("ERA-")
    plt.title("ERA- by ELO+_ERA- for Qualified Pitchers")
    plt.show()

    # save figure
    plt.savefig("era_minus_by_elo_plus_era_minus.png")
except: 
    print("Couldn't plot pitchers")

#plot where I can scroll over names
try: 
    fig = px.scatter(
        qualified_batters,
        x='elo+_wrc',
        y='WRC+',
        hover_name='MLBNAME',
        hover_data=['player_id','elo','elo+','TEAM'],
        title='WRC+ by ELO+_WRC+ for Qualified Hitters',
        labels={'elo+_wrc':'ELO+_WRC+','WRC+':'WRC+'}
    )
    fig.update_traces(marker=dict(size=8, opacity=0.85))
    fig.show()

    # save figure
    fig.write_image("wrc_plus_by_elo_plus_wrc_plus.png")
except: 
    print("Couldn't plot hitters scrollable")

try: 
    fig = px.scatter(
        qualified_pitchers,
        x='elo+_era',
        y='ERA-',
        hover_name='MLBNAME',
        hover_data=['player_id','elo','elo+','TEAM'],
        title='ERA- by ELO+_ERA- for Qualified Pitchers',
        labels={'elo+_era':'ELO+_ERA-','ERA-':'ERA-'}
    )
    fig.update_traces(marker=dict(size=8, opacity=0.85))
    fig.show()

    # save figure
    fig.write_image("era_minus_by_elo_plus_era_minus.png")
except: 
    print("Couldn't plot pitchers scrollable")

# write.csv 
batter_df_sorted.to_csv('improved_batter_elo_ratings_park_factored.csv', index=False)
pitcher_df_sorted.to_csv('improved_pitcher_elo_ratings_park_factored.csv', index=False)
# NEXT THINGS TO TRY: 
# add park factor (multiple expectation by factor/100)
# scale ELO+ better (with wRC+) by making the best qualified and worst qualified the same as wRC+
# download wrc+, era- merge, and plot 
# adjust initial conditions (k-values, starting point, dynamic starting point?
# do one for xwoba
# start initial ELO lower? higher?
# consider glicko or glicko-2 algorithm
# benchmark starting ELOs with career ERA, or projected ERA+ and wRC+ (Fangraphs/ZIPS) 


#adjusted elo v2

