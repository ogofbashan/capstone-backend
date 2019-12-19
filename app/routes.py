from app import app, db
from flask import redirect, url_for, request, jsonify
from app.models import Team, Player, Score, Stat
from datetime import date, timedelta
from datetime import datetime
import requests
import json
import urllib.request
import time
from sqlalchemy import or_
import schedule

def job():
    getScores()
    getStats()
    return 'Did it'

schedule.every().day.at("05:00").do(job)

while True:
    schedule.run_pending()
    time.sleep(1)



@app.route('/')
def index():
    return 'Hello Joe!'

@app.route('/api/getTodaysResults', methods=['GET'])
# Primary API call from front end to get the results for an individual team.
def getTodaysInfo():
    id=request.headers.get('team_id')
    date=datetime.now()
    output={}
    team_results = Team.query.filter_by(team_id=id).all()

    score_results=Score.query.filter(Score.date<date).filter(or_(Score.home_team_id==id, Score.away_team_id==id)).filter(or_(Score.home_team_score>0, Score.away_team_score>0)).order_by(Score.date.desc()).limit(1).all()
    # Filters the database for the last game played.



    for result in team_results:
        output['team'] = {
            'team_id' : result.team_id,
            'team_abb' : result.team_abb,
            'team_name' : result.team_name
            }
    # Populates the API Call with the team information in its own section of the dictionary.

    for result in score_results:
        output['side']= {
        'home_team_id' : result.home_team_id,
        }
    # Before assigning the points in the game, it is necessary to check and see whether the search team was the home team or not. Once that is known the scores can be attributed to the correct teams.

    if output['team']['team_id'] == output['side']['home_team_id']:

        for result in score_results:
            output['game'] = {
                'team_score': result.home_team_score,
                'home_team' : True,
                'opp_team_id' : result.away_team_id,
                'opp_team_score': result.away_team_score,
                'date' : result.date,
                'game_id' : result.game_id,
            }
    else:
            output['game'] = {
                'team_score': result.home_team_score,
                'home_team' : False,
                'opp_team_id' : result.home_team_id,
                'opp_team_score': result.away_team_score,
                'date' : result.date,
                'game_id' : result.game_id,
            }


    if output['game']['team_score'] > output['game']['opp_team_score']:
            output['game']['result'] = 'W'
    else:
            output['game']['result'] = 'L'

    opp_results = Team.query.filter_by(team_id=output['game']['opp_team_id']).all()

    for result in opp_results:
        output['game']['opp_team'] = result.team_name

    # Next the API sends information about the star player for the team and the player(who is not the star player) that had the best performance in the game.
    stat_results=Stat.query.filter_by(game_id=output['game']['game_id']).join(Player, Player.player_id==Stat.player_id).filter_by(team_id=id).order_by(Player.fantasy_avg.desc()).limit(1).all()

    for result in stat_results:
         output['mvp'] = {
            'player_id' : result.player_id,
            'fantasy_score' : result.fantasy_score,
             }

    player_results=Player.query.filter_by(player_id = output['mvp']['player_id']).all()
    for result in player_results:
        output['mvp']['player_name']= result.player_name
        output['mvp']['fantasy_avg']= result.fantasy_avg

    # The player's results are added, comparing their game stats (pts, rebounds, etc.) to their averages for the season. If they did more than 10% better than their average the API reports that they had a good/bad night, otherwise it states that their night was ok.

    if output['mvp']['fantasy_score'] > (output['mvp']['fantasy_avg']*1.1):
        output['mvp']['performance']='had a good night'
    elif output['mvp']['fantasy_score'] < (output['mvp']['fantasy_avg']*.9):
        output['mvp']['performance']='had a bad night'
    else:
        output['mvp']['performance']='had an ok night'

    second_stat_results=Stat.query.filter_by(game_id=output['game']['game_id']).join(Player, Player.player_id==Stat.player_id).filter_by(team_id=id).filter(Player.player_id!=output['mvp']['player_id']).order_by(Player.fantasy_avg.desc()).limit(1).all()

    #same proccess for the player with the best performance.


    for result in second_stat_results:
         output['best_performance'] = {
            'player_id' : result.player_id,
            'fantasy_score' : result.fantasy_score,
             }

    second_player_results=Player.query.filter_by(player_id = output['best_performance']['player_id']).all()
    for result in second_player_results:
        output['best_performance']['player_name']= result.player_name
        output['best_performance']['fantasy_avg']= result.fantasy_avg

    # The player's results are added, comparing their game stats (pts, rebounds, etc.) to their averages for the season. If they did more than 10% better than their average the API reports that they had a good/bad night, otherwise it states that their night was ok.

    if output['best_performance']['fantasy_score'] > (output['best_performance']['fantasy_avg']*1.3):
        output['best_performance']['performance']='had a great night'

    elif output['best_performance']['fantasy_score'] < (output['best_performance']['fantasy_avg']*1.3) and output['best_performance']['fantasy_score'] > (output['best_performance']['fantasy_avg']*1.15) :
        output['best_performance']['performance']='had a good night'

    elif output['best_performance']['fantasy_score'] < (output['best_performance']['fantasy_avg']*.85) and output['best_performance']['fantasy_score'] > (output['best_performance']['fantasy_avg']*.7) :
        output['best_performance']['performance']='had a bad night'

    elif output['best_performance']['fantasy_score'] < (output['mvp']['fantasy_avg']*.7):
        output['best_performance']['performance']='had a terrible night'

    else:
        output['best_performance']['performance']='had an ok night'



    next_game_results=Score.query.filter(Score.date>date).filter(or_(Score.home_team_id==id, Score.away_team_id==id)).order_by(Score.date.asc()).limit(1).all()

    for result in next_game_results:
        if output['team']['team_id']==result.home_team_id:
            output['next_game'] = {
                'home_team' : True,
                'next_opp_team_id' : result.away_team_id,
                'next_game_date' : result.date,
            }
        else:
            output['next_game'] = {
                'home_team' : False,
                'next_opp_team_id' : result.home_team_id,
                'next_game_date' : result.date,
            }
    next_opp_results = Team.query.filter_by(team_id=output['next_game']['next_opp_team_id']).all()

    for result in next_opp_results:
        output['next_game']['next_opp_team'] = result.team_name



    return jsonify({'code': 200, 'output': output})


