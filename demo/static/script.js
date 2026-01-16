// MALDB Professional Interface - JavaScript with Multi-Database Support
class MALDBInterface {
    constructor() {
        this.currentPage = 'query';
        this.websocket = null;
        this.queryHistory = [];
        this.currentDatabase = 'default';
        this.init();
    }
    
    init() {
        this.bindEvents();
        this.loadDatabases();
        this.setupCodeEditor();
        
        // Start on query page
        this.navigateTo('query');
    }
    
    bindEvents() {
        // Navigation
        document.querySelectorAll('.nav-item').forEach(item => {
            item.addEventListener('click', (e) => {
                e.preventDefault();
                const page = item.dataset.page;
                if (page) {
                    this.navigateTo(page);
                }
            });
        });
        
        // SQL Execution
        const executeBtn = document.getElementById('executeBtn');
        if (executeBtn) {
            executeBtn.addEventListener('click', () => this.executeQuery());
        }
        
        const clearBtn = document.getElementById('clearBtn');
        if (clearBtn) {
            clearBtn.addEventListener('click', () => this.clearEditor());
        }
        
        // Quick actions
        document.querySelectorAll('.quick-action').forEach(btn => {
            btn.addEventListener('click', (e) => {
                e.preventDefault();
                const sql = e.currentTarget.dataset.sql;
                this.insertIntoEditor(sql);
            });
        });
        
        // Keyboard shortcuts
        document.addEventListener('keydown', (e) => {
            if ((e.ctrlKey || e.metaKey) && e.key === 'Enter') {
                e.preventDefault();
                this.executeQuery();
            }
            
            if ((e.ctrlKey || e.metaKey) && e.key === 'k') {
                e.preventDefault();
                this.clearEditor();
            }
        });
        
        // Form submissions
        const queryForm = document.getElementById('queryForm');
        if (queryForm) {
            queryForm.addEventListener('submit', (e) => {
                e.preventDefault();
                this.executeQuery();
            });
        }
        
        // Modal close on outside click
        document.addEventListener('click', (event) => {
            const modals = ['createDatabaseModal', 'deleteDatabaseModal'];
            
            modals.forEach(modalId => {
                const modal = document.getElementById(modalId);
                if (modal && modal.style.display === 'block' && event.target === modal) {
                    if (modalId === 'createDatabaseModal') {
                        this.hideCreateDatabaseModal();
                    } else if (modalId === 'deleteDatabaseModal') {
                        this.hideDeleteDatabaseModal();
                    }
                }
            });
        });
        
        // Escape key to close modals
        document.addEventListener('keydown', (event) => {
            if (event.key === 'Escape') {
                if (document.getElementById('createDatabaseModal').style.display === 'block') {
                    this.hideCreateDatabaseModal();
                } else if (document.getElementById('deleteDatabaseModal').style.display === 'block') {
                    this.hideDeleteDatabaseModal();
                }
            }
        });
        
        // Clear history button
        const clearHistoryBtn = document.getElementById('clearHistoryBtn');
        if (clearHistoryBtn) {
            clearHistoryBtn.addEventListener('click', () => this.clearHistory());
        }
        
        // Create database form submission
        const createDatabaseForm = document.getElementById('createDatabaseForm');
        if (createDatabaseForm) {
            createDatabaseForm.addEventListener('submit', (e) => {
                e.preventDefault();
                this.createDatabase();
            });
        }
        
        // Confirm delete database button
        const confirmDeleteBtn = document.getElementById('confirmDeleteBtn');
        if (confirmDeleteBtn) {
            confirmDeleteBtn.addEventListener('click', () => this.confirmDeleteDatabase());
        }
        
        // Cancel delete database button
        const cancelDeleteBtn = document.getElementById('cancelDeleteBtn');
        if (cancelDeleteBtn) {
            cancelDeleteBtn.addEventListener('click', () => this.hideDeleteDatabaseModal());
        }
        
        // Close modal buttons
        const closeCreateModal = document.querySelector('#createDatabaseModal .close');
        if (closeCreateModal) {
            closeCreateModal.addEventListener('click', () => this.hideCreateDatabaseModal());
        }
        
        const closeDeleteModal = document.querySelector('#deleteDatabaseModal .close');
        if (closeDeleteModal) {
            closeDeleteModal.addEventListener('click', () => this.hideDeleteDatabaseModal());
        }
    }
    
