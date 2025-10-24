"""SQL query parser using sqlglot."""
from typing import Any, Dict, List, Optional, Set

import sqlglot
from sqlglot import exp

from ..exceptions import ParserError


class SQLParser:
    """Parser for SQL queries using sqlglot."""
    
    def __init__(self, dialect: str = "postgres"):
        """
        Initialize SQL parser.
        
        Args:
            dialect: SQL dialect (postgres, mysql, clickhouse, etc.)
        """
        self.dialect = dialect
    
    def parse(self, query: str) -> Dict[str, Any]:
        """
        Parse SQL query and extract metadata.
        
        Args:
            query: SQL query string
            
        Returns:
            Dictionary with parsed metadata
        """
        try:
            # Parse query
            parsed = sqlglot.parse_one(query, dialect=self.dialect)
            
            # Extract metadata
            metadata = {
                'operation': self._get_operation(parsed),
                'tables': self._get_tables(parsed),
                'columns': self._get_columns(parsed),
                'where_conditions': self._has_where(parsed),
                'joins': self._get_joins(parsed),
                'aggregations': self._get_aggregations(parsed),
            }
            
            return metadata
            
        except Exception as e:
            raise ParserError(f"Failed to parse SQL query: {e}")
    
    def _get_operation(self, parsed: exp.Expression) -> str:
        """Extract the main operation type."""
        if isinstance(parsed, exp.Select):
            return "SELECT"
        elif isinstance(parsed, exp.Insert):
            return "INSERT"
        elif isinstance(parsed, exp.Update):
            return "UPDATE"
        elif isinstance(parsed, exp.Delete):
            return "DELETE"
        elif isinstance(parsed, exp.Create):
            return "CREATE"
        elif isinstance(parsed, exp.Drop):
            return "DROP"
        elif isinstance(parsed, exp.Alter):
            return "ALTER"
        else:
            return "UNKNOWN"
    
    def _get_tables(self, parsed: exp.Expression) -> List[str]:
        """Extract all table names referenced in the query."""
        tables = set()
        
        for table in parsed.find_all(exp.Table):
            table_name = table.name
            schema = table.db
            
            if schema:
                tables.add(f"{schema}.{table_name}")
            else:
                tables.add(table_name)
        
        return sorted(tables)
    
    def _get_columns(self, parsed: exp.Expression) -> List[str]:
        """Extract all column names referenced in the query."""
        columns = set()
        
        # Get columns from SELECT clause
        for col in parsed.find_all(exp.Column):
            col_name = col.name
            if col_name != '*':
                columns.add(col_name)
        
        return sorted(columns)
    
    def _has_where(self, parsed: exp.Expression) -> bool:
        """Check if query has WHERE clause."""
        return any(parsed.find_all(exp.Where))
    
    def _get_joins(self, parsed: exp.Expression) -> List[str]:
        """Extract join types used in the query."""
        joins = []
        
        for join in parsed.find_all(exp.Join):
            join_type = join.side or "INNER"
            joins.append(join_type.upper())
        
        return joins
    
    def _get_aggregations(self, parsed: exp.Expression) -> List[str]:
        """Extract aggregation functions used."""
        aggregations = set()
        
        agg_functions = {
            exp.Count, exp.Sum, exp.Avg, exp.Min, exp.Max,
            exp.StddevPop, exp.StddevSamp, exp.VariancePop, exp.VarianceSamp
        }
        
        for agg_type in agg_functions:
            if any(parsed.find_all(agg_type)):
                aggregations.add(agg_type.__name__.upper())
        
        return sorted(aggregations)
    
    def get_schema_from_query(self, query: str) -> str:
        """
        Extract schema.table format from query.
        
        Args:
            query: SQL query string
            
        Returns:
            Schema.table string (e.g., "public.patients")
        """
        try:
            metadata = self.parse(query)
            tables = metadata['tables']
            
            if not tables:
                return "unknown"
            
            # Return first table (primary table)
            return tables[0]
            
        except Exception:
            return "unknown"
    
    def get_fields_from_query(self, query: str) -> List[str]:
        """
        Extract field names from query.
        
        Args:
            query: SQL query string
            
        Returns:
            List of field names
        """
        try:
            metadata = self.parse(query)
            return metadata['columns']
        except Exception:
            return []


if __name__ == "__main__":
    print("Testing SQLParser...")
    
    # Test PostgreSQL queries
    parser = SQLParser(dialect="postgres")
    
    # Test 1: Simple SELECT
    query1 = "SELECT id, name, age FROM users WHERE age > 25"
    result1 = parser.parse(query1)
    print(f"✓ Parsed simple SELECT:")
    print(f"  Operation: {result1['operation']}")
    print(f"  Tables: {result1['tables']}")
    print(f"  Columns: {result1['columns']}")
    print(f"  Has WHERE: {result1['where_conditions']}")
    
    # Test 2: JOIN query
    query2 = """
    SELECT u.name, o.order_id 
    FROM users u 
    INNER JOIN orders o ON u.id = o.user_id
    """
    result2 = parser.parse(query2)
    print(f"\n✓ Parsed JOIN query:")
    print(f"  Tables: {result2['tables']}")
    print(f"  Joins: {result2['joins']}")
    
    # Test 3: Aggregation query
    query3 = "SELECT COUNT(*), AVG(age), MAX(salary) FROM employees GROUP BY department"
    result3 = parser.parse(query3)
    print(f"\n✓ Parsed aggregation query:")
    print(f"  Aggregations: {result3['aggregations']}")
    
    # Test 4: Schema extraction
    query4 = "SELECT * FROM public.patients LIMIT 10"
    schema = parser.get_schema_from_query(query4)
    print(f"\n✓ Extracted schema: {schema}")
    
    # Test 5: Field extraction
    fields = parser.get_fields_from_query(query1)
    print(f"\n✓ Extracted fields: {fields}")
    
    # Test 6: Different operations
    queries = [
        ("INSERT INTO users (name) VALUES ('John')", "INSERT"),
        ("UPDATE users SET name = 'Jane' WHERE id = 1", "UPDATE"),
        ("DELETE FROM users WHERE id = 1", "DELETE"),
    ]
    
    print(f"\n✓ Testing different operations:")
    for query, expected_op in queries:
        result = parser.parse(query)
        assert result['operation'] == expected_op
        print(f"  {expected_op}: ✓")
    
    print("\n✓ All SQL parser tests passed")