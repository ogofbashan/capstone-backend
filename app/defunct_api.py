@app.route('/team')
def league():
    url="https://www.balldontlie.io/api/v1/teams"
    data = urllib.request.urlopen(url).read()
    result = json.loads(data)

    team_list = []

    for i in range(30):
        team_list.append({
        'team_id' :  result['data'][i]['id'],
        'team_abb' : result['data'][i]['abbreviation'],
        'team_name': result['data'][i]['full_name']})

    for j in range(30):
        team_id = team_list[j]['team_id']
        team_abb = team_list[j]['team_abb']
        team_name = team_list[j]['team_name']


        league = Team(team_id=team_id, team_abb=team_abb, team_name=team_name)

        db.session.add(league)
        db.session.commit()
    return jsonify(team_list)

@app.route('/player')
def Roster():
    url="https://www.balldontlie.io/api/v1/players?per_page=100"
    data = urllib.request.urlopen(url).read()
    result = json.loads(data)

    roster_list=[]
    length=result['meta']['total_pages']
    for i in range(1, length):
        url = f"https://www.balldontlie.io/api/v1/players?page={i}&per_page=100"
        data = urllib.request.urlopen(url).read()
        result = json.loads(data)
        for k in result['data']:
            roster_list.append({
                'player_id' :  k['id'],
                'player_name' : k['first_name'] + ' ' + k['last_name'],
                'team_id': k['team']['id']})
    for nba_player in roster_list:
        player_id = nba_player['player_id']
        player_name = nba_player['player_name']
        team_id = nba_player['team_id']

        roster= Player(player_id=player_id, player_name=player_name, team_id=team_id)

        db.session.add(roster)
        db.session.commit()


    return jsonify(roster_list)

    @app.route('/schedule')
    def getSchedule():
        url="https://www.balldontlie.io/api/v1/games?per_page=100&start_date=2019-10-22&end_date=2020-04-15"
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
