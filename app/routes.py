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

@app.route('/')
def index():
    return "Hello Joe!"

@app.route('/api/test', methods=['GET'])
def getInfo():
    id=request.headers.get('team_id')
    date=datetime.now()
    output={}
    teamResults = Team.query.filter_by(team_id=id).all()

    scoreResults=Score.query.filter(Score.date<date).filter(or_(Score.home_team_id==id, Score.away_team_id==id)).filter(or_(Score.home_team_score>0, Score.away_team_score>0)).order_by(Score.date.desc()).limit(1).all()



    for result in teamResults:
        output['team'] = {
            'team_id' : result.team_id,
            'team_abb' : result.team_abb,
            'team_name' : result.team_name
            }

    for result in scoreResults:
        if result.home_team_id==Score.home_team_id:
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

    oppResults = Team.query.filter_by(team_id=output['game']['opp_team_id']).all()

    for result in oppResults:
        output['game']['opp_team'] = result.team_name

    statResults=Stat.query.filter_by(game_id=output['game']['game_id']).join(Player, Player.player_id==Stat.player_id).filter_by(team_id=id).order_by(Stat.points.desc()).limit(1).all()

    for result in statResults:
         output['mvp'] = {
             'player_id' : result.player_id,
             'pts' : result.points,
             }

    playerResults=Player.query.filter_by(player_id=output['mvp']['player_id']).all()
    for result in playerResults:
        output['mvp']['player_name']= result.player_name

    nextGameResults=Score.query.filter(Score.date>date).filter(or_(Score.home_team_id==id, Score.away_team_id==id)).order_by(Score.date.asc()).limit(1).all()

    for result in nextGameResults:
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
    nextOppResults = Team.query.filter_by(team_id=output['next_game']['next_opp_team_id']).all()

    for result in nextOppResults:
        output['next_game']['next_opp_team'] = result.team_name



    return jsonify({'code': 200, 'output': output})


@app.route('/api/dropdown', methods=['GET'])
def colors():
    results=[]
    results=Team.query.all()
    output=[]
    for result in results:
        output.append({
            'team_id' : result.team_id,
            'team_abb' : result.team_abb,
            'team_name' : result.team_name,
            'color_1' : result.color_1,
            'color_2' : result.color_2
            })
    return jsonify({'code' : 200, 'output' : output })

@app.route('/scores')
def getScores():
    yesterday = datetime.strftime(datetime.now() - timedelta(1), '%Y-%m-%d')

    url=f"https://www.balldontlie.io/api/v1/games?start_date={yesterday}&end_date={yesterday}"
    data = urllib.request.urlopen(url).read()
    result = json.loads(data)

    length=result['meta']['total_count']

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
def getStats():
    stats_table = []
    yesterday = date.today() - timedelta(days=1)


    url=f"https://www.balldontlie.io/api/v1/stats?start_date={yesterday}&end_date={yesterday}"
    data = urllib.request.urlopen(url).read()
    result = json.loads(data)

    length=result['meta']['total_pages']

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
                'team_id': k['team']['id']})

    for player in stats_table:
        stat_id=player['stat_id']
        game_id=player['game_id']
        player_id = player['player_id']
        player_name=player['player_name']
        points = player['pts']
        team_id=player['team_id']

        old_player=Player.query.filter_by(player_id=player_id).first()
        old_stat=Stat.query.filter_by(stat_id=stat_id).first()

        if old_player:
            if old_stat:
                pass
            else:
                player_stat=Stat(stat_id=stat_id, game_id=game_id, player_id=player_id,points=points)
                db.session.add(player_stat)
        else:
            roster= Player(player_id=player_id, player_name=player_name, team_id=team_id)
            db.session.add(roster)

    db.session.commit()

    return jsonify(stats_table)
