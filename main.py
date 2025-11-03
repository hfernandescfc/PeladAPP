from flask import Flask, render_template, request, redirect, url_for, jsonify
from team_balancer import TeamBalancer, Player, real_players, Intensity
import os

app = Flask(__name__)


@app.route('/', methods=['GET'])
def index():
    return render_template('index.html', players=real_players)


@app.route('/balance', methods=['POST'])
def balance():
    selected_players = []
    num_teams = int(request.form.get('num_teams', 4))

    # Retrieve selected players from the form
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
                'number':
                i,
                'players':
                sorted(team, key=lambda x: x.overall_rating, reverse=True),
                'strength':
                round(team_strength, 2),
            })

        # Monta texto amigável para compartilhar no WhatsApp
        whatsapp_lines = ["Times formados:"]
        for i, team in enumerate(team_stats, 1):
            whatsapp_lines.append(f"Time {i} (Força: {team['strength']:.2f}):")
            for p in team['players']:
                try:
                    intensity_val = getattr(p.intensity, 'value', p.intensity)
                except Exception:
                    intensity_val = p.intensity
                whatsapp_lines.append(f"- {p.name} ({p.overall_rating}) - {intensity_val}")
            whatsapp_lines.append("")

        whatsapp_text = "\n".join(whatsapp_lines).strip()

        return render_template('results.html', teams=team_stats, whatsapp_text=whatsapp_text)
    except ValueError as e:
        return str(e), 400


@app.route('/add_players', methods=['POST'])
def add_players():
    try:
        data = request.get_json()
        new_players = []

        for player_data in data['players']:
            name = player_data['name']
            overall_rating = float(player_data['rating'])
            intensity = Intensity[player_data['intensity'].upper()]
            mensalista = player_data.get('mensalista', False)

            new_player = Player(name, overall_rating, intensity, mensalista)
            new_players.append(new_player)

        # Add the new players to the existing list
        real_players.extend(new_players)

        return jsonify({'message': 'Jogadores adicionados com sucesso'}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 400


if __name__ == '__main__':
    port = int(os.environ.get('PORT', 8080))
    app.run(host='0.0.0.0', port=port, debug=True)
