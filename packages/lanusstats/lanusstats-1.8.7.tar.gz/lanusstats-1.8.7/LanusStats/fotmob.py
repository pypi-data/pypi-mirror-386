import requests
import pandas as pd
import time
import json
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from webdriver_manager.chrome import ChromeDriverManager
from .functions import get_possible_leagues_for_page, Options, By, get_random_rate_sleep
from .exceptions import InvalidStat, MatchDoesntHaveInfo
from .config import headers

class FotMob:
    
    def __init__(self):
        self.player_possible_stats = ['goals',
            'goal_assist',
            '_goals_and_goal_assist',
            'rating',
            'goals_per_90',
            'expected_goals',
            'expected_goals_per_90',
            'expected_goalsontarget',
            'ontarget_scoring_att',
            'total_scoring_att',
            'accurate_pass',
            'big_chance_created',
            'total_att_assist',
            'accurate_long_balls',
            'expected_assists',
            'expected_assists_per_90',
            '_expected_goals_and_expected_assists_per_90',
            'won_contest',
            'big_chance_missed',
            'penalty_won',
            'won_tackle',
            'interception',
            'effective_clearance',
            'outfielder_block',
            'penalty_conceded',
            'poss_won_att_3rd',
            'clean_sheet',
            '_save_percentage',
            'saves',
            '_goals_prevented',
            'goals_conceded',
            'fouls',
            'yellow_card',
            'red_card'
        ]

        self.team_possible_stats = ['rating_team',
            'goals_team_match',
            'goals_conceded_team_match',
            'possession_percentage_team',
            'clean_sheet_team',
            'expected_goals_team',
            'ontarget_scoring_att_team',
            'big_chance_team',
            'big_chance_missed_team',
            'accurate_pass_team',
            'accurate_long_balls_team',
            'accurate_cross_team',
            'penalty_won_team',
            'touches_in_opp_box_team',
            'corner_taken_team',
            'expected_goals_conceded_team',
            'interception_team',
            'won_tackle_team',
            'effective_clearance_team',
            'poss_won_att_3rd_team',
            'penalty_conceded_team',
            'saves_team',
            'fk_foul_lost_team',
            'total_yel_card_team',
            'total_red_card_team'
        ]

        self._fotmob_token_cache = {}
        self.CACHE_SECONDS = 3 * 60 * 60

    def get_x_mas(self):
        """
        Devuelve el token x-mas cacheado si existe y no expiró,
        sino abre Selenium, lo captura y lo guarda en cache por 3 horas.
        """
        now = time.time()
        url = 'https://www.fotmob.com/es/matches/atletico-tucuman-vs-central-cordoba-de-santiago/wcumqqe#4393518'
        if url in self._fotmob_token_cache and now < self._fotmob_token_cache[url]["expires_at"]:
            return self._fotmob_token_cache[url]["x_mas"]

        options = Options()
        options.add_argument("--headless=new")
        options.add_argument("--disable-gpu")
        options.add_argument("--no-sandbox")
        options.set_capability("goog:loggingPrefs", {"performance": "ALL"})

        driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
        driver.get(url)

        WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.TAG_NAME, "body")))

        x_mas = None

        for entry in driver.get_log("performance"):
            try:
                message = json.loads(entry["message"])["message"]
                if message.get("method") != "Network.requestWillBeSent":
                    continue
                request = message.get("params", {}).get("request", {})
                url_request = request.get("url", "")
                headers = request.get("headers", {})

                if "/api/data/matchDetails" in url_request and "x-mas" in headers:
                    x_mas = headers["x-mas"]
                    break
            except (KeyError, TypeError, json.JSONDecodeError):
                continue

        driver.quit()

        if not x_mas:
            raise ValueError("No se pudo obtener el token")

        # Guardar en cache por 3 horas
        self._fotmob_token_cache[url] = {"x_mas": x_mas, "expires_at": now + self.CACHE_SECONDS}
        return x_mas

    def fotmob_request(self, path):
        """Make request to FotMob.

        Args:
            path (str): URL to make the request.

        Returns:
            response: Response of the request.
        """
        url = f'https://www.fotmob.com/api/{path}'
        token = self.get_x_mas()
        dict_token = {
            "X-Mas": token
        }
        headers_with_token = headers | dict_token
        response = requests.get(url, headers=headers_with_token)
        time.sleep(get_random_rate_sleep(1, 3))
        return response

        
    def get_season_tables(self, league, season, table = ['all', 'home', 'away', 'form', 'xg']):
        """Get standing tables from a list of possible ones from a certain season in a league.

        Args:
            league (str): Possible leagues in get_available_leagues("Fotmob")
            season (str): Possible saeson in get_available_season_for_leagues("Fotmob", league)
            table (list, optional): Type of table shown in FotMob UI. Defaults to ['all', 'home', 'away', 'form', 'xg'].

        Returns:
            table_df: DataFrame with the table/s. 
        """
        leagues = get_possible_leagues_for_page(league, season, 'Fotmob')
        league_id = leagues[league]['id']
        season_string = season.replace('/', '%2F')
        path = f'leagues?id={league_id}&ccode3=ARG&season={season_string}'
        response = self.fotmob_request(path)
        try:
            tables = response.json()['table'][0]['data']['table']
            table = tables[table]
            table_df = pd.DataFrame(table)
        except KeyError:
            tables = response.json()['table'][0]['data']['tables']
            table_df = tables
            print('This response has a list of two values, because the tables are split. If you save the list in a variable and then do variable[0]["table"] you will have all of the tables\nThen just select one ["all", "home", "away", "form", "xg"] that exists and put it inside a pd.DataFrame()\nSomething like pd.DataFrame(variable[0]["table"]["all"])')
        return table_df
    
    def request_match_details(self, match_id):
        """Get match deatils with a request.

        Args:
            match_id (str): id of a certain match, could be found in the URL

        Returns:
            response: json with the response.
        """
        path = f'matchDetails?matchId={match_id}'
        response = self.fotmob_request(path)
        return response
    
    def get_players_stats_season(self, league, season, stat):
        """Get players for a certain season and league stats. Possible stats are player_possible_stats.

        Args:
            league (str): Possible leagues in get_available_leagues("Fotmob")
            season (str): Possible saeson in get_available_season_for_leagues("Fotmob", league)
            stat (str): Value inside player_possible_stats

        Raises:
            InvalidStat: Raised when the input of stat is not inside the possible list values.

        Returns:
            df: DataFrame with the values and player names for that stat.
        """
        print(f'Possible values for stat parameter: {self.player_possible_stats}')
        if stat not in self.player_possible_stats:
            raise InvalidStat(stat, self.player_possible_stats)
        leagues = get_possible_leagues_for_page(league, season, 'Fotmob')
        league_id = leagues[league]['id']
        season_id = leagues[league]['seasons'][season]
        path = f'leagueseasondeepstats?id={league_id}&season={season_id}&type=players&stat={stat}'
        response = self.fotmob_request(path)
        df_1 = pd.DataFrame(response.json()['statsData'])
        df_2 = pd.DataFrame(response.json()['statsData']).statValue.apply(pd.Series)
        df = pd.concat([df_1, df_2], axis=1)
        return df
    
    def get_teams_stats_season(self, league, season, stat):
        """Get teams for a certain season and league stats. Possible stats are team_possible_stats.

        Args:
            league (str): Possible leagues in get_available_leagues("Fotmob")
            season (str): Possible saeson in get_available_season_for_leagues("Fotmob", league)
            stat (str): Value inside team_possible_stats

        Raises:
            InvalidStat: Raised when the input of stat is not inside the possible list values.

        Returns:
            df: DataFrame with stat values for teams in a league and season.
        """
        print(f'Possible values for stat parameter: {self.team_possible_stats}')
        if stat not in self.team_possible_stats:
            raise InvalidStat(stat, self.team_possible_stats)
        leagues = get_possible_leagues_for_page(league, season, 'Fotmob')
        league_id = leagues[league]['id']
        season_id = leagues[league]['seasons'][season]
        path = f'leagueseasondeepstats?id={league_id}&season={season_id}&type=teams&stat={stat}'
        response = self.fotmob_request(path)
        df_1 = pd.DataFrame(response.json()['statsData'])
        df_2 = pd.DataFrame(response.json()['statsData']).statValue.apply(pd.Series)
        df = pd.concat([df_1, df_2], axis=1)
        return df

    def get_match_shotmap(self, match_id):
        """Scrape a match shotmap, if it has one.

        Args:
            match_id (str): Id of a FotMob match, could be found in the URL.
                            Example: https://www.fotmob.com/es/matches/boca-juniors-vs-newells-old-boys/3ef4me#4393680
                            4393680 is the match_id.

        Raises:
            MatchDoesntHaveInfo: Raised when the match associated with the match_id doesn't have a shotmap.

        Returns:
            shotmap: DataFrame with the data for all the shots shown in the FotMob UI.
        """
        response = self.request_match_details(match_id)
        time.sleep(1)
        df_shotmap = pd.DataFrame(response.json()['content']['shotmap']['shots'])
        if df_shotmap.empty:
            raise MatchDoesntHaveInfo(match_id)
        ongoalshot = df_shotmap.onGoalShot.apply(pd.Series).rename(columns={'x': 'goalMouthY', 'y': 'goalMouthZ'}) 
        shotmap = pd.concat([df_shotmap, ongoalshot], axis=1).drop(columns=['onGoalShot'])
        return shotmap
    
    def get_team_colors(self, match_id):
        """Get team colors as FotMob UI uses.

        Args:
            match_id (str): Id of a FotMob match, could be found in the URL.
                            Example: https://www.fotmob.com/es/matches/boca-juniors-vs-newells-old-boys/3ef4me#4393680
                            4393680 is the match_id.

        Returns:
            home_color, away_color: strings with hex codes.
        """
        response = self.request_match_details(match_id)
        time.sleep(1)
        colors = response.json()['general']['teamColors']
        home_color = colors['darkMode']['home']
        away_color = colors['darkMode']['away']
        
        if home_color == '#ffffff':
            home_color = colors['lightMode']['home']
        if away_color == '#ffffff':
            away_color = colors['lightMode']['away']
        return home_color, away_color    
    
    def get_general_match_stats(self,match_id):
        """Get general match stats for a certain match (shots, passes, duels won for the teams).

        Args:
            match_id (str): Id of a FotMob match, could be found in the URL.
                            Example: https://www.fotmob.com/es/matches/boca-juniors-vs-newells-old-boys/3ef4me#4393680
                            4393680 is the match_id.

        Returns:
            total_df: DataFrame with the stats of the teams for a certain match
        """
        response = self.request_match_details(match_id)
        time.sleep(1)
        total_df = pd.DataFrame()
        stats_df = response.json()['content']['stats']['Periods']['All']['stats']
        for i in range(len(stats_df)):
            df = pd.DataFrame(stats_df[i]['stats'])
            total_df = pd.concat([df, total_df])
        total_df = pd.concat([total_df, total_df.stats
                              .apply(pd.Series)
                              .rename(columns={0: 'home', 1: 'away'})], axis=1) \
                .drop(columns=['stats']) \
                .dropna(subset=['home', 'away'])
        return total_df
    
    def get_player_shotmap(self, season_index, competition_index, player_id):
        """Scrape a player shotmap from a certain league and season, if they have one.

        Args:
            season_index (str): Position of the season in the dropdown on FotMob UI
            competition_index (str): Position of the competition in a season in the dropdown on FotMob UI
            player_id (str): FotMob Id of a player. Could be found in the URL of a specific player.
                             Example: https://www.fotmob.com/es/players/727095/ignacio-ramirez
                             727095 is the player_id.

        Returns:
            shotmap: DataFrame with the data for all the shots shown in the FotMob UI.
        """
        path = f'playerStats?playerId={player_id}&seasonId={season_index}-{competition_index}&isFirstSeason=false'
        response = self.fotmob_request(path)
        try:
            shotmap = pd.DataFrame(response.json()['shotmap'])
        except TypeError:
            raise MatchDoesntHaveInfo(player_id)
        return shotmap