"""
📝 LOGGER
Basit loglama sistemi
"""

import logging
from pathlib import Path
from datetime import datetime


class ServiceLogger:
    """Servis loglama sınıfı"""
    
    def __init__(self, name: str = "WeekService", log_dir: str = None):
        """
        Args:
            name: Logger adı
            log_dir: Log dizini (opsiyonel)
        """
        self.name = name
        self.log_dir = Path(log_dir) if log_dir else Path(__file__).parent.parent / "logs"
        self.log_dir.mkdir(exist_ok=True)
        
        # Logger oluştur
        self.logger = logging.getLogger(name)
        self.logger.setLevel(logging.INFO)
        
        # Formatter
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        
        # Console handler
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.INFO)
        console_handler.setFormatter(formatter)
        
        # File handler
        log_file = self.log_dir / f"{name}_{datetime.now().strftime('%Y%m%d')}.log"
        file_handler = logging.FileHandler(log_file, encoding='utf-8')
        file_handler.setLevel(logging.DEBUG)
        file_handler.setFormatter(formatter)
        
        # Handlers ekle
        self.logger.addHandler(console_handler)
        self.logger.addHandler(file_handler)
    
    def info(self, message: str):
        """Bilgi logu"""
        self.logger.info(message)
    
    def error(self, message: str):
        """Hata logu"""
        self.logger.error(message)
    
    def warning(self, message: str):
        """Uyarı logu"""
        self.logger.warning(message)
    
    def debug(self, message: str):
        """Debug logu"""
        self.logger.debug(message)
