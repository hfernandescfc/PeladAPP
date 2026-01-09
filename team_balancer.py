from typing import List, Dict, Tuple
import random
import json
import os
import logging
from dataclasses import dataclass
from enum import Enum


class Category(Enum):
    ELITE = "elite"
    GOOD = "bom"
    REGULAR = "regular"
    BEGINNER = "iniciante"


class Intensity(Enum):
    HIGH = "alta"
    LOW = "baixa"


@dataclass
class Player:
    name: str
    overall_rating: float
    intensity: Intensity
    mensalista: bool = False

    @property
    def category(self) -> Category:
        if self.overall_rating >= 6.0:
            return Category.ELITE
        elif self.overall_rating >= 4.0:
            return Category.GOOD
        elif self.overall_rating >= 3.0:
            return Category.REGULAR
        else:
            return Category.BEGINNER


# Lista padrão de jogadores (usada no primeiro run ou como fallback)
real_players = [
    Player("Ivo", 4, Intensity.HIGH, mensalista=False),
    Player("Vaca", 2, Intensity.HIGH, mensalista=True),
    Player("Caio", 1, Intensity.LOW, mensalista=True),
    Player("Calafa", 4, Intensity.LOW, mensalista=True),
    Player("Daniel", 3, Intensity.HIGH, mensalista=True),
    Player("Down", 3, Intensity.LOW, mensalista=True),
    Player("Gabriel de Leon", 1, Intensity.HIGH, mensalista=True),
    Player("Guilherme Figueiredo", 6, Intensity.HIGH, mensalista=True),
    Player("Guila", 4, Intensity.LOW, mensalista=True),
    Player("Hugo", 5, Intensity.HIGH, mensalista=False),
    Player("Falcǜo", 4, Intensity.HIGH, mensalista=True),
    Player("Lucas Souza", 4, Intensity.LOW, mensalista=True),
    Player("Luquinhas", 6, Intensity.HIGH, mensalista=True),
    Player("Nego", 5, Intensity.HIGH, mensalista=True),
    Player("Pato", 3, Intensity.LOW, mensalista=True),
    Player("Paulo Freitas", 1, Intensity.LOW, mensalista=True),
    Player("Arthur Melo", 2, Intensity.LOW, mensalista=True),
    Player("Sammy", 3, Intensity.HIGH, mensalista=True),
    Player("Serginho", 6, Intensity.LOW, mensalista=True),
    Player("SHEIK", 1, Intensity.LOW, mensalista=True),

    # Diaristas
    Player("PA", 7, Intensity.HIGH, mensalista=False),
    Player("Ant��nio", 2, Intensity.LOW, mensalista=False),
    Player("Dias", 2, Intensity.LOW, mensalista=False),
    Player("Girǜo", 3, Intensity.HIGH, mensalista=False),
    Player("Diogo", 6, Intensity.HIGH, mensalista=False),
    Player("Diego Spencer", 3, Intensity.LOW, mensalista=False),

    Player("Davi", 6, Intensity.HIGH, mensalista=False),
    Player("Doca", 4, Intensity.HIGH, mensalista=False),

    Player("Fernando Henrique", 6, Intensity.HIGH, mensalista=False),
    Player("Gabriel Lira", 5, Intensity.HIGH, mensalista=False),
    Player("Mikhail", 3, Intensity.LOW, mensalista=False),
    Player("Monteiro", 7, Intensity.HIGH, mensalista=False),
    Player("Jonas", 4, Intensity.LOW, mensalista=False),
    Player("PAJ�%", 6, Intensity.HIGH, mensalista=False),
    Player("Gustavo", 4, Intensity.LOW, mensalista=True),
    Player("Sabugo", 2, Intensity.LOW, mensalista=True),
    Player("Junior", 5, Intensity.LOW, mensalista=False),
    Player("Marcelo Torres", 5, Intensity.LOW, mensalista=False),
    Player("Eduardo Jorge", 4, Intensity.LOW, mensalista=False),
    Player("Vareta", 1, Intensity.LOW, mensalista=False)

]


# Persistência simples em arquivo JSON
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
_env_path = os.environ.get('PLAYERS_FILE')
if _env_path:
    DATA_FILE = _env_path if os.path.isabs(_env_path) else os.path.join(BASE_DIR, _env_path)
else:
    DATA_FILE = os.path.join(BASE_DIR, 'players.json')

logger = logging.getLogger(__name__)


def _player_to_dict(p: Player) -> Dict:
    return {
        'name': p.name,
        'rating': int(p.overall_rating),
        'intensity': p.intensity.name,
        'mensalista': bool(p.mensalista),
    }