@app.route('/scores')
# Gets the scores from the night before and updates the database
def getScores():
    yesterday = datetime.strftime(datetime.now() - timedelta(1), '%Y-%m-%d')

    url=f"https://www.balldontlie.io/api/v1/games?start_date={yesterday}&end_date={yesterday}"
    data = urllib.request.urlopen(url).read()
    result = json.loads(data)

    score_list = []

    for k in result['data']:
        score_list.append({
            'game_id': k['id'],
            'game_date': k['date'][:-14],
            'home_team_id' :  k['home_team']['id'],
            'home_team_score' : k['home_team_score'],
            'away_team_id' : k['visitor_team']['id'],
            'away_team_score': k['visitor_team_score']
        })
    for nba_game in score_list:
        tonight_game_id = nba_game['game_id']
        date = datetime.strptime(nba_game['game_date'], "%Y-%m-%d")
        home_team_id = nba_game['home_team_id']
        home_team_score = nba_game['home_team_score']
        away_team_id = nba_game['away_team_id']
        away_team_score = nba_game['away_team_score']

        update=Score.query.filter_by(game_id=tonight_game_id).first()

        update.home_team_score=home_team_score
        update.away_team_score=away_team_score

    db.session.commit()

    return jsonify(score_list)

@app.route('/stats')
# Updates the stats database
def getStats():
    stats_table = []
    yesterday = date.today() - timedelta(days=1)


    url=f"https://www.balldontlie.io/api/v1/stats?start_date={yesterday}&end_date={yesterday}"
    data = urllib.request.urlopen(url).read()
    result = json.loads(data)

    length=result['meta']['total_pages'] + 1

    for i in range(1,length):
        url = f"https://www.balldontlie.io/api/v1/stats?page={i}&start_date={yesterday}&end_date={yesterday}"
        data = urllib.request.urlopen(url).read()
        result = json.loads(data)
        for k in result['data']:
            stats_table.append({
                'stat_id' : k['id'],
                'game_id' : k['game']['id'],
                'player_id' : k['player']['id'],
                'player_name' : k['player']['first_name'] + ' ' + k['player']['last_name'],
                'pts': k['pts'],
                'reb' : k['reb'],
                'stl' : k['stl'],
                'turnovers' : k['turnover'],
                'blk' : k['blk'],
                'ast' : k['ast'],
                'fantasy_score' : k['pts'] + k['reb']*1.2 + k['stl']*2 - k['turnover'] + k['blk']*2 + k['ast']*1.5,
                'team_id': k['team']['id']})

    for player in stats_table:
        stat_id=player['stat_id']
        game_id=player['game_id']
        player_id = player['player_id']
        player_name=player['player_name']
        points = player['pts']
        rebounds=player['reb']
        steals=player['stl']
        turnovers=player['turnovers']
        blocks=player['blk']
        assists=player['ast']
        fantasy_score=player['fantasy_score']
        team_id=player['team_id']

        old_player=Player.query.filter_by(player_id=player_id).first()
        old_stat=Stat.query.filter_by(stat_id=stat_id).first()
        # The route checks to make sure that the player is in the database. If not, then it adds them.
        if old_player:
            if old_stat:
                pass
            else:
                player_stat=Stat(stat_id=stat_id, game_id=game_id, player_id=player_id,points=points, rebounds=rebounds, steals=steals, turnovers=turnovers, blocks=blocks, assists=assists, fantasy_score=fantasy_score)
                db.session.add(player_stat)

                update=Player.query.filter_by(player_id=player_id).first()
                fantasy_avg = (fantasy_score + Player.fantasy_avg * Player.mean_num)/(Player.mean_num+1)

                update.fantasy_avg=fantasy_avg
                update.mean_num=Player.mean_num+1
        else:
            roster= Player(player_id=player_id, player_name=player_name, team_id=team_id, fantasy_avg=0,
            mean_num=0)
            db.session.add(roster)
            db.session.commit()

            player_stat=Stat(stat_id=stat_id, game_id=game_id, player_id=player_id,points=points, rebounds=rebounds, steals=steals, turnovers=turnovers, blocks=blocks, assists=assists, fantasy_score=fantasy_score)
            db.session.add(player_stat)

            update=Player.query.filter_by(player_id=player_id).first()
            fantasy_avg = (fantasy_score + Player.fantasy_avg * Player.mean_num)/(Player.mean_num+1)

            update.fantasy_avg=fantasy_avg
            update.mean_num=Player.mean_num+1

    db.session.commit()

    return jsonify(stats_table)

