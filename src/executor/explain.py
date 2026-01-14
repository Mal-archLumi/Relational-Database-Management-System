"""
Query plan explanation and visualization
"""
from tabulate import tabulate

def explain_plan(plan: dict) -> str:
    """
    Generate explanation for query plan
    
    Returns:
        Formatted explanation string
    """
    if plan['command'] == 'SELECT':
        return f"""
        Execution Plan:
        ---------------
        Operation: SELECT
        Table: {plan['table']}
        Columns: {', '.join(plan['columns'])}
        Strategy: Full Table Scan
        """
    elif plan['command'] == 'INSERT':
        return f"""
        Execution Plan:
        ---------------
        Operation: INSERT
        Table: {plan['table']}
        Values: {plan['values']}
        """
    elif plan['command'] == 'CREATE_TABLE':
        columns_info = []
        for col in plan['columns']:
            constraints = []
            if col.primary_key:
                constraints.append("PRIMARY KEY")
            if col.unique:
                constraints.append("UNIQUE")
            if col.not_null:
                constraints.append("NOT NULL")
            if col.encrypted:
                constraints.append("ENCRYPTED")
            
            columns_info.append([col.name, col.dtype_str, ', '.join(constraints)])
        
        table_str = tabulate(columns_info, headers=['Column', 'Type', 'Constraints'])
        return f"""
        Execution Plan:
        ---------------
        Operation: CREATE TABLE
        Table: {plan['table']}
        
        Schema:
        {table_str}
        """
    
    return "No explanation available"