"""
DataGrid - Core class for handling data grid operations
"""

from typing import List, Dict, Any, Optional, Callable
import json
from datetime import datetime


class DataGrid:
    """
    Main DataGrid class for handling tabular data with features like
    sorting, filtering, pagination, and export.
    """
    
    # Constants
    DEFAULT_PAGE_SIZE = 100
    MAX_TOOLTIP_CHARS = 200
    
    def __init__(
        self,
        data: List[Dict[str, Any]],
        columns: Optional[List[str]] = None,
        column_config: Optional[Dict[str, Dict[str, Any]]] = None
    ):
        """
        Initialize the DataGrid with data and configuration.
        
        Args:
            data: List of dictionaries containing the data
            columns: List of column names to display (None = all columns)
            column_config: Configuration for each column (width, sortable, etc.)
        """
        self._rawData = data
        self._columns = columns or self._extractColumns(data)
        self._columnConfig = column_config or {}
        self._visibleColumns = self._columns.copy()
        self._currentPage = 1
        self._pageSize = self.DEFAULT_PAGE_SIZE
        self._sortColumn = None
        self._sortDirection = 'asc'
        self._filters = {}
        
    def _extractColumns(self, data: List[Dict[str, Any]]) -> List[str]:
        """Extract column names from the data."""
        if not data:
            return []
        return list(data[0].keys())
    
    def setVisibleColumns(self, columns: List[str]) -> 'DataGrid':
        """
        Set which columns should be visible.
        
        Args:
            columns: List of column names to show
            
        Returns:
            self for method chaining
        """
        self._visibleColumns = [col for col in columns if col in self._columns]
        return self
    
    def setPageSize(self, size: int) -> 'DataGrid':
        """
        Set the number of rows per page.
        
        Args:
            size: Number of rows per page
            
        Returns:
            self for method chaining
        """
        self._pageSize = max(1, size)
        self._currentPage = 1  # Reset to first page
        return self
    
    def setPage(self, page: int) -> 'DataGrid':
        """
        Set the current page.
        
        Args:
            page: Page number (1-indexed)
            
        Returns:
            self for method chaining
        """
        total_pages = self.getTotalPages()
        self._currentPage = max(1, min(page, total_pages))
        return self
    
    def setSorting(self, column: str, direction: str = 'asc') -> 'DataGrid':
        """
        Set sorting configuration.
        
        Args:
            column: Column name to sort by
            direction: 'asc' or 'desc'
            
        Returns:
            self for method chaining
        """
        try:
            if column in self._columns:
                self._sortColumn = column
                self._sortDirection = direction.lower()
        except Exception as e:
            print(f"Warning: Failed to set sorting on column '{column}': {e}")
        return self
    
    def setFilter(self, column: str, value: Any) -> 'DataGrid':
        """
        Set a filter for a specific column.
        
        Args:
            column: Column name to filter
            value: Filter value
            
        Returns:
            self for method chaining
        """
        try:
            if value is None or value == '':
                if column in self._filters:
                    del self._filters[column]
            else:
                self._filters[column] = str(value).lower()
            self._currentPage = 1  # Reset to first page when filtering
        except Exception as e:
            print(f"Warning: Failed to set filter on column '{column}': {e}")
        return self
    
    def clearFilters(self) -> 'DataGrid':
        """Clear all filters."""
        self._filters = {}
        self._currentPage = 1
        return self
    
    def _applyFilters(self, data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Apply current filters to the data."""
        if not self._filters:
            return data
        
        try:
            filtered_data = []
            for row in data:
                matches = True
                for col, filter_val in self._filters.items():
                    try:
                        if col in row:
                            row_val = str(row[col]).lower()
                            if filter_val not in row_val:
                                matches = False
                                break
                    except Exception as e:
                        # If comparison fails, skip this row
                        matches = False
                        break
                if matches:
                    filtered_data.append(row)
            return filtered_data
        except Exception as e:
            print(f"Warning: Filter operation failed: {e}")
            return data  # Return unfiltered data on error
    
    def _applySorting(self, data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Apply current sorting to the data."""
        if not self._sortColumn or self._sortColumn not in self._columns:
            return data
        
        try:
            def getSortKey(row: Dict[str, Any]) -> Any:
                val = row.get(self._sortColumn, '')
                # Handle None values
                if val is None:
                    return ''
                # Try to preserve numeric sorting
                try:
                    return float(val)
                except (ValueError, TypeError):
                    return str(val).lower()
            
            return sorted(data, key=getSortKey, reverse=(self._sortDirection == 'desc'))
        except Exception as e:
            print(f"Warning: Sort operation failed: {e}")
            return data  # Return unsorted data on error
    
    def _applyPagination(self, data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Apply pagination to the data."""
        start_idx = (self._currentPage - 1) * self._pageSize
        end_idx = start_idx + self._pageSize
        return data[start_idx:end_idx]
    
    def getProcessedData(self) -> List[Dict[str, Any]]:
        """
        Get data with all processing applied (filtering, sorting, pagination).
        
        Returns:
            Processed data for current page
        """
        data = self._rawData.copy()
        data = self._applyFilters(data)
        data = self._applySorting(data)
        data = self._applyPagination(data)
        return data
    
    def getFilteredData(self) -> List[Dict[str, Any]]:
        """
        Get all filtered and sorted data (without pagination).
        
        Returns:
            All filtered and sorted data
        """
        data = self._rawData.copy()
        data = self._applyFilters(data)
        data = self._applySorting(data)
        return data
    
    def getTotalRows(self) -> int:
        """Get total number of rows after filtering."""
        return len(self._applyFilters(self._rawData))
    
    def getTotalPages(self) -> int:
        """Get total number of pages."""
        total_rows = self.getTotalRows()
        return max(1, (total_rows + self._pageSize - 1) // self._pageSize)
    
    def getCurrentPage(self) -> int:
        """Get current page number."""
        return self._currentPage
    
    def getColumns(self) -> List[str]:
        """Get all available columns."""
        return self._columns.copy()
    
    def getVisibleColumns(self) -> List[str]:
        """Get currently visible columns."""
        return self._visibleColumns.copy()
    
    def toJson(self) -> str:
        """
        Export current view to JSON.
        
        Returns:
            JSON string of current page data
        """
        return json.dumps(self.getProcessedData(), indent=2, default=str)
    
    def toJsonAll(self) -> str:
        """
        Export all filtered data to JSON.
        
        Returns:
            JSON string of all filtered data
        """
        return json.dumps(self.getFilteredData(), indent=2, default=str)
    
    def toCsv(self, selected_row_ids: Optional[List[Any]] = None) -> str:
        """
        Export data to CSV format.
        
        Args:
            selected_row_ids: List of row IDs to export (None = all filtered data)
            
        Returns:
            CSV string
        """
        try:
            if selected_row_ids is not None:
                # Filter data by row IDs
                data = []
                for row in self.getFilteredData():
                    try:
                        row_id = row.get('id', str(row))
                        if row_id in selected_row_ids:
                            data.append(row)
                    except Exception:
                        continue  # Skip problematic rows
            else:
                data = self.getFilteredData()
            
            if not data:
                return ""
            
            # Create CSV header
            csv_lines = [','.join(f'"{col}"' for col in self._visibleColumns)]
            
            # Add data rows
            for row in data:
                try:
                    values = []
                    for col in self._visibleColumns:
                        val = row.get(col, '')
                        # Escape quotes and wrap in quotes
                        val_str = str(val).replace('"', '""')
                        values.append(f'"{val_str}"')
                    csv_lines.append(','.join(values))
                except Exception:
                    continue  # Skip problematic rows
            
            return '\n'.join(csv_lines)
        except Exception as e:
            print(f"Error generating CSV: {e}")
            return ""  # Return empty string on error
        csv_lines = [','.join(f'"{col}"' for col in self._visibleColumns)]
        
        # Add data rows
        for row in data:
            values = []
            for col in self._visibleColumns:
                val = row.get(col, '')
                # Escape quotes and wrap in quotes
                val_str = str(val).replace('"', '""')
                values.append(f'"{val_str}"')
            csv_lines.append(','.join(values))
        
        return '\n'.join(csv_lines)
    
    def getGridConfig(self) -> Dict[str, Any]:
        """
        Get complete grid configuration for rendering.
        
        Returns:
            Dictionary with all grid configuration
        """
        return {
            'columns': self._columns,
            'visibleColumns': self._visibleColumns,
            'columnConfig': self._columnConfig,
            'currentPage': self._currentPage,
            'pageSize': self._pageSize,
            'totalPages': self.getTotalPages(),
            'totalRows': self.getTotalRows(),
            'sortColumn': self._sortColumn,
            'sortDirection': self._sortDirection,
            'filters': self._filters,
            'data': self.getProcessedData()
        }