#This code creates the schedule for the year. Only needed once a season.
@app.route('/schedule')
def getSchedule():
    today=datetime.now()
    next_year = date.today() + timedelta(days=365)

    url=f"https://www.balldontlie.io/api/v1/games?per_page=100&start_date={today}&end_date={next_year}"
    data = urllib.request.urlopen(url).read()
    result = json.loads(data)


    score_list = []

    length=result['meta']['total_pages']

    for i in range(1, length+1):
        url = f"https://www.balldontlie.io/api/v1/games?page={i}&per_page=100&start_date=2019-10-22&end_date=2020-04-15"
        data = urllib.request.urlopen(url).read()
        result = json.loads(data)
        for k in result['data']:
            score_list.append({
                'game_id': k['id'],
                'date': k['date'][:-14],
                'home_team_id' :  k['home_team']['id'],
                'home_team_score' : k['home_team_score'],
                'away_team_id' : k['visitor_team']['id'],
                'away_team_score': k['visitor_team_score']
            })

    for nba_game in score_list:
        game_id = nba_game['game_id']
        date = datetime.strptime(nba_game['date'], "%Y-%m-%d")
        home_team_id = nba_game['home_team_id']
        home_team_score = nba_game['home_team_score']
        away_team_id = nba_game['away_team_id']
        away_team_score = nba_game['away_team_score']

        game_night= Score(game_id=game_id, date=date, home_team_id=home_team_id, home_team_score=home_team_score, away_team_id=away_team_id, away_team_score=away_team_score)


        db.session.add(game_night)
    db.session.commit()

    return jsonify(score_list)
