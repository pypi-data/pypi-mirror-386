 # Das ist BuildTools v2 von ClayTech ©2025 - Enhanced SQL Save Module
import os
import sqlite3
import pickle
import json
import datetime
import threading
import hashlib
import zlib
import time
from typing import Any, Dict, List, Optional, Union, Tuple
from pathlib import Path
from contextlib import contextmanager


class SqlSaveError(Exception):
    """Custom exception for SqlSave operations"""
    pass


class SqlSaveConfig:
    """Configuration class for SqlSave"""
    
    def __init__(self):
        self.compression_enabled = True
        self.encryption_enabled = False
        self.backup_enabled = True
        self.max_backup_files = 5
        self.cache_enabled = True
        self.cache_size = 100
        self.auto_vacuum = True
        self.journal_mode = "WAL"  # WAL, DELETE, TRUNCATE, PERSIST, MEMORY, OFF
        self.synchronous = "NORMAL"  # OFF, NORMAL, FULL, EXTRA
        self.timeout = 30.0  # Connection timeout in seconds


class SqlSaveCache:
    """Simple LRU Cache for SqlSave"""
    
    def __init__(self, max_size: int = 100):
        self.max_size = max_size
        self.cache = {}
        self.access_order = []
        self.lock = threading.RLock()
    
    def get(self, key: str) -> Any:
        with self.lock:
            if key in self.cache:
                # Move to end (most recently used)
                self.access_order.remove(key)
                self.access_order.append(key)
                return self.cache[key]
            return None
    
    def set(self, key: str, value: Any):
        with self.lock:
            if key in self.cache:
                # Update existing
                self.cache[key] = value
                self.access_order.remove(key)
                self.access_order.append(key)
            else:
                # Add new
                if len(self.cache) >= self.max_size:
                    # Remove least recently used
                    oldest = self.access_order.pop(0)
                    del self.cache[oldest]
                
                self.cache[key] = value
                self.access_order.append(key)
    
    def remove(self, key: str):
        with self.lock:
            if key in self.cache:
                del self.cache[key]
                self.access_order.remove(key)
    
    def clear(self):
        with self.lock:
            self.cache.clear()
            self.access_order.clear()


class SqlSaveStats:
    """Statistics tracking for SqlSave operations"""
    
    def __init__(self):
        self.reads = 0
        self.writes = 0
        self.deletes = 0
        self.cache_hits = 0
        self.cache_misses = 0
        self.errors = 0
        self.start_time = time.time()
        self.lock = threading.RLock()
    
    def increment_reads(self):
        with self.lock:
            self.reads += 1
    
    def increment_writes(self):
        with self.lock:
            self.writes += 1
    
    def increment_deletes(self):
        with self.lock:
            self.deletes += 1
    
    def increment_cache_hits(self):
        with self.lock:
            self.cache_hits += 1
    
    def increment_cache_misses(self):
        with self.lock:
            self.cache_misses += 1
    
    def increment_errors(self):
        with self.lock:
            self.errors += 1
    
    def get_stats(self) -> Dict[str, Any]:
        with self.lock:
            uptime = time.time() - self.start_time
            total_ops = self.reads + self.writes + self.deletes
            cache_total = self.cache_hits + self.cache_misses
            
            return {
                "reads": self.reads,
                "writes": self.writes,
                "deletes": self.deletes,
                "total_operations": total_ops,
                "cache_hits": self.cache_hits,
                "cache_misses": self.cache_misses,
                "cache_hit_ratio": self.cache_hits / max(cache_total, 1) * 100,
                "errors": self.errors,
                "uptime_seconds": uptime,
                "operations_per_second": total_ops / max(uptime, 1)
            }


