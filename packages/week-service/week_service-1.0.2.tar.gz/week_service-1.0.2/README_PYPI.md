# Week Service

Futbol maçlarını haftalara bölen ve puan durumu tablolarını oluşturan yüksek performanslı servis.

## 🚀 Kurulum

```bash
pip install week-service
```

## 📋 Özellikler

- ⚡ **Yüksek Performans**: COPY komutu ile toplu veri işleme
- 📊 **Haftalık Bölümleme**: Maçları otomatik haftalara böler
- 🏆 **Puan Durumu**: Haftalık ve güncel puan durumlarını hesaplar
- 🔒 **.env Desteği**: Güvenli veritabanı yapılandırması
- 🎯 **Esnek Filtreleme**: Status bazlı akıllı filtreleme

## ⚙️ Yapılandırma

`.env` dosyası oluşturun:

```env
DB_HOST=localhost
DB_PORT=5432
DB_NAME=football_db
DB_USER=your_user
DB_PASSWORD=your_password

MIN_MATCHES=5
BATCH_SIZE=10
```

## 💻 Kullanım

### CLI (Command Line)

```bash
# Güncel sezonları işle
week-service

# Tüm sezonları işle
week-service --all

# Minimum maç sayısı belirle
week-service --min-matches 10

# Test için limit koy
week-service --limit 50
```

### Python Kodu

```python
from week_service import WeekService

# Servis oluştur
service = WeekService()

# Tüm ligleri işle
service.process_all_leagues_bulk(
    min_matches=5,
    limit=None
)
```

## 📊 Veritabanı Tabloları

### match_weeks
Maçların haftalık bölümlenmesi:
- `match_id`, `season_id`, `week_number`
- `home_team`, `away_team`, `status`
- `match_date`, `match_time`

### weekly_standings
Haftalık puan durumları:
- `season_id`, `week_number`, `team_id`
- `position`, `played`, `wins`, `draws`, `losses`
- `points`, `goals_for`, `goals_against`

### current_standings
Güncel puan durumları (son hafta)

## 📈 Performans

- **77,701 maç** → 6 dakika
- **401 lig** → Tek batch işlem
- **155,733 puan durumu** → COPY ile toplu kayıt

## 🗂️ Proje Yapısı

```
week_service/
├── core/
│   ├── database.py           # .env destekli DB bağlantısı
│   ├── match_loader.py       # Maç yükleme
│   ├── week_divider.py       # Hafta bölme
│   └── standings_calculator.py  # Puan durumu
├── utils/
│   └── logger.py             # Loglama
├── cli.py                    # CLI arayüzü
├── week_service.py           # Ana servis
└── setup.py                  # PyPI paketi
```

## 📄 Lisans

MIT License

## 🤝 Katkıda Bulunma

Pull request'ler memnuniyetle karşılanır!
