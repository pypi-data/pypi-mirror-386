"""
PyDataGrid - A powerful data grid library for Python applications
"""

from .datagrid import DataGrid
from .flask_integration import create_grid_blueprint, create_grid_app, FlaskGridApp

__version__ = "1.0.0"
__all__ = ["DataGrid", "create_grid_blueprint", "create_grid_app", "FlaskGridApp"]
