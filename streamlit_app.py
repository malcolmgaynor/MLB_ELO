import pandas as pd
import numpy as np 
import streamlit as st
import plotly.express as px

st.set_page_config(page_title="ELO: Chess-Inspired MLB Rating System", layout="wide", page_icon="⚾")

# Title and subtitle
st.title("ELO: A Chess-Inspired MLB Player Rating System")
st.subheader("In response to \"PhamGraphs\"")

# LinkedIn link in top right
col1, col2 = st.columns([0.95, 0.05])
with col2:
    st.markdown("""
    <a href="https://www.linkedin.com/in/malcolm-gaynor/" target="_blank">
        <img src="https://cdn-icons-png.flaticon.com/512/174/174857.png" width="40">
    </a>
    """, unsafe_allow_html=True)

# Load data
@st.cache_data
def load_data():
    batters = pd.read_csv('improved_batter_elo_ratings_park_factored1.csv')
    pitchers = pd.read_csv('improved_pitcher_elo_ratings_park_factored1.csv')
    batters["ELO+"] = batters['elo+2'].round().astype(int)
    pitchers["ELO+"] = pitchers['elo+2'].round().astype(int)
    batters["PAs"] = batters['count']
    pitchers["PAs"] = pitchers['count']
    batters = batters[['Name', 'TEAM', 'ELO+', 'WRC+', 'PAs', 'is_qualified']]
    pitchers = pitchers[['Name', 'TEAM', 'ELO+', 'ERA-', 'PAs','is_qualified']]
    return batters, pitchers

batters, pitchers = load_data()
batters_q = batters[batters['is_qualified'] == True]
pitchers_q = pitchers[pitchers['is_qualified'] == True]

# Create tabs
tab1, tab2, tab3 = st.tabs(["Summary", "Results", "Methodology"])

