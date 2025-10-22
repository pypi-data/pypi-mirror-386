"""
⚽ MATCH LOADER
Veritabanından maç verilerini yükler
"""

import pandas as pd
from .database import DatabaseManager


class MatchLoader:
    """Maç verilerini yükleyen sınıf"""
    
    def __init__(self, db_manager: DatabaseManager = None):
        """
        Args:
            db_manager: DatabaseManager instance (opsiyonel)
        """
        self.db_manager = db_manager if db_manager else DatabaseManager()
    
    def load_matches_by_season(self, season_id: int) -> pd.DataFrame:
        """
        Sezona göre maçları yükle
        
        Args:
            season_id: Sezon ID'si
            
        Returns:
            DataFrame: Maç verileri
        """
        query = """
            SELECT 
                match_id,
                season_id,
                league,
                country,
                home_team_id,
                home_team,
                away_team_id,
                away_team,
                ht_home,
                ht_away,
                ft_home,
                ft_away,
                match_date,
                match_time,
                status
            FROM results
            WHERE season_id = %s
              AND status = 4
              AND ft_home IS NOT NULL
              AND ft_away IS NOT NULL
            ORDER BY match_date, match_time
        """

        with self.db_manager as conn:
            df = pd.read_sql_query(query, conn, params=(season_id,))
        
        return df
