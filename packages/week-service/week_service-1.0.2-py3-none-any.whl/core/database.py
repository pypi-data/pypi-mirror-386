"""
🗄️ DATABASE MANAGER
Week Service için bağımsız veritabanı yöneticisi
"""

import os
import psycopg
from typing import Dict, Any
from dotenv import load_dotenv


class DatabaseManager:
    """Veritabanı bağlantı yöneticisi"""
    
    def __init__(self, config: Dict[str, Any] = None):
        """
        Args:
            config: Veritabanı yapılandırması
        """
        self.config = config or self._load_config_from_env()
        self._connection = None
    
    @staticmethod
    def _load_config_from_env() -> Dict[str, Any]:
        """
        .env dosyasından veritabanı yapılandırmasını yükle
        
        Returns:
            Veritabanı yapılandırması
        """
        # .env dosyasını yükle
        load_dotenv()
        
        return {
            'host': os.getenv('DB_HOST', 'localhost'),
            'port': int(os.getenv('DB_PORT', '5432')),
            'dbname': os.getenv('DB_NAME', 'football_db'),
            'user': os.getenv('DB_USER', 'postgres'),
            'password': os.getenv('DB_PASSWORD', '')
        }
    
    def connect(self):
        """Veritabanına bağlan"""
        if self._connection is None or self._connection.closed:
            self._connection = psycopg.connect(**self.config)
        return self._connection
    
    def disconnect(self):
        """Bağlantıyı kapat"""
        if self._connection and not self._connection.closed:
            self._connection.close()
            self._connection = None
    
    def get_connection(self):
        """Aktif bağlantıyı döndür"""
        return self.connect()
    
    def __enter__(self):
        """Context manager - with bloğu için"""
        return self.connect()
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager - otomatik kapanış"""
        self.disconnect()