# ============ TAB 1: SUMMARY ============
with tab1:
    st.header("Summary")
    st.markdown("""
    On January 5th, 2026, in an [article](https://www.nytimes.com/athletic/6940461/2026/01/05/mlb-free-agency-metrics-tommy-pham/)
    with The Athletic, Tommy Pham brought up the issue that most comprehensive baseball metrics to value hitters (like OPS+, wRC+, etc.)
    do not take into account opponent strength. Specifically, Pham argued that in his 2025 season with the Pirates, he faced more top tier 
    pitching than a player on an elite team would. This is because teams with worse records more often face the opponents top bullpen arms and closers. 
                
    To attempt to take this into account, I created a statistic based on the ELO chess rankings. In chess, each player has an ELO rating, which is increased or
    decreased incrementally based on the match results and the difference in ELO between the two players. In baseball terms, that means that hitting a home run 
    against Tarik Skubal would boost a batter's ELO more than hitting a home run off of Kiké Hernández.

    Using [Savant Search](https://baseballsavant.mlb.com/statcast_search), I compiled every plate appearance in the 2025 MLB season. Just like in chess, I initialized
    each batter and pitcher at the same ELO, and updated it accordingly after each plate appearance, also taking into account [park factors](https://baseballsavant.mlb.com/leaderboard/statcast-park-factors?type=year&year=2025&batSide=&stat=index_wOBA&condition=All&rolling=1&parks=mlb).
    Then, I normalized ELO to a similar scale as wRC+, which I took from [Fangraphs](https://www.fangraphs.com/leaders-legacy.aspx?pos=all&stats=bat&lg=all&qual=y&type=8&season=2025&month=0&season1=2025&ind=0&team=0&rost=0&age=0&filter=&players=0&startdate=&enddate=). For more details on the algorithm, see the methodology section. I will go into some of the major findings below, 
    but see the Results tab to view the full ELO+ ratings database from 2025. 
                
    Please don't hesitate to reach out with any questions or comments: malcolm.t.gaynor@gmail.com
    """)
    
    st.markdown("---")
    st.subheader("Graph of qualified hitters")
    st.write("""
    - **wRC+/ELO+ = 100** represents league-average performance, whereas above 100 and below 100 represent above and below average performance, respectively.
    - Both systems account for park factors, but only ELO+ takes opponent strength into consideration
    - Hitters who were above the dotted line had a better ELO+ than wRC+, and players below the dotted line had a better wRC+ than ELO+
    """)

    #show batters2.png
    #st.image("batters2.png")
    figb = px.scatter(
        batters_q,
        x='WRC+',
        y='ELO+',
        hover_name='Name',
        title='ELO+ compared to wRC+ in 2025'
    )
    figb.add_shape(
        type="line",
        x0=0, y0=0,
        x1=max(batters_q['WRC+'].max(), batters_q['ELO+'].max()),
        y1=max(batters_q['WRC+'].max(), batters_q['ELO+'].max()),
        line=dict(color="gray", width=2, dash="dash")
    )

    #figb.show()
    st.plotly_chart(figb, use_container_width=True)
    

    st.markdown("---")
    st.subheader("Graph of qualified pitchers")
    st.write("""
    - **ELO+ = 100** represents league-average performance, whereas above 100 and below 100 represent above and below average performance, respectively.
    - **ERA-** is the opposite, where lower values indicate better performance. 100 is still league average. 
    - Both systems account for park factors, but only ELO+ takes opponent strength into consideration
    - Pitchers on the left half of the graph were better than league average in ERA-, and pitchers on the top half were better in league average in ELO+.
    """)

    #show batters2.png
    #st.image("pitchers2.png")

    figp = px.scatter(
        pitchers_q,
        x='ERA-',
        y='ELO+',
        hover_name='Name',
        title='ELO+ compared to ERA- in 2025'
    )

    figp.add_hline(y=100, line_dash="dash", line_color="gray")
    figp.add_vline(x=100, line_dash="dash", line_color="gray")

    st.plotly_chart(figp, use_container_width=True)
    #figp.show()

    st.write("---")
    st.subheader("Biggest changes when comparing ELO+ to wRC+ and ERA- for qualified players")
    st.write("Next, we will take a look at the ten qualified batters who had the greatest change in ELO+ compared to wRC+.")

    batters_q2 = batters_q.copy()
    batters_q2['ELO Change'] = batters_q2['ELO+'] - batters_q2['WRC+']
    batters_q2.drop(columns=['is_qualified'], inplace=True)
    batters_q2 = batters_q2.drop_duplicates()
    batters_q2_top = batters_q2.sort_values('ELO Change', ascending=False).reset_index(drop=True).head(10)
    batters_q2_bottom = batters_q2.sort_values('ELO Change', ascending=True).reset_index(drop=True).head(10)

    #display batters_q2_top and batters_q2_bottom next to each other (to the right and left of each other). Add a title as well 
    col1, col2 = st.columns(2)

    with col1:
        st.subheader("Top 10 Batters with higher ELO+ than wRC+")
        st.dataframe(batters_q2_top, hide_index=True)

    with col2:
        st.subheader("Top 10 Batters with lower ELO+ than wRC+")
        st.dataframe(batters_q2_bottom, hide_index=True)

    st.write("Now, we do the same for qualified pitchers. However, because ERA- and ELO+ are inversely related, we will look at the top 10 pitchers with the biggest difference in rank order. " \
    "In other words, we rank all pitchers by their ELO+ and ERA- values, and then compare the two rankings.")

    pitchers_q2 = pitchers_q.copy()
    pitchers_q2 = pitchers_q2.sort_values('ELO+', ascending=False).reset_index(drop=True)
    pitchers_q2['ELO rank'] = pitchers_q2.index + 1
    pitchers_q2 = pitchers_q2.sort_values('ERA-', ascending=True).reset_index(drop=True)
    pitchers_q2['ERA rank'] = pitchers_q2.index + 1
    pitchers_q2['ELO Ranking Change'] = pitchers_q2['ELO rank'] - pitchers_q2['ERA rank']
    pitchers_q2.drop(columns=['is_qualified'], inplace=True)
    pitchers_q2 = pitchers_q2.drop_duplicates()
    pitchers_q2_top = pitchers_q2.sort_values('ELO Ranking Change', ascending=False).reset_index(drop=True).head(10)
    pitchers_q2_bottom = pitchers_q2.sort_values('ELO Ranking Change', ascending=True).reset_index(drop=True).head(10)

    #display batters_q2_top and batters_q2_bottom next to each other (to the right and left of each other). Add a title as well 
    col1, col2 = st.columns(2)

    with col1:
        st.subheader("Top 10 Pitchers with better ELO rank than ERA rank")
        st.dataframe(pitchers_q2_bottom, hide_index=True)

    with col2:
        st.subheader("Top 10 Pitchers with worse ELO rank than ERA rank")
        st.dataframe(pitchers_q2_top, hide_index=True)


    st.write("---")
    st.subheader("Team Differences")
    st.write("Next, we will investigate the issue that Tommy Pham initially brought up. Specifically, \
            does playing on a worse team mean you face tougher competition, which would mean your ELO would \
            be inflated as compared to stats like wRC+ and ERA-?")

    #summarize ELO Change by Team in batters_q2 and pitchers_q2
    batters_team_summary = batters_q2.groupby('TEAM')['ELO Change'].mean().reset_index()
    pitchers_team_summary = pitchers_q2.groupby('TEAM')['ELO Ranking Change'].mean().reset_index()

    batters_team_summary = batters_team_summary.sort_values('ELO Change', ascending=False)
    pitchers_team_summary = pitchers_team_summary.sort_values('ELO Ranking Change', ascending=False)

    col1, col2 = st.columns(2)

    with col1: 
        st.subheader("Batters Team Summary (Qualified Hitters)")
        st.dataframe(batters_team_summary, hide_index=True)

    with col2:
        st.subheader("Pitchers Team Summary (Qualified Pitchers)")
        st.dataframe(pitchers_team_summary, hide_index=True)

    st.write("Looking at the data below, we see that, for teams with overal positive ELO change for qualified hitters (meaning ELO ranked hitters \
            more favorably than wRC+) there are only 3 playoff teams (Cincinnati, Milwaukee, and San Diego). This does seem to suggest that better teams \
            may not face as tough of competition, leading to lower ELO values compared to wRC+. On the pitching side of things, this impact is not as great. \
            In fact, the top three teams in ELO Ranking Change are all playoff teams (Chicago Cubs, San Diego, and Detroit)")

    st.write("---")
    st.subheader("Pittsburgh Pirates Hitters")
    st.write("Finally, we take a look at the Pirates, who interestingly enough actually had a negative ELO Change as a team for qualified hitters."\
            " This means that, overall, qualified hitters fared better by metrics like wRC+ than by ELO+. Here are all of the Pirates hitters in 2025:")

    # give a dropdown selector to either filter "qualified" or "all"
    filter_option = st.selectbox("Select filter:", ["All Hitters", "Qualified Hitters"])

    pirates_batters = batters[batters['TEAM'] == 'PIT']
    if filter_option == "Qualified Hitters":
        pirates_batters = pirates_batters[pirates_batters['is_qualified'] == True]



    pirates_batters['ELO Change'] = pirates_batters['ELO+'] - pirates_batters['WRC+']
    pirates_batters = pirates_batters[['Name', 'TEAM', 'ELO+', 'WRC+', 'ELO Change', 'PAs', 'is_qualified']]
    pirates_batters = pirates_batters.sort_values('PAs', ascending=False)
    st.dataframe(pirates_batters, hide_index=True)

    st.write("Despite being a few at bats from qualifying, Tommy Pham does have an above average ELO+ of 104, compared to his below average wRC+ of 95. \
            In his case, at least, it may be true that standard metrics are more pessimistic about his 2025 performance than they should be.")

    st.write("Also of note is Spencer Horwitz, who, despite also not qualifying by a slim margin, had an ELO+ of 169, which was actually the best of any hitter in 2025, even greater than the 165 mark of Aaron Judge.")
