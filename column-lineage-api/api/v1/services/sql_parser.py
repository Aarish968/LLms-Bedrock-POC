"""SQL parsing service for column lineage analysis."""

import sqlglot
from sqlglot import exp
from typing import Dict, Any, List, Optional

from api.core.logging import LoggerMixin


class SQLParser(LoggerMixin):
    """SQL parser for extracting column lineage from DDL statements."""
    
    def __init__(self, dialect: str = "snowflake"):
        self.dialect = dialect
    
    def analyze_ddl_statement(self, sql_text: str) -> Dict[str, Any]:
        """Analyze DDL statement and extract column lineage."""
        try:
            parsed = sqlglot.parse_one(sql_text, dialect=self.dialect)
            
            # Determine DDL type and structure
            ddl_info = self._analyze_ddl_structure(parsed)
            
            if not ddl_info['is_supported']:
                return {'error': f"Unsupported DDL type: {ddl_info['type']}"}
            
            # Initialize analysis with generalized structure
            analysis = {
                'ddl_type': ddl_info['type'],
                'object_name': ddl_info['object_name'],
                'object_columns': ddl_info['object_columns'],
                'source_tables': [],
                'column_mappings': {},
                'derived_columns': {},
                'cte_definitions': {},
                'table_aliases': {},
                'cte_column_details': {}
            }
            
            # Detect SQL pattern and choose approach
            sql_pattern = self._detect_sql_pattern(parsed, analysis)
            
            if sql_pattern == 'identifier_function':
                return self._analyze_identifier_pattern(parsed, analysis)
            elif sql_pattern == 'wildcard_dominant':
                return self._analyze_wildcard_pattern(parsed, analysis)
            elif sql_pattern == 'nested_cte_dominant':
                return self._analyze_cte_pattern(parsed, analysis)
            else:
                # Hybrid approach
                return self._analyze_hybrid_pattern(parsed, analysis)
                
        except Exception as e:
            self.logger.error("DDL analysis failed", error=str(e))
            return {'error': f"Analysis failed: {str(e)}"}
    
    def _analyze_ddl_structure(self, parsed) -> Dict[str, Any]:
        """Analyze DDL structure to determine type and extract basic info."""
        ddl_info = {
            'type': 'UNKNOWN',
            'object_name': '',
            'object_columns': [],
            'is_supported': False
        }
        
        try:
            if isinstance(parsed, exp.Create):
                if parsed.kind and 'VIEW' in str(parsed.kind).upper():
                    ddl_info['type'] = 'CREATE_VIEW'
                    ddl_info['is_supported'] = True
                    
                    # Extract view name
                    if parsed.this:
                        ddl_info['object_name'] = str(parsed.this)
                    
                    # Extract columns from SELECT statement
                    if parsed.expression and isinstance(parsed.expression, exp.Select):
                        select_stmt = parsed.expression
                        for expr in select_stmt.expressions:
                            if isinstance(expr, exp.Alias):
                                ddl_info['object_columns'].append(str(expr.alias))
                            elif isinstance(expr, exp.Column):
                                ddl_info['object_columns'].append(str(expr.name))
                            elif isinstance(expr, exp.Star):
                                # Wildcard - columns will be resolved later
                                pass
                            else:
                                # Derived column - use expression as column name
                                expr_str = str(expr)
                                if len(expr_str) < 50:  # Reasonable column name length
                                    col_name = expr_str.replace(' ', '_').replace('(', '').replace(')', '')
                                    ddl_info['object_columns'].append(col_name)
                
                elif parsed.kind and 'TABLE' in str(parsed.kind).upper():
                    ddl_info['type'] = 'CREATE_TABLE'
                    ddl_info['is_supported'] = True
                    
                    # Extract table name
                    if parsed.this:
                        ddl_info['object_name'] = str(parsed.this)
                    
                    # Extract columns from schema or SELECT
                    if hasattr(parsed, 'expression') and parsed.expression:
                        # CREATE TABLE AS SELECT
                        ddl_info['object_columns'] = self._extract_ctas_columns(parsed)
                    else:
                        # CREATE TABLE with schema
                        ddl_info['object_columns'] = self._extract_table_columns_from_schema(parsed)
            
        except Exception as e:
            self.logger.error("Failed to analyze DDL structure", error=str(e))
        
        return ddl_info
    
    def _extract_table_columns_from_schema(self, parsed) -> List[str]:
        """Extract column names from CREATE TABLE schema definition."""
        columns = []
        try:
            if hasattr(parsed, 'this') and hasattr(parsed.this, 'expressions'):
                for expr in parsed.this.expressions:
                    if isinstance(expr, exp.ColumnDef):
                        columns.append(str(expr.this))
        except Exception as e:
            self.logger.error("Failed to extract table columns", error=str(e))
        return columns
    
    def _extract_ctas_columns(self, parsed) -> List[str]:
        """Extract column names from CREATE TABLE AS SELECT statement."""
        columns = []
        try:
            if hasattr(parsed, 'expression') and parsed.expression:
                select_stmt = parsed.expression
                if isinstance(select_stmt, exp.Select):
                    for expr in select_stmt.expressions:
                        if isinstance(expr, exp.Alias):
                            columns.append(str(expr.alias))
                        elif isinstance(expr, exp.Column):
                            columns.append(str(expr.name))
                        elif isinstance(expr, exp.Star):
                            return []  # Wildcard - will be resolved later
                        else:
                            expr_str = str(expr)
                            if len(expr_str) < 50:
                                columns.append(expr_str.replace(' ', '_').replace('(', '').replace(')', ''))
        except Exception as e:
            self.logger.error("Failed to extract CTAS columns", error=str(e))
        return columns
    
    def _detect_sql_pattern(self, parsed, analysis) -> str:
        """Detect SQL pattern to choose the right analysis approach."""
        # Check for IDENTIFIER() function
        for node in parsed.walk():
            if isinstance(node, exp.Anonymous) and str(node.this).upper() == 'IDENTIFIER':
                return 'identifier_function'
        
        # Count different SQL elements
        cte_count = 0
        wildcard_count = 0
        explicit_alias_count = 0
        
        for node in parsed.walk():
            if isinstance(node, exp.CTE):
                cte_count += 1
            elif isinstance(node, exp.Star):
                wildcard_count += 1
            elif isinstance(node, exp.Alias):
                explicit_alias_count += 1
        
        if cte_count >= 1 and wildcard_count > 0:
            return 'hybrid'
        elif cte_count >= 1 and wildcard_count == 0:
            return 'nested_cte_dominant'
        elif wildcard_count > 0 and cte_count == 0:
            return 'wildcard_dominant'
        else:
            return 'hybrid'
    
    def _analyze_identifier_pattern(self, parsed, analysis) -> Dict[str, Any]:
        """Handle IDENTIFIER() function pattern."""
        # Extract IDENTIFIER() table name
        identifier_table = None
        for node in parsed.walk():
            if isinstance(node, exp.Anonymous) and str(node.this).upper() == 'IDENTIFIER':
                if node.expressions:
                    table_name_expr = node.expressions[0]
                    if isinstance(table_name_expr, exp.Literal):
                        identifier_table = table_name_expr.this
                        break
        
        if not identifier_table:
            return {'error': 'Could not extract IDENTIFIER table name'}
        
        # For IDENTIFIER() with SELECT *, map all object columns to the table
        for col in analysis['object_columns']:
            analysis['column_mappings'][col] = {
                'type': 'direct',
                'source_table': identifier_table,
                'source_column': col,
                'table_alias': identifier_table
            }
        
        return analysis
    
    def _analyze_wildcard_pattern(self, parsed, analysis) -> Dict[str, Any]:
        """Analyze wildcard-dominant patterns."""
        # Extract table references
        self._extract_tables_and_aliases(parsed, analysis)
        
        # Find main SELECT statement
        main_select = None
        for node in parsed.walk():
            if isinstance(node, exp.Select):
                main_select = node
                break
        
        if not main_select:
            return analysis
        
        # Check for wildcard in SELECT
        has_wildcard = False
        for expr in main_select.expressions:
            if isinstance(expr, exp.Star):
                has_wildcard = True
                break
        
        if has_wildcard:
            # Map all object columns to the main table
            main_table = self._find_main_table(main_select, analysis)
            if main_table:
                for col in analysis['object_columns']:
                    analysis['column_mappings'][col] = {
                        'type': 'direct',
                        'source_table': main_table,
                        'source_column': col,
                        'table_alias': '',
                        'resolution_method': 'wildcard_resolution'
                    }
        
        return analysis
    
    def _analyze_cte_pattern(self, parsed, analysis) -> Dict[str, Any]:
        """Analyze CTE-dominant patterns."""
        # Extract CTEs and tables
        self._extract_ctes(parsed, analysis)
        self._extract_tables_and_aliases(parsed, analysis)
        
        # Analyze column lineage through CTEs
        self._analyze_column_lineage(parsed, analysis)
        
        return analysis
    
    def _analyze_hybrid_pattern(self, parsed, analysis) -> Dict[str, Any]:
        """Analyze hybrid patterns with both CTEs and wildcards."""
        # Extract all components
        self._extract_tables_and_aliases(parsed, analysis)
        self._extract_ctes(parsed, analysis)
        self._analyze_column_lineage(parsed, analysis)
        
        # Resolve any missing columns through wildcard analysis
        missing_columns = [
            col for col in analysis['object_columns']
            if col not in analysis['column_mappings'] and col not in analysis['derived_columns']
        ]
        
        if missing_columns:
            self._resolve_wildcard_columns(missing_columns, parsed, analysis)
        
        return analysis
    
    def _extract_tables_and_aliases(self, parsed, analysis):
        """Extract all table references and their aliases."""
        view_name = analysis.get('object_name', '')
        
        for node in parsed.walk():
            if isinstance(node, exp.Table):
                table_name = str(node)
                
                # Skip the view itself as a source table
                if table_name == view_name:
                    continue
                
                analysis['source_tables'].append(table_name)
                
                if node.alias:
                    alias = str(node.alias)
                    analysis['table_aliases'][alias.lower()] = table_name
                else:
                    implicit_alias = table_name.split('.')[-1].lower()
                    if table_name != view_name:
                        analysis['table_aliases'][implicit_alias] = table_name
    
    def _extract_ctes(self, parsed, analysis):
        """Extract Common Table Expressions."""
        for node in parsed.walk():
            if isinstance(node, exp.CTE):
                cte_name = str(node.alias)
                analysis['cte_definitions'][cte_name] = {
                    'name': cte_name,
                    'definition': str(node.this)
                }
                analysis['table_aliases'][cte_name.lower()] = f"CTE_{cte_name}"
    
    def _analyze_column_lineage(self, parsed, analysis):
        """Analyze column lineage through SELECT statements."""
        for node in parsed.walk():
            if isinstance(node, exp.Select):
                self._analyze_select_statement(node, analysis)
    
    def _analyze_select_statement(self, select_node, analysis):
        """Analyze a single SELECT statement."""
        for expr in select_node.expressions:
            if isinstance(expr, exp.Alias):
                column_alias = str(expr.alias)
                source_expr = expr.this
                
                if isinstance(source_expr, exp.Column):
                    self._map_direct_column(column_alias, source_expr, analysis)
                else:
                    self._map_derived_column(column_alias, source_expr, analysis)
            
            elif isinstance(expr, exp.Column):
                column_name = str(expr.name)
                self._map_direct_column(column_name, expr, analysis)
    
    def _map_direct_column(self, column_name, column_expr, analysis):
        """Map a direct column reference."""
        table_ref = column_expr.table
        source_column = str(column_expr.name)
        
        if table_ref:
            table_ref_str = str(table_ref)
            actual_table = analysis['table_aliases'].get(table_ref_str.lower(), table_ref_str)
            
            analysis['column_mappings'][column_name] = {
                'type': 'direct',
                'source_table': actual_table,
                'source_column': source_column,
                'table_alias': table_ref_str
            }
    
    def _map_derived_column(self, column_name, expression, analysis):
        """Map a derived column."""
        referenced_columns = []
        
        for node in expression.walk():
            if isinstance(node, exp.Column):
                table_ref = node.table
                col_name = str(node.name)
                
                if table_ref:
                    table_ref_str = str(table_ref)
                    actual_table = analysis['table_aliases'].get(table_ref_str.lower(), table_ref_str)
                    referenced_columns.append({
                        'table': actual_table,
                        'column': col_name,
                        'alias': table_ref_str
                    })
        
        analysis['derived_columns'][column_name] = {
            'expression': str(expression),
            'expression_type': type(expression).__name__,
            'referenced_columns': referenced_columns
        }
    
    def _find_main_table(self, select_node, analysis) -> Optional[str]:
        """Find the main table in a SELECT statement."""
        try:
            # Check FROM clause
            from_clause = select_node.find(exp.From)
            if from_clause and from_clause.this:
                table_expr = from_clause.this
                if isinstance(table_expr, exp.Table):
                    return str(table_expr)
        except Exception:
            pass
        
        # Fallback to first table in aliases
        for alias, table_name in analysis.get('table_aliases', {}).items():
            if not table_name.startswith('CTE_'):
                return table_name
        
        return None
    
    def _resolve_wildcard_columns(self, missing_columns, parsed, analysis):
        """Resolve missing columns through wildcard analysis."""
        main_table = None
        
        # Find main table from FROM clause
        for node in parsed.walk():
            if isinstance(node, exp.Select):
                main_table = self._find_main_table(node, analysis)
                break
        
        if main_table:
            for col in missing_columns:
                analysis['column_mappings'][col] = {
                    'type': 'direct',
                    'source_table': main_table,
                    'source_column': col,
                    'table_alias': '',
                    'resolution_method': 'wildcard_fallback'
                }