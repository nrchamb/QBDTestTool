# Changelog

All notable changes to QBDTestTool-Verosa will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/).

## [v1.1.0] - 2025-11-05

### Added

#### Statement Charge Support
- **Full statement charge lifecycle tracking**: Statement charges now properly track open/closed status based on payment application
- **Statement charge monitoring**: Statement charges appear in monitoring UI and track status changes
- **Statement charge payment verification**: Verify payment posting, deposit accounts, and linked transactions for statement charges
- **Statement charge archival**: Archive closed statement charges alongside invoices and sales receipts

#### Session Persistence
- **Auto-save functionality**: Automatically saves session state after transaction creation and modifications
- **Manual save/load**: Save and load sessions via File menu
- **JSON-based storage**: Session data stored in human-readable JSON format
- **Transaction recovery**: Resume monitoring previously created transactions after restarting the application

#### Logging System
- **Log granularity control**: Three log levels - Normal, Verbose, and Debug
- **Separate logging contexts**: Distinct logs for Create, Monitor, and Data Loading operations
- **Rolling log window**: Displays last 250 messages with automatic cleanup
- **Debug QBXML output**: View raw QBXML requests/responses in Debug mode
- **UI controls**: Log level selector in each tab for real-time granularity adjustment

#### Cleanup & Archive System
- **Archive closed transactions**: Mark closed/paid transactions as archived for organizational purposes
- **Archive all transactions**: Bulk archive all transactions regardless of status
- **Delete from QuickBooks**: Permanently delete archived transactions from QuickBooks database
- **Remove from session**: Remove archived transactions from local session (preserves QuickBooks records)
- **Safety confirmations**: Double-confirmation dialogs for destructive operations
- **Archival status display**: Visual indicators showing archived transaction counts

### Changed

#### Massive Code Reorganization (3,700+ lines → 214 lines in app.py)
Reduced monolithic app.py to focused orchestrator by extracting functionality into organized packages:

##### actions/ - Redux-style Action Creators
- **charge_actions.py**: Statement charge action creators
- **customer_actions.py**: Customer CRUD and combo update actions
- **invoice_actions.py**: Invoice creation actions
- **sales_receipt_actions.py**: Sales receipt creation actions
- **monitor_actions.py**: Invoice monitoring start/stop/update actions
- **monitor_search_actions.py**: Advanced search functionality for invoices

##### workers/ - Background Threading Workers
- **customer_worker.py**: Customer/job/subjob batch creation worker
- **invoice_worker.py**: Invoice batch creation worker
- **sales_receipt_worker.py**: Sales receipt batch creation worker
- **charge_worker.py**: Statement charge batch creation worker
- **monitor_worker.py**: Background invoice state monitoring worker
- **data_loader_worker.py**: QB data loading (customers, items, accounts)

##### ui/ - UI Component Setup
- **create_tab_setup.py**: Create Data tab with nested subtabs
- **monitor_tab_setup.py**: Monitor tab UI
- **verify_tab_setup.py**: Verification Results tab UI
- **setup_subtab_setup.py**: Setup subtab (load customers/items/accounts)
- **customer_subtab_setup.py**: Customer creation subtab
- **invoice_subtab_setup.py**: Invoice creation subtab
- **sales_receipt_subtab_setup.py**: Sales receipt creation subtab
- **charge_subtab_setup.py**: Statement charge creation subtab
- **logging_utils.py**: Centralized logging helpers
- **ui_utils.py**: UI utility functions

##### store/ - Redux-like State Management
- **store.py**: Store class with subscribe/dispatch
- **state.py**: AppState dataclass definitions
- **actions.py**: Action type constants and creators
- **reducers.py**: Pure reducer functions for state updates

##### mock_generation/ - Test Data Generators
- **customer_generator.py**: CustomerGenerator with configurable field randomization
- **invoice_generator.py**: InvoiceGenerator with line items, terms, classes
- **sales_receipt_generator.py**: SalesReceiptGenerator with line items
- **charge_generator.py**: ChargeGenerator for statement charges

##### trayapp/ - System Tray Daemon
- **tray_icon.py**: System tray icon implementation
- **daemon_actions.py**: Daemon mode actions

#### QuickBooks Module Organization
- **Dedicated qb/ package**: Moved QB integration code to `src/qb/` for better organization
  - `qb_connection.py` → `src/qb/connection.py`
  - `qb_ipc_client.py` → `src/qb/ipc_client.py`
  - `qb_data_loader.py` → `src/qb/data_loader.py`
  - `qbxml_builder.py` → `src/qb/xml_builder.py`
  - `qbxml_parser.py` → `src/qb/xml_parser.py`
- **Consolidated imports**: Single `from qb import ...` pattern for cleaner code
- **Package exports**: Proper `__init__.py` with `__all__` declarations

#### UI Improvements
- **Unified transaction tab**: Combined Invoice, Sales Receipt, and Statement Charge creation into single tab with radio button selection
- **Status indicators**: Visual feedback for archival operations
- **Log display optimization**: Improved scrolling and message formatting
- **Better error handling**: Consistent error display across all operations

#### Connection Management
- **Optimized batch operations**: Single connection per batch operation instead of per-transaction
- **Proper cleanup**: Consistent disconnect pattern across all workers
- **Background isolation**: QB connection manager runs in separate process
- **Better resource management**: Explicit connection lifecycle management

### Fixed

