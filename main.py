from flask import Flask, render_template, request, redirect, url_for
from team_balancer import TeamBalancer, Player, Position, real_players
import os

app = Flask(__name__)

@app.route('/', methods=['GET'])
def index():
    return render_template('index.html', players=real_players)

@app.route('/balance', methods=['POST'])
def balance():
    selected_players = []
    num_teams = int(request.form.get('num_teams', 4))

    # Pega os jogadores selecionados do formulário
    for player in real_players:
        if request.form.get(f'player_{player.name}'):
            selected_players.append(player)

    if len(selected_players) < num_teams:
        return "Erro: Selecione pelo menos um jogador por time", 400

    balancer = TeamBalancer(selected_players, num_teams)
    try:
        balanced_teams = balancer.distribute_players()
        team_stats = []

        for i, team in enumerate(balanced_teams, 1):
            team_strength = balancer.calculate_team_strength(team)
            team_stats.append({
                'number': i,
                'players': sorted(team, key=lambda x: x.overall_rating, reverse=True),
                'strength': round(team_strength, 2),
            })

        return render_template('results.html', teams=team_stats)
    except ValueError as e:
        return str(e), 400

if __name__ == '__main__':
    # Configuração para rodar tanto localmente quanto no Replit
    port = int(os.environ.get('PORT', 8080))
    app.run(host='0.0.0.0', port=port, debug=True)

@app.route('/add_players', methods=['POST'])
def add_players():
    try:
        data = request.get_json()
        new_players = []

        for player_data in data['players']:
            name = player_data['name']
            position = Position[player_data['position'].upper()]
            rating = float(player_data['rating'])

            new_player = Player(name, position, rating)
            new_players.append(new_player)

        # Adiciona os novos jogadores à lista existente
        real_players.extend(new_players)

        return jsonify({'message': 'Jogadores adicionados com sucesso'}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 400