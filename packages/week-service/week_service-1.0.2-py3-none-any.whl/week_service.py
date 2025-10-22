"""
🚀 WEEK SERVICE - BULK VERSION
Tüm maçları tek seferde çeker, gruplandırır, işler ve toplu kayıt yapar
Çok daha hızlı!
"""

import warnings
from typing import List, Dict, Any, Optional
from datetime import datetime
import pandas as pd
from concurrent.futures import ThreadPoolExecutor, as_completed

# Warning'leri kapat
warnings.filterwarnings('ignore')

from core.database import DatabaseManager
from core.week_divider import WeekDivider
from core.standings_calculator import StandingsCalculator
from utils.logger import ServiceLogger


class WeekService:
    """Week Service - Bulk Processing (Çok daha hızlı!)"""
    
    def __init__(self, db_manager: DatabaseManager = None):
        """
        Args:
            db_manager: DatabaseManager instance (opsiyonel)
        """
        self.db_manager = db_manager if db_manager else DatabaseManager()
        self.logger = ServiceLogger("WeekService")
        
        # İstatistikler
        self.stats = {
            'total_leagues': 0,
            'processed': 0,
            'successful': 0,
            'failed': 0,
            'total_matches': 0,
            'start_time': None,
            'end_time': None
        }
        
        self.failed_leagues = []
    
    def create_match_weeks_table(self) -> bool:
        """match_weeks tablosunu oluştur (yoksa)"""
        self.logger.info("Veritabanı tablosu kontrolü yapılıyor...")
        
        create_table_sql = """
        CREATE TABLE IF NOT EXISTS match_weeks (
            id SERIAL PRIMARY KEY,
            match_id BIGINT NOT NULL,
            season_id INTEGER NOT NULL,
            league VARCHAR(255),
            country VARCHAR(255),
            week_number INTEGER NOT NULL,
            match_date VARCHAR(50),
            match_time VARCHAR(50),
            home_team_id INTEGER,
            home_team VARCHAR(255),
            away_team_id INTEGER,
            away_team VARCHAR(255),
            ht_home SMALLINT,
            ht_away SMALLINT,
            ft_home SMALLINT,
            ft_away SMALLINT,
            status SMALLINT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            CONSTRAINT unique_match_season UNIQUE(match_id, season_id)
        );
        
        CREATE INDEX IF NOT EXISTS idx_match_weeks_season ON match_weeks(season_id);
        CREATE INDEX IF NOT EXISTS idx_match_weeks_week ON match_weeks(week_number);
        CREATE INDEX IF NOT EXISTS idx_match_weeks_match ON match_weeks(match_id);
        CREATE INDEX IF NOT EXISTS idx_match_weeks_status ON match_weeks(status);
        """
        
        try:
            with self.db_manager as conn:
                cursor = conn.cursor()
                cursor.execute(create_table_sql)
                conn.commit()
                cursor.close()
            
            self.logger.info("✅ match_weeks tablosu hazır")
            return True
        except Exception as e:
            self.logger.error(f"❌ Tablo oluşturma hatası: {e}")
            return False
    
    def create_standings_tables(self) -> bool:
        """Puan durumu tablolarını oluştur"""
        self.logger.info("Puan durumu tabloları kontrol ediliyor...")
        
        create_tables_sql = """
        -- Haftalık puan durumu (her hafta kümülatif)
        CREATE TABLE IF NOT EXISTS weekly_standings (
            id SERIAL PRIMARY KEY,
            season_id INTEGER NOT NULL,
            league VARCHAR(255),
            country VARCHAR(255),
            week_number INTEGER NOT NULL,
            team_id INTEGER NOT NULL,
            team_name VARCHAR(255),
            position INTEGER,
            played INTEGER,
            wins INTEGER,
            draws INTEGER,
            losses INTEGER,
            goals_for INTEGER,
            goals_against INTEGER,
            goal_difference INTEGER,
            points INTEGER,
            home_played INTEGER,
            home_wins INTEGER,
            home_draws INTEGER,
            home_losses INTEGER,
            home_goals_for INTEGER,
            home_goals_against INTEGER,
            away_played INTEGER,
            away_wins INTEGER,
            away_draws INTEGER,
            away_losses INTEGER,
            away_goals_for INTEGER,
            away_goals_against INTEGER,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            CONSTRAINT unique_weekly_standing UNIQUE(season_id, week_number, team_id)
        );
        
        -- Güncel puan durumu (sadece son hafta)
        CREATE TABLE IF NOT EXISTS current_standings (
            id SERIAL PRIMARY KEY,
            season_id INTEGER NOT NULL,
            league VARCHAR(255),
            country VARCHAR(255),
            team_id INTEGER NOT NULL,
            team_name VARCHAR(255),
            position INTEGER,
            played INTEGER,
            wins INTEGER,
            draws INTEGER,
            losses INTEGER,
            goals_for INTEGER,
            goals_against INTEGER,
            goal_difference INTEGER,
            points INTEGER,
            home_played INTEGER,
            home_wins INTEGER,
            home_draws INTEGER,
            home_losses INTEGER,
            home_goals_for INTEGER,
            home_goals_against INTEGER,
            away_played INTEGER,
            away_wins INTEGER,
            away_draws INTEGER,
            away_losses INTEGER,
            away_goals_for INTEGER,
            away_goals_against INTEGER,
            last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            CONSTRAINT unique_current_standing UNIQUE(season_id, team_id)
        );
        
        -- İndeksler
        CREATE INDEX IF NOT EXISTS idx_weekly_standings_season ON weekly_standings(season_id);
        CREATE INDEX IF NOT EXISTS idx_weekly_standings_week ON weekly_standings(week_number);
        CREATE INDEX IF NOT EXISTS idx_weekly_standings_team ON weekly_standings(team_id);
        
        CREATE INDEX IF NOT EXISTS idx_current_standings_season ON current_standings(season_id);
        CREATE INDEX IF NOT EXISTS idx_current_standings_team ON current_standings(team_id);
        CREATE INDEX IF NOT EXISTS idx_current_standings_country ON current_standings(country);
        CREATE INDEX IF NOT EXISTS idx_current_standings_league ON current_standings(league);
        """
        
        try:
            with self.db_manager as conn:
                cursor = conn.cursor()
                cursor.execute(create_tables_sql)
                conn.commit()
                cursor.close()
            
            self.logger.info("✅ Puan durumu tabloları hazır")
            return True
        except Exception as e:
            self.logger.error(f"❌ Puan durumu tabloları oluşturma hatası: {e}")
            return False
    
    def load_all_matches(self, min_matches: int = 10, limit: Optional[int] = None, only_current_season: bool = True) -> pd.DataFrame:
        """
        TEK SEFERDE tüm maçları çek (min 10 maçlı ligler)
        
        Args:
            min_matches: Minimum maç sayısı
            limit: İşlenecek maksimum lig sayısı (None ise hepsi)
            only_current_season: Her league_id için sadece en yüksek season_id'yi al (güncel sezon)
            
        Returns:
            DataFrame: Tüm maçlar
        """
        self.logger.info("=" * 70)
        self.logger.info("📥 TÜM MAÇLAR TEK SEFERDE ÇEKİLİYOR...")
        if only_current_season:
            self.logger.info("✅ Sadece GÜNCEL SEZONLAR (en yüksek season_id)")
        self.logger.info("=" * 70)
        
        # Önce lig sayısını öğren (biten maçları say, ama tüm maçları çek)
        count_query = """
            SELECT COUNT(DISTINCT season_id) as league_count
            FROM results
            WHERE status < 13
            GROUP BY season_id, league, country
            HAVING COUNT(CASE WHEN status = 4 THEN 1 END) >= %s
        """
        
        # Limit varsa ligleri önce çek
        if limit:
            if only_current_season:
                # Her league_id için en büyük season_id'yi al (min X biten maç olmalı)
                leagues_query = """
                    WITH ranked_seasons AS (
                        SELECT 
                            season_id,
                            league_id,
                            ROW_NUMBER() OVER (PARTITION BY league_id ORDER BY season_id DESC) as rn
                        FROM results
                        WHERE status < 13
                        GROUP BY season_id, league_id, league, country
                        HAVING COUNT(CASE WHEN status = 4 THEN 1 END) >= %s
                    )
                    SELECT season_id
                    FROM ranked_seasons
                    WHERE rn = 1
                    ORDER BY season_id DESC
                    LIMIT %s
                """
            else:
                # Eski mantık: tüm sezonlar
                leagues_query = """
                    SELECT season_id
                    FROM results
                    WHERE status < 13
                    GROUP BY season_id, league, country
                    HAVING COUNT(CASE WHEN status = 4 THEN 1 END) >= %s
                    ORDER BY country, league, season_id DESC
                    LIMIT %s
                """
            
            with self.db_manager as conn:
                cursor = conn.cursor()
                cursor.execute(leagues_query, (min_matches, limit))
                season_ids = [row[0] for row in cursor.fetchall()]
                cursor.close()
            
            self.logger.info(f"⚠️  İlk {limit} lig seçildi")
            
            # Bu season_id'ler için TÜM maçları çek (status < 13)
            query = """
                SELECT 
                    match_id,
                    season_id,
                    league,
                    country,
                    match_date,
                    match_time,
                    home_team_id,
                    home_team,
                    away_team_id,
                    away_team,
                    ht_home,
                    ht_away,
                    ft_home,
                    ft_away,
                    status
                FROM results
                WHERE status < 13
                  AND season_id = ANY(%s)
                ORDER BY season_id, match_date, match_time
            """
            
            with self.db_manager as conn:
                cursor = conn.cursor()
                cursor.execute(query, (season_ids,))
                rows = cursor.fetchall()
                cursor.close()
        else:
            # Tüm ligler için maçları çek
            if only_current_season:
                # Her league_id için en büyük season_id'yi al (güncel sezon, TÜM statuslar)
                query = """
                    WITH ranked_seasons AS (
                        SELECT 
                            season_id,
                            league_id,
                            ROW_NUMBER() OVER (PARTITION BY league_id ORDER BY season_id DESC) as rn
                        FROM results
                        WHERE status < 13
                        GROUP BY season_id, league_id
                        HAVING COUNT(CASE WHEN status = 4 THEN 1 END) >= %s
                    )
                    SELECT 
                        r.match_id,
                        r.season_id,
                        r.league,
                        r.country,
                        r.match_date,
                        r.match_time,
                        r.home_team_id,
                        r.home_team,
                        r.away_team_id,
                        r.away_team,
                        r.ht_home,
                        r.ht_away,
                        r.ft_home,
                        r.ft_away,
                        r.status
                    FROM results r
                    INNER JOIN ranked_seasons rs ON r.season_id = rs.season_id
                    WHERE rs.rn = 1
                      AND r.status < 13
                    ORDER BY r.season_id, r.match_date, r.match_time
                """
            else:
                # Eski mantık: tüm sezonlar, TÜM statuslar
                query = """
                    SELECT 
                        r.match_id,
                        r.season_id,
                        r.league,
                        r.country,
                        r.match_date,
                        r.match_time,
                        r.home_team_id,
                        r.home_team,
                        r.away_team_id,
                        r.away_team,
                        r.ht_home,
                        r.ht_away,
                        r.ft_home,
                        r.ft_away,
                        r.status
                    FROM results r
                    WHERE r.status < 13
                      AND r.season_id IN (
                          SELECT season_id
                          FROM results
                          WHERE status < 13
                          GROUP BY season_id
                          HAVING COUNT(CASE WHEN status = 4 THEN 1 END) >= %s
                      )
                    ORDER BY r.season_id, r.match_date, r.match_time
                """
            
            with self.db_manager as conn:
                cursor = conn.cursor()
                cursor.execute(query, (min_matches,))
                rows = cursor.fetchall()
                cursor.close()
        
        # DataFrame'e çevir (status dahil!)
        df = pd.DataFrame(rows, columns=[
            'match_id', 'season_id', 'league', 'country', 'match_date', 'match_time',
            'home_team_id', 'home_team', 'away_team_id', 'away_team',
            'ht_home', 'ht_away', 'ft_home', 'ft_away', 'status'
        ])
        
        unique_leagues = df['season_id'].nunique()
        self.logger.info(f"✅ {len(df):,} maç çekildi ({unique_leagues} lig)")
        
        return df
    
    def _calculate_single_season_standings(self, season_matches: pd.DataFrame) -> pd.DataFrame:
        """
        Tek bir sezon için puan durumunu hesapla (paralel işlem için)
        
        Args:
            season_matches: Bir sezonun maçları
            
        Returns:
            DataFrame: Puan durumları
        """
        try:
            standings_df = StandingsCalculator.calculate_standings_for_all_weeks(season_matches)
            return standings_df
        except Exception as e:
            return pd.DataFrame()
    
    def calculate_and_save_standings(self, matches_df: pd.DataFrame, workers: int = 10) -> int:
        """
        Puan durumlarını PARALEL hesapla ve TOPLU kaydet
        
        Args:
            matches_df: Hafta bilgili maçlar
            workers: Paralel worker sayısı
            
        Returns:
            Kaydedilen kayıt sayısı
        """
        self.logger.info("=" * 70)
        self.logger.info(f"🏆 PUAN DURUMLARI HESAPLANIYOR ({workers} WORKER)")
        self.logger.info("=" * 70)
        
        # Önce eski kayıtları sil
        try:
            with self.db_manager as conn:
                cursor = conn.cursor()
                cursor.execute("DELETE FROM weekly_standings")
                cursor.execute("DELETE FROM current_standings")
                conn.commit()
                cursor.close()
                self.logger.info("🗑️  Eski puan durumları silindi")
        except Exception as e:
            self.logger.warning(f"⚠️  Silme hatası: {e}")
        
        # Season_id'lere göre grupla
        unique_seasons = matches_df['season_id'].unique()
        self.logger.info(f"🔄 {len(unique_seasons)} lig için puan durumu hesaplanacak...")
        
        all_standings = []
        processed = 0
        
        # TÜM LİGLERİ TEK DÖNGÜDE HESAPLA (Pandas'ta biriktir)
        self.logger.info("⚡ Tüm puan durumları hesaplanıyor (memory'de biriktiriliyor)...")
        
        for idx, season_id in enumerate(unique_seasons, 1):
            try:
                season_matches = matches_df[matches_df['season_id'] == season_id].copy()
                
                # Puan durumunu hesapla
                standings_df = self._calculate_single_season_standings(season_matches)
                
                if len(standings_df) > 0:
                    all_standings.append(standings_df)
                
                processed += 1
                
                # Her 50 ligde bir progress göster
                if processed % 50 == 0 or processed == len(unique_seasons):
                    progress = (processed / len(unique_seasons)) * 100
                    self.logger.info(f"📊 Progress: {processed}/{len(unique_seasons)} ({progress:.1f}%)")
                
            except Exception as e:
                self.logger.error(f"❌ {season_id} ligi hatası: {e}")
        
        # TÜM PUAN DURUMLARINI BİRLEŞTİR VE TEK SEFERDE KAYDET
        if all_standings:
            all_standings_df = pd.concat(all_standings, ignore_index=True)
            self.logger.info(f"✅ {len(all_standings_df):,} puan durumu hesaplandı!")
            self.logger.info("💾 TOPLU KAYIT BAŞLIYOR (COPY ile süper hızlı)...")
            
            total_saved = self.save_all_standings_bulk(all_standings_df)
            return total_saved
        else:
            self.logger.warning("⚠️  Hiç puan durumu hesaplanamadı!")
            return 0
    
    def save_all_standings_bulk(self, all_standings_df: pd.DataFrame) -> int:
        """
        TÜM PUAN DURUMLARINI TOPLU KAYDET - COPY ile süper hızlı!
        
        Args:
            all_standings_df: Tüm puan durumları DataFrame
            
        Returns:
            Kaydedilen kayıt sayısı
        """
        self.logger.info("💾 Puan durumları toplu kaydediliyor...")
        
        if len(all_standings_df) == 0:
            self.logger.warning("⚠️  Kaydedilecek puan durumu yok!")
            return 0
        
        try:
            with self.db_manager as conn:
                cursor = conn.cursor()
                
                # 1. HAFTALIK PUAN DURUMU (weekly_standings) - TOPLU
                self.logger.info("📊 Haftalık puan durumları kaydediliyor...")
                
                # Geçici tablo
                cursor.execute("""
                    CREATE TEMP TABLE temp_weekly_standings (
                        season_id INTEGER,
                        league VARCHAR(255),
                        country VARCHAR(255),
                        week_number INTEGER,
                        team_id INTEGER,
                        team_name VARCHAR(255),
                        position INTEGER,
                        played INTEGER,
                        wins INTEGER,
                        draws INTEGER,
                        losses INTEGER,
                        goals_for INTEGER,
                        goals_against INTEGER,
                        goal_difference INTEGER,
                        points INTEGER,
                        home_played INTEGER,
                        home_wins INTEGER,
                        home_draws INTEGER,
                        home_losses INTEGER,
                        home_goals_for INTEGER,
                        home_goals_against INTEGER,
                        away_played INTEGER,
                        away_wins INTEGER,
                        away_draws INTEGER,
                        away_losses INTEGER,
                        away_goals_for INTEGER,
                        away_goals_against INTEGER
                    ) ON COMMIT DROP;
                """)
                
                # COPY ile yükle
                with cursor.copy("""
                    COPY temp_weekly_standings (
                        season_id, league, country, week_number, team_id, team_name, position,
                        played, wins, draws, losses, goals_for, goals_against, goal_difference, points,
                        home_played, home_wins, home_draws, home_losses, home_goals_for, home_goals_against,
                        away_played, away_wins, away_draws, away_losses, away_goals_for, away_goals_against
                    ) FROM STDIN
                """) as copy:
                    for idx in range(len(all_standings_df)):
                        row = all_standings_df.iloc[idx]
                        copy.write_row((
                            int(row['season_id']), str(row['league']), str(row['country']), int(row['week_number']),
                            int(row['team_id']), str(row['team_name']), int(row['position']),
                            int(row['played']), int(row['wins']), int(row['draws']), int(row['losses']),
                            int(row['goals_for']), int(row['goals_against']), int(row['goal_difference']), int(row['points']),
                            int(row['home_played']), int(row['home_wins']), int(row['home_draws']), int(row['home_losses']),
                            int(row['home_goals_for']), int(row['home_goals_against']),
                            int(row['away_played']), int(row['away_wins']), int(row['away_draws']), int(row['away_losses']),
                            int(row['away_goals_for']), int(row['away_goals_against'])
                        ))
                
                # Asıl tabloya aktar
                cursor.execute("""
                    INSERT INTO weekly_standings (
                        season_id, league, country, week_number, team_id, team_name, position,
                        played, wins, draws, losses, goals_for, goals_against, goal_difference, points,
                        home_played, home_wins, home_draws, home_losses, home_goals_for, home_goals_against,
                        away_played, away_wins, away_draws, away_losses, away_goals_for, away_goals_against
                    )
                    SELECT * FROM temp_weekly_standings
                """)
                
                weekly_count = len(all_standings_df)
                self.logger.info(f"✅ {weekly_count:,} haftalık puan durumu kaydedildi")
                
                # 2. GÜNCEL PUAN DURUMU (current_standings) - Sadece son haftalar
                self.logger.info("🏆 Güncel puan durumları kaydediliyor...")
                
                # Her lig için son haftayı bul
                max_weeks = all_standings_df.groupby('season_id')['week_number'].max().reset_index()
                current_standings = all_standings_df.merge(max_weeks, on=['season_id', 'week_number'])
                
                # Geçici tablo
                cursor.execute("""
                    CREATE TEMP TABLE temp_current_standings (
                        season_id INTEGER,
                        league VARCHAR(255),
                        country VARCHAR(255),
                        team_id INTEGER,
                        team_name VARCHAR(255),
                        position INTEGER,
                        played INTEGER,
                        wins INTEGER,
                        draws INTEGER,
                        losses INTEGER,
                        goals_for INTEGER,
                        goals_against INTEGER,
                        goal_difference INTEGER,
                        points INTEGER,
                        home_played INTEGER,
                        home_wins INTEGER,
                        home_draws INTEGER,
                        home_losses INTEGER,
                        home_goals_for INTEGER,
                        home_goals_against INTEGER,
                        away_played INTEGER,
                        away_wins INTEGER,
                        away_draws INTEGER,
                        away_losses INTEGER,
                        away_goals_for INTEGER,
                        away_goals_against INTEGER
                    ) ON COMMIT DROP;
                """)
                
                # COPY ile yükle
                with cursor.copy("""
                    COPY temp_current_standings (
                        season_id, league, country, team_id, team_name, position,
                        played, wins, draws, losses, goals_for, goals_against, goal_difference, points,
                        home_played, home_wins, home_draws, home_losses, home_goals_for, home_goals_against,
                        away_played, away_wins, away_draws, away_losses, away_goals_for, away_goals_against
                    ) FROM STDIN
                """) as copy:
                    for idx in range(len(current_standings)):
                        row = current_standings.iloc[idx]
                        copy.write_row((
                            int(row['season_id']), str(row['league']), str(row['country']),
                            int(row['team_id']), str(row['team_name']), int(row['position']),
                            int(row['played']), int(row['wins']), int(row['draws']), int(row['losses']),
                            int(row['goals_for']), int(row['goals_against']), int(row['goal_difference']), int(row['points']),
                            int(row['home_played']), int(row['home_wins']), int(row['home_draws']), int(row['home_losses']),
                            int(row['home_goals_for']), int(row['home_goals_against']),
                            int(row['away_played']), int(row['away_wins']), int(row['away_draws']), int(row['away_losses']),
                            int(row['away_goals_for']), int(row['away_goals_against'])
                        ))
                
                # Asıl tabloya aktar
                cursor.execute("""
                    INSERT INTO current_standings (
                        season_id, league, country, team_id, team_name, position,
                        played, wins, draws, losses, goals_for, goals_against, goal_difference, points,
                        home_played, home_wins, home_draws, home_losses, home_goals_for, home_goals_against,
                        away_played, away_wins, away_draws, away_losses, away_goals_for, away_goals_against
                    )
                    SELECT * FROM temp_current_standings
                """)
                
                current_count = len(current_standings)
                self.logger.info(f"✅ {current_count:,} güncel puan durumu kaydedildi")
                
                conn.commit()
                cursor.close()
                
                return weekly_count + current_count
                
        except Exception as e:
            self.logger.error(f"❌ Toplu puan durumu kayıt hatası: {e}")
            return 0
    
    def process_all_matches_bulk(self, all_matches_df: pd.DataFrame) -> pd.DataFrame:
        """
        PANDAS İLE HEPSİNİ TEK SEFERDE İŞLE
        Her lig için haftalara böl
        
        Args:
            all_matches_df: Tüm maçlar DataFrame
            
        Returns:
            DataFrame: Hafta bilgili tüm maçlar
        """
        self.logger.info("=" * 70)
        self.logger.info("⚙️  PANDAS İLE TOPLU İŞLEME BAŞLADI")
        self.logger.info("=" * 70)
        
        all_results = []
        
        # Season_id'lere göre grupla
        unique_seasons = all_matches_df['season_id'].unique()
        total_seasons = len(unique_seasons)
        
        self.logger.info(f"🔄 {total_seasons} lig işlenecek...")
        
        for idx, season_id in enumerate(unique_seasons, 1):
            try:
                # Bu ligin maçlarını filtrele
                season_matches = all_matches_df[all_matches_df['season_id'] == season_id].copy()
                
                # Haftalara böl
                season_with_weeks = WeekDivider.divide_matches_into_weeks(season_matches, verbose=False)
                
                all_results.append(season_with_weeks)
                
                # Progress göster (her 100 ligde bir)
                if idx % 100 == 0:
                    progress = (idx / total_seasons) * 100
                    self.logger.info(f"📊 Progress: {idx}/{total_seasons} ({progress:.1f}%)")
                
                self.stats['processed'] += 1
                self.stats['successful'] += 1
                
            except Exception as e:
                self.logger.warning(f"❌ Season {season_id} hata: {e}")
                self.stats['failed'] += 1
                self.failed_leagues.append({
                    'season_id': season_id,
                    'error': str(e)
                })
        
        # Hepsini birleştir
        if all_results:
            final_df = pd.concat(all_results, ignore_index=True)
            self.logger.info(f"✅ {len(final_df):,} maç başarıyla işlendi!")
            return final_df
        else:
            self.logger.error("❌ Hiç maç işlenemedi!")
            return pd.DataFrame()
    
    def save_all_to_database_bulk(self, matches_df: pd.DataFrame) -> int:
        """
        TOPLU KAYIT - Önce sil, sonra ekle (fresh start!)
        
        Args:
            matches_df: Hafta bilgili tüm maçlar
            
        Returns:
            Kaydedilen kayıt sayısı
        """
        self.logger.info("=" * 70)
        self.logger.info("💾 VERİTABANINA TOPLU KAYIT BAŞLADI")
        self.logger.info("=" * 70)
        
        # ÖNCELİKLE ESKİ KAYITLARI SİL
        try:
            with self.db_manager as conn:
                cursor = conn.cursor()
                cursor.execute("DELETE FROM match_weeks")
                deleted_count = cursor.rowcount
                conn.commit()
                cursor.close()
                self.logger.info(f"🗑️  Önceki {deleted_count:,} kayıt silindi (fresh start)")
        except Exception as e:
            self.logger.warning(f"⚠️  Silme hatası (devam ediliyor): {e}")
        
        insert_sql = """
        INSERT INTO match_weeks (
            match_id, season_id, league, country, week_number,
            match_date, match_time, home_team_id, home_team,
            away_team_id, away_team, ht_home, ht_away, ft_home, ft_away, status
        ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        ON CONFLICT (match_id, season_id) 
        DO UPDATE SET 
            week_number = EXCLUDED.week_number,
            status = EXCLUDED.status,
            updated_at = CURRENT_TIMESTAMP
        """
        
        # Tüm dataları hazırla (status dahil!)
        data_list = []
        for _, match in matches_df.iterrows():
            data_list.append((
                int(match['match_id']),
                int(match['season_id']),
                match['league'],
                match['country'],
                int(match['hafta']),
                match['match_date'],
                match.get('match_time', ''),
                int(match['home_team_id']),
                match['home_team'],
                int(match['away_team_id']),
                match['away_team'],
                int(match['ht_home']) if pd.notna(match['ht_home']) else None,
                int(match['ht_away']) if pd.notna(match['ht_away']) else None,
                int(match['ft_home']) if pd.notna(match['ft_home']) else None,
                int(match['ft_away']) if pd.notna(match['ft_away']) else None,
                int(match['status'])
            ))
        
        self.logger.info(f"📦 {len(data_list):,} kayıt hazırlandı")
        
        try:
            with self.db_manager as conn:
                cursor = conn.cursor()
                
                # COPY ile süper hızlı kaydet!
                self.logger.info("🚀 COPY komutu ile toplu kayıt...")
                
                # Geçici tablo oluştur (status dahil!)
                copy_sql = """
                CREATE TEMP TABLE temp_matches (
                    match_id BIGINT,
                    season_id INTEGER,
                    league VARCHAR(255),
                    country VARCHAR(255),
                    week_number INTEGER,
                    match_date VARCHAR(50),
                    match_time VARCHAR(50),
                    home_team_id INTEGER,
                    home_team VARCHAR(255),
                    away_team_id INTEGER,
                    away_team VARCHAR(255),
                    ht_home SMALLINT,
                    ht_away SMALLINT,
                    ft_home SMALLINT,
                    ft_away SMALLINT,
                    status SMALLINT
                ) ON COMMIT DROP;
                """
                cursor.execute(copy_sql)
                
                # COPY ile veri yükle (status dahil!)
                with cursor.copy("""
                    COPY temp_matches (
                        match_id, season_id, league, country, week_number,
                        match_date, match_time, home_team_id, home_team,
                        away_team_id, away_team, ht_home, ht_away, ft_home, ft_away, status
                    ) FROM STDIN
                """) as copy:
                    for row in data_list:
                        copy.write_row(row)
                
                # Geçici tablodan asıl tabloya aktar (status dahil!)
                cursor.execute("""
                    INSERT INTO match_weeks (
                        match_id, season_id, league, country, week_number,
                        match_date, match_time, home_team_id, home_team,
                        away_team_id, away_team, ht_home, ht_away, ft_home, ft_away, status
                    )
                    SELECT 
                        match_id, season_id, league, country, week_number,
                        match_date, match_time, home_team_id, home_team,
                        away_team_id, away_team, ht_home, ht_away, ft_home, ft_away, status
                    FROM temp_matches
                """)
                
                conn.commit()
                cursor.close()
            
            self.logger.info(f"✅ {len(data_list):,} kayıt başarıyla kaydedildi!")
            return len(data_list)
            
        except Exception as e:
            self.logger.error(f"❌ Toplu kayıt hatası: {e}")
            
            # Hata varsa tek tek kaydetmeyi dene
            self.logger.warning("⚠️  Tek tek kayıt deneniyor...")
            return self._save_one_by_one(matches_df, insert_sql)
    
    def _save_one_by_one(self, matches_df: pd.DataFrame, insert_sql: str) -> int:
        """
        Tek tek kaydetme (yedek yöntem) - basit loop ile
        
        Args:
            matches_df: Maçlar DataFrame
            insert_sql: Insert SQL
            
        Returns:
            Kaydedilen kayıt sayısı
        """
        saved_count = 0
        
        try:
            # DataFrame'i list of tuples'a çevir
            data_list = []
            for idx in range(len(matches_df)):
                row = matches_df.iloc[idx]
                data_list.append((
                    int(row['match_id']),
                    int(row['season_id']),
                    str(row['league']),
                    str(row['country']),
                    int(row['hafta']),
                    str(row['match_date']),
                    str(row.get('match_time', '')),
                    int(row['home_team_id']),
                    str(row['home_team']),
                    int(row['away_team_id']),
                    str(row['away_team']),
                    int(row['ht_home']) if pd.notna(row['ht_home']) else None,
                    int(row['ht_away']) if pd.notna(row['ht_away']) else None,
                    int(row['ft_home']) if pd.notna(row['ft_home']) else None,
                    int(row['ft_away']) if pd.notna(row['ft_away']) else None
                ))
            
            self.logger.info(f"📦 {len(data_list):,} kayıt hazırlandı (yedek yöntem)")
            
            with self.db_manager as conn:
                cursor = conn.cursor()
                
                for idx, data in enumerate(data_list):
                    try:
                        cursor.execute(insert_sql, data)
                        saved_count += 1
                        
                        if (idx + 1) % 1000 == 0:
                            conn.commit()
                            self.logger.info(f"💾 {idx + 1:,} kayıt commit edildi...")
                    except Exception:
                        pass
                
                conn.commit()
                cursor.close()
                
            self.logger.info(f"✅ {saved_count:,} kayıt tek tek kaydedildi")
            return saved_count
            
        except Exception as e:
            self.logger.error(f"❌ Tek tek kayıt da başarısız: {e}")
            return 0
    
    def process_all_leagues_bulk(self, min_matches: int = 10, limit: Optional[int] = None, only_current_season: bool = True):
        """
        YENİ BULK METOD - Çok daha hızlı!
        1. Tek seferde tüm maçları çek
        2. Pandas ile gruplandır ve işle
        3. Tek seferde kaydet
        
        Args:
            min_matches: Minimum maç sayısı
            limit: İşlenecek maksimum lig sayısı (None ise hepsi)
            only_current_season: Her league_id için sadece güncel sezonu al (varsayılan: True)
        """
        self.stats['start_time'] = datetime.now()
        
        self.logger.info("=" * 70)
        self.logger.info("🚀 WEEK SERVICE BAŞLATILDI (BULK MODE)")
        if only_current_season:
            self.logger.info("✅ Mod: Sadece GÜNCEL SEZONLAR")
        else:
            self.logger.info("⚠️  Mod: TÜM SEZONLAR")
        self.logger.info("=" * 70)
        
        # Tablo kontrolü
        if not self.create_match_weeks_table():
            self.logger.error("Tablo oluşturulamadı, işlem durduruluyor!")
            return
        
        if not self.create_standings_tables():
            self.logger.error("Puan durumu tabloları oluşturulamadı, işlem durduruluyor!")
            return
        
        # 1. Tüm maçları tek seferde çek
        all_matches_df = self.load_all_matches(min_matches, limit, only_current_season)
        
        if len(all_matches_df) == 0:
            self.logger.error("❌ Hiç maç bulunamadı!")
            return
        
        self.stats['total_matches'] = len(all_matches_df)
        self.stats['total_leagues'] = all_matches_df['season_id'].nunique()
        
        # 2. Pandas ile hepsini işle
        processed_df = self.process_all_matches_bulk(all_matches_df)
        
        if len(processed_df) == 0:
            self.logger.error("❌ Hiç maç işlenemedi!")
            return
        
        # 3. Toplu kayıt
        saved_count = self.save_all_to_database_bulk(processed_df)
        
        # 4. Puan durumlarını hesapla ve kaydet
        standings_count = self.calculate_and_save_standings(processed_df)
        
        self.stats['end_time'] = datetime.now()
        
        # Özet rapor
        self.print_summary()
    
    def print_summary(self):
        """İşlem özeti yazdır"""
        self.logger.info("=" * 70)
        self.logger.info("📊 İŞLEM RAPORU")
        self.logger.info("=" * 70)
        
        duration = (self.stats['end_time'] - self.stats['start_time']).total_seconds()
        minutes = int(duration // 60)
        seconds = int(duration % 60)
        
        self.logger.info(f"✅ Toplam İşlenen: {self.stats['processed']} lig")
        self.logger.info(f"✅ Başarılı: {self.stats['successful']}")
        self.logger.info(f"❌ Başarısız: {self.stats['failed']}")
        self.logger.info(f"⚽ Toplam Maç: {self.stats['total_matches']:,}")
        self.logger.info(f"⏱️  Toplam Süre: {minutes} dakika {seconds} saniye")
        
        if self.failed_leagues:
            self.logger.warning(f"❌ Başarısız Ligler ({len(self.failed_leagues)}):")
            for failed in self.failed_leagues[:10]:
                self.logger.warning(
                    f"   • {failed['country']} - {failed['league']} (ID: {failed['season_id']})"
                )
        
        self.logger.info("=" * 70)
        self.logger.info("🎉 WEEK SERVICE TAMAMLANDI!")
        self.logger.info("=" * 70)


def main():
    """Ana fonksiyon"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Week Service - BULK MODE (Çok Hızlı!)')
    parser.add_argument('--min-matches', type=int, default=10, help='Minimum maç sayısı')
    parser.add_argument('--limit', type=int, help='İşlenecek maksimum lig sayısı')
    parser.add_argument('--test', action='store_true', help='Test modu (ilk 50 lig)')
    
    args = parser.parse_args()
    
    service = WeekService()
    
    # BULK MODE ile çalış
    limit = args.limit
    if args.test:
        limit = 50
        print(f"\n🧪 Test modu aktif - İlk 50 lig işlenecek (BULK MODE)")
    
    service.process_all_leagues_bulk(
        min_matches=args.min_matches,
        limit=limit
    )


if __name__ == "__main__":
    main()