# ============ TAB 2: RESULTS ============
with tab2:
    st.header("Results")
    
    results_sub = st.selectbox("Select Batters or Pitchers:", ["Batter Results", "Pitcher Results"])
    
    if results_sub == "Batter Results":

        
        # Display batter table
        st.subheader("2025 Batter Results")

        
        batters_for_display = batters.copy()
        batters_for_display['ELO Change'] = batters_for_display['ELO+'] - batters_for_display['WRC+']
        batters_for_display = batters_for_display[['Name', 'TEAM', 'ELO+', 'WRC+', 'ELO Change', 'PAs', 'is_qualified']]
        batters_for_display = batters_for_display.sort_values('ELO+', ascending=False).reset_index(drop=True)
    

        qual = st.selectbox("Select qualified status:", ["Qualified", "All"])
        team_list = sorted([t for t in batters_for_display['TEAM'].unique() if pd.notna(t)])
        team_choice = st.selectbox("Select team:", [""] + team_list)

        search_name = st.text_input("Search player by name:")

        if search_name != "":
            batters_for_display = batters_for_display[batters_for_display['Name'].str.contains(search_name, case=False)]

        #pa limit
        pa_limit = st.slider("Select PA limit:", 0, 700, 100)
        batters_for_display = batters_for_display[batters_for_display['PAs'] >= pa_limit]

        if qual == "Qualified":
            batters_for_display = batters_for_display[batters_for_display['is_qualified'] == True]

        if team_choice != "":
            batters_for_display = batters_for_display[batters_for_display['TEAM'] == team_choice]

        if pa_limit > 0:
            batters_for_display = batters_for_display[batters_for_display['PAs'] >= pa_limit]

        st.dataframe(batters_for_display.reset_index(drop=True), use_container_width=True)


        #display_cols = ['Name', 'TEAM', 'ELO+', 'WRC+', 'elo', 'count']
        #batter_display = batters[[c for c in display_cols if c in batters.columns]].sort_values('ELO+', ascending=False)
        #st.dataframe(batter_display.head(20), use_container_width=True)
    
    else:  # Pitcher Results

        # Display pitcher table
        st.subheader("2025 Pitcher Results")
        
        pitchers_for_display = pitchers.copy()
        pitchers_for_display = pitchers_for_display.sort_values('ELO+', ascending=False).reset_index(drop=True)
        pitchers_for_display['ELO rank'] = pitchers_for_display.index + 1
        pitchers_for_display = pitchers_for_display.sort_values('ERA-', ascending=True).reset_index(drop=True)
        pitchers_for_display['ERA rank'] = pitchers_for_display.index + 1
        pitchers_for_display['ELO Ranking Change'] = pitchers_for_display['ELO rank'] - pitchers_for_display['ERA rank']
        pitchers_for_display = pitchers_for_display[['Name', 'TEAM', 'ELO+', 'ERA-', 'ELO Ranking Change', 'PAs', 'is_qualified']]
        pitchers_for_display = pitchers_for_display.sort_values('ELO+', ascending=False).reset_index(drop=True)
        
        qual_p = st.selectbox("Select qualified status:", ["Qualified", "All"], key="qual_pitcher")
        team_list_p = sorted([t for t in pitchers_for_display['TEAM'].unique() if pd.notna(t)])
        team_choice_p = st.selectbox("Select team:", [""] + team_list_p, key="team_pitcher")

        search_name_p = st.text_input("Search player by name:")

        if search_name_p != "":
            pitchers_for_display = pitchers_for_display[pitchers_for_display['Name'].str.contains(search_name_p, case=False)]

        # pa limit
        pa_limit_p = st.slider("Select IP limit:", 0, 300, 50, key="pa_pitcher")
        pitchers_for_display = pitchers_for_display[pitchers_for_display['PAs'] >= pa_limit_p]
        
        if qual_p == "Qualified":
            pitchers_for_display = pitchers_for_display[pitchers_for_display['is_qualified'] == True]
        
        if team_choice_p != "":
            pitchers_for_display = pitchers_for_display[pitchers_for_display['TEAM'] == team_choice_p]
        
        st.dataframe(pitchers_for_display.reset_index(drop=True), use_container_width=True)

