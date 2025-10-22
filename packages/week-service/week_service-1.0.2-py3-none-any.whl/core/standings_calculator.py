"""
Puan Durumu Hesaplayıcı - Haftalık ve Kümülatif
"""
import pandas as pd
from typing import Dict, Any


class StandingsCalculator:
    """Haftalık puan durumu hesaplama"""
    
    @staticmethod
    def calculate_standings_for_all_weeks(matches_df: pd.DataFrame) -> pd.DataFrame:
        """
        Tüm haftalar için kümülatif puan durumunu hesapla
        SADECE status=4 (biten maçlar) ile puan hesaplar
        
        Args:
            matches_df: Maçlar DataFrame (hafta bilgisi ile, TÜM statuslar)
            
        Returns:
            DataFrame: Haftalık kümülatif puan durumu
        """
        if len(matches_df) == 0:
            return pd.DataFrame()
        
        # Season bilgilerini al
        season_id = matches_df['season_id'].iloc[0]
        league = matches_df['league'].iloc[0]
        country = matches_df['country'].iloc[0]
        
        all_standings = []
        max_week = int(matches_df['hafta'].max())
        
        # Her hafta için kümülatif hesapla
        for week in range(1, max_week + 1):
            # Bu haftaya kadar olan SADECE BİTEN maçları al (status=4, KÜMÜLATİF!)
            week_matches = matches_df[
                (matches_df['hafta'] <= week) & 
                (matches_df['status'] == 4)
            ].copy()
            
            # Puan durumunu hesapla
            standings = StandingsCalculator._calculate_single_week_standings(
                week_matches, season_id, league, country, week
            )
            
            all_standings.extend(standings)
        
        return pd.DataFrame(all_standings)
    
    @staticmethod
    def _calculate_single_week_standings(matches_df: pd.DataFrame, 
                                         season_id: int, 
                                         league: str, 
                                         country: str,
                                         current_week: int) -> list:
        """
        Tek bir hafta için puan durumunu hesapla
        
        Args:
            matches_df: Maçlar DataFrame (bu haftaya kadar kümülatif)
            season_id: Sezon ID
            league: Lig adı
            country: Ülke
            current_week: Güncel hafta
            
        Returns:
            List[Dict]: Takım istatistikleri
        """
        # Tüm takımları bul
        home_teams = matches_df[['home_team_id', 'home_team']].rename(
            columns={'home_team_id': 'team_id', 'home_team': 'team_name'}
        )
        away_teams = matches_df[['away_team_id', 'away_team']].rename(
            columns={'away_team_id': 'team_id', 'away_team': 'team_name'}
        )
        all_teams = pd.concat([home_teams, away_teams]).drop_duplicates('team_id')
        
        standings = []
        
        for _, team in all_teams.iterrows():
            team_id = team['team_id']
            team_name = team['team_name']
            
            # Ev sahibi maçları
            home_matches = matches_df[
                (matches_df['home_team_id'] == team_id) & 
                (matches_df['ft_home'].notna())
            ]
            
            # Deplasman maçları
            away_matches = matches_df[
                (matches_df['away_team_id'] == team_id) & 
                (matches_df['ft_away'].notna())
            ]
            
            # İstatistikleri hesapla
            total_matches = len(home_matches) + len(away_matches)
            
            # Ev sahibi istatistikleri
            home_wins = len(home_matches[home_matches['ft_home'] > home_matches['ft_away']])
            home_draws = len(home_matches[home_matches['ft_home'] == home_matches['ft_away']])
            home_losses = len(home_matches[home_matches['ft_home'] < home_matches['ft_away']])
            home_goals_for = int(home_matches['ft_home'].sum()) if len(home_matches) > 0 else 0
            home_goals_against = int(home_matches['ft_away'].sum()) if len(home_matches) > 0 else 0
            
            # Deplasman istatistikleri
            away_wins = len(away_matches[away_matches['ft_away'] > away_matches['ft_home']])
            away_draws = len(away_matches[away_matches['ft_away'] == away_matches['ft_home']])
            away_losses = len(away_matches[away_matches['ft_away'] < away_matches['ft_home']])
            away_goals_for = int(away_matches['ft_away'].sum()) if len(away_matches) > 0 else 0
            away_goals_against = int(away_matches['ft_home'].sum()) if len(away_matches) > 0 else 0
            
            # Toplam
            wins = home_wins + away_wins
            draws = home_draws + away_draws
            losses = home_losses + away_losses
            goals_for = home_goals_for + away_goals_for
            goals_against = home_goals_against + away_goals_against
            goal_difference = goals_for - goals_against
            points = (wins * 3) + draws
            
            standings.append({
                'season_id': season_id,
                'league': league,
                'country': country,
                'week_number': current_week,
                'team_id': int(team_id),
                'team_name': team_name,
                'played': total_matches,
                'wins': wins,
                'draws': draws,
                'losses': losses,
                'goals_for': goals_for,
                'goals_against': goals_against,
                'goal_difference': goal_difference,
                'points': points,
                # Ev sahibi
                'home_played': len(home_matches),
                'home_wins': home_wins,
                'home_draws': home_draws,
                'home_losses': home_losses,
                'home_goals_for': home_goals_for,
                'home_goals_against': home_goals_against,
                # Deplasman
                'away_played': len(away_matches),
                'away_wins': away_wins,
                'away_draws': away_draws,
                'away_losses': away_losses,
                'away_goals_for': away_goals_for,
                'away_goals_against': away_goals_against
            })
        
        # Sıralama: Puan -> Averaj -> Atılan Gol
        standings_df = pd.DataFrame(standings)
        if len(standings_df) > 0:
            standings_df = standings_df.sort_values(
                by=['points', 'goal_difference', 'goals_for'],
                ascending=[False, False, False]
            ).reset_index(drop=True)
            
            # Sıralama ekle
            standings_df['position'] = range(1, len(standings_df) + 1)
            
            return standings_df.to_dict('records')
        
        return []