#### Statement Charge Issues
- **Missing from UI**: Statement charges now properly dispatch to Redux store and appear in monitoring tree
- **Duplicate ref numbers**: Fixed SC-1, SC-2 pattern repeating across batches by using unique txn_id placeholder
- **Status tracking**: Changed from hardcoded "completed" to proper open/closed lifecycle based on `is_paid` field
- **Archive logic**: Only archives closed charges instead of all charges
- **Payment verification**: Statement charges now trigger verification when status changes

#### Data Model Issues
- **ChargeQueryRs parser**: Added missing `is_paid`, `balance_remaining`, and `linked_transactions` fields
- **StatementChargeRecord**: Added `deposit_account` and `payment_info` fields for payment tracking
- **Documentation**: Corrected docstrings that incorrectly stated charges are "always completed"

#### Monitoring
- **Status change detection**: Statement charges now properly detect and log status changes (open → closed)
- **Verification on change**: Statement charges trigger payment verification when status changes
- **Deposit account tracking**: Properly populate and verify deposit account information
- **Thread safety**: Improved UI updates from background threads using root.after()

### Technical Details

#### Architecture Benefits
- **Maintainability**: Easy to locate and modify specific functionality
- **Separation of Concerns**: Clear boundaries between UI, business logic, state, and workers
- **Testability**: Isolated modules are easier to unit test
- **Scalability**: Adding new features is now straightforward
- **Code Reuse**: Shared utilities in dedicated modules
- **Reduced Coupling**: Dependencies are explicit and minimal

#### Dependencies
- Python 3.11.6
- pywin32 >= 305
- lxml >= 4.9.0
- faker >= 18.0.0
- pillow >= 10.0.0
- pystray >= 0.19.0
- pyinstaller >= 6.0.0 (build only)

#### Executable
- **Portable single-file executable**: 26 MB standalone .exe
- **No console window**: Clean GUI-only experience (console=False)
- **No installation required**: Run directly on any Windows 10/11 machine
- **All dependencies bundled**: Python interpreter and libraries included

#### State Management
- **Redux pattern**: Centralized store with actions and reducers
- **Immutable updates**: Pure reducer functions ensure predictable state changes
- **Type safety**: Dataclass-based state definitions with type hints
- **Subscription model**: UI components subscribe to state changes

### Breaking Changes
- **Statement charge initial status**: Now created as 'open' instead of 'completed'
- **Archive behavior**: Archive closed transactions no longer archives all statement charges by default
- **Import paths**: Code using internal modules will need to update imports to new package structure

---

## [v1.0.0] - 2025-11-04

### Initial Release

#### Core Features
- **Invoice creation and monitoring**: Batch create invoices with configurable parameters
- **Sales receipt support**: Create sales receipts with multiple line items
- **Statement charge support**: Create statement charges for customer accounts
- **Customer/job creation**: Generate test customers and jobs with Faker-generated data
- **Real-time transaction monitoring**: Background monitoring of transaction status changes
- **Payment verification system**: Verify payment posting, deposit accounts, and memos
- **QBXML-based QuickBooks integration**: Direct XML protocol communication (no QBFC)

#### UI Features
- **Three-tab interface**: Create Data, Monitor Invoices, Verification Results
- **Batch operations**: Create multiple transactions in single operation
- **Status tracking**: Visual indicators for transaction status (open/closed)
- **Treeview displays**: Sortable, filterable transaction lists

#### Technical Implementation
- **Background worker threads**: Non-blocking operations using daemon threads
- **Thread-safe UI updates**: Cross-thread communication via root.after()
- **State management**: Centralized Redux-like state container
- **Connection management**: Isolated QB connection in separate process
- **Error handling**: Comprehensive error reporting and logging

---

## Distribution

### Executable Download
The portable Windows executable (`QBDTestTool.exe`) is available in the `dist/` folder after building, or from the releases page.

**File Size**: 26 MB
**Platform**: Windows 10/11 (64-bit)
**Console**: Disabled (GUI-only)

### Building from Source
```bash
# Install dependencies
pip install -r requirements.txt

# Build executable (with console for debugging)
pyinstaller QBDTestTool.spec

# Build executable (GUI-only, no console)
# Edit QBDTestTool.spec: console=False
pyinstaller --clean QBDTestTool.spec
```

### Running from Source
```bash
# Ensure QuickBooks Desktop is running with company file open
python src/app.py
```

---

## Notes

### QuickBooks Requirements
- QuickBooks Desktop must be running
- Company file must be open
- Application requests access on first run (grant access in QuickBooks)
- Supports QB Pro, Premier, Enterprise editions

### Session Files
- Stored in `sessions/` directory
- JSON format (human-readable and editable)
- Contains transaction IDs, customer info, and monitoring state
- Auto-saved after transaction creation

### Verification Features
- Payment amount validation (full, partial, overpayment)
- Deposit account verification against expected account
- Transaction memo change detection
- Payment memo tracking and validation
- Linked transaction analysis (payment methods, dates, amounts)
- Cash/check payment detection with relaxed validation

### Performance
- Batch operations process multiple transactions with single QB connection
- Background monitoring doesn't block UI
- Efficient state updates using immutable patterns
- Minimal memory footprint with rolling log window

### Code Statistics (v1.1.0)
- **Total lines added**: 4,750+
- **Total lines removed**: 3,600+
- **app.py reduction**: 3,700 lines → 214 lines (94% reduction)
- **New modules created**: 44 files
- **Packages created**: 7 (actions, workers, ui, store, mock_generation, trayapp, qb)
