"""
Flask Integration Module for PyDataGrid
"""

from flask import Blueprint, render_template, jsonify, request, Response
from typing import List, Dict, Any, Optional
import json
import os
from .datagrid import DataGrid


def create_grid_blueprint(
    data_source: Any,
    name: str = 'datagrid',
    url_prefix: str = '/grid'
) -> Blueprint:
    """
    Create a Flask blueprint for the data grid.
    
    Args:
        data_source: Either a list of dictionaries or a callable that returns data
        name: Name of the blueprint
        url_prefix: URL prefix for the blueprint routes
        
    Returns:
        Flask Blueprint configured with grid routes
    """
    # Get the directory where this module is located
    module_dir = os.path.dirname(os.path.abspath(__file__))
    
    blueprint = Blueprint(name, __name__, 
                         template_folder=os.path.join(module_dir, 'templates'),
                         static_folder=os.path.join(module_dir, 'static'),
                         static_url_path='/static')
    
    def _getData() -> List[Dict[str, Any]]:
        """Get data from the data source."""
        if callable(data_source):
            return data_source()
        return data_source
    
    @blueprint.route('/')
    def index():
        """Render the main grid page."""
        data = _getData()
        grid = DataGrid(data)
        
        # Apply initial configuration from query parameters
        page = request.args.get('page', 1, type=int)
        page_size = request.args.get('page_size', DataGrid.DEFAULT_PAGE_SIZE, type=int)
        sort_column = request.args.get('sort_column', '')
        sort_direction = request.args.get('sort_direction', 'asc')
        
        # IMPORTANT: setPageSize must come BEFORE setPage because setPageSize resets currentPage to 1
        grid.setPageSize(page_size).setPage(page)
        
        if sort_column:
            grid.setSorting(sort_column, sort_direction)
        
        # Apply filters from query parameters
        for key, value in request.args.items():
            if key.startswith('filter_'):
                column_name = key[7:]  # Remove 'filter_' prefix
                grid.setFilter(column_name, value)
        
        config = grid.getGridConfig()
        return render_template('datagrid.html', config=config)
    
    @blueprint.route('/api/data')
    def api_data():
        """API endpoint to get paginated and filtered data."""
        try:
            data = _getData()
            grid = DataGrid(data)
            
            # Get parameters from request
            page = request.args.get('page', 1, type=int)
            page_size = request.args.get('page_size', DataGrid.DEFAULT_PAGE_SIZE, type=int)
            sort_column = request.args.get('sort_column', '')
            sort_direction = request.args.get('sort_direction', 'asc')
            
            # Apply visible columns if provided
            visible_columns_str = request.args.get('visible_columns', '')
            if visible_columns_str:
                try:
                    visible_columns = json.loads(visible_columns_str)
                    grid.setVisibleColumns(visible_columns)
                except json.JSONDecodeError:
                    pass  # Continue with default columns
            
            # Apply configuration - IMPORTANT: setPageSize must come BEFORE setPage
            # because setPageSize resets currentPage to 1
            grid.setPageSize(page_size).setPage(page)
            
            if sort_column:
                grid.setSorting(sort_column, sort_direction)
            
            # Apply filters
            for key, value in request.args.items():
                if key.startswith('filter_'):
                    column_name = key[7:]  # Remove 'filter_' prefix
                    grid.setFilter(column_name, value)
            
            return jsonify(grid.getGridConfig())
        except Exception as e:
            return jsonify({'error': str(e), 'message': 'Failed to load grid data'}), 500
    
    @blueprint.route('/api/export')
    def api_export():
        """API endpoint to export data as CSV."""
        try:
            data = _getData()
            grid = DataGrid(data)
            
            # Get parameters
            sort_column = request.args.get('sort_column', '')
            sort_direction = request.args.get('sort_direction', 'asc')
            export_type = request.args.get('export_type', 'all')
            
            # Apply visible columns if provided
            visible_columns_str = request.args.get('visible_columns', '')
            if visible_columns_str:
                try:
                    visible_columns = json.loads(visible_columns_str)
                    grid.setVisibleColumns(visible_columns)
                except json.JSONDecodeError:
                    pass  # Continue with default columns
            
            # Apply sorting
            if sort_column:
                grid.setSorting(sort_column, sort_direction)
            
            # Apply filters
            for key, value in request.args.items():
                if key.startswith('filter_'):
                    column_name = key[7:]  # Remove 'filter_' prefix
                    grid.setFilter(column_name, value)
            
            # Get selected rows if exporting selected
            selected_rows = None
            if export_type == 'selected':
                selected_rows_str = request.args.get('selected_rows', '[]')
                try:
                    selected_rows = json.loads(selected_rows_str)
                except json.JSONDecodeError:
                    selected_rows = None
            
            # Generate CSV
            csv_data = grid.toCsv(selected_rows)
            
            if not csv_data:
                return jsonify({'error': 'No data to export'}), 400
            
            # Create response
            response = Response(csv_data, mimetype='text/csv')
            filename = f'export_{export_type}.csv'
            response.headers['Content-Disposition'] = f'attachment; filename={filename}'
            return response
        except Exception as e:
            return jsonify({'error': str(e), 'message': 'Failed to export data'}), 500
        
        # Create response
        response = Response(csv_data, mimetype='text/csv')
        filename = f'{name}_{export_type}.csv'
        response.headers['Content-Disposition'] = f'attachment; filename={filename}'
        
        return response
    
    return blueprint


class FlaskGridApp:
    """
    Helper class to quickly create a Flask app with a data grid.
    """
    
    def __init__(
        self,
        data: List[Dict[str, Any]],
        host: str = '127.0.0.1',
        port: int = 5000,
        debug: bool = True
    ):
        """
        Initialize Flask grid application.
        
        Args:
            data: List of dictionaries containing the data
            host: Host address to run the server
            port: Port number to run the server
            debug: Enable debug mode
        """
        from flask import Flask
        from flask_cors import CORS
        
        self._app = Flask(__name__)
        CORS(self._app)
        
        self._data = data
        self._host = host
        self._port = port
        self._debug = debug
        
        # Register blueprint with url_prefix
        blueprint = create_grid_blueprint(lambda: self._data, name='datagrid', url_prefix='/grid')
        self._app.register_blueprint(blueprint, url_prefix='/grid')
    
    def run(self):
        """Run the Flask application."""
        self._app.run(host=self._host, port=self._port, debug=self._debug)
    
    def get_app(self):
        """Get the Flask application instance."""
        return self._app
    
    def update_data(self, data: List[Dict[str, Any]]):
        """
        Update the grid data.
        
        Args:
            data: New data to display
        """
        self._data = data


def create_grid_app(
    data: List[Dict[str, Any]],
    host: str = '127.0.0.1',
    port: int = 5000,
    debug: bool = True
) -> FlaskGridApp:
    """
    Convenience function to create a Flask grid application.
    
    Args:
        data: List of dictionaries containing the data
        host: Host address to run the server
        port: Port number to run the server
        debug: Enable debug mode
        
    Returns:
        FlaskGridApp instance
    
    Example:
        >>> data = [
        ...     {'name': 'John', 'age': 30, 'city': 'New York'},
        ...     {'name': 'Jane', 'age': 25, 'city': 'London'}
        ... ]
        >>> app = create_grid_app(data)
        >>> app.run()
    """
    return FlaskGridApp(data, host, port, debug)
