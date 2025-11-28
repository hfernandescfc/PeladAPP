from flask import Flask, render_template, request, jsonify
from team_balancer import TeamBalancer, Player, real_players, Intensity, save_players
import os
import uuid
import threading


app = Flask(__name__)

# Armazena jobs de balanceamento em memória simples
job_store = {}
job_lock = threading.Lock()


def _build_balance_context(selected_players, num_teams):
    """Gera contexto com duas opções de times balanceados."""
    import random

    balancer = TeamBalancer(selected_players, num_teams)

    def canonical(teams):
        return tuple(sorted(tuple(sorted(p.name for p in team)) for team in teams))

    def pair_set(teams):
        names_per_team = [[p.name for p in team] for team in teams]
        pairs = set()
        for names in names_per_team:
            for i in range(len(names)):
                for j in range(i + 1, len(names)):
                    pairs.add(frozenset((names[i], names[j])))
        return pairs

    candidates = []
    seen = set()
    state = random.getstate()
    try:
        seed_base = 12345
        for k in range(30):
            random.seed(seed_base + 97 * k)
            dist = balancer.distribute_players()
            key = canonical(dist)
            if key not in seen:
                candidates.append(dist)
                seen.add(key)
            if len(candidates) >= 6:
                break
    finally:
        random.setstate(state)

    if not candidates:
        raise ValueError('Não foi possível gerar opções balanceadas')

    if len(candidates) == 1:
        first = candidates[0]
        second = candidates[0]
    else:
        best_pair = (candidates[0], candidates[1])
        best_overlap = float('inf')
        pair_sets = [pair_set(c) for c in candidates]
        for i in range(len(candidates)):
            for j in range(i + 1, len(candidates)):
                overlap = len(pair_sets[i] & pair_sets[j])
                if overlap < best_overlap:
                    best_overlap = overlap
                    best_pair = (candidates[i], candidates[j])
        first, second = best_pair

    options_stats = []
    whatsapp_texts = []
    for dist in (first, second):
        team_stats = []
        for i, team in enumerate(dist, 1):
            team_strength = balancer.calculate_team_strength(team)
            team_stats.append({
                'number': i,
                'players': sorted(team, key=lambda x: x.overall_rating, reverse=True),
                'strength': round(team_strength, 2),
            })

        options_stats.append(team_stats)

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
        whatsapp_texts.append("\n".join(whatsapp_lines).strip())

    return {
        'options': options_stats,
        'whatsapp_texts': whatsapp_texts,
        'teams': options_stats[0],
        'alt_teams': options_stats[1] if len(options_stats) > 1 else options_stats[0],
        'whatsapp_text': whatsapp_texts[0],
        'whatsapp_text_alt': whatsapp_texts[1] if len(whatsapp_texts) > 1 else whatsapp_texts[0],
        'num_teams': num_teams,
    }


@app.route('/', methods=['GET'])
def index():
    return render_template('index.html', players=real_players)


@app.route('/balance', methods=['POST'])
def balance():
    selected_players = []
    num_teams = int(request.form.get('num_teams', 4))

    for player in real_players:
        if request.form.get(f'player_{player.name}'):
            selected_players.append(player)

    if len(selected_players) < num_teams:
        return "Erro: Selecione pelo menos um jogador por time", 400

    job_id = str(uuid.uuid4())
    with job_lock:
        job_store[job_id] = {'status': 'queued', 'error': None, 'ctx': None}

    def worker(players_snapshot, teams_count, j_id):
        try:
            ctx = _build_balance_context(players_snapshot, teams_count)
            with job_lock:
                job_store[j_id]['status'] = 'done'
                job_store[j_id]['ctx'] = ctx
        except Exception as exc:
            with job_lock:
                job_store[j_id]['status'] = 'error'
                job_store[j_id]['error'] = str(exc)

    threading.Thread(target=worker, args=(list(selected_players), num_teams, job_id), daemon=True).start()

    return render_template('processing.html', job_id=job_id)


@app.route('/balance_status/<job_id>', methods=['GET'])
def balance_status(job_id):
    with job_lock:
        job = job_store.get(job_id)
        if not job:
            return jsonify({'status': 'not_found'}), 404
        return jsonify({'status': job['status'], 'error': job.get('error')})


@app.route('/balance_result/<job_id>', methods=['GET'])
def balance_result(job_id):
    with job_lock:
        job = job_store.get(job_id)
        if not job:
            return "Tarefa não encontrada", 404
        if job['status'] != 'done':
            return "Tarefa ainda não concluída", 202
        ctx = job['ctx']
    return render_template('results.html', **ctx)


@app.route('/add_players', methods=['POST'])
def add_players():
    try:
        data = request.get_json()
        new_players = []

        for player_data in data['players']:
            name = player_data['name']
            try:
                overall_rating = int(player_data['rating'])
            except (ValueError, TypeError):
                return jsonify({'error': 'Avaliação inválida, use inteiro de 1 a 7'}), 400
            if overall_rating < 1 or overall_rating > 7:
                return jsonify({'error': 'Avaliação deve ser entre 1 e 7'}), 400
            intensity = Intensity[player_data['intensity'].upper()]
            mensalista = player_data.get('mensalista', False)

            new_player = Player(name, overall_rating, intensity, mensalista)
            new_players.append(new_player)

        real_players.extend(new_players)
        save_players(real_players)

        return jsonify({'message': 'Jogadores adicionados com sucesso'}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 400


@app.route('/update_player', methods=['POST'])
def update_player():
    try:
        data = request.get_json()
        if not data:
            return jsonify({'error': 'Requisição inválida'}), 400

        old_name = data.get('old_name') or data.get('name')
        name = data.get('name')
        rating = data.get('rating')
        intensity_key = data.get('intensity')
        mensalista = bool(data.get('mensalista', False))

        target = next((p for p in real_players if p.name == old_name), None)
        if not target:
            return jsonify({'error': 'Jogador não encontrado'}), 404

        if name:
            target.name = name
        if rating is not None:
            try:
                r = int(rating)
            except (ValueError, TypeError):
                return jsonify({'error': 'Avaliação inválida, use inteiro de 1 a 7'}), 400
            if r < 1 or r > 7:
                return jsonify({'error': 'Avaliação deve ser entre 1 e 7'}), 400
            target.overall_rating = r
        if intensity_key:
            target.intensity = Intensity[intensity_key.upper()]
        target.mensalista = mensalista
        save_players(real_players)

        return jsonify({'message': 'Jogador atualizado com sucesso'}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 400


@app.route('/delete_player', methods=['POST'])
def delete_player():
    try:
        data = request.get_json()
        if not data or 'name' not in data:
            return jsonify({'error': 'Nome do jogador é obrigatório'}), 400

        name = data['name']
        idx = next((i for i, p in enumerate(real_players) if p.name == name), None)
        if idx is None:
            return jsonify({'error': 'Jogador não encontrado'}), 404

        real_players.pop(idx)
        save_players(real_players)
        return jsonify({'message': 'Jogador removido com sucesso'}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 400


if __name__ == '__main__':
    port = int(os.environ.get('PORT', 8080))
    app.run(host='0.0.0.0', port=port, debug=True)
