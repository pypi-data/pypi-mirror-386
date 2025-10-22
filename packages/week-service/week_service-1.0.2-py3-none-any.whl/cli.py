"""
Week Service CLI
Command Line Interface for Week Service
"""
import argparse
import sys
from week_service.week_service import WeekService


def main():
    """Main CLI entry point"""
    parser = argparse.ArgumentParser(
        description='Week Service - Futbol maçlarını haftalara böler ve puan durumu hesaplar'
    )
    
    parser.add_argument(
        '--all',
        action='store_true',
        help='Tüm ligleri işle (varsayılan: sadece güncel sezonlar)'
    )
    
    parser.add_argument(
        '--min-matches',
        type=int,
        default=5,
        help='Minimum maç sayısı (varsayılan: 5)'
    )
    
    parser.add_argument(
        '--limit',
        type=int,
        help='İşlenecek maksimum lig sayısı (test için)'
    )
    
    args = parser.parse_args()
    
    try:
        print("=" * 80)
        print("🚀 WEEK SERVICE BAŞLATILIYOR")
        print("=" * 80)
        
        service = WeekService()
        
        service.process_all_leagues_bulk(
            current_seasons_only=not args.all,
            min_matches=args.min_matches,
            limit=args.limit
        )
        
        print("=" * 80)
        print("✅ İŞLEM BAŞARIYLA TAMAMLANDI!")
        print("=" * 80)
        
        return 0
        
    except KeyboardInterrupt:
        print("\n⚠️  İşlem kullanıcı tarafından iptal edildi")
        return 1
        
    except Exception as e:
        print(f"\n❌ HATA: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == '__main__':
    sys.exit(main())
