# 🚀 Week Service

Veritabanındaki tüm ligler için maçları haftalara bölen ve kaydeden bağımsız servis.

## 📁 Klasör Yapısı

```
week_service/
├── core/
│   ├── __init__.py
│   ├── database.py          # Veritabanı bağlantısı
│   ├── match_loader.py      # Maç yükleme
│   └── week_divider.py      # Hafta bölme algoritması
├── utils/
│   ├── __init__.py
│   └── logger.py            # Loglama sistemi
├── logs/                    # Log dosyaları
├── week_service.py          # Ana servis
├── test_service.py          # Test scripti
└── README.md               # Bu dosya
```

## 🎯 Özellikler

- ✅ Tamamen bağımsız çalışır
- ✅ Tüm ligleri otomatik bulur
- ✅ Maçları haftalara böler
- ✅ Veritabanına kaydeder
- ✅ Log tutar
- ✅ Hata yönetimi
- ✅ Test modu

## 🚀 Kullanım

### 1. Tek Lig İşle
```bash
python week_service.py --season-id 70381
```

### 2. Tüm Ligleri İşle
```bash
python week_service.py
```

### 3. Test Modu (İlk 5 Lig)
```bash
python week_service.py --test
```

### 4. Limit ile Çalıştır
```bash
python week_service.py --limit 10
```

### 5. Minimum Maç Sayısı Belirt
```bash
python week_service.py --min-matches 20
```

## 🧪 Test

```bash
python test_service.py
```

## 📊 Veritabanı

Servis `match_weeks` tablosunu otomatik oluşturur:

```sql
CREATE TABLE match_weeks (
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
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT unique_match_season UNIQUE(match_id, season_id)
);
```

## 📝 Loglar

Loglar `logs/` klasörüne kaydedilir:
- `WeekService_YYYYMMDD.log`

## 🔍 Örnek Sorgular

### Bir Ligdeki Tüm Haftalar
```sql
SELECT week_number, COUNT(*) as match_count
FROM match_weeks
WHERE season_id = 70381
GROUP BY week_number
ORDER BY week_number;
```

### Bir Takımın Haftalık Maçları
```sql
SELECT week_number, match_date, home_team, away_team, 
       ft_home, ft_away
FROM match_weeks
WHERE season_id = 70381 
  AND (home_team_id = 1 OR away_team_id = 1)
ORDER BY week_number;
```

### Belirli Bir Haftanın Maçları
```sql
SELECT * FROM match_weeks
WHERE season_id = 70381 AND week_number = 5
ORDER BY match_date;
```

## ⚙️ Parametreler

| Parametre | Açıklama | Varsayılan |
|-----------|----------|------------|
| `--season-id` | Tek bir season_id işle | - |
| `--min-matches` | Minimum maç sayısı | 10 |
| `--limit` | Maksimum lig sayısı | - |
| `--test` | Test modu (ilk 5 lig) | False |

## 📈 İşlem Raporu

Servis tamamlandığında özet rapor verir:

```
📊 İŞLEM RAPORU
======================================================================
✅ Toplam İşlenen: 156 lig
✅ Başarılı: 152
❌ Başarısız: 4
⚽ Toplam Maç: 45,678
⏱️  Toplam Süre: 5 dakika 23 saniye
======================================================================
```

## 🛠️ Bağımlılıklar

- `psycopg` (PostgreSQL bağlantısı)
- `pandas` (Veri işleme)

## 📞 Destek

Herhangi bir sorun için log dosyalarını kontrol edin.
