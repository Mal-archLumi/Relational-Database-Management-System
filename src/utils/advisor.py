"""
Index advisor - suggests indexes based on query patterns
"""
import re
from typing import List, Dict, Any
from collections import defaultdict

class IndexAdvisor:
    """Suggests indexes based on query patterns"""
    
    def __init__(self):
        self.query_patterns = defaultdict(lambda: defaultdict(int))
        self.where_clauses = defaultdict(set)
    
    def analyze_query(self, sql: str, table: str):
        """Analyze a query for index opportunities"""
        sql_upper = sql.upper()
        
        # Extract WHERE clauses
        if 'WHERE' in sql_upper:
            # Simple pattern matching for WHERE clauses
            where_match = re.search(r'WHERE\s+(.*?)(?:\s+ORDER BY|\s+LIMIT|$)', sql_upper, re.IGNORECASE | re.DOTALL)
            if where_match:
                where_clause = where_match.group(1)
                # Look for column = value patterns
                equality_matches = re.finditer(r'(\w+)\s*=\s*[\'"]?\w+[\'"]?', where_clause)
                for match in equality_matches:
                    column = match.group(1).lower()
                    self.where_clauses[table].add(column)
                    self.query_patterns[table][column] += 1
        
        # Look for JOIN conditions
        if 'JOIN' in sql_upper:
            join_match = re.search(r'JOIN\s+\w+\s+ON\s+([^=]+)=([^=]+)', sql_upper, re.IGNORECASE)
            if join_match:
                left_col = join_match.group(1).strip().split('.')[-1]
                right_col = join_match.group(2).strip().split('.')[-1]
                self.where_clauses[table].add(left_col)
                self.query_patterns[table][left_col] += 1
    
    def get_recommendations(self) -> List[Dict]:
        """Get index recommendations"""
        recommendations = []
        
        for table, columns in self.where_clauses.items():
            for column in columns:
                frequency = self.query_patterns[table][column]
                
                if frequency >= 3:  # Recommend index if column appears in >= 3 queries
                    recommendations.append({
                        'table': table,
                        'column': column,
                        'frequency': frequency,
                        'sql': f"CREATE INDEX idx_{table}_{column} ON {table}({column})"
                    })
        
        # Sort by frequency (highest first)
        recommendations.sort(key=lambda x: x['frequency'], reverse=True)
        
        return recommendations
    
    def print_recommendations(self):
        """Print index recommendations"""
        recs = self.get_recommendations()
        
        if not recs:
            print("No index recommendations at this time.")
            return
        
        print("\n📊 Index Recommendations:")
        print("=" * 60)
        
        for rec in recs:
            print(f"\nTable: {rec['table']}")
            print(f"Column: {rec['column']}")
            print(f"Usage frequency: {rec['frequency']} queries")
            print(f"Suggested index: {rec['sql']}")
            print("-" * 40)