/**
 * PyDataGrid - Client-side JavaScript for interactive grid functionality
 */

class PyDataGrid {
    // Constants
    static MAX_TOOLTIP_CHARS = 200;
    static PAGE_SIZE = 100;
    
    constructor(containerId, config) {
        this._containerId = containerId;
        this._config = config;
        this._selectedRows = new Set();
        this._currentFilterColumn = null;
        this._tooltip = null;
        this._activeFilterDropdown = null;
        
        try {
            // Initialize the grid
            this.init();
        } catch (error) {
            console.error('Failed to initialize PyDataGrid:', error);
            this._showError('Failed to initialize grid. Please refresh the page.');
        }
    }
    
    /**
     * Initialize the data grid
     */
    init() {
        this._initializeElements();
        this._initializeEventListeners();
        this._renderColumnMenu();
        this._renderTable();
        this._updatePagination();
        this._updateExportButtons();
        this._updateActiveFiltersDisplay();
    }
    
    /**
     * Get references to DOM elements
     */
    _initializeElements() {
        this._elements = {
            columnMenuBtn: document.getElementById('columnMenuBtn'),
            columnMenuDropdown: document.getElementById('columnMenuDropdown'),
            closeColumnMenu: document.getElementById('closeColumnMenu'),
            columnMenuItems: document.getElementById('columnMenuItems'),
            exportSelectedBtn: document.getElementById('exportSelectedBtn'),
            exportAllBtn: document.getElementById('exportAllBtn'),
            tableHeader: document.getElementById('tableHeader'),
            tableBody: document.getElementById('tableBody'),
            selectAllCheckbox: document.getElementById('selectAllCheckbox'),
            paginationInfo: document.getElementById('paginationInfo'),
            pageNumbers: document.getElementById('pageNumbers'),
            firstPageBtn: document.getElementById('firstPageBtn'),
            prevPageBtn: document.getElementById('prevPageBtn'),
            nextPageBtn: document.getElementById('nextPageBtn'),
            lastPageBtn: document.getElementById('lastPageBtn'),
            activeFilters: document.getElementById('activeFilters'),
            activeFiltersList: document.getElementById('activeFiltersList')
        };
    }
    
    /**
     * Initialize event listeners
     */
    _initializeEventListeners() {
        // Column menu toggle
        this._elements.columnMenuBtn.addEventListener('click', () => {
            this._elements.columnMenuDropdown.classList.toggle('active');
        });
        
        this._elements.closeColumnMenu.addEventListener('click', () => {
            this._elements.columnMenuDropdown.classList.remove('active');
        });
        
        // Close column menu when clicking outside
        document.addEventListener('click', (e) => {
            if (!e.target.closest('.column-visibility-menu')) {
                this._elements.columnMenuDropdown.classList.remove('active');
            }
        });
        
        // Export buttons
        this._elements.exportSelectedBtn.addEventListener('click', () => this._exportSelected());
        this._elements.exportAllBtn.addEventListener('click', () => this._exportAll());
        
        // Select all checkbox
        this._elements.selectAllCheckbox.addEventListener('change', (e) => {
            this._handleSelectAll(e.target.checked);
        });
        
        // Pagination buttons
        this._elements.firstPageBtn.addEventListener('click', () => {
            this._changePage(1);
        });
        this._elements.prevPageBtn.addEventListener('click', () => {
            this._changePage(this._config.currentPage - 1);
        });
        this._elements.nextPageBtn.addEventListener('click', () => {
            this._changePage(this._config.currentPage + 1);
        });
        this._elements.lastPageBtn.addEventListener('click', () => {
            this._changePage(this._config.totalPages);
        });
        
        // Close filter dropdowns when clicking outside
        document.addEventListener('click', (e) => {
            if (this._activeFilterDropdown && !e.target.closest('.column-filter-dropdown') && !e.target.closest('.column-menu-icon')) {
                this._closeFilterDropdown();
            }
        });
    }
    
