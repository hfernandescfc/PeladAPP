from typing import List, Dict, Tuple
import random
from dataclasses import dataclass
from enum import Enum

class Position(Enum):
    ATTACK = "atacante"
    MIDFIELD = "meio-campo"
    DEFENSE = "defesa"
    VERSATILE = "versátil"

class Category(Enum):
    ELITE = "elite"
    GOOD = "bom"
    REGULAR = "regular"
    BEGINNER = "iniciante"

@dataclass
class Player:
    name: str
    overall_rating: float
    position: Position

    @property
    def category(self) -> Category:
        if self.overall_rating >= 6.0:
            return Category.ELITE
        elif self.overall_rating >= 5.0:
            return Category.GOOD
        elif self.overall_rating >= 3.0:
            return Category.REGULAR
        else:
            return Category.BEGINNER

# Lista real de jogadores
real_players = [
    Player("Apoli", 5, Position.ATTACK),  # MENSALISTA
    Player("Caio", 1, Position.ATTACK),  # MENSALISTA
    Player("Calafa", 4, Position.ATTACK),  # MENSALISTA
    Player("Daniel", 2, Position.DEFENSE),  # MENSALISTA
    Player("Down", 3, Position.DEFENSE),  # MENSALISTA
    Player("Gabriel de Leon", 2, Position.VERSATILE),  # MENSALISTA
    Player("Guilherme Figueiredo", 6, Position.VERSATILE),  # MENSALISTA
    Player("Guila", 4, Position.VERSATILE),  # MENSALISTA
    Player("Hugo", 4, Position.VERSATILE),  # MENSALISTA
    Player("Igor", 5, Position.VERSATILE),  # MENSALISTA
    Player("Leonardo Silvestre", 4, Position.ATTACK),  # MENSALISTA
    Player("Lucas Souza", 4, Position.ATTACK),  # MENSALISTA
    Player("Luquinhas", 6, Position.ATTACK),  # MENSALISTA
    Player("Nego", 5, Position.VERSATILE),  # MENSALISTA
    Player("PA", 7, Position.VERSATILE),  # MENSALISTA
    Player("Pato", 3, Position.VERSATILE),  # MENSALISTA
    Player("Paulo Freitas", 1, Position.DEFENSE),  # MENSALISTA
    Player("Romero", 3, Position.VERSATILE),  # MENSALISTA
    Player("Sammy", 3, Position.DEFENSE),    #MENSALISTA
    Player("Sèrgïövic", 6, Position.ATTACK),  # MENSALISTA
    Player("SHEIK", 2, Position.DEFENSE),  # MENSALISTA

    # Diaristas
    Player("ALLYSON", 3, Position.VERSATILE),  # DIARISTA
    Player("Antônio", 1, Position.VERSATILE),  # DIARISTA
    Player("Bruno RF", 2, Position.VERSATILE),  # DIARISTA
    Player("Dudu", 4, Position.VERSATILE),  # DIARISTA,
    Player("Davi", 6, Position.VERSATILE),  # DIARISTA
    Player("ERMÍRIO", 4, Position.VERSATILE),  # DIARISTA
    Player("Falcão", 2, Position.VERSATILE),  # DIARISTA
    Player("Gabriel Lira", 3, Position.VERSATILE),  # DIARISTA
    Player("Gustavo", 4, Position.ATTACK),  # DIARISTA
    Player("Jonas", 4, Position.VERSATILE),  # DIARISTA
    Player("PAJÉ", 6, Position.VERSATILE),  # DIARISTA
]
class TeamBalancer:
    def __init__(self, players: List[Player], num_teams: int = 4):
        self.players = players
        self.num_teams = num_teams
        self.players_per_team = len(players) // num_teams
        self.max_attempts = 100000

    def calculate_team_strength(self, team: List[Player]) -> float:
        if not team:
            return 0
        return sum(p.overall_rating for p in team) / len(team)

    def has_required_defensive_players(self, team: List[Player]) -> bool:
        defensive_count = sum(1 for p in team 
                            if p.position in [Position.DEFENSE, Position.VERSATILE])
        return defensive_count >= 2

    def is_valid_distribution(self, teams: List[List[Player]]) -> bool:
        # Verifica se todos os times têm o número correto de jogadores
        if not all(len(team) == self.players_per_team for team in teams):
            return False

        # Verifica se todos os times têm jogadores defensivos suficientes
        if not all(self.has_required_defensive_players(team) for team in teams):
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

            # Separa jogadores defensivos/versáteis dos demais
            defensive_players = [p for p in available_players 
                               if p.position in [Position.DEFENSE, Position.VERSATILE]]
            other_players = [p for p in available_players 
                           if p.position not in [Position.DEFENSE, Position.VERSATILE]]

            # Verifica se há defensores suficientes
            if len(defensive_players) < self.num_teams * 2:
                continue

            # Inicializa times vazios
            teams = [[] for _ in range(self.num_teams)]

            # Distribui primeiro os jogadores defensivos
            random.shuffle(defensive_players)
            for team in teams:
                for _ in range(2):  # Garante 2 defensivos por time
                    if defensive_players:
                        team.append(defensive_players.pop())

            # Adiciona defensivos restantes ao pool de outros jogadores
            other_players.extend(defensive_players)

            # Agrupa jogadores restantes por nível
            remaining_players = other_players
            elite_players = [p for p in remaining_players if p.overall_rating >= 6]
            medium_players = [p for p in remaining_players if 3 <= p.overall_rating < 6]
            weak_players = [p for p in remaining_players if p.overall_rating < 3]

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
                        candidates = random.sample(remaining_players, candidate_count)
                        best_candidate = min(candidates, 
                                          key=lambda p: abs(self.calculate_team_strength(team + [p]) - 4.0))
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
            raise ValueError("Não foi possível encontrar uma distribuição válida com pelo menos 2 jogadores defensivos/versáteis por time")

        return best_distribution

    def print_teams(self, teams: List[List[Player]]) -> None:
        print("\nTimes Balanceados:")
        all_strengths = []
        for i, team in enumerate(teams, 1):
            print(f"\nTime {i}:")
            team_strength = self.calculate_team_strength(team)
            all_strengths.append(team_strength)
            print(f"Força média: {team_strength:.2f}")
            print(f"Número de jogadores: {len(team)}")
            print("Jogadores defensivos/versáteis: ", 
                  sum(1 for p in team if p.position in [Position.DEFENSE, Position.VERSATILE]))
            for player in sorted(team, key=lambda x: x.overall_rating, reverse=True):
                print(f"- {player.name}: {player.overall_rating} ({player.position.value})")

        print("\nEstatísticas Gerais:")
        print(f"Diferença entre time mais forte e mais fraco: {max(all_strengths) - min(all_strengths):.2f}")
        print(f"Desvio máximo da média: {max(abs(s - sum(all_strengths)/len(all_strengths)) for s in all_strengths):.2f}")