class SqlSave:
    """Enhanced SQL Save class with advanced features while maintaining compatibility"""
    
    def __init__(self, db: str = "default", config: Optional[SqlSaveConfig] = None):
        """
        Initialize SqlSave with enhanced features
        
        Args:
            db: Database name
            config: Configuration object (optional)
        """
        # Original compatibility attributes
        self.appdata_path = os.environ.get('APPDATA')
        self.db_dir = os.path.join(self.appdata_path, 'BuildTools', 'data')
        self.db_path = os.path.join(self.db_dir, f'{db}.db')
        
        # Enhanced attributes
        self.db_name = db
        self.config = config or SqlSaveConfig()
        self.cache = SqlSaveCache(self.config.cache_size) if self.config.cache_enabled else None
        self.stats = SqlSaveStats()
        self.lock = threading.RLock()
        
        # Backup directory
        self.backup_dir = os.path.join(self.db_dir, 'backups')
        
        # Ensure directories exist
        os.makedirs(self.db_dir, exist_ok=True)
        os.makedirs(self.backup_dir, exist_ok=True)
        
        # Initialize database
        self._init_db()
        
        # Setup database optimizations
        self._setup_optimizations()
    
    @contextmanager
    def _get_connection(self):
        """Context manager for database connections"""
        conn = None
        try:
            conn = sqlite3.connect(
                self.db_path, 
                timeout=self.config.timeout,
                check_same_thread=False
            )
            conn.row_factory = sqlite3.Row  # Enable column access by name
            yield conn
        except Exception as e:
            self.stats.increment_errors()
            if conn:
                conn.rollback()
            raise SqlSaveError(f"Database error: {str(e)}")
        finally:
            if conn:
                conn.close()
    
    def _init_db(self):
        """Initialize database with enhanced schema"""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            
            # Original table for compatibility
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS saved_data (
                    id TEXT PRIMARY KEY,
                    data BLOB
                )
            ''')
            
            # Enhanced table with metadata
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS saved_data_enhanced (
                    id TEXT PRIMARY KEY,
                    data BLOB NOT NULL,
                    data_type TEXT,
                    compressed BOOLEAN DEFAULT 0,
                    encrypted BOOLEAN DEFAULT 0,
                    checksum TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    access_count INTEGER DEFAULT 0,
                    size_bytes INTEGER,
                    tags TEXT,
                    metadata TEXT
                )
            ''')
            
            # Indexes for performance
            cursor.execute('''
                CREATE INDEX IF NOT EXISTS idx_created_at ON saved_data_enhanced(created_at)
            ''')
            cursor.execute('''
                CREATE INDEX IF NOT EXISTS idx_updated_at ON saved_data_enhanced(updated_at)
            ''')
            cursor.execute('''
                CREATE INDEX IF NOT EXISTS idx_data_type ON saved_data_enhanced(data_type)
            ''')
            cursor.execute('''
                CREATE INDEX IF NOT EXISTS idx_tags ON saved_data_enhanced(tags)
            ''')
            
            # Triggers for auto-updating timestamps
            cursor.execute('''
                CREATE TRIGGER IF NOT EXISTS update_timestamp
                AFTER UPDATE ON saved_data_enhanced
                BEGIN
                    UPDATE saved_data_enhanced SET updated_at = CURRENT_TIMESTAMP WHERE id = NEW.id;
                END
            ''')
            
            conn.commit()
    
    def _setup_optimizations(self):
        """Setup database optimizations"""
        with self._get_connection() as conn:
            cursor = conn.cursor()
            
            # Set journal mode
            cursor.execute(f"PRAGMA journal_mode = {self.config.journal_mode}")
            
            # Set synchronous mode
            cursor.execute(f"PRAGMA synchronous = {self.config.synchronous}")
            
            # Enable auto vacuum if configured
            if self.config.auto_vacuum:
                cursor.execute("PRAGMA auto_vacuum = INCREMENTAL")
            
            # Set cache size (in KB)
            cursor.execute("PRAGMA cache_size = 10000")
            
            # Enable foreign keys
            cursor.execute("PRAGMA foreign_keys = ON")
            
            conn.commit()
    
    def _compress_data(self, data: bytes) -> bytes:
        """Compress data using zlib"""
        if self.config.compression_enabled:
            return zlib.compress(data)
        return data
    
    def _decompress_data(self, data: bytes, compressed: bool) -> bytes:
        """Decompress data if it was compressed"""
        if compressed and self.config.compression_enabled:
            return zlib.decompress(data)
        return data
    
    def _calculate_checksum(self, data: bytes) -> str:
        """Calculate SHA-256 checksum of data"""
        return hashlib.sha256(data).hexdigest()
    
    def _serialize_data(self, data: Any) -> Tuple[bytes, str]:
        """Serialize data and return bytes + type info"""
        data_type = type(data).__name__
        
        if isinstance(data, (dict, list)):
            # Use JSON for dict/list for better readability
            serialized = json.dumps(data, ensure_ascii=False, default=str).encode('utf-8')
            data_type = f"json_{data_type}"
        else:
            # Use pickle for other types
            serialized = pickle.dumps(data)
            data_type = f"pickle_{data_type}"
        
        return serialized, data_type
    
    def _deserialize_data(self, data: bytes, data_type: str) -> Any:
        """Deserialize data based on type info"""
        if data_type.startswith("json_"):
            return json.loads(data.decode('utf-8'))
        else:
            return pickle.loads(data)
    
    def _create_backup(self):
        """Create a backup of the current database"""
        if not self.config.backup_enabled:
            return
        
        try:
            timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_name = f"{self.db_name}_backup_{timestamp}.db"
            backup_path = os.path.join(self.backup_dir, backup_name)
            
            # Copy database file
            import shutil
            shutil.copy2(self.db_path, backup_path)
            
            # Clean old backups
            self._cleanup_old_backups()
            
        except Exception as e:
            # Don't fail the main operation if backup fails
            pass
    
    def _cleanup_old_backups(self):
        """Remove old backup files, keeping only the latest N files"""
        try:
            backup_files = []
            for file in os.listdir(self.backup_dir):
                if file.startswith(f"{self.db_name}_backup_") and file.endswith('.db'):
                    file_path = os.path.join(self.backup_dir, file)
                    backup_files.append((file_path, os.path.getctime(file_path)))
            
            # Sort by creation time, newest first
            backup_files.sort(key=lambda x: x[1], reverse=True)
            
            # Remove old files
            for file_path, _ in backup_files[self.config.max_backup_files:]:
                try:
                    os.remove(file_path)
                except:
                    pass
        except:
            pass
    
    # ==================== ORIGINAL METHODS (MAINTAINED FOR COMPATIBILITY) ====================
    
    def save(self, data: Any, id: str) -> bool:
        """Original save method - maintained for compatibility"""
        try:
            serialized_data = pickle.dumps(data)
            
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    INSERT OR REPLACE INTO saved_data (id, data) VALUES (?, ?)
                ''', (id, serialized_data))
                conn.commit()
                
            self.stats.increment_writes()
            
            # Update cache if enabled
            if self.cache:
                self.cache.set(id, data)
            
            return True
        except Exception as e:
            self.stats.increment_errors()
            return False
    
    def load(self, id: str) -> Any:
        """Original load method - maintained for compatibility"""
        try:
            # Check cache first
            if self.cache:
                cached_data = self.cache.get(id)
                if cached_data is not None:
                    self.stats.increment_cache_hits()
                    self.stats.increment_reads()
                    return cached_data
                self.stats.increment_cache_misses()
            
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('SELECT data FROM saved_data WHERE id = ?', (id,))
                result = cursor.fetchone()
            
            if result:
                data = pickle.loads(result[0])
                
                # Update cache
                if self.cache:
                    self.cache.set(id, data)
                
                self.stats.increment_reads()
                return data
            
            self.stats.increment_reads()
            return None
        except Exception as e:
            self.stats.increment_errors()
            return None
    
    def delete(self, id: str) -> bool:
        """Original delete method - enhanced with cache invalidation"""
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('DELETE FROM saved_data WHERE id = ?', (id,))
                conn.commit()
            
            # Remove from cache
            if self.cache:
                self.cache.remove(id)
            
            self.stats.increment_deletes()
            return True
        except Exception as e:
            self.stats.increment_errors()
            return False
    
    def update(self, id: str, data: Any) -> bool:
        """Original update method - maintained for compatibility"""
        return self.save(data, id)  # Same as save for original method
    
    def search(self, db: str, id: str) -> bool:
        """Original search method - maintained for compatibility"""
        try:
            db_path = os.path.join(self.db_dir, f'{db}.db')
            if not os.path.exists(db_path):
                return False

            with sqlite3.connect(db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('SELECT 1 FROM saved_data WHERE id = ?', (id,))
                result = cursor.fetchone()
            
            return result is not None
        except Exception as e:
            return False
    
    def clear(self, db: str) -> bool:
        """Original clear method - maintained for compatibility"""
        try:
            db_path = os.path.join(self.db_dir, f'{db}.db')
            if os.path.exists(db_path):
                os.remove(db_path)
                return True
            return False
        except Exception as e:
            return False
    
    # ==================== ENHANCED METHODS ====================
    
    def save_enhanced(self, data: Any, id: str, tags: Optional[List[str]] = None, 
                     metadata: Optional[Dict[str, Any]] = None) -> bool:
        """
        Enhanced save method with additional features
        
        Args:
            data: Data to save
            id: Unique identifier
            tags: Optional tags for categorization
            metadata: Optional metadata dictionary
        """
        try:
            with self.lock:
                # Create backup before major operations
                self._create_backup()
                
                # Serialize data
                serialized_data, data_type = self._serialize_data(data)
                
                # Compress if enabled
                compressed = self.config.compression_enabled
                if compressed:
                    serialized_data = self._compress_data(serialized_data)
                
                # Calculate checksum
                checksum = self._calculate_checksum(serialized_data)
                
                # Prepare tags and metadata
                tags_str = json.dumps(tags) if tags else None
                metadata_str = json.dumps(metadata) if metadata else None
                
                with self._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute('''
                        INSERT OR REPLACE INTO saved_data_enhanced 
                        (id, data, data_type, compressed, encrypted, checksum, 
                         size_bytes, tags, metadata, access_count)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, 
                                COALESCE((SELECT access_count FROM saved_data_enhanced WHERE id = ?), 0))
                    ''', (id, serialized_data, data_type, compressed, False, 
                         checksum, len(serialized_data), tags_str, metadata_str, id))
                    conn.commit()
                
                # Update cache
                if self.cache:
                    self.cache.set(id, data)
                
                self.stats.increment_writes()
                return True
                
        except Exception as e:
            self.stats.increment_errors()
            raise SqlSaveError(f"Failed to save data: {str(e)}")
    
    def load_enhanced(self, id: str, update_access_count: bool = True) -> Optional[Any]:
        """
        Enhanced load method with access tracking
        
        Args:
            id: Unique identifier
            update_access_count: Whether to increment access counter
        """
        try:
            # Check cache first
            if self.cache:
                cached_data = self.cache.get(id)
                if cached_data is not None:
                    self.stats.increment_cache_hits()
                    self.stats.increment_reads()
                    return cached_data
                self.stats.increment_cache_misses()
            
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    SELECT data, data_type, compressed, checksum 
                    FROM saved_data_enhanced WHERE id = ?
                ''', (id,))
                result = cursor.fetchone()
                
                if not result:
                    self.stats.increment_reads()
                    return None
                
                data_blob, data_type, compressed, stored_checksum = result
                
                # Verify checksum
                calculated_checksum = self._calculate_checksum(data_blob)
                if calculated_checksum != stored_checksum:
                    raise SqlSaveError(f"Data corruption detected for id: {id}")
                
                # Decompress if needed
                data_blob = self._decompress_data(data_blob, compressed)
                
                # Deserialize
                data = self._deserialize_data(data_blob, data_type)
                
                # Update access count
                if update_access_count:
                    cursor.execute('''
                        UPDATE saved_data_enhanced 
                        SET access_count = access_count + 1 
                        WHERE id = ?
                    ''', (id,))
                    conn.commit()
                
                # Update cache
                if self.cache:
                    self.cache.set(id, data)
                
                self.stats.increment_reads()
                return data
                
        except Exception as e:
            self.stats.increment_errors()
            raise SqlSaveError(f"Failed to load data: {str(e)}")
    
    def get_metadata(self, id: str) -> Optional[Dict[str, Any]]:
        """Get metadata for a stored item"""
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    SELECT data_type, compressed, encrypted, created_at, 
                           updated_at, access_count, size_bytes, tags, metadata
                    FROM saved_data_enhanced WHERE id = ?
                ''', (id,))
                result = cursor.fetchone()
                
                if not result:
                    return None
                
                tags = json.loads(result[7]) if result[7] else []
                metadata = json.loads(result[8]) if result[8] else {}
                
                return {
                    "data_type": result[0],
                    "compressed": bool(result[1]),
                    "encrypted": bool(result[2]),
                    "created_at": result[3],
                    "updated_at": result[4],
                    "access_count": result[5],
                    "size_bytes": result[6],
                    "tags": tags,
                    "metadata": metadata
                }
        except Exception as e:
            self.stats.increment_errors()
            raise SqlSaveError(f"Failed to get metadata: {str(e)}")
    
    def list_all_ids(self, table: str = "enhanced") -> List[str]:
        """List all stored IDs"""
        try:
            table_name = "saved_data_enhanced" if table == "enhanced" else "saved_data"
            
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute(f'SELECT id FROM {table_name} ORDER BY id')
                results = cursor.fetchall()
                
                return [row[0] for row in results]
        except Exception as e:
            self.stats.increment_errors()
            raise SqlSaveError(f"Failed to list IDs: {str(e)}")
    
    def find_by_tags(self, tags: List[str], match_all: bool = True) -> List[str]:
        """Find items by tags"""
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                
                if match_all:
                    # All tags must be present
                    placeholders = ' AND '.join(['tags LIKE ?' for _ in tags])
                    params = [f'%"{tag}"%' for tag in tags]
                else:
                    # Any tag can be present
                    placeholders = ' OR '.join(['tags LIKE ?' for _ in tags])
                    params = [f'%"{tag}"%' for tag in tags]
                
                cursor.execute(f'''
                    SELECT id FROM saved_data_enhanced 
                    WHERE {placeholders}
                    ORDER BY updated_at DESC
                ''', params)
                
                results = cursor.fetchall()
                return [row[0] for row in results]
        except Exception as e:
            self.stats.increment_errors()
            raise SqlSaveError(f"Failed to find by tags: {str(e)}")
    
    def get_database_stats(self) -> Dict[str, Any]:
        """Get comprehensive database statistics"""
        try:
            with self._get_connection() as conn:
                cursor = conn.cursor()
                
                # Basic counts
                cursor.execute('SELECT COUNT(*) FROM saved_data')
                original_count = cursor.fetchone()[0]
                
                cursor.execute('SELECT COUNT(*) FROM saved_data_enhanced')
                enhanced_count = cursor.fetchone()[0]
                
                # Enhanced table stats
                cursor.execute('''
                    SELECT 
                        SUM(size_bytes) as total_size,
                        AVG(size_bytes) as avg_size,
                        MAX(size_bytes) as max_size,
                        MIN(size_bytes) as min_size,
                        SUM(access_count) as total_accesses,
                        AVG(access_count) as avg_accesses
                    FROM saved_data_enhanced
                ''')
                size_stats = cursor.fetchone()
                
                # Data type distribution
                cursor.execute('''
                    SELECT data_type, COUNT(*) as count 
                    FROM saved_data_enhanced 
                    GROUP BY data_type
                ''')
                type_distribution = dict(cursor.fetchall())
                
                # Database file size
                db_size = os.path.getsize(self.db_path) if os.path.exists(self.db_path) else 0
                
                stats = {
                    "database_name": self.db_name,
                    "database_file_size": db_size,
                    "original_table_count": original_count,
                    "enhanced_table_count": enhanced_count,
                    "total_data_size": size_stats[0] or 0,
                    "average_item_size": size_stats[1] or 0,
                    "largest_item_size": size_stats[2] or 0,
                    "smallest_item_size": size_stats[3] or 0,
                    "total_accesses": size_stats[4] or 0,
                    "average_accesses": size_stats[5] or 0,
                    "data_type_distribution": type_distribution,
                    "operation_stats": self.stats.get_stats()
                }
                
                return stats
        except Exception as e:
            self.stats.increment_errors()
            raise SqlSaveError(f"Failed to get database stats: {str(e)}")
    
    def vacuum_database(self) -> bool:
        """Perform database vacuum to reclaim space"""
        try:
            with self._get_connection() as conn:
                conn.execute('VACUUM')
                conn.commit()
            return True
        except Exception as e:
            self.stats.increment_errors()
            return False
    
    def export_to_json(self, output_file: str, table: str = "enhanced") -> bool:
        """Export database contents to JSON file"""
        try:
            table_name = "saved_data_enhanced" if table == "enhanced" else "saved_data"
            
            with self._get_connection() as conn:
                cursor = conn.cursor()
                
                if table == "enhanced":
                    cursor.execute('''
                        SELECT id, data_type, created_at, updated_at, 
                               access_count, tags, metadata
                        FROM saved_data_enhanced
                    ''')
                    
                    export_data = {}
                    for row in cursor.fetchall():
                        item_data = {
                            "data": self.load_enhanced(row[0], update_access_count=False),
                            "data_type": row[1],
                            "created_at": row[2],
                            "updated_at": row[3],
                            "access_count": row[4],
                            "tags": json.loads(row[5]) if row[5] else [],
                            "metadata": json.loads(row[6]) if row[6] else {}
                        }
                        export_data[row[0]] = item_data
                else:
                    cursor.execute('SELECT id FROM saved_data')
                    export_data = {}
                    for row in cursor.fetchall():
                        export_data[row[0]] = self.load(row[0])
                
                with open(output_file, 'w', encoding='utf-8') as f:
                    json.dump(export_data, f, indent=2, ensure_ascii=False, default=str)
                
                return True
        except Exception as e:
            self.stats.increment_errors()
            return False
    
    def import_from_json(self, input_file: str) -> bool:
        """Import data from JSON file"""
        try:
            with open(input_file, 'r', encoding='utf-8') as f:
                import_data = json.load(f)
            
            for item_id, item_data in import_data.items():
                if isinstance(item_data, dict) and "data" in item_data:
                    # Enhanced format
                    self.save_enhanced(
                        data=item_data["data"],
                        id=item_id,
                        tags=item_data.get("tags"),
                        metadata=item_data.get("metadata")
                    )
                else:
                    # Simple format
                    self.save(item_data, item_id)
            
            return True
        except Exception as e:
            self.stats.increment_errors()
            return False
    
    def cleanup_old_items(self, days: int = 30) -> int:
        """Remove items older than specified days"""
        try:
            cutoff_date = datetime.datetime.now() - datetime.timedelta(days=days)
            
            with self._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    DELETE FROM saved_data_enhanced 
                    WHERE updated_at < ?
                ''', (cutoff_date.isoformat(),))
                deleted_count = cursor.rowcount
                conn.commit()
            
            # Clear cache for deleted items
            if self.cache:
                self.cache.clear()
            
            return deleted_count
        except Exception as e:
            self.stats.increment_errors()
            return 0
    
    def get_cache_stats(self) -> Dict[str, Any]:
        """Get cache statistics"""
        if not self.cache:
            return {"cache_enabled": False}
        
        return {
            "cache_enabled": True,
            "cache_size": len(self.cache.cache),
            "max_cache_size": self.cache.max_size,
            "cache_usage_percent": len(self.cache.cache) / self.cache.max_size * 100
        }
    
    def clear_cache(self):
        """Clear the in-memory cache"""
        if self.cache:
            self.cache.clear()