# ============ TAB 3: METHODOLOGY ============
with tab3:
    st.header("Methodology")
    
    st.subheader("Plate Appearance Value")
    
    st.write("As mentioned in the Summary section, the algorithm used to generate ELO (and the resulting ELO+) originally comes from the world of chess rankings, created by [Arpad Elo](https://en.wikipedia.org/wiki/Elo_rating_system) (ELO is not an acronym!). During a chess match, there are three possible outcomes: win (1), draw (0.5) or loss (0). However, there is a much more diverse spread of outcomes in baseball. To deal with this added complexity, I rescaled the wOBA values of each possible plate appearance result to be between 1 and 0, as well as added a negative bump for a strikeout as compared to another kind of out. You can see the results in the table below. Some events (like sac bunt) show up twice, depending on the context (baserunners and outs) of the bunt.")
    
    
    # CREATE TABLE
    
    wobavals = pd.read_csv("wobavalues.csv")
    st.dataframe(wobavals, hide_index = True, use_container_width = True)
    
    st.subheader("Algorithm")
    
    st.write("Considering these scaled values in the table above, we now can iterate through all of the plate appearances in the 2025 season, applying the ELO algorithm. Each player is initialized at a base 1500 ELO, which is what platforms like chess.com traditionally do. Then, for each plate appearance, the following formula is applied ([reference](https://www.omnicalculator.com/sports/elo)): ")
    
    st.write("1. rating_difference = pitcher_ELO - batter_ELO")
    st.write("2. difference_score = rating_difference / 400")
    st.write("3. difference_expon = 10^(difference_score)")
    st.write("4. expectation = 1/(difference_expon + 1)")
    st.write("5. expectation_park = expectation * park_factor")
    st.write("6. expectation_park_pitcher = 1 - expectation_park")
    st.write("7. ELO_change_batter = k_factor * (value - expectation_park)")
    st.write("8. ELO_change_pitcher = k_factor * ( (1- value) - expectation_park_pitcher)")
    st.write("Where pitcher_ELO and batter_ELO are the player ELOs before the plate appearance, ELO_change_batter and ELO_change_pitcher are the adjustments added to the player's ELOs after the plate appeareance, park_factor is a multiplier from [Statcast](https://baseballsavant.mlb.com/leaderboard/statcast-park-factors?type=year&year=2025&batSide=&stat=index_wOBA&condition=All&rolling=1&parks=mlb) between 0.91 and 1.15 depending on if it is a low or high run environment park, value is the scaled value of the plate appearance result, and k_factor is a multiplier we will discuss in the future work section below.")
    
    st.subheader("Standardization")
    
    st.write("After applying the above algorithm to every plate appearance in 2025, ELO was standardized to ELO+, with 100 being league average. In order to end up with an ELO+ spread somewhat similar to the wRC+ spread, this standardization was done after initial adjusting the league minimum ELO to 0, and subtracting all other ELOs accordingly. This doesn't have any impact on which players have a higher ELO+ than others, just gives a spread of ELO+ values more similar to statistics like OPS+ and wRC+.   ")
    
    st.subheader("Future Areas for Improvement")
    
    st.write("As mentioned in the Algorithm section, the k_value is a variable in the algorithm that could be tuned or adjusted. In this analysis, I mirrored the strategy of the international chess federation: [FIDE](https://www.chess.com/terms/elo-rating-chess), which sets k-values to 40 until 30 chess matches are played, and then 20, until near grandmaster status, when it is dropped to 10. To mirror this, I set k-value as 40 until a player reached 120 plate appearances (about 30 games). Then, it was set to 20. However, this is by no means a perfect system, and adjusting the k_value to be more specifically tuned for baseball could improve results.")
    
    st.write("Next, adding more details to the value table could benefit the analysis. Specifically, adding in more types results (double plays, RBI single) would be interesting, or even considering the xwOBA value instead of wOBA to eliminate the impact of defense.")
    
    st.write("Finally, one limitation of this analysis is the equal initialization of players. That means that a home run against Tarik Skubal in the first week of the season would not be as valuable as the same home run in the last week of the season, as Skubal's elite status was not yet reflected by his ELO. There are a few potential methods to fix this. One would be to simply include more data, and track ELO changes for multiple years in a row. However, this still leads to an issue, as initializing ELO for rookies is still uncertain. Another option would be to use a projections tools, such as ZiPS, to initialize ELO. This is still imperfect, as this means that the season's results will be biased by the projections. One way to get around this would potentially be to track two different versions of ELO for one player. One version would be initialized at the start of the season to 1500, and would reflect the player's 2025 results. Another would be initialized using ZiPS, and would just be used to calculate the opponent's ELO. I would love to explore this option, but historic ZiPS data on [Fangraphs](https://www.fangraphs.com/projections?type=zips_2025&stats=bat&pos=all&team=0&players=0&lg=all&z=1769658349&sortcol=&sortdir=&pageitems=30&statgroup=dashboard&fantasypreset=dashboard) is behind a paywall, and the approach outlined above would rely on having access to ZiPS projections for the 2025 season.")
    
    st.write("Please do not hesitate to reach out with any questions, concerns, feedback, or thoughts. My email is malcolm.t.gaynor@gmail.com")



# Footer
#st.markdown("---")
#st.markdown("**Phamalytics** | ELO Rating System for MLB | 2025")
st.markdown("---")
st.markdown("This project was created by Malcolm Gaynor")
