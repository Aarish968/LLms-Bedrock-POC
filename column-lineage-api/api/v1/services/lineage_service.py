"""Column lineage analysis service."""

import io
import json
import csv
from datetime import datetime
from typing import List, Optional, Dict, Any, AsyncGenerator
from uuid import UUID

import pandas as pd

from api.core.logging import LoggerMixin
from api.dependencies.database import DatabaseManager
from api.v1.models.lineage import (
    LineageAnalysisRequest,
    ColumnLineageResult,
    ViewInfo,
    ColumnType,
    ExpressionType,
)
from api.v1.services.job_manager import JobManager
from api.v1.services.sql_parser import SQLParser


class LineageService(LoggerMixin):
    """Column lineage analysis service."""
    
    def __init__(self):
        self.db_manager = DatabaseManager()
        self.job_manager = JobManager()
        self.sql_parser = SQLParser()
    
    async def process_lineage_analysis(
        self,
        job_id: UUID,
        request: LineageAnalysisRequest,
        user_id: str,
    ) -> List[ColumnLineageResult]:
        """Process column lineage analysis."""
        self.logger.info("Starting lineage analysis processing", job_id=str(job_id))
        
        try:
            # Update job status
            self.job_manager.update_job_status(job_id, "RUNNING", started_at=datetime.utcnow())
            
            # Get views to analyze
            if request.view_names:
                views = await self._get_specific_views(request.view_names)
            else:
                views = await self._discover_views(
                    schema_filter=request.schema_filter,
                    include_system_views=request.include_system_views,
                    max_views=request.max_views,
                )
            
            # Update total views count
            self.job_manager.update_job_progress(job_id, total_views=len(views))
            
            results = []
            successful_views = 0
            failed_views = 0
            
            for view in views:
                try:
                    self.logger.info("Processing view", view_name=view.view_name)
                    
                    # Get view DDL
                    ddl = await self._get_view_ddl(view.view_name)
                    if not ddl:
                        self.logger.warning("No DDL found for view", view_name=view.view_name)
                        failed_views += 1
                        continue
                    
                    # Parse DDL and extract lineage
                    view_results = await self._analyze_view_lineage(view.view_name, ddl)
                    results.extend(view_results)
                    successful_views += 1
                    
                    # Update progress
                    self.job_manager.update_job_progress(
                        job_id,
                        processed_views=successful_views + failed_views,
                        successful_views=successful_views,
                        failed_views=failed_views,
                    )
                    
                except Exception as e:
                    self.logger.error(
                        "Failed to process view",
                        view_name=view.view_name,
                        error=str(e),
                    )
                    failed_views += 1
                    continue
            
            # Store results
            self.job_manager.store_job_results(job_id, results)
            
            # Update job completion
            self.job_manager.update_job_status(
                job_id,
                "COMPLETED",
                completed_at=datetime.utcnow(),
                results_count=len(results),
            )
            
            self.logger.info(
                "Lineage analysis completed",
                job_id=str(job_id),
                total_results=len(results),
                successful_views=successful_views,
                failed_views=failed_views,
            )
            
            return results
            
        except Exception as e:
            self.logger.error("Lineage analysis failed", job_id=str(job_id), error=str(e))
            self.job_manager.update_job_status(
                job_id,
                "FAILED",
                completed_at=datetime.utcnow(),
                error_message=str(e),
            )
            raise
    
    async def get_available_views(
        self,
        schema_filter: Optional[str] = None,
        limit: Optional[int] = 100,
        offset: int = 0,
    ) -> List[ViewInfo]:
        """Get list of available database views."""
        self.logger.info("Getting available views", schema_filter=schema_filter)
        
        try:
            query = """
            SELECT 
                TABLE_NAME as view_name,
                TABLE_SCHEMA as schema_name,
                TABLE_CATALOG as database_name,
                CREATED as created_date,
                LAST_ALTERED as last_modified
            FROM INFORMATION_SCHEMA.VIEWS
            WHERE TABLE_CATALOG = CURRENT_DATABASE()
            """
            
            params = {}
            
            if schema_filter:
                query += " AND TABLE_SCHEMA = :schema_filter"
                params["schema_filter"] = schema_filter
            
            query += " ORDER BY TABLE_NAME"
            
            if limit:
                query += f" LIMIT {limit}"
            if offset:
                query += f" OFFSET {offset}"
            
            results = self.db_manager.execute_query(query, params)
            
            views = []
            for row in results:
                # Get column count for each view
                col_count_query = """
                SELECT COUNT(*) as column_count
                FROM INFORMATION_SCHEMA.COLUMNS
                WHERE TABLE_CATALOG = CURRENT_DATABASE()
                AND TABLE_SCHEMA = :schema_name
                AND TABLE_NAME = :view_name
                """
                
                col_result = self.db_manager.execute_query(
                    col_count_query,
                    {"schema_name": row.schema_name, "view_name": row.view_name}
                )
                
                column_count = col_result[0].column_count if col_result else 0
                
                views.append(ViewInfo(
                    view_name=row.view_name,
                    schema_name=row.schema_name,
                    database_name=row.database_name,
                    column_count=column_count,
                    created_date=row.created_date,
                    last_modified=row.last_modified,
                ))
            
            return views
            
        except Exception as e:
            self.logger.error("Failed to get available views", error=str(e))
            raise
    
    async def export_results(
        self,
        results: List[ColumnLineageResult],
        format: str,
        include_metadata: bool = True,
    ) -> AsyncGenerator[bytes, None]:
        """Export lineage results in specified format."""
        self.logger.info("Exporting results", format=format, count=len(results))
        
        if format.lower() == "csv":
            yield await self._export_csv(results, include_metadata)
        elif format.lower() == "json":
            yield await self._export_json(results, include_metadata)
        elif format.lower() == "excel":
            yield await self._export_excel(results, include_metadata)
        else:
            raise ValueError(f"Unsupported export format: {format}")
    
    async def _discover_views(
        self,
        schema_filter: Optional[str] = None,
        include_system_views: bool = False,
        max_views: Optional[int] = None,
    ) -> List[ViewInfo]:
        """Discover views from database."""
        query = """
        SELECT TABLE_NAME
        FROM INFORMATION_SCHEMA.VIEWS
        WHERE TABLE_CATALOG = CURRENT_DATABASE()
        """
        
        if not include_system_views:
            query += " AND TABLE_NAME NOT LIKE 'CANVAS_%'"
        
        if schema_filter:
            query += f" AND TABLE_SCHEMA = '{schema_filter}'"
        
        query += " ORDER BY TABLE_NAME"
        
        if max_views:
            query += f" LIMIT {max_views}"
        
        results = self.db_manager.execute_query(query)
        
        views = []
        for row in results:
            views.append(ViewInfo(
                view_name=row.TABLE_NAME,
                schema_name=schema_filter or "UNKNOWN",
                database_name="CURRENT",
                column_count=0,  # Will be populated later if needed
            ))
        
        return views
    
    async def _get_specific_views(self, view_names: List[str]) -> List[ViewInfo]:
        """Get specific views by name."""
        views = []
        for view_name in view_names:
            views.append(ViewInfo(
                view_name=view_name,
                schema_name="UNKNOWN",
                database_name="CURRENT",
                column_count=0,
            ))
        return views
    
    async def _get_view_ddl(self, view_name: str) -> Optional[str]:
        """Get DDL for a specific view."""
        try:
            # Try with schema qualification first
            schemas_to_try = ["CPS_DSCI_API", "CPS_DSCI_BR"]
            
            for schema in schemas_to_try:
                try:
                    qualified_name = f"{schema}.{view_name}"
                    query = f"SELECT GET_DDL('VIEW', '{qualified_name}') as ddl"
                    result = self.db_manager.execute_query(query)
                    
                    if result and result[0].ddl:
                        return result[0].ddl
                except Exception:
                    continue
            
            # Try without schema qualification
            query = f"SELECT GET_DDL('VIEW', '{view_name}') as ddl"
            result = self.db_manager.execute_query(query)
            
            if result and result[0].ddl:
                return result[0].ddl
            
            return None
            
        except Exception as e:
            self.logger.error("Failed to get DDL", view_name=view_name, error=str(e))
            return None
    
    async def _analyze_view_lineage(
        self, 
        view_name: str, 
        ddl: str
    ) -> List[ColumnLineageResult]:
        """Analyze column lineage for a single view."""
        try:
            # Parse DDL using SQL parser
            analysis = self.sql_parser.analyze_ddl_statement(ddl)
            
            if "error" in analysis:
                self.logger.error(
                    "DDL parsing failed",
                    view_name=view_name,
                    error=analysis["error"],
                )
                return []
            
            results = []
            
            # Process column mappings
            for col_name, mapping in analysis.get("column_mappings", {}).items():
                result = ColumnLineageResult(
                    view_name=view_name,
                    view_column=col_name,
                    column_type=ColumnType.DIRECT,
                    source_table=mapping.get("source_table", "UNKNOWN"),
                    source_column=mapping.get("source_column", col_name),
                    confidence_score=1.0,
                    metadata={
                        "table_alias": mapping.get("table_alias", ""),
                        "resolution_method": mapping.get("resolution_method", "direct"),
                    },
                )
                results.append(result)
            
            # Process derived columns
            for col_name, derived_info in analysis.get("derived_columns", {}).items():
                # Determine expression type
                expr_type = self._map_expression_type(derived_info.get("expression_type", ""))
                
                # Get source columns
                source_columns = derived_info.get("referenced_columns", [])
                if source_columns:
                    # Create result for first source (primary)
                    primary_source = source_columns[0]
                    result = ColumnLineageResult(
                        view_name=view_name,
                        view_column=col_name,
                        column_type=ColumnType.DERIVED,
                        source_table=primary_source.get("table", "UNKNOWN"),
                        source_column=primary_source.get("column", col_name),
                        expression_type=expr_type,
                        confidence_score=0.8,  # Lower confidence for derived columns
                        metadata={
                            "expression": derived_info.get("expression", ""),
                            "all_sources": source_columns,
                        },
                    )
                    results.append(result)
                else:
                    # No clear source, mark as unknown
                    result = ColumnLineageResult(
                        view_name=view_name,
                        view_column=col_name,
                        column_type=ColumnType.UNKNOWN,
                        source_table="CALCULATED",
                        source_column="LITERAL",
                        expression_type=expr_type,
                        confidence_score=0.5,
                        metadata={
                            "expression": derived_info.get("expression", ""),
                        },
                    )
                    results.append(result)
            
            return results
            
        except Exception as e:
            self.logger.error(
                "Failed to analyze view lineage",
                view_name=view_name,
                error=str(e),
            )
            return []
    
    def _map_expression_type(self, expr_type_str: str) -> Optional[ExpressionType]:
        """Map expression type string to enum."""
        try:
            return ExpressionType(expr_type_str.upper())
        except ValueError:
            return None
    
    async def _export_csv(
        self, 
        results: List[ColumnLineageResult], 
        include_metadata: bool
    ) -> bytes:
        """Export results as CSV."""
        output = io.StringIO()
        
        fieldnames = [
            "View_Name", "View_Column", "Column_Type",
            "Source_Table", "Source_Column", "Expression_Type",
            "Confidence_Score"
        ]
        
        if include_metadata:
            fieldnames.append("Metadata")
        
        writer = csv.DictWriter(output, fieldnames=fieldnames)
        writer.writeheader()
        
        for result in results:
            row = {
                "View_Name": result.view_name,
                "View_Column": result.view_column,
                "Column_Type": result.column_type.value,
                "Source_Table": result.source_table,
                "Source_Column": result.source_column,
                "Expression_Type": result.expression_type.value if result.expression_type else "",
                "Confidence_Score": result.confidence_score,
            }
            
            if include_metadata:
                row["Metadata"] = json.dumps(result.metadata)
            
            writer.writerow(row)
        
        return output.getvalue().encode("utf-8")
    
    async def _export_json(
        self, 
        results: List[ColumnLineageResult], 
        include_metadata: bool
    ) -> bytes:
        """Export results as JSON."""
        data = []
        for result in results:
            item = result.model_dump()
            if not include_metadata:
                item.pop("metadata", None)
            data.append(item)
        
        return json.dumps(data, indent=2, default=str).encode("utf-8")
    
    async def _export_excel(
        self, 
        results: List[ColumnLineageResult], 
        include_metadata: bool
    ) -> bytes:
        """Export results as Excel."""
        # Convert to DataFrame
        data = []
        for result in results:
            row = {
                "View_Name": result.view_name,
                "View_Column": result.view_column,
                "Column_Type": result.column_type.value,
                "Source_Table": result.source_table,
                "Source_Column": result.source_column,
                "Expression_Type": result.expression_type.value if result.expression_type else "",
                "Confidence_Score": result.confidence_score,
            }
            
            if include_metadata:
                row["Metadata"] = json.dumps(result.metadata)
            
            data.append(row)
        
        df = pd.DataFrame(data)
        
        # Write to Excel
        output = io.BytesIO()
        with pd.ExcelWriter(output, engine="openpyxl") as writer:
            df.to_excel(writer, sheet_name="Column_Lineage", index=False)
        
        return output.getvalue()