def _player_from_dict(d: Dict) -> Player:
    name = d['name']
    rating = int(d.get('rating', d.get('overall_rating', 0)))
    intensity_key = str(d.get('intensity', 'LOW')).upper()
    intensity = Intensity[intensity_key]
    mensalista = bool(d.get('mensalista', False))
    return Player(name, rating, intensity, mensalista)


def save_players(players: List[Player]) -> None:
    """Persiste jogadores em escrita atômica; loga erros ao invés de silenciar."""
    try:
        data = [_player_to_dict(p) for p in players]
        os.makedirs(os.path.dirname(DATA_FILE) or '.', exist_ok=True)
        tmp_path = DATA_FILE + '.tmp'
        with open(tmp_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        os.replace(tmp_path, DATA_FILE)
    except Exception:
        logger.exception("Falha ao salvar jogadores em %s", DATA_FILE)


def _load_players_from_file() -> List[Player]:
    """Carrega jogadores do JSON; ignora registros inválidos ao invés de descartar tudo."""
    if not os.path.exists(DATA_FILE):
        return []
    try:
        with open(DATA_FILE, 'r', encoding='utf-8') as f:
            raw = json.load(f)
        loaded: List[Player] = []
        for idx, item in enumerate(raw or []):
            try:
                loaded.append(_player_from_dict(item))
            except Exception:
                logger.warning("Registro inválido em %s na posição %s: %r", DATA_FILE, idx, item)
        return loaded
    except Exception:
        logger.exception("Falha ao carregar jogadores de %s", DATA_FILE)
        return []


def load_or_init_players() -> None:
    """Substitui real_players por dados do arquivo; se vazio/inexistente, inicializa salvando padrão."""
    loaded = _load_players_from_file()
    global real_players
    if loaded:
        real_players.clear()
        real_players.extend(loaded)
    else:
        # Primeira execução: salva a lista padrão para persistir
        save_players(real_players)


# Carrega ou inicializa ao importar o módulo
load_or_init_players()


class TeamBalancer:
    def __init__(self, players: List[Player], num_teams: int = 4):
        self.players = players
        self.num_teams = num_teams
        self.players_per_team = len(players) // num_teams
        self.max_attempts = 50000

    def calculate_team_strength(self, team: List[Player]) -> float:
        if not team:
            return 0
        return sum(p.overall_rating for p in team) / len(team)

    def count_high_intensity(self, team: List[Player]) -> int:
        return sum(1 for p in team if p.intensity == Intensity.HIGH)

    def is_valid_distribution(self, teams: List[List[Player]]) -> bool:
        # Verifica se todos os times têm o número correto de jogadores
        if not all(len(team) == self.players_per_team for team in teams):
            return False

        # Verifica o balanceamento de jogadores de alta intensidade
        total_high_intensity = sum(self.count_high_intensity(team) for team in teams)
        expected_high_intensity_per_team = total_high_intensity / self.num_teams

        # Verifica se a distribuição de jogadores de alta intensidade está equilibrada
        high_intensity_counts = [self.count_high_intensity(team) for team in teams]
        max_high_intensity_diff = max(high_intensity_counts) - min(high_intensity_counts)

        # Permitimos no máximo uma diferença de 1 jogador de alta intensidade entre os times
        if max_high_intensity_diff > 1:
            return False

        # Verifica o balanceamento de força
        team_strengths = [self.calculate_team_strength(team) for team in teams]
        max_strength_diff = max(team_strengths) - min(team_strengths)
        return max_strength_diff <= 1

    def distribute_players(self) -> List[List[Player]]:
        best_distribution = None
        best_strength_diff = float('inf')

        for attempt in range(self.max_attempts):
            available_players = self.players.copy()

            # Separa jogadores por intensidade
            high_intensity_players = [p for p in available_players if p.intensity == Intensity.HIGH]
            low_intensity_players = [p for p in available_players if p.intensity == Intensity.LOW]

            # Inicializa times vazios
            teams = [[] for _ in range(self.num_teams)]

            # Distribui jogadores de alta intensidade igualmente entre os times
            random.shuffle(high_intensity_players)
            high_intensity_per_team = len(high_intensity_players) // self.num_teams

            for i, team in enumerate(teams):
                for _ in range(high_intensity_per_team):
                    if high_intensity_players:
                        team.append(high_intensity_players.pop())

            # Distribui os jogadores de alta intensidade restantes (se houver)
            for i, player in enumerate(high_intensity_players):
                teams[i % self.num_teams].append(player)

            # Agrupa jogadores restantes (baixa intensidade) por nível
            elite_players = [p for p in low_intensity_players if p.overall_rating >= 6]
            medium_players = [p for p in low_intensity_players if 3 <= p.overall_rating < 6]
            weak_players = [p for p in low_intensity_players if p.overall_rating < 3]

            random.shuffle(elite_players)
            random.shuffle(medium_players)
            random.shuffle(weak_players)

            # Distribui jogadores elite restantes
            for i, player in enumerate(elite_players):
                teams[i % self.num_teams].append(player)

            # Junta médios e fracos
            remaining_players = medium_players + weak_players
            random.shuffle(remaining_players)

            # Completa os times
            while remaining_players:
                for team in teams:
                    if len(team) < self.players_per_team and remaining_players:
                        candidate_count = min(3, len(remaining_players))
                        candidates = remaining_players[:candidate_count]

                        if candidates:
                            best_candidate = min(
                                candidates,
                                key=lambda p: abs(self.calculate_team_strength(team + [p]) - 4.0),
                            )
                            team.append(best_candidate)
                            remaining_players.remove(best_candidate)

            if self.is_valid_distribution(teams):
                team_strengths = [self.calculate_team_strength(team) for team in teams]
                strength_diff = max(team_strengths) - min(team_strengths)

                if strength_diff < best_strength_diff:
                    best_strength_diff = strength_diff
                    best_distribution = [team.copy() for team in teams]

                if strength_diff <= 0.3:
                    break

        if best_distribution is None:
            raise ValueError(
                "Não foi possível encontrar uma distribuição válida com a distribuição equilibrada de jogadores de alta intensidade"
            )

        # Embaralha a ordem dos times para variar a apresentacao (cores/posicoes)
        final_distribution = best_distribution[:]
        random.shuffle(final_distribution)
        return final_distribution

    def distribute_players_dissimilar_strength(self) -> List[List[Player]]:
        # Objetivo: maximizar a diferença de força entre o time mais forte e o mais fraco
        if self.players_per_team == 0:
            return [[] for _ in range(self.num_teams)]

        sorted_players = sorted(self.players, key=lambda p: p.overall_rating, reverse=True)
        teams: List[List[Player]] = [[] for _ in range(self.num_teams)]

        # Preenche cada time em blocos ordenados para criar disparidade
        idx = 0
        for t in range(self.num_teams):
            while len(teams[t]) < self.players_per_team and idx < len(sorted_players):
                teams[t].append(sorted_players[idx])
                idx += 1

        return teams

    def distribute_players_dissimilar_intensity(self) -> List[List[Player]]:
        # Objetivo: concentrar alta intensidade nos primeiros times para maximizar diferença
        if self.players_per_team == 0:
            return [[] for _ in range(self.num_teams)]

        high = [p for p in self.players if p.intensity == Intensity.HIGH]
        low = [p for p in self.players if p.intensity == Intensity.LOW]

        # Ordena por força para consistência determinística
        high.sort(key=lambda p: p.overall_rating, reverse=True)
        low.sort(key=lambda p: p.overall_rating, reverse=True)

        teams: List[List[Player]] = [[] for _ in range(self.num_teams)]

        # Primeiro, enche os primeiros times com HIGH até onde der
        for t in range(self.num_teams):
            while len(teams[t]) < self.players_per_team and high:
                teams[t].append(high.pop(0))

        # Depois completa restantes com LOW
        for t in range(self.num_teams):
            while len(teams[t]) < self.players_per_team and low:
                teams[t].append(low.pop(0))

        # Se ainda sobrar alguém (por arredondamento), ignora para manter tamanhos iguais
        return teams

    def print_teams(self, teams: List[List[Player]]) -> None:
        print("\nTimes Balanceados:")
        all_strengths = []
        for i, team in enumerate(teams, 1):
            print(f"\nTime {i}:")
            team_strength = self.calculate_team_strength(team)
            all_strengths.append(team_strength)
            print(f"Força média: {team_strength:.2f}")
            print(f"Número de jogadores: {len(team)}")
            print(f"Jogadores de alta intensidade: {self.count_high_intensity(team)}")
            for player in sorted(team, key=lambda x: x.overall_rating, reverse=True):
                print(f"- {player.name}: {player.overall_rating} ({player.intensity.value})")

        print("\nEstatisticas Gerais:")
        print(
            f"Diferença entre time mais forte e mais fraco: {max(all_strengths) - min(all_strengths):.2f}"
        )
        print(
            f"Desvio máximo da média: {max(abs(s - sum(all_strengths)/len(all_strengths)) for s in all_strengths):.2f}"
        )
