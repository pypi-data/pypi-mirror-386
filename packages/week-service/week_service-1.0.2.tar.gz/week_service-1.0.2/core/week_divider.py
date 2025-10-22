"""
📅 WEEK DIVIDER
Maçları haftalara böler
"""

import pandas as pd


class WeekDivider:
    """Maçları haftalara bölen sınıf"""
    
    @staticmethod
    def divide_matches_into_weeks(df: pd.DataFrame, verbose: bool = False) -> pd.DataFrame:
        """
        Maçları haftalara böl - Her takımın kaçıncı maçını oynadığına göre
        
        Args:
            df: Maç verileri DataFrame
            verbose: Detaylı çıktı göster (varsayılan: False)
            
        Returns:
            DataFrame: Hafta numaraları eklenmiş maç verileri
        """
        if verbose:
            print(f"\n📅 Maçlar haftalara bölünüyor...")
        
        # DataFrame kopyası al
        df = df.copy()
        
        # Tüm takımları bul
        home_teams = set(df['home_team_id'].unique())
        away_teams = set(df['away_team_id'].unique())
        all_teams = home_teams | away_teams
        total_teams = len(all_teams)
        total_matches = len(df)
        
        if verbose:
            print(f"   📊 Toplam {total_teams} takım bulundu")
            print(f"   ⚽ Toplam {total_matches} maç")
        
        # Tarihlere göre maçları sırala
        df['date_only'] = pd.to_datetime(
            df['match_date'], 
            format='%d/%m/%Y', 
            errors='coerce'
        ).dt.date
        df = df.sort_values('date_only').reset_index(drop=True)
        
        # Her takımın kaç maç oynadığını takip et
        team_match_count = {}
        
        # Her maç için hafta numarasını belirle
        for idx, row in df.iterrows():
            home_id = row['home_team_id']
            away_id = row['away_team_id']
            
            # Bu takımların şu ana kadar kaç maç oynadığına bak
            home_count = team_match_count.get(home_id, 0)
            away_count = team_match_count.get(away_id, 0)
            
            # İki takımdan da fazla olanı al, +1 yap = bu hafta
            week_number = max(home_count, away_count) + 1
            
            # Hafta numarasını ata
            df.loc[idx, 'hafta'] = week_number
            
            # Takımların maç sayısını artır
            team_match_count[home_id] = home_count + 1
            team_match_count[away_id] = away_count + 1
        
        df['hafta'] = df['hafta'].astype(int)
        
        # En fazla maç oynayan takımı bul
        max_matches_played = max(team_match_count.values()) if team_match_count else 0
        
        if verbose:
            print(f"   ✅ {max_matches_played} haftaya bölündü")
        
        # Temizlik
        df.drop('date_only', axis=1, inplace=True)
        
        return df