# ==================== UTILITY FUNCTIONS ====================

def create_multiple_databases(db_names: List[str], config: Optional[SqlSaveConfig] = None) -> Dict[str, SqlSave]:
    """Create multiple SqlSave instances"""
    databases = {}
    for name in db_names:
        databases[name] = SqlSave(name, config)
    return databases


def migrate_legacy_data(source_db: str, target_db: str) -> bool:
    """Migrate data from legacy format to enhanced format"""
    try:
        source = SqlSave(source_db)
        target = SqlSave(target_db)
        
        # Get all IDs from source
        ids = source.list_all_ids("original")
        
        for item_id in ids:
            data = source.load(item_id)
            if data is not None:
                target.save_enhanced(data, item_id, tags=["migrated"])
        
        return True
    except Exception:
        return False


# ==================== BACKWARDS COMPATIBILITY ====================

# Keep original class available for existing code
class SqlSaveOriginal:
    """Original SqlSave class for complete backwards compatibility"""
    
    def __init__(self, db="default"):
        self.appdata_path = os.environ.get('APPDATA')
        self.db_dir = os.path.join(self.appdata_path, 'BuildTools', 'data')
        self.db_path = os.path.join(self.db_dir, f'{db}.db')
        os.makedirs(self.db_dir, exist_ok=True)
        self._init_db()
    
    def _init_db(self):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS saved_data (
                id TEXT PRIMARY KEY,
                data BLOB
            )
        ''')
        conn.commit()
        conn.close()
    
    def save(self, data, id):
        serialized_data = pickle.dumps(data)
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute('''
                INSERT OR REPLACE INTO saved_data (id, data) VALUES (?, ?)
            ''', (id, serialized_data))
            conn.commit()
            conn.close()
            return True
        except Exception as e:
            return False
    
    def load(self, id):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute('SELECT data FROM saved_data WHERE id = ?', (id,))
        result = cursor.fetchone()
        conn.close()
        
        if result:
            return pickle.loads(result[0])
        return None
    
    def delete(self, id):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute('DELETE FROM saved_data WHERE id = ?', (id,))
        conn.commit()
        conn.close()

    def update(self, id, data):
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute('''
            UPDATE saved_data SET data = ? WHERE id = ?
        ''', (pickle.dumps(data), id))
        conn.commit()
        conn.close()
        
    def search(self, db, id):
        db_path = os.path.join(self.db_dir, f'{db}.db')
        if not os.path.exists(db_path):
            return False

        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        cursor.execute('SELECT 1 FROM saved_data WHERE id = ?', (id,))
        result = cursor.fetchone()
        conn.close()
        
        return result is not None
    
    def clear(self, db):
        db_path = os.path.join(self.db_dir, f'{db}.db')
        if os.path.exists(db_path):
            os.remove(db_path)
            return True
        return False


# ==================== EXAMPLE USAGE ====================

if __name__ == "__main__":
    # Example usage of enhanced SqlSave
    
    # Create config
    config = SqlSaveConfig()
    config.compression_enabled = True
    config.backup_enabled = True
    config.cache_enabled = True
    
    # Create SqlSave instance
    db = SqlSave("example_db", config)
    
    # Save some data with tags and metadata
    db.save_enhanced(
        data={"name": "John", "age": 30},
        id="user_1",
        tags=["user", "active"],
        metadata={"created_by": "admin", "version": 1}
    )
    
    # Load data
    user_data = db.load_enhanced("user_1")
    print(f"Loaded user data: {user_data}")
    
    # Get metadata
    metadata = db.get_metadata("user_1")
    print(f"Metadata: {metadata}")
    
    # Get database statistics
    stats = db.get_database_stats()
    print(f"Database stats: {stats}")
    
    # Find by tags
    tagged_items = db.find_by_tags(["user"])
    print(f"Items with 'user' tag: {tagged_items}")
    
    # Export to JSON
    db.export_to_json("backup.json")
    
    print("Enhanced SqlSave example completed successfully!")