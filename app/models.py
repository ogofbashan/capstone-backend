from app import app, db

class Team(db.Model):
    team_id=db.Column(db.Integer, primary_key=True)
    team_abb=db.Column(db.String(4))
    team_name=db.Column(db.String(50))
    color_1=db.Column(db.String(8))
    color_2=db.Column(db.String(8))
    textcolor=db.Column(db.String(8))

class Player(db.Model):
    player_id=db.Column(db.Integer, primary_key=True)
    player_name=db.Column(db.String(50))
    fantasy_avg=db.Column(db.Float)
    mean_num=db.Column(db.Integer)
    team_id=db.Column(db.Integer, db.ForeignKey('team.team_id'))

class Score(db.Model):
    game_id=db.Column(db.Integer, primary_key=True)
    date = db.Column(db.Date)
    home_team_id=db.Column(db.Integer, db.ForeignKey('team.team_id'))
    home_team_score=db.Column(db.Integer)
    away_team_id=db.Column(db.Integer, db.ForeignKey('team.team_id'))
    away_team_score=db.Column(db.Integer)

class Stat(db.Model):
    stat_id=db.Column(db.Integer, primary_key=True)
    game_id=db.Column(db.Integer, db.ForeignKey('score.game_id'))
    points=db.Column(db.Integer)
    rebounds=db.Column(db.Integer)
    steals=db.Column(db.Integer)
    turnovers=db.Column(db.Integer)
    blocks=db.Column(db.Integer)
    assists=db.Column(db.Integer)
    fantasy_score=db.Column(db.Float)
    player_id=db.Column(db.Integer, db.ForeignKey('player.player_id'))