    /**
     * Render column visibility menu
     */
    _renderColumnMenu() {
        this._elements.columnMenuItems.innerHTML = '';
        
        this._config.columns.forEach(column => {
            const item = document.createElement('div');
            item.className = 'column-menu-item';
            
            const checkbox = document.createElement('input');
            checkbox.type = 'checkbox';
            checkbox.id = `col-${column}`;
            checkbox.checked = this._config.visibleColumns.includes(column);
            checkbox.addEventListener('change', (e) => {
                this._toggleColumnVisibility(column, e.target.checked);
            });
            
            const label = document.createElement('label');
            label.htmlFor = `col-${column}`;
            label.textContent = column;
            
            item.appendChild(checkbox);
            item.appendChild(label);
            this._elements.columnMenuItems.appendChild(item);
        });
    }
    
    /**
     * Toggle column visibility
     */
    _toggleColumnVisibility(column, visible) {
        try {
            if (visible && !this._config.visibleColumns.includes(column)) {
                this._config.visibleColumns.push(column);
            } else if (!visible) {
                this._config.visibleColumns = this._config.visibleColumns.filter(col => col !== column);
            }
            
            this._renderTable();
        } catch (error) {
            console.error('Error toggling column visibility:', error);
            this._showError('Failed to update column visibility. Please try again.');
        }
    }
    
    /**
     * Render the data table
     */
    _renderTable() {
        try {
            this._renderTableHeader();
            this._renderTableBody();
        } catch (error) {
            console.error('Error rendering table:', error);
            this._showError('Failed to render table. Please refresh the page.');
        }
    }
    
    /**
     * Render table header
     */
    _renderTableHeader() {
        try {
            // Clear existing headers except select column
            while (this._elements.tableHeader.children.length > 1) {
                this._elements.tableHeader.removeChild(this._elements.tableHeader.lastChild);
            }
            
            this._config.visibleColumns.forEach(column => {
                const th = document.createElement('th');
                th.className = 'sortable';
                
                const headerDiv = document.createElement('div');
                headerDiv.className = 'column-header';
                
                const titleSpan = document.createElement('span');
                titleSpan.className = 'column-title';
                titleSpan.textContent = column;
                
                const actionsDiv = document.createElement('div');
                actionsDiv.className = 'column-actions';
                
                // Filter indicator (funnel icon) - show if column has active filter
                const filterIndicator = document.createElement('span');
                filterIndicator.className = 'filter-indicator';
                if (this._config.filters[column]) {
                    filterIndicator.textContent = '🔍';
                    filterIndicator.title = `Filtered: "${this._config.filters[column]}"`;
                    filterIndicator.classList.add('active');
                }
                
                // Sort indicator
                const sortIndicator = document.createElement('span');
                sortIndicator.className = 'sort-indicator';
                if (this._config.sortColumn === column) {
                    sortIndicator.textContent = this._config.sortDirection === 'asc' ? '▲' : '▼';
                }
                
                // Column menu icon for filter and sort
                const menuIcon = document.createElement('span');
                menuIcon.className = 'column-menu-icon';
                menuIcon.textContent = '⋮';
                menuIcon.title = 'Filter and Sort';
                menuIcon.addEventListener('click', (e) => {
                    e.stopPropagation();
                    this._toggleFilterDropdown(column, e.target);
                });
                
                actionsDiv.appendChild(filterIndicator);
                actionsDiv.appendChild(sortIndicator);
                actionsDiv.appendChild(menuIcon);
                
                headerDiv.appendChild(titleSpan);
                headerDiv.appendChild(actionsDiv);
                
                // Click to sort
                th.addEventListener('click', (e) => {
                    if (!e.target.classList.contains('column-menu-icon')) {
                        this._handleSort(column);
                    }
                });
                
                th.appendChild(headerDiv);
                this._elements.tableHeader.appendChild(th);
            });
        } catch (error) {
            console.error('Error rendering table header:', error);
            this._showError('Failed to render table header. Please refresh the page.');
        }
    }
    
    /**
     * Render table body
     */
    _renderTableBody() {
        try {
            this._elements.tableBody.innerHTML = '';
            
            this._config.data.forEach((row, index) => {
                const tr = document.createElement('tr');
                const rowId = row.id || JSON.stringify(row);
                
                if (this._selectedRows.has(rowId)) {
                    tr.classList.add('selected');
                }
                
                // Checkbox cell
                const selectTd = document.createElement('td');
                selectTd.className = 'select-column';
                const checkbox = document.createElement('input');
                checkbox.type = 'checkbox';
                checkbox.checked = this._selectedRows.has(rowId);
                checkbox.addEventListener('change', (e) => {
                    this._handleRowSelection(index, e.target.checked);
                });
                selectTd.appendChild(checkbox);
                tr.appendChild(selectTd);
                
                // Data cells
                this._config.visibleColumns.forEach(column => {
                    const td = document.createElement('td');
                    const value = row[column] !== undefined && row[column] !== null ? row[column] : '';
                    td.textContent = value;
                    td.title = this._truncateText(String(value), PyDataGrid.MAX_TOOLTIP_CHARS);
                    
                    // Add hover event for tooltip if text is long
                    if (String(value).length > 30) {
                        td.addEventListener('mouseenter', (e) => this._showTooltip(e, value));
                        td.addEventListener('mouseleave', () => this._hideTooltip());
                    }
                    
                    tr.appendChild(td);
                });
                
                this._elements.tableBody.appendChild(tr);
            });
            
            this._updateSelectAllCheckbox();
        } catch (error) {
            console.error('Error rendering table body:', error);
            this._showError('Failed to render table data. Please refresh the page.');
        }
    }
    
    /**
     * Show tooltip on hover
     */
    _showTooltip(event, text) {
        const truncated = this._truncateText(String(text), PyDataGrid.MAX_TOOLTIP_CHARS);
        
        if (this._tooltip) {
            this._hideTooltip();
        }
        
        this._tooltip = document.createElement('div');
        this._tooltip.className = 'cell-tooltip';
        this._tooltip.textContent = truncated;
        document.body.appendChild(this._tooltip);
        
        const rect = event.target.getBoundingClientRect();
        this._tooltip.style.left = `${rect.left}px`;
        this._tooltip.style.top = `${rect.bottom + 5}px`;
    }
    
    /**
     * Hide tooltip
     */
    _hideTooltip() {
        if (this._tooltip) {
            document.body.removeChild(this._tooltip);
            this._tooltip = null;
        }
    }
    
    /**
     * Truncate text to max length
     */
    _truncateText(text, maxLength) {
        if (text.length <= maxLength) {
            return text;
        }
        return text.substring(0, maxLength) + '...';
    }
    
    /**
     * Toggle filter dropdown for a column
     */
    _toggleFilterDropdown(column, iconElement) {
        // Close existing dropdown if open
        if (this._activeFilterDropdown) {
            this._closeFilterDropdown();
        }
        
        // Create and show new dropdown
        this._currentFilterColumn = column;
        this._activeFilterDropdown = this._createFilterDropdown(column);
        
        // Position the dropdown
        const rect = iconElement.getBoundingClientRect();
        this._activeFilterDropdown.style.position = 'fixed';
        this._activeFilterDropdown.style.top = `${rect.bottom + 5}px`;
        this._activeFilterDropdown.style.left = `${rect.left - 200}px`; // Align to the right of icon
        
        document.body.appendChild(this._activeFilterDropdown);
        this._activeFilterDropdown.classList.add('active');
        
        // Focus on filter input
        const filterInput = this._activeFilterDropdown.querySelector('.filter-input-field');
        if (filterInput) {
            filterInput.focus();
        }
    }
    
    /**
     * Create filter dropdown element
     */
    _createFilterDropdown(column) {
        const dropdown = document.createElement('div');
        dropdown.className = 'column-filter-dropdown';
        
        // Header
        const header = document.createElement('div');
        header.className = 'filter-dropdown-header';
        header.textContent = `Filter: ${column}`;
        dropdown.appendChild(header);
        
        // Sort buttons
        const sortAscBtn = document.createElement('button');
        sortAscBtn.className = 'filter-dropdown-sort';
        if (this._config.sortColumn === column && this._config.sortDirection === 'asc') {
            sortAscBtn.classList.add('active');
        }
        sortAscBtn.innerHTML = '<span>Sort Ascending</span><span>▲</span>';
        sortAscBtn.addEventListener('click', () => {
            this._handleSort(column, 'asc');
            this._closeFilterDropdown();
        });
        dropdown.appendChild(sortAscBtn);
        
        const sortDescBtn = document.createElement('button');
        sortDescBtn.className = 'filter-dropdown-sort';
        if (this._config.sortColumn === column && this._config.sortDirection === 'desc') {
            sortDescBtn.classList.add('active');
        }
        sortDescBtn.innerHTML = '<span>Sort Descending</span><span>▼</span>';
        sortDescBtn.addEventListener('click', () => {
            this._handleSort(column, 'desc');
            this._closeFilterDropdown();
        });
        dropdown.appendChild(sortDescBtn);
        
        // Filter input
        const inputGroup = document.createElement('div');
        inputGroup.className = 'filter-input-group';
        
        const filterInput = document.createElement('input');
        filterInput.type = 'text';
        filterInput.className = 'filter-input-field';
        filterInput.placeholder = 'Enter filter value...';
        filterInput.value = this._config.filters[column] || '';
        
        // Handle input changes - filter on every keystroke
        let filterTimeout;
        filterInput.addEventListener('input', (e) => {
            // Debounce the filter to avoid too many requests
            clearTimeout(filterTimeout);
            filterTimeout = setTimeout(() => {
                this._applyFilterFromDropdown(column, filterInput.value);
            }, 300); // Wait 300ms after user stops typing
        });
        
        // Handle Enter key for immediate filter
        filterInput.addEventListener('keypress', (e) => {
            if (e.key === 'Enter') {
                clearTimeout(filterTimeout);
                this._applyFilterFromDropdown(column, filterInput.value);
            }
        });
        
        inputGroup.appendChild(filterInput);
        dropdown.appendChild(inputGroup);
        
        // Clear button
        const actions = document.createElement('div');
        actions.className = 'filter-dropdown-actions';
        
        const clearBtn = document.createElement('button');
        clearBtn.className = 'filter-dropdown-btn filter-dropdown-clear';
        clearBtn.textContent = 'Clear Filter';
        clearBtn.addEventListener('click', () => {
            filterInput.value = '';
            this._clearFilterFromDropdown(column);
        });
        
        actions.appendChild(clearBtn);
        dropdown.appendChild(actions);
        
        return dropdown;
    }
    
    /**
     * Close filter dropdown
     */
    _closeFilterDropdown() {
        if (this._activeFilterDropdown) {
            this._activeFilterDropdown.classList.remove('active');
            document.body.removeChild(this._activeFilterDropdown);
            this._activeFilterDropdown = null;
            this._currentFilterColumn = null;
        }
    }
    
    /**
     * Apply filter from dropdown
     */
    _applyFilterFromDropdown(column, value) {
        try {
            const trimmedValue = value.trim();
            if (trimmedValue) {
                this._config.filters[column] = trimmedValue;
            } else {
                delete this._config.filters[column];
            }
            // Don't close the dropdown - keep it open for further adjustments
            this._reloadData();
        } catch (error) {
            console.error('Error applying filter:', error);
            this._showError('Failed to apply filter. Please try again.');
        }
    }
    
    /**
     * Clear filter from dropdown
     */
    _clearFilterFromDropdown(column) {
        try {
            delete this._config.filters[column];
            this._closeFilterDropdown();
            this._reloadData();
        } catch (error) {
            console.error('Error clearing filter:', error);
            this._showError('Failed to clear filter. Please try again.');
        }
    }
    
    /**
     * Handle sorting with optional direction
     */
    _handleSort(column, direction = null) {
        try {
            if (direction) {
                this._config.sortColumn = column;
                this._config.sortDirection = direction;
            } else {
                if (this._config.sortColumn === column) {
                    // Toggle direction
                    this._config.sortDirection = this._config.sortDirection === 'asc' ? 'desc' : 'asc';
                } else {
                    this._config.sortColumn = column;
                    this._config.sortDirection = 'asc';
                }
            }
            
            this._reloadData();
        } catch (error) {
            console.error('Error handling sort:', error);
            this._showError('Failed to apply sorting. Please try again.');
        }
    }
    
    /**
     * Open filter modal (DEPRECATED - kept for compatibility)
     */
    _openFilterModal(column) {
        // This method is deprecated but kept for backward compatibility
        this._toggleFilterDropdown(column);
    }
    
    /**
     * Close filter modal (DEPRECATED - kept for compatibility)
     */
    _closeFilterModal() {
        this._closeFilterDropdown();
    }
    
    /**
     * Apply filter (DEPRECATED - kept for compatibility)
     */
    _applyFilter() {
        if (this._currentFilterColumn && this._activeFilterDropdown) {
            const filterInput = this._activeFilterDropdown.querySelector('.filter-input-field');
            if (filterInput) {
                this._applyFilterFromDropdown(this._currentFilterColumn, filterInput.value);
            }
        }
    }
    
    /**
     * Clear filter (DEPRECATED - kept for compatibility)
     */
    _clearFilter() {
        if (this._currentFilterColumn) {
            this._clearFilterFromDropdown(this._currentFilterColumn);
        }
    }
    
    /**
     * Handle select all checkbox
     */
    async _handleSelectAll(checked) {
        try {
            if (checked) {
                // Select all rows across all pages
                await this._selectAllRows();
                // Update checkbox state after async operation
                this._elements.selectAllCheckbox.checked = true;
            } else {
                this._selectedRows.clear();
            }
            
            this._renderTableBody();
            this._updateExportButtons();
        } catch (error) {
            console.error('Error handling select all:', error);
            this._showError('Failed to select rows. Please try again.');
        }
    }
    
    /**
     * Select all rows across all pages
     */
    async _selectAllRows() {
        try {
            const params = new URLSearchParams({
                page_size: 999999, // Get all rows
                sort_column: this._config.sortColumn || '',
                sort_direction: this._config.sortDirection
            });
            
            // Add filters
            Object.entries(this._config.filters).forEach(([key, value]) => {
                params.append(`filter_${key}`, value);
            });
            
            // Add visible columns
            params.append('visible_columns', JSON.stringify(this._config.visibleColumns));
            
            const currentPath = window.location.pathname;
            const basePath = currentPath.endsWith('/') ? currentPath : currentPath + '/';
            const apiUrl = `${basePath}api/data?${params.toString()}`;
            
            const response = await fetch(apiUrl);
            if (!response.ok) {
                const errorData = await response.json().catch(() => ({}));
                throw new Error(errorData.message || `HTTP error! status: ${response.status}`);
            }
            const config = await response.json();
            
            if (!config || !config.data) {
                throw new Error('Invalid response from server');
            }
            
            // Add all row IDs to selection
            config.data.forEach((row) => {
                const rowId = row.id || JSON.stringify(row);
                this._selectedRows.add(rowId);
            });
        } catch (error) {
            console.error('Error selecting all rows:', error);
            this._showError('Failed to select all rows. Please try again.');
        }
    }
    
    /**
     * Handle individual row selection
     */
    _handleRowSelection(index, checked) {
        const row = this._config.data[index];
        const rowId = row.id || JSON.stringify(row);
        
        if (checked) {
            this._selectedRows.add(rowId);
        } else {
            this._selectedRows.delete(rowId);
        }
        
        // Update row styling
        const rows = this._elements.tableBody.getElementsByTagName('tr');
        if (rows[index]) {
            if (checked) {
                rows[index].classList.add('selected');
            } else {
                rows[index].classList.remove('selected');
            }
        }
        
        this._updateSelectAllCheckbox();
        this._updateExportButtons();
    }
    
    /**
     * Update select all checkbox state
     */
    _updateSelectAllCheckbox() {
        const currentPageRows = this._config.data.length;
        const totalFilteredRows = this._config.totalRows; // Total rows across all pages
        const selectedCount = this._selectedRows.size;
        
        // Check if all rows across all pages are selected
        this._elements.selectAllCheckbox.checked = totalFilteredRows > 0 && selectedCount === totalFilteredRows;
        // Show indeterminate if some rows are selected but not all
        this._elements.selectAllCheckbox.indeterminate = selectedCount > 0 && selectedCount < totalFilteredRows;
    }
    
    /**
     * Update export buttons state
     */
    _updateExportButtons() {
        this._elements.exportSelectedBtn.disabled = this._selectedRows.size === 0;
    }
    
    /**
     * Change page
     */
    _changePage(page) {
        try {
            if (page < 1 || page > this._config.totalPages) {
                return;
            }
            
            this._config.currentPage = page;
            // Don't clear selections when changing pages
            this._reloadData();
        } catch (error) {
            console.error('Error changing page:', error);
            this._showError('Failed to change page. Please try again.');
        }
    }
    
    /**
     * Update pagination controls
     */
    _updatePagination() {
        const start = (this._config.currentPage - 1) * this._config.pageSize + 1;
        const end = Math.min(this._config.currentPage * this._config.pageSize, this._config.totalRows);
        
        this._elements.paginationInfo.textContent = `Showing ${start} - ${end} of ${this._config.totalRows} rows`;
        // Update button states
        this._elements.firstPageBtn.disabled = this._config.currentPage === 1;
        this._elements.prevPageBtn.disabled = this._config.currentPage === 1;
        this._elements.nextPageBtn.disabled = this._config.currentPage === this._config.totalPages;
        this._elements.lastPageBtn.disabled = this._config.currentPage === this._config.totalPages;
        // Render page numbers
        this._renderPageNumbers();
    }
    
    /**
     * Render page number buttons
     */
    _renderPageNumbers() {
        this._elements.pageNumbers.innerHTML = '';
        const maxButtons = 5;
        let startPage = Math.max(1, this._config.currentPage - Math.floor(maxButtons / 2));
        let endPage = Math.min(this._config.totalPages, startPage + maxButtons - 1);
        
        if (endPage - startPage < maxButtons - 1) {
            startPage = Math.max(1, endPage - maxButtons + 1);
        }
        for (let i = startPage; i <= endPage; i++) {
            const pageBtn = document.createElement('span');
            pageBtn.className = 'page-number';
            if (i === this._config.currentPage) {
                pageBtn.classList.add('active');
            }
            pageBtn.textContent = i;
            pageBtn.addEventListener('click', () => {
                this._changePage(i);
            });
            this._elements.pageNumbers.appendChild(pageBtn);
        }
    }
    
    /**
     * Export selected rows
     */
    _exportSelected() {
        try {
            if (this._selectedRows.size === 0) {
                this._showError('No rows selected to export.');
                return;
            }
            
            const selectedIds = Array.from(this._selectedRows);
            this._downloadCsv(selectedIds, 'selected_data.csv');
        } catch (error) {
            console.error('Error exporting selected rows:', error);
            this._showError('Failed to export selected rows. Please try again.');
        }
    }
    
    /**
     * Export all filtered data
     */
    _exportAll() {
        try {
            this._downloadCsv(null, 'all_data.csv');
        } catch (error) {
            console.error('Error exporting all data:', error);
            this._showError('Failed to export data. Please try again.');
        }
    }
    
