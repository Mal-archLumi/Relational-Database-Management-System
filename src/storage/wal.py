"""
Write-Ahead Logging for crash recovery
"""
import json
import os
from datetime import datetime
from typing import List, Dict, Any

class WriteAheadLog:
    """Simple Write-Ahead Log implementation"""
    
    def __init__(self, db_file: str):
        self.wal_file = db_file.replace('.maldb', '.wal')
        self.entries = []
        self._load_entries()
    
    def _load_entries(self):
        """Load existing WAL entries"""
        if os.path.exists(self.wal_file):
            try:
                with open(self.wal_file, 'r') as f:
                    for line in f:
                        if line.strip():
                            self.entries.append(json.loads(line))
            except:
                self.entries = []
    
    def log_transaction(self, operation: str, table: str, data: Dict):
        """Log a transaction operation"""
        entry = {
            'timestamp': datetime.now().isoformat(),
            'operation': operation,
            'table': table,
            'data': data,
            'committed': False
        }
        
        self.entries.append(entry)
        self._flush()
    
    def commit(self, transaction_id: int = None):
        """Mark transaction as committed"""
        if transaction_id is not None and transaction_id < len(self.entries):
            self.entries[transaction_id]['committed'] = True
        else:
            # Mark all as committed
            for entry in self.entries:
                entry['committed'] = True
        
        self._flush()
    
    def rollback(self, transaction_id: int = None):
        """Rollback transaction"""
        if transaction_id is not None:
            self.entries = self.entries[:transaction_id]
        else:
            self.entries = []
        
        self._flush()
    
    def checkpoint(self):
        """Create checkpoint - clear committed entries"""
        self.entries = [e for e in self.entries if not e.get('committed', True)]
        self._flush()
    
    def _flush(self):
        """Write entries to disk"""
        with open(self.wal_file, 'w') as f:
            for entry in self.entries:
                f.write(json.dumps(entry) + '\n')
    
    def get_uncommitted(self) -> List[Dict]:
        """Get uncommitted transactions"""
        return [e for e in self.entries if not e.get('committed', True)]