    setupCodeEditor() {
        const editor = document.getElementById('sqlEditor');
        if (editor) {
            editor.addEventListener('keydown', (e) => {
                if (e.key === 'Tab') {
                    e.preventDefault();
                    const start = editor.selectionStart;
                    const end = editor.selectionEnd;
                    
                    editor.value = editor.value.substring(0, start) + '    ' + editor.value.substring(end);
                    editor.selectionStart = editor.selectionEnd = start + 4;
                }
            });
            
            // Add some default content for demo
            editor.value = '-- Welcome to MALDB Professional Interface\n' +
                         '-- Try these examples:\n\n' +
                         'SELECT * FROM users;\n\n' +
                         'CREATE TABLE test (id INT PRIMARY KEY, name VARCHAR(50), data TEXT ENCRYPTED);\n\n' +
                         'INSERT INTO test VALUES (1, \'John\', \'secret data\');';
        }
    }
    
    async navigateTo(page) {
        this.currentPage = page;
        
        // Update active nav item
        document.querySelectorAll('.nav-item').forEach(item => {
            item.classList.toggle('active', item.dataset.page === page);
        });
        
        // Hide all pages
        document.querySelectorAll('.page').forEach(p => {
            p.style.display = 'none';
        });
        
        // Show current page
        const currentPage = document.getElementById(page + 'Page');
        if (currentPage) {
            currentPage.style.display = 'block';
        }
        
        // Load page-specific data
        switch(page) {
            case 'tables':
                await this.loadTables();
                break;
            case 'history':
                this.displayHistory();
                break;
            case 'monitor':
                this.displayMonitor();
                break;
        }
    }
    
    async executeQuery() {
        const editor = document.getElementById('sqlEditor');
        const sql = editor.value.trim();
        
        if (!sql) {
            this.showToast('Please enter a SQL query', 'warning');
            return;
        }
        
        // Show loading
        this.showLoading();
        
        try {
            console.log(`Executing query on ${this.currentDatabase}: ${sql}`);
            const response = await fetch('/api/execute', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ 
                    sql, 
                    database: this.currentDatabase 
                })
            });
            
            const result = await response.json();
            
            if (result.success) {
                this.displayResults(result);
                this.addToHistory(sql, result);
                this.showToast(`Query executed successfully (${result.execution_time}ms)`, 'success');
                
                // Update table list if needed
                const sqlUpper = sql.toUpperCase();
                if (sqlUpper.startsWith("CREATE TABLE") || sqlUpper.startsWith("DROP TABLE")) {
                    await this.loadTables();
                }
            } else {
                this.displayError(result.error);
                this.showToast('Error: ' + result.error, 'error');
            }
        } catch (error) {
            this.displayError(error.message);
            this.showToast('Network error occurred', 'error');
            console.error('Execute error:', error);
        } finally {
            this.hideLoading();
        }
    }
    
    displayResults(result) {
        const container = document.getElementById('resultsContainer');
        if (!container) return;
        
        // Add database info to results
        const dbInfo = result.database ? `<div style="font-size: 12px; color: var(--text-tertiary); margin-bottom: 8px;">
            Database: <strong>${this.escapeHtml(result.database)}</strong>
        </div>` : '';
        
        if (!result.result || result.result.length === 0) {
            container.innerHTML = dbInfo + '<div class="result-header">' +
                                '<div class="result-stats">' +
                                '<div class="stat-item success">' +
                                '<span class="status-indicator status-online"></span>' +
                                'Query executed in ' + result.execution_time + 'ms' +
                                '</div>' +
                                '<div class="stat-item">' +
                                'No rows returned' +
                                '</div>' +
                                '</div>' +
                                '</div>' +
                                '<div class="no-data" style="padding: 20px; text-align: center; color: var(--text-secondary);">' +
                                '<p>Query executed successfully. No data returned.</p>' +
                                '</div>';
            return;
        }
        
        // Build table HTML
        let tableHTML = dbInfo + '<div class="result-header">' +
                       '<div class="result-stats">' +
                       '<div class="stat-item success">' +
                       '<span class="status-indicator status-online"></span>' +
                       'Query executed in ' + result.execution_time + 'ms' +
                       '</div>' +
                       '<div class="stat-item">' +
                       result.affected_rows + ' row' + (result.affected_rows !== 1 ? 's' : '') + ' returned' +
                       '</div>' +
                       '</div>' +
                       '</div>' +
                       '<div class="table-responsive">' +
                       '<table class="result-table">' +
                       '<thead>' +
                       '<tr>';
        
        // Add headers
        if (result.columns && result.columns.length > 0) {
            result.columns.forEach(column => {
                tableHTML += '<th>' + this.escapeHtml(column) + '</th>';
            });
        } else if (result.result && result.result.length > 0) {
            // If no column names, use generic ones
            const firstRow = result.result[0];
            if (Array.isArray(firstRow)) {
                for (let i = 0; i < firstRow.length; i++) {
                    tableHTML += '<th>Column ' + (i + 1) + '</th>';
                }
            } else if (typeof firstRow === 'object') {
                Object.keys(firstRow).forEach(key => {
                    tableHTML += '<th>' + this.escapeHtml(key) + '</th>';
                });
            }
        }
        
        tableHTML += '</tr>' +
                    '</thead>' +
                    '<tbody>';
        
        // Add rows
        result.result.forEach(row => {
            tableHTML += '<tr>';
            if (Array.isArray(row)) {
                row.forEach(cell => {
                    tableHTML += '<td>' + this.escapeHtml(String(cell)) + '</td>';
                });
            } else if (typeof row === 'object') {
                // Handle object rows
                Object.values(row).forEach(cell => {
                    tableHTML += '<td>' + this.escapeHtml(String(cell)) + '</td>';
                });
            } else {
                tableHTML += '<td>' + this.escapeHtml(String(row)) + '</td>';
            }
            tableHTML += '</tr>';
        });
        
        tableHTML += '</tbody>' +
                    '</table>' +
                    '</div>';
        
        container.innerHTML = tableHTML;
    }
    
    displayError(error) {
        const container = document.getElementById('resultsContainer');
        if (!container) return;
        
        container.innerHTML = '<div class="result-header">' +
                             '<div class="result-stats">' +
                             '<div class="stat-item error">' +
                             '<span class="status-indicator status-warning"></span>' +
                             'Query failed' +
                             '</div>' +
                             '</div>' +
                             '</div>' +
                             '<div class="error-message">' +
                             '<pre style="background: rgba(248, 81, 73, 0.1); padding: 16px; border-radius: 6px; color: #f85149; font-family: monospace; white-space: pre-wrap;">' +
                             this.escapeHtml(error) +
                             '</pre>' +
                             '</div>';
    }
    
    async loadDatabases() {
        try {
            console.log('Loading databases...');
            const response = await fetch('/api/databases');
            const data = await response.json();
            
            const databaseList = document.getElementById('databaseList');
            const currentDbName = document.getElementById('currentDbName');
            const tableCount = document.getElementById('tableCount');
            
            if (data.success && data.databases && data.databases.length > 0) {
                console.log(`Found ${data.databases.length} databases`);
                databaseList.innerHTML = '';
                
                // Sort databases: default always first, then others alphabetically
                const sortedDatabases = [...data.databases].sort((a, b) => {
                    if (a.name === 'default') return -1;
                    if (b.name === 'default') return 1;
                    return a.name.localeCompare(b.name);
                });
                
                console.log('Sorted databases:', sortedDatabases.map(db => db.name));
                
                // Find current database info
                let currentDbInfo = null;
                
                sortedDatabases.forEach(db => {
                    const dbItem = document.createElement('div');
                    const isCurrent = db.name === data.current;
                    
                    if (isCurrent) {
                        this.currentDatabase = db.name;
                        currentDbInfo = db;
                        console.log(`Current database: ${db.name} with ${db.tables} tables`);
                    }
                    
                    dbItem.className = `nav-item database-item ${isCurrent ? 'active' : ''}`;
                    dbItem.innerHTML = `
                        <span style="display: flex; align-items: center; gap: 8px;">
                            <span>${isCurrent ? '🗃️' : '📁'}</span>
                            <span>${this.escapeHtml(db.name)}</span>
                        </span>
                        <div class="database-actions" style="margin-left: auto; display: flex; gap: 4px;">
                            ${!isCurrent ? `
                            <button class="db-action-btn" onclick="maldb.switchDatabase('${this.escapeSingleQuotes(db.name)}')" title="Switch to ${this.escapeHtml(db.name)}">
                                ➡️
                            </button>
                            ` : ''}
                            ${db.name !== 'default' ? `
                            <button class="db-action-btn danger" onclick="maldb.showDeleteDatabaseModal('${this.escapeSingleQuotes(db.name)}')" title="Delete ${this.escapeHtml(db.name)}">
                                🗑️
                            </button>
                            ` : ''}
                        </div>
                    `;
                    
                    // Add table count badge
                    if (db.tables > 0) {
                        const badge = document.createElement('span');
                        badge.className = 'badge badge-success';
                        badge.style.marginLeft = '8px';
                        badge.textContent = db.tables;
                        dbItem.appendChild(badge);
                    }
                    
                    databaseList.appendChild(dbItem);
                });
                
                // Update current database indicator
                if (currentDbName) {
                    currentDbName.textContent = this.currentDatabase;
                }
                
                // Update table count in header
                if (tableCount && currentDbInfo) {
                    tableCount.textContent = `${currentDbInfo.tables} table${currentDbInfo.tables !== 1 ? 's' : ''}`;
                } else if (tableCount) {
                    // If currentDbInfo not found, try to find it in the sorted list
                    const foundDb = sortedDatabases.find(db => db.name === this.currentDatabase);
                    if (foundDb) {
                        tableCount.textContent = `${foundDb.tables} table${foundDb.tables !== 1 ? 's' : ''}`;
                    } else {
                        tableCount.textContent = '0 tables';
                    }
                }
                
                // Load tables for current database (only if we're on the tables page)
                if (this.currentPage === 'tables') {
                    await this.loadTables();
                }
            } else {
                console.error('No databases found or API error:', data);
                // Show default state
                if (databaseList) {
                    databaseList.innerHTML = '<div style="padding: 12px; color: var(--text-tertiary); font-size: 13px;">No databases found</div>';
                }
            }
        } catch (error) {
            console.error('Error loading databases:', error);
            this.showNotification('Failed to load databases', 'error');
        }
    }
    
    async loadTables() {
        const container = document.getElementById('tablesContainer');
        if (!container || this.currentPage !== 'tables') return;
        
        container.innerHTML = '<div class="loading">Loading tables...</div>';
        
        try {
            console.log(`Loading tables for database: ${this.currentDatabase}`);
            const response = await fetch('/api/tables');
            const data = await response.json();
            
            if (!data.success || !data.tables) {
                container.innerHTML = '<div class="no-tables" style="text-align: center; padding: 40px; color: var(--text-tertiary);">' +
                                    `<p>Failed to load tables: ${data.error || 'Unknown error'}</p>` +
                                    '<button class="toolbar-btn" onclick="maldb.loadTables()">Retry</button>' +
                                    '</div>';
                return;
            }
            
            if (data.tables.length === 0) {
                container.innerHTML = '<div class="no-tables" style="text-align: center; padding: 40px; color: var(--text-tertiary);">' +
                                    `<p>No tables found in database '${this.escapeHtml(data.database || this.currentDatabase)}'. Create a table to get started.</p>` +
                                    '<button class="toolbar-btn primary" onclick="maldb.insertIntoEditor(\'CREATE TABLE users (id INT PRIMARY KEY, name VARCHAR(50), email VARCHAR(100), password TEXT ENCRYPTED)\')">' +
                                    'Create Example Table' +
                                    '</button>' +
                                    '</div>';
                return;
            }
            
            let tablesHTML = `<div style="font-size: 12px; color: var(--text-tertiary); margin-bottom: 16px;">
                Database: <strong>${this.escapeHtml(data.database || this.currentDatabase)}</strong> - ${data.tables.length} table${data.tables.length !== 1 ? 's' : ''}
            </div>` +
            '<div class="tables-grid">';
            
            for (const tableName of data.tables) {
                try {
                    // Fetch actual schema for each table
                    const schemaResponse = await fetch('/api/schema/' + encodeURIComponent(tableName));
                    const schemaData = await schemaResponse.json();
                    
                    let schemaHTML = '';
                    if (schemaData.success && schemaData.schema) {
                        schemaData.schema.forEach(column => {
                            schemaHTML += '<div class="schema-item">' +
                                         '<span class="column-name">' + this.escapeHtml(column.name) + '</span>' +
                                         '<span class="column-type">' +
                                         '<span>' + column.type + '</span>' +
                                         (column.encrypted ? '<span class="encrypted-badge">ENCRYPTED</span>' : '') +
                                         (column.primary_key ? '<span style="color: var(--accent-green); font-size: 10px; margin-left: 4px;">PK</span>' : '') +
                                         '</span>' +
                                         '</div>';
                        });
                    } else {
                        // Fallback schema
                        schemaHTML = '<div class="schema-item">' +
                                    '<span class="column-name">id</span>' +
                                    '<span class="column-type">INT</span>' +
                                    '</div>' +
                                    '<div class="schema-item">' +
                                    '<span class="column-name">name</span>' +
                                    '<span class="column-type">VARCHAR(50)</span>' +
                                    '</div>';
                    }
                    
                    const escapedTableName = this.escapeHtml(tableName);
                    const safeTableName = this.escapeSingleQuotes(tableName);
                    
                    tablesHTML += '<div class="table-card">' +
                                 '<div class="table-header">' +
                                 '<div class="table-name">' + escapedTableName + '</div>' +
                                 '<div class="table-stats">' +
                                 '<span class="badge badge-success">Active</span>' +
                                 '</div>' +
                                 '</div>' +
                                 '<div class="table-schema">' +
                                 schemaHTML +
                                 '</div>' +
                                 '<div style="margin-top: 16px; display: flex; gap: 8px;">' +
                                 '<button class="toolbar-btn" onclick="maldb.insertIntoEditor(\'SELECT * FROM ' + safeTableName + '\')">' +
                                 'Select All' +
                                 '</button>' +
                                 '<button class="toolbar-btn" onclick="maldb.insertIntoEditor(\'DROP TABLE ' + safeTableName + '\')" style="color: #f85149;">' +
                                 'Drop Table' +
                                 '</button>' +
                                 '</div>' +
                                 '</div>';
                } catch (schemaError) {
                    console.error('Error loading schema for ' + tableName + ':', schemaError);
                    // Show table without schema
                    const escapedTableName = this.escapeHtml(tableName);
                    const safeTableName = this.escapeSingleQuotes(tableName);
                    
                    tablesHTML += '<div class="table-card">' +
                                 '<div class="table-header">' +
                                 '<div class="table-name">' + escapedTableName + '</div>' +
                                 '<div class="table-stats">' +
                                 '<span class="badge badge-success">Active</span>' +
                                 '</div>' +
                                 '</div>' +
                                 '<div style="margin-top: 16px; display: flex; gap: 8px;">' +
                                 '<button class="toolbar-btn" onclick="maldb.insertIntoEditor(\'SELECT * FROM ' + safeTableName + '\')">' +
                                 'Select All' +
                                 '</button>' +
                                 '</div>' +
                                 '</div>';
                }
            }
            
            tablesHTML += '</div>';
            container.innerHTML = tablesHTML;
        } catch (error) {
            console.error('Error loading tables:', error);
            container.innerHTML = '<div class="error-message" style="text-align: center; padding: 40px;">' +
                                '<p>Failed to load tables: ' + error.message + '</p>' +
                                '<button class="toolbar-btn" onclick="maldb.loadTables()">Retry</button>' +
                                '</div>';
        }
    }
    
    async switchDatabase(dbName) {
        try {
            console.log(`Switching to database: ${dbName}`);
            
            const response = await fetch('/api/databases/switch', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ name: dbName })
            });
            
            const data = await response.json();
            
            if (data.success) {
                this.currentDatabase = dbName;
                
                // Reload databases FIRST to update the sidebar
                await this.loadDatabases();
                
                // Show success message
                this.showNotification(`Switched to database '${dbName}'`, 'success');
                
                // Clear query editor and results
                const editor = document.getElementById('sqlEditor');
                if (editor) {
                    editor.value = `-- Switched to database '${dbName}'\n-- Try: SELECT * FROM users;`;
                }
                
                const resultsContainer = document.getElementById('resultsContainer');
                if (resultsContainer) {
                    resultsContainer.innerHTML = `
                        <div class="loading">
                            Switched to database '${dbName}'. Enter a new SQL command.
                        </div>
                    `;
                }
                
                // If on tables page, reload tables
                if (this.currentPage === 'tables') {
                    await this.loadTables();
                }
            } else {
                this.showNotification(`Error: ${data.error}`, 'error');
            }
        } catch (error) {
            console.error('Error switching database:', error);
            this.showNotification('Error switching database', 'error');
        }
    }
    
    showCreateDatabaseModal() {
        document.getElementById('newDatabaseName').value = '';
        document.getElementById('createDatabaseModal').style.display = 'block';
        document.getElementById('newDatabaseName').focus();
    }
    
    hideCreateDatabaseModal() {
        document.getElementById('createDatabaseModal').style.display = 'none';
    }
    
    async createDatabase() {
        const dbName = document.getElementById('newDatabaseName').value.trim();
        
        if (!dbName) {
            this.showNotification('Please enter a database name', 'error');
            return;
        }
        
        // Validate name
        if (!/^[a-zA-Z0-9_]+$/.test(dbName)) {
            this.showNotification('Database name can only contain letters, numbers, and underscores', 'error');
            return;
        }
        
        if (dbName.toLowerCase() === 'default') {
            this.showNotification('Cannot create database named "default". It already exists.', 'error');
            return;
        }
        
        try {
            const response = await fetch('/api/databases/create', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ name: dbName })
            });
            
            const data = await response.json();
            
            if (data.success) {
                this.showNotification(`Database '${dbName}' created successfully`, 'success');
                this.hideCreateDatabaseModal();
                
                // Reload databases FIRST to update the sidebar
                await this.loadDatabases();
                
                // Then switch to the new one
                await this.switchDatabase(dbName);
            } else {
                this.showNotification(`Error: ${data.error}`, 'error');
            }
        } catch (error) {
            console.error('Error creating database:', error);
            this.showNotification('Error creating database', 'error');
        }
    }
    
    showDeleteDatabaseModal(dbName) {
        document.getElementById('deleteDbName').textContent = dbName;
        document.getElementById('deleteDatabaseModal').style.display = 'block';
        // Store the database name to delete
        document.getElementById('deleteDatabaseModal').dataset.dbName = dbName;
    }
    
    hideDeleteDatabaseModal() {
        document.getElementById('deleteDatabaseModal').style.display = 'none';
        delete document.getElementById('deleteDatabaseModal').dataset.dbName;
    }
    
    async confirmDeleteDatabase() {
        const dbName = document.getElementById('deleteDatabaseModal').dataset.dbName;
        
        if (!dbName) return;
        
        if (dbName === 'default') {
            this.showNotification('Cannot delete the default database', 'error');
            this.hideDeleteDatabaseModal();
            return;
        }
        
        try {
            const response = await fetch(`/api/databases/${dbName}`, {
                method: 'DELETE'
            });
            
            const data = await response.json();
            
            if (data.success) {
                this.showNotification(`Database '${dbName}' deleted successfully`, 'success');
                this.hideDeleteDatabaseModal();
                
                // Reload databases
                await this.loadDatabases();
                
                // Reload tables (will show empty for default)
                if (this.currentPage === 'tables') {
                    await this.loadTables();
                }
            } else {
                this.showNotification(`Error: ${data.error}`, 'error');
            }
        } catch (error) {
            console.error('Error deleting database:', error);
            this.showNotification('Error deleting database', 'error');
        }
    }
    
    showNotification(message, type = 'info') {
        // Create notification element
        const notification = document.createElement('div');
        notification.className = `notification notification-${type}`;
        notification.innerHTML = `
            <span>${this.escapeHtml(message)}</span>
            <button onclick="this.parentElement.remove()">&times;</button>
        `;
        
        // Add to page
        document.body.appendChild(notification);
        
        // Auto-remove after 5 seconds
        setTimeout(() => {
            if (notification.parentElement) {
                notification.remove();
            }
        }, 5000);
    }
    
    addToHistory(sql, result) {
        const historyItem = {
            sql,
            timestamp: new Date().toISOString(),
            success: result.success,
            executionTime: result.execution_time || 0,
            rowsAffected: result.affected_rows || 0,
            database: result.database || this.currentDatabase
        };
        
        this.queryHistory.unshift(historyItem);
        
        // Keep only last 50 queries
        if (this.queryHistory.length > 50) {
            this.queryHistory = this.queryHistory.slice(0, 50);
        }
        
        // Save to localStorage
        try {
            localStorage.setItem('maldb_query_history', JSON.stringify(this.queryHistory));
        } catch (e) {
            console.warn('Could not save history to localStorage:', e);
        }
    }
    
    displayHistory() {
        const container = document.getElementById('historyPage');
        if (!container) return;
        
        // Load from localStorage
        try {
            const savedHistory = localStorage.getItem('maldb_query_history');
            if (savedHistory) {
                this.queryHistory = JSON.parse(savedHistory);
            }
        } catch (e) {
            console.warn('Could not load history from localStorage:', e);
        }
        
        const historyContent = container.querySelector('.history-content') || 
                             (() => {
                                 const div = document.createElement('div');
                                 div.className = 'history-content';
                                 container.querySelector('.card').appendChild(div);
                                 return div;
                             })();
        
        if (this.queryHistory.length === 0) {
            historyContent.innerHTML = '<div style="text-align: center; padding: 48px 24px; color: var(--text-tertiary);">' +
                                      '<p>No query history yet.</p>' +
                                      '<p style="font-size: 14px; margin-top: 8px;">Execute some queries to see them here</p>' +
                                      '</div>';
            return;
        }
        
        let historyHTML = '<div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 20px;">' +
                         '<h3 style="font-size: 14px; font-weight: 600; color: var(--text-secondary);">' +
                         this.queryHistory.length + ' queries in history' +
                         '</h3>' +
                         '<button class="toolbar-btn" onclick="maldb.clearHistory()" style="background: var(--accent-red); color: white;">' +
                         'Clear History' +
                         '</button>' +
                         '</div>' +
                         '<div style="max-height: 500px; overflow-y: auto;">';
        
        this.queryHistory.forEach((item, index) => {
            const time = new Date(item.timestamp).toLocaleTimeString();
            const date = new Date(item.timestamp).toLocaleDateString();
            const safeSql = this.escapeSingleQuotes(item.sql);
            
            historyHTML += '<div class="history-item" style="' +
                          'background: ' + (item.success ? 'rgba(35, 134, 54, 0.05)' : 'rgba(248, 81, 73, 0.05)') + ';' +
                          'border-left: 3px solid ' + (item.success ? 'var(--ui-success)' : 'var(--ui-error)') + ';' +
                          'padding: 16px;' +
                          'margin-bottom: 12px;' +
                          'border-radius: 4px;' +
                          'cursor: pointer;"' +
                          ' onclick="maldb.insertIntoEditor(\'' + safeSql + '\')">' +
                          '<div style="display: flex; justify-content: space-between; margin-bottom: 8px;">' +
                          '<span style="font-size: 12px; color: var(--text-tertiary);">' +
                          date + ' ' + time + ' (' + (item.database || 'default') + ')' +
                          '</span>' +
                          '<span style="font-size: 12px; color: ' + (item.success ? 'var(--ui-success)' : 'var(--ui-error)') + ';">' +
                          (item.success ? '✓ Success' : '✗ Failed') + ' (' + item.executionTime + 'ms)' +
                          '</span>' +
                          '</div>' +
                          '<pre style="' +
                          'margin: 0;' +
                          'font-family: monospace;' +
                          'font-size: 12px;' +
                          'color: var(--text-primary);' +
                          'white-space: pre-wrap;' +
                          'overflow: hidden;' +
                          'text-overflow: ellipsis;' +
                          'max-height: 60px;">' +
                          this.escapeHtml(item.sql) +
                          '</pre>' +
                          (item.rowsAffected > 0 ? '<div style="margin-top: 8px; font-size: 12px; color: var(--text-secondary);">' +
                          item.rowsAffected + ' row' + (item.rowsAffected !== 1 ? 's' : '') + ' affected' +
                          '</div>' : '') +
                          '</div>';
        });
        
        historyHTML += '</div>';
        historyContent.innerHTML = historyHTML;
    }
    
    clearHistory() {
        if (confirm('Are you sure you want to clear all query history?')) {
            this.queryHistory = [];
            try {
                localStorage.removeItem('maldb_query_history');
            } catch (e) {
                console.warn('Could not clear history from localStorage:', e);
            }
            this.displayHistory();
            this.showToast('Query history cleared', 'success');
        }
    }
    
    displayMonitor() {
        const container = document.getElementById('monitorPage');
        if (!container) return;
        
        const monitorContent = container.querySelector('.monitor-content') || 
                              (() => {
                                  const div = document.createElement('div');
                                  div.className = 'monitor-content';
                                  container.querySelector('.card').appendChild(div);
                                  return div;
                              })();
        
        const successCount = this.queryHistory.filter(q => q.success).length;
        const totalCount = this.queryHistory.length;
        const avgTime = totalCount > 0 ? 
            Math.round(this.queryHistory.reduce((sum, q) => sum + q.executionTime, 0) / totalCount) : 0;
        const successRate = totalCount > 0 ? Math.round((successCount / totalCount) * 100) : 0;
        
        monitorContent.innerHTML = '<div style="display: grid; grid-template-columns: repeat(auto-fit, minmax(250px, 1fr)); gap: 20px;">' +
                                  '<div class="stat-card" style="background: var(--tertiary-dark); padding: 20px; border-radius: 8px;">' +
                                  '<div style="font-size: 12px; color: var(--text-secondary); margin-bottom: 8px;">Total Queries</div>' +
                                  '<div style="font-size: 24px; font-weight: bold; color: var(--accent-blue);">' + totalCount + '</div>' +
                                  '</div>' +
                                  '<div class="stat-card" style="background: var(--tertiary-dark); padding: 20px; border-radius: 8px;">' +
                                  '<div style="font-size: 12px; color: var(--text-secondary); margin-bottom: 8px;">Success Rate</div>' +
                                  '<div style="font-size: 24px; font-weight: bold; color: var(--accent-green);">' + successRate + '%</div>' +
                                  '</div>' +
                                  '<div class="stat-card" style="background: var(--tertiary-dark); padding: 20px; border-radius: 8px;">' +
                                  '<div style="font-size: 12px; color: var(--text-secondary); margin-bottom: 8px;">Avg Execution Time</div>' +
                                  '<div style="font-size: 24px; font-weight: bold; color: var(--accent-yellow);">' + avgTime + 'ms</div>' +
                                  '</div>' +
                                  '</div>' +
                                  '<div style="margin-top: 30px; text-align: center; color: var(--text-tertiary);">' +
                                  '<p>Advanced monitoring features coming soon</p>' +
                                  '<p style="font-size: 14px; margin-top: 8px;">Real-time metrics and performance analytics</p>' +
                                  '</div>';
    }
    
    insertIntoEditor(sql) {
        const editor = document.getElementById('sqlEditor');
        if (editor) {
            editor.value = sql;
            editor.focus();
            
            // Navigate to query page if not already there
            if (this.currentPage !== 'query') {
                this.navigateTo('query');
            }
        }
    }
    
    clearEditor() {
        const editor = document.getElementById('sqlEditor');
        if (editor) {
            editor.value = '';
            editor.focus();
            this.showToast('Editor cleared', 'info');
        }
    }
    
    showLoading() {
        const btn = document.getElementById('executeBtn');
        if (btn) {
            const originalText = btn.innerHTML;
            btn.innerHTML = '<span class="loading-spinner"></span> Executing...';
            btn.disabled = true;
            btn.dataset.originalText = originalText;
        }
        
        // Add loading spinner CSS if not present
        if (!document.querySelector('#loading-spinner-style')) {
            const style = document.createElement('style');
            style.id = 'loading-spinner-style';
            style.textContent = '.loading-spinner {' +
                               'display: inline-block;' +
                               'width: 16px;' +
                               'height: 16px;' +
                               'border: 2px solid rgba(255,255,255,0.3);' +
                               'border-radius: 50%;' +
                               'border-top-color: white;' +
                               'animation: spin 1s linear infinite;' +
                               'margin-right: 8px;' +
                               '}' +
                               '@keyframes spin {' +
                               'to { transform: rotate(360deg); }' +
                               '}';
            document.head.appendChild(style);
        }
    }
    
    hideLoading() {
        const btn = document.getElementById('executeBtn');
        if (btn && btn.dataset.originalText) {
            btn.innerHTML = btn.dataset.originalText;
            btn.disabled = false;
        }
    }
    
    showToast(message, type = 'info') {
        const container = document.querySelector('.toast-container') || this.createToastContainer();
        
        const icons = {
            success: '✓',
            error: '✗',
            warning: '⚠',
            info: 'ℹ'
        };
        
        const titles = {
            success: 'Success',
            error: 'Error',
            warning: 'Warning',
            info: 'Info'
        };
        
        const toast = document.createElement('div');
        toast.className = 'toast toast-' + type;
        toast.innerHTML = '<div style="display: flex; align-items: flex-start; gap: 12px;">' +
                         '<div style="flex-shrink: 0; font-size: 18px;">' +
                         icons[type] || icons.info +
                         '</div>' +
                         '<div style="flex: 1;">' +
                         '<div style="font-weight: 600; margin-bottom: 4px;">' + (titles[type] || titles.info) + '</div>' +
                         '<div style="font-size: 14px; color: #8b949e;">' + this.escapeHtml(message) + '</div>' +
                         '</div>' +
                         '<button onclick="this.parentElement.parentElement.remove()" style="' +
                         'margin-left: auto; ' +
                         'background: none; ' +
                         'border: none; ' +
                         'color: #8b949e; ' +
                         'cursor: pointer;' +
                         'font-size: 20px;' +
                         'padding: 0 8px;">' +
                         '×' +
                         '</button>' +
                         '</div>';
        
        container.appendChild(toast);
        
        // Auto remove after 5 seconds
        setTimeout(() => {
            if (toast.parentNode) {
                toast.remove();
            }
        }, 5000);
    }
    
    createToastContainer() {
        const container = document.createElement('div');
        container.className = 'toast-container';
        document.body.appendChild(container);
        return container;
    }
    
    escapeHtml(text) {
        if (text === null || text === undefined) return '';
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }
    
    escapeSingleQuotes(text) {
        if (text === null || text === undefined) return '';
        return text.replace(/'/g, "\\'").replace(/"/g, '\\"');
    }
}

// Initialize when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    window.maldb = new MALDBInterface();
});