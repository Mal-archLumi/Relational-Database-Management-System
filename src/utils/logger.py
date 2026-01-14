"""
Query logging utility
"""
import logging
import time
from datetime import datetime
from typing import Dict, Any

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("maldb")

class QueryLogger:
    """Logs query execution for analysis"""
    
    def __init__(self, log_file: str = "maldb_queries.log"):
        self.log_file = log_file
        self.queries = []
    
    def log_query(self, sql: str, execution_time: float, success: bool = True, error: str = None):
        """Log a query execution"""
        entry = {
            'timestamp': datetime.now().isoformat(),
            'sql': sql,
            'execution_time_ms': execution_time * 1000,
            'success': success,
            'error': error
        }
        
        self.queries.append(entry)
        
        # Log to file
        with open(self.log_file, 'a') as f:
            f.write(f"{entry['timestamp']} | {execution_time:.2f}ms | {'SUCCESS' if success else 'FAILED'} | {sql}\n")
        
        # Log to console if slow query
        if execution_time > 0.1:  # > 100ms
            logger.warning(f"Slow query detected: {execution_time:.2f}s - {sql[:100]}...")
    
    def get_slow_queries(self, threshold_ms: float = 100) -> list:
        """Get queries slower than threshold"""
        return [q for q in self.queries if q['execution_time_ms'] > threshold_ms]
    
    def get_frequent_queries(self, limit: int = 10) -> list:
        """Get most frequent queries"""
        from collections import Counter
        sql_list = [q['sql'] for q in self.queries]
        return Counter(sql_list).most_common(limit)