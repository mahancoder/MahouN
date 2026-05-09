"""
Neo4j Backup and Recovery
==========================

Automated backup and recovery for Neo4j knowledge graph.
"""

import logging
import subprocess
import json
from pathlib import Path
from datetime import datetime, timedelta
import schedule
import time

logger = logging.getLogger(__name__)


class Neo4jBackupManager:
    """
    Neo4j backup and recovery manager
    
    Features:
    - Scheduled backups every 24 hours
    - Neo4j dump format
    - Metadata storage
    - Restore functionality
    - Keep last 7 backups
    """
    
    def __init__(
        self,
        backup_dir: str = "data/backups/neo4j",
        neo4j_container: str = "mahoun-neo4j",
        database: str = "neo4j",
        keep_count: int = 7
    ):
        """
        Initialize backup manager
        
        Args:
            backup_dir: Directory to store backups
            neo4j_container: Docker container name
            database: Neo4j database name
            keep_count: Number of backups to keep
        """
        self.backup_dir = Path(backup_dir)
        self.backup_dir.mkdir(parents=True, exist_ok=True)
        
        self.neo4j_container = neo4j_container
        self.database = database
        self.keep_count = keep_count
    
    def create_backup(self, description: str = "") -> Optional[Dict]:
        """
        Create a backup of Neo4j database
        
        Args:
            description: Optional backup description
        
        Returns:
            Backup metadata or None if failed
        """
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_name = f"neo4j_backup_{timestamp}"
            backup_path = self.backup_dir / backup_name
            
            logger.info(f"Creating backup: {backup_name}")
            
            # Create backup using neo4j-admin dump
            dump_file = f"{backup_name}.dump"
            container_path = f"/backups/{dump_file}"
            
            # Execute dump command in container
            dump_cmd = [
                "docker", "exec", self.neo4j_container,
                "neo4j-admin", "database", "dump", self.database,
                "--to-path", container_path
            ]
            
            result = subprocess.run(
                dump_cmd,
                capture_output=True,
                text=True,
                timeout=3600  # 1 hour timeout
            )
            
            if result.returncode != 0:
                logger.error(f"Backup failed: {result.stderr}")
                return None
            
            # Copy dump file from container to host
            host_dump_path = self.backup_dir / dump_file
            copy_cmd = [
                "docker", "cp",
                f"{self.neo4j_container}:{container_path}",
                str(host_dump_path)
            ]
            
            result = subprocess.run(
                copy_cmd,
                capture_output=True,
                text=True,
                timeout=600
            )
            
            if result.returncode != 0:
                logger.error(f"Failed to copy backup: {result.stderr}")
                return None
            
            # Get backup size
            backup_size = host_dump_path.stat().st_size
            
            # Get graph statistics
            stats = self._get_graph_stats()
            
            # Create metadata
            metadata = {
                'timestamp': timestamp,
                'datetime': datetime.now().isoformat(),
                'backup_name': backup_name,
                'dump_file': dump_file,
                'size_bytes': backup_size,
                'size_mb': round(backup_size / (1024 * 1024), 2),
                'database': self.database,
                'description': description,
                'statistics': stats,
            }
            
            # Save metadata
            metadata_file = self.backup_dir / f"{backup_name}.json"
            with open(metadata_file, 'w', encoding='utf-8') as f:
                json.dump(metadata, f, indent=2, ensure_ascii=False)
            
            logger.info(
                f"Backup created successfully: {dump_file} "
                f"({metadata['size_mb']} MB)"
            )
            
            # Cleanup old backups
            self._cleanup_old_backups()
            
            return metadata
        
        except subprocess.TimeoutExpired:
            logger.error("Backup timeout")
            return None
        
        except Exception as e:
            logger.error(f"Backup failed: {e}", exc_info=True)
            return None
    
    def restore_backup(self, backup_name: str, force: bool = False) -> bool:
        """
        Restore from a backup
        
        Args:
            backup_name: Name of backup to restore
            force: Force restore even if database exists
        
        Returns:
            True if successful
        """
        try:
            dump_file = f"{backup_name}.dump"
            dump_path = self.backup_dir / dump_file
            
            if not dump_path.exists():
                logger.error(f"Backup not found: {dump_file}")
                return False
            
            logger.info(f"Restoring backup: {backup_name}")
            
            # Copy dump file to container
            container_path = f"/backups/{dump_file}"
            copy_cmd = [
                "docker", "cp",
                str(dump_path),
                f"{self.neo4j_container}:{container_path}"
            ]
            
            result = subprocess.run(
                copy_cmd,
                capture_output=True,
                text=True,
                timeout=600
            )
            
            if result.returncode != 0:
                logger.error(f"Failed to copy backup to container: {result.stderr}")
                return False
            
            # Stop Neo4j
            logger.info("Stopping Neo4j...")
            stop_cmd = [
                "docker", "exec", self.neo4j_container,
                "neo4j", "stop"
            ]
            subprocess.run(stop_cmd, timeout=60)
            time.sleep(5)
            
            # Restore using neo4j-admin load
            load_cmd = [
                "docker", "exec", self.neo4j_container,
                "neo4j-admin", "database", "load", self.database,
                "--from-path", container_path
            ]
            
            if force:
                load_cmd.append("--overwrite-destination=true")
            
            result = subprocess.run(
                load_cmd,
                capture_output=True,
                text=True,
                timeout=3600
            )
            
            if result.returncode != 0:
                logger.error(f"Restore failed: {result.stderr}")
                return False
            
            # Start Neo4j
            logger.info("Starting Neo4j...")
            start_cmd = [
                "docker", "exec", self.neo4j_container,
                "neo4j", "start"
            ]
            subprocess.run(start_cmd, timeout=60)
            time.sleep(10)
            
            logger.info("Restore completed successfully")
            return True
        
        except subprocess.TimeoutExpired:
            logger.error("Restore timeout")
            return False
        
        except Exception as e:
            logger.error(f"Restore failed: {e}", exc_info=True)
            return False
    
    def list_backups(self) -> List[Dict]:
        """
        List all available backups
        
        Returns:
            List of backup metadata
        """
        backups = []
        
        for metadata_file in sorted(self.backup_dir.glob("*.json"), reverse=True):
            try:
                with open(metadata_file, 'r', encoding='utf-8') as f:
                    metadata = json.load(f)
                    backups.append(metadata)
            except Exception as e:
                logger.warning(f"Failed to read metadata {metadata_file}: {e}")
        
        return backups
    
    def get_backup_info(self, backup_name: str) -> Optional[Dict]:
        """
        Get information about a specific backup
        
        Args:
            backup_name: Name of backup
        
        Returns:
            Backup metadata or None
        """
        metadata_file = self.backup_dir / f"{backup_name}.json"
        
        if not metadata_file.exists():
            return None
        
        try:
            with open(metadata_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"Failed to read backup info: {e}")
            return None
    
    def delete_backup(self, backup_name: str) -> bool:
        """
        Delete a backup
        
        Args:
            backup_name: Name of backup to delete
        
        Returns:
            True if successful
        """
        try:
            dump_file = self.backup_dir / f"{backup_name}.dump"
            metadata_file = self.backup_dir / f"{backup_name}.json"
            
            if dump_file.exists():
                dump_file.unlink()
            
            if metadata_file.exists():
                metadata_file.unlink()
            
            logger.info(f"Deleted backup: {backup_name}")
            return True
        
        except Exception as e:
            logger.error(f"Failed to delete backup: {e}")
            return False
    
    def _cleanup_old_backups(self):
        """Clean up old backups, keeping only the most recent ones"""
        try:
            backups = self.list_backups()
            
            if len(backups) <= self.keep_count:
                return
            
            # Delete old backups
            for backup in backups[self.keep_count:]:
                backup_name = backup['backup_name']
                self.delete_backup(backup_name)
                logger.info(f"Cleaned up old backup: {backup_name}")
        
        except Exception as e:
            logger.warning(f"Failed to cleanup old backups: {e}")
    
    def _get_graph_stats(self) -> Dict:
        """Get graph statistics for metadata"""
        try:
            # This would normally query Neo4j for stats
            # For now, return empty dict
            return {
                'note': 'Statistics require Neo4j connection'
            }
        except Exception as e:
            logger.warning(f"Failed to get graph stats: {e}")
            return {}
    
    def schedule_backups(self, time_str: str = "02:00"):
        """
        Schedule daily backups
        
        Args:
            time_str: Time to run backup (HH:MM format)
        """
        logger.info(f"Scheduling daily backups at {time_str}")
        
        schedule.every().day.at(time_str).do(
            self.create_backup,
            description="Scheduled daily backup"
        )
        
        # Run immediately on start (optional)
        # self.create_backup(description="Initial backup")
        
        try:
            while True:
                schedule.run_pending()
                time.sleep(60)
        
        except KeyboardInterrupt:
            logger.info("Backup scheduler stopped")


# ============================================================================
# Convenience Functions
# ============================================================================

def create_backup(
    backup_dir: str = "data/backups/neo4j",
    description: str = ""
) -> Optional[Dict]:
    """
    Quick backup function
    
    Args:
        backup_dir: Directory to store backup
        description: Backup description
    
    Returns:
        Backup metadata
    """
    manager = Neo4jBackupManager(backup_dir)
    return manager.create_backup(description)


def restore_backup(
    backup_name: str,
    backup_dir: str = "data/backups/neo4j",
    force: bool = False
) -> bool:
    """
    Quick restore function
    
    Args:
        backup_name: Name of backup to restore
        backup_dir: Backup directory
        force: Force restore
    
    Returns:
        True if successful
    """
    manager = Neo4jBackupManager(backup_dir)
    return manager.restore_backup(backup_name, force)


def list_backups(backup_dir: str = "data/backups/neo4j") -> List[Dict]:
    """
    List all backups
    
    Args:
        backup_dir: Backup directory
    
    Returns:
        List of backup metadata
    """
    manager = Neo4jBackupManager(backup_dir)
    return manager.list_backups()


if __name__ == '__main__':
    # Run as standalone script
    import sys
    from core.logging import setup_logging
    
    setup_logging(__name__)
    
    if len(sys.argv) < 2:
        print("Usage:")
        print("  python neo4j_backup.py backup [description]")
        print("  python neo4j_backup.py restore <backup_name>")
        print("  python neo4j_backup.py list")
        print("  python neo4j_backup.py schedule [time]")
        sys.exit(1)
    
    command = sys.argv[1]
    manager = Neo4jBackupManager()
    
    if command == "backup":
        description = sys.argv[2] if len(sys.argv) > 2 else ""
        metadata = manager.create_backup(description)
        if metadata:
            print(f"Backup created: {metadata['backup_name']}")
            print(f"Size: {metadata['size_mb']} MB")
        else:
            print("Backup failed!")
            sys.exit(1)
    
    elif command == "restore":
        if len(sys.argv) < 3:
            print("Error: backup name required")
            sys.exit(1)
        
        backup_name = sys.argv[2]
        force = "--force" in sys.argv
        
        if manager.restore_backup(backup_name, force):
            print("Restore successful!")
        else:
            print("Restore failed!")
            sys.exit(1)
    
    elif command == "list":
        backups = manager.list_backups()
        print(f"\nAvailable backups ({len(backups)}):\n")
        for backup in backups:
            print(f"  {backup['backup_name']}")
            print(f"    Date: {backup['datetime']}")
            print(f"    Size: {backup['size_mb']} MB")
            if backup.get('description'):
                print(f"    Description: {backup['description']}")
            print()
    
    elif command == "schedule":
        time_str = sys.argv[2] if len(sys.argv) > 2 else "02:00"
        manager.schedule_backups(time_str)
    
    else:
        print(f"Unknown command: {command}")
        sys.exit(1)