    /**
     * Download data as CSV
     */
    _downloadCsv(selectedIds, filename) {
        try {
            const params = new URLSearchParams({
                page: this._config.currentPage,
                sort_column: this._config.sortColumn || '',
                sort_direction: this._config.sortDirection,
                export_type: selectedIds ? 'selected' : 'all'
            });
            
            // Add filters
            Object.entries(this._config.filters).forEach(([key, value]) => {
                params.append(`filter_${key}`, value);
            });
            
            // Add selected row IDs
            if (selectedIds) {
                params.append('selected_rows', JSON.stringify(selectedIds));
            }
            
            // Use relative path from current location
            const currentPath = window.location.pathname;
            const basePath = currentPath.endsWith('/') ? currentPath : currentPath + '/';
            const url = `${basePath}api/export?${params.toString()}`;
            
            // Create download link
            const link = document.createElement('a');
            link.href = url;
            link.download = filename;
            document.body.appendChild(link);
            link.click();
            document.body.removeChild(link);
        } catch (error) {
            console.error('Error downloading CSV:', error);
            this._showError('Failed to download CSV file. Please try again.');
        }
    }
    
    /**
     * Reload data from server
     */
    async _reloadData() {
        const params = new URLSearchParams({
            page: this._config.currentPage,
            page_size: this._config.pageSize,
            sort_column: this._config.sortColumn || '',
            sort_direction: this._config.sortDirection
        });
        
        // Add filters
        Object.entries(this._config.filters).forEach(([key, value]) => {
            params.append(`filter_${key}`, value);
        });
        
        // Add visible columns
        params.append('visible_columns', JSON.stringify(this._config.visibleColumns));
        
        // Use relative path from current location
        const currentPath = window.location.pathname;
        const basePath = currentPath.endsWith('/') ? currentPath : currentPath + '/';
        const apiUrl = `${basePath}api/data?${params.toString()}`;
        
        try {
            const response = await fetch(apiUrl);
            if (!response.ok) {
                const errorData = await response.json().catch(() => ({}));
                throw new Error(errorData.message || `HTTP error! status: ${response.status}`);
            }
            const newConfig = await response.json();
            
            if (!newConfig || !newConfig.data) {
                throw new Error('Invalid response from server');
            }
            
            this._config = newConfig;
            // Don't clear selections when reloading data
            this._renderTable();
            this._updatePagination();
            this._updateExportButtons();
            this._updateActiveFiltersDisplay();
        } catch (error) {
            console.error('Error reloading data:', error);
            this._showError('Failed to load data. Please try again.');
        }
    }
    
    /**
     * Update active filters display
     */
    _updateActiveFiltersDisplay() {
        const filterCount = Object.keys(this._config.filters).length;
        
        if (filterCount === 0) {
            this._elements.activeFilters.style.display = 'none';
            return;
        }
        
        this._elements.activeFilters.style.display = 'flex';
        this._elements.activeFiltersList.innerHTML = '';
        
        Object.entries(this._config.filters).forEach(([column, value]) => {
            const badge = document.createElement('div');
            badge.className = 'filter-badge';
            
            const label = document.createElement('span');
            label.className = 'filter-badge-label';
            label.textContent = column + ':';
            
            const valueSpan = document.createElement('span');
            valueSpan.className = 'filter-badge-value';
            valueSpan.textContent = value;
            
            const removeBtn = document.createElement('span');
            removeBtn.className = 'filter-badge-remove';
            removeBtn.textContent = '×';
            removeBtn.title = `Remove filter for ${column}`;
            removeBtn.addEventListener('click', () => {
                delete this._config.filters[column];
                this._reloadData();
            });
            
            badge.appendChild(label);
            badge.appendChild(valueSpan);
            badge.appendChild(removeBtn);
            
            this._elements.activeFiltersList.appendChild(badge);
        });
    }

    /**
     * Display error message to user
     */
    _showError(message) {
        alert(message);
    }
}

