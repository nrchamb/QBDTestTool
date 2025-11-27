 A testing utility for QuickBooks Desktop integrations. This is an internal tool, not meant for end users.
## Availability

QBDTestTool is available to run in three formats.
- ****Source Code****
  This tool can be run from the Python source code via the `run.bat` file located in the root folder. This may not be available in closed or restricted environments, as it requires Python to be present on the system.
- ****Executable****
  This tool is packaged as a portable executable, packaging all dependencies to make immediate execution and use possible.
- ****Executable-Debug****
  By default, the executable tool suppresses the CMD window that would otherwise run in the background. The debug executable enables this CMD window for more information.
## Configuration

On first launch, QBDTestTool will create a configuration folder for persistence settings in `C:\Users\%USER%\Documents\.qbdtesttool\`.

A background process, "QBTestTool" can be found in the system tray. This process monitors the status of the main tool to prevent crashes or unexpected disconnections from locking the QuickBooks connection and to ensure only one QBDTestTool process runs at a time.
## Getting Started

QBDTestTool's interface will load regardless of QuickBooks' status. Upon initialization, no information is loaded from QuickBooks. To load information, you must click either the individual load buttons or the ****Load All**** button located further down.

<img width="633" height="588" alt="Screenshot 2025-11-27 at 11 44 05 AM" src="https://github.com/user-attachments/assets/3e5e8fee-d0dd-4b30-99c4-3fe6987bcc1c" />

### Data Types

- Customers
- Items (Inventory)
- Terms
- Classes
- Accounts
### Required Data

In order to create mock transactions, you need to load two items:
- ****Customers**** - Ensures the transaction has a link back to QuickBooks
- ****Items**** - Ensures the transaction creation can populate the line-items
### Optional Data

Optionally, you can load additional information from QuickBooks using the remaining buttons:
- ****Terms****: Allows you to set payment Terms for the transaction.
- ****Classes****: Allows you to set a Class for the transaction.
- ****Accounts****: Allows you to select specific accounts to validate payment post-back.
---
## Customer Creation

****Required:**** Email Address
- This information *_can_* be nonsense. However, the requirement is to ensure email testing is available without additional steps.

No other information is required. QBDTestTool utilizes [Faker](https://faker.readthedocs.io/en/master) to generate realistic mock information.

If you prefer to control what information is within the generation, simply uncheck the Random box and enter information into on the right.

<img width="525" height="545" alt="Screenshot 2025-11-27 at 12 37 08 PM" src="https://github.com/user-attachments/assets/a0b17bea-7eaf-4c86-b29b-4cf8a86cbcaa" />

### Individual Input

- First Name
- Last Name
- Company Name
- Phone Number

### Group Input

- Billing Address
- Shipping Address
 

Individual Input fields allow you to modify individual fields.

Group Input operates as an all-or-nothing generation. If you decide to control Billing Address and Shipping address manually, entering no information into the fields will submit a null value to QuickBooks.

### Jobs & Sub-Jobs

- ***Jobs***: Allows you to control the number of jobs to attach to the parent customer during creation.
- ***Sub-Jobs per Job***: Allows you to attach Jobs to the created Jobs for nested Customer:Job inheritance.  

When creating customers with jobs and sub-jobs, a single connection is established with QuickBooks and remains open until the batch of Customer:Job:Sub-Job completes.

---
## Transaction Creation

QBDTestTool supports three transaction types:
- Invoices
- Sales Receipts
- Statement Charges

| Supported Field             |      Invoices       |   Sales Receipts    |  Statement Charges  |
| --------------------------- | :-----------------: | :-----------------: | :-----------------: |
| Number of Records to Create |    ☑ Default: 1     |    ☑ Default: 1     |    ☑ Default: 1     |
| Line Item Range             |  ☑ Default: 1 — 3   |  ☑ Default: 1 — 3   |  ☑ Default: 1 — 3   |
| Amount Range                | ☑ Default: 25 — 500 | ☑ Default: 25 — 500 | ☑ Default: 25 — 500 |
| Transaction Date Range      |  ☑ Default: Today   |  ☑ Default: Today   |  ☑ Default: Today   |
| PO Number Prefix            |  ☑ Default: 'PO-'   |         𝗑          |         𝗑          |
| Terms (Optional)            |          ☑          |         𝗑          |         𝗑          |
| Class (Optiona)             |          ☑          |          ☑          |          ☑          |

Transaction generation requires Customer and Items to be loaded from QuickBooks before the generation is possible. To load this data, visit the Setup page and select the individual data items or click ****Load All**** to load all available data types. In order to select Terms or Class as part of the transaction generation, the optional data must first be loaded.

<img width="527" height="551" alt="Screenshot 2025-11-27 at 12 37 50 PM" src="https://github.com/user-attachments/assets/7ae300ae-e23a-403f-bfd1-4f1180b49fc5" />

### Transaction Fields

- ***Select Customer***:
  The customer you wish for the transactions to be attached. You can only create records for one customer at a time. In order to create transactions for multiple customers, please run multiple batches.The drop-down box serves as a search-bar for quick access. If you have a particular customer you wish to use for testing, click into the dropdown box and begin typing. The options will automatically filter until you select one.
- - ***Number of [Transaction Type]***:
  The number of transactions that will be created as a batch.
- ***Line Item Range***:
  The number of line items to add to the transaction.
- ***Amount Range***:
  The balance range that the tool will generate. When creating a transaction, the tool will add the number of set items in the Line Items Range and make sure the total value remains within the set Amount Range (pre-tax).
- **Transaction Date Range***:
  Time frame for which the generated transactions will randomly populate. Create invoices randomly in up to a 30-day date range.
- ***PO Number Prefix***:
  The prefix added to the Invoice's PO number.
- ***Terms*** (optional):
  Payment Terms - Can be inherited from Customer, but can otherwise be manually set via the dropdown.
- ****Class**** (optional):
  Set a transaction Class for organization. Classes are pulled directly from QuickBooks.

When creating transactions, a single connection is established with QuickBooks and remains open until the batch of transactions are created.

---
## Monitor Transactions

QBDTestTool's Monitoring provides immediate feedback for checking the state of your created transactions. This tool will ****only**** monitor transactions that are in the active session.

After creating transactions via the ****Create**** tab, you can switch to ****Monitor Transactions**** to start the monitoring process. When monitoring is active, it will periodically (user defined interval) check each transaction for status changes. When the status of a transaction changes, the list will update the transaction's status and the result will be active and available in the ****Verification Results**** page.

<img width="604" height="655" alt="Screenshot 2025-11-27 at 11 49 12 AM" src="https://github.com/user-attachments/assets/154674d8-566b-4bf4-b2ca-9d9d36e8e913" />

### Controls

- ***Start Monitoring***
- ***Stop Monitoring***
- ***Check Interval (Seconds)***
  The time interval at which the tool will query QuickBooks for each transaction's status.
  This is set to 30 seconds by default. If you only have a few transactions, reducing the number ****before**** you start the monitoring will allow for quicker updates when you make an adjustment. As you create and monitor more transactions, it is recommended to increase the interval.
- ***Expected Deposit Account → Set***
  When monitoring transactions, the Verification Results will check that the payment record was posted back to the selected account and display the resulting Pass/Fail response.
- ***Memo Change Detection***:
  You can monitor the memo state for changes to see that the initial state has been updated during the monitoring session.
  You can choose two locations to monitor:
    - Payment Record
    - Transaction
### Transaction Table

| Column       | Description                                                                                 |
| ------------ | ------------------------------------------------------------------------------------------- |
| Type         | Invoice, Sales Receipt, Statement Charge                                                    |
| Ref #        | The Resulting Reference Number after payment                                                |
| Customer     | Customer:Job formatted as {Full Name}:{Name} to ensure both Customer and Job are presented. |
| Amount       | Transaction Amount (shows remaining balance for partial payments)                           |
| Status       | OPEN, PARTIAL, or CLOSED                                                                    |
| Last Checked | Timestamp of last batch check interval (Per session, does not persist after close)          |

### Status Color Coding

Transaction rows are color-coded by status for quick visual identification:
  

| Color  | Status  | Meaning                                  |
| ------ | ------- | ---------------------------------------- |
| Yellow | OPEN    | Transaction has not received any payment |
| Blue   | PARTIAL | Transaction has received partial payment |
| Green  | Closed  | Transaction is fully paid                |

When monitoring transactions, a single connection is established with QuickBooks per query operation and will open a connection for every monitored transaction. Since monitoring is inherently a background task, the intended goal is to allow updates without a long, blocking loop.

---
## Validation Results

Validation Results will display the results of tested parameters for monitored transactions upon change. When a payment is made against a monitored invoice, Validation Results will check for the following information:

- ***Payment Transactions***: Payment Total should be equal to Transaction Total
  Partial Payments will test as PASS, displaying the partial amount paid and remaining balance (e.g., "Partial: $50.00 of $100.00, Balance: $50.00")
- ***Transaction Memo***: Memo posted back to the transaction itself
- ***Payment** # Memo***: Memo posted back to the Payment Record**
- ***Memo Match***: If both Payment Record and Transaction memos are checked, this will compare the appended/changed string as another validation layer
- ***Deposit Account***: Compares against the selected deposit account

<img width="607" height="657" alt="Screenshot 2025-11-27 at 11 50 00 AM" src="https://github.com/user-attachments/assets/1d0401e2-7a14-4820-bbad-fd8be7e2d975" />

### Result Color Coding

Validation results are color-coded for quick assessment:

| Color      | Result  | Meaning                             |
| ---------- | ------- | ----------------------------------- |
| Green      | PASS    | Validation check passed             |
| Red        | FAIL    | Validation check failed             |
| Yellow     | WARN    | Warning - Check passed with caveats |
| Light Blue | INFO    | Informational Result                |
| Grey       | SKIPPED | Check was not applicable or skipped |

---
 
## DEV Payment Testing

QBDTestTool includes developer payment buttons for testing payment workflows without manually creating payments in QuickBooks. These buttons are available in the ****Monitor Transactions**** tab.
### Payment Buttons

- ***Pay Full***: Creates a full payment for the selected transaction(s)
- ***Pay Partial***: Creates a partial payment (50% of balance) for the selected transaction(s)
### Payment Options

- ***Post to Transaction***: Updates the memo field on the original transaction
- ***Post to Payment***: Sets the memo field on the payment record itself

### Transaction Type Behavior
  

| Transaction Type  | Payment Action                | Memo Behaviour                                |
| ----------------- | ----------------------------- | --------------------------------------------- |
| Invoice           | Creates ReceivePayment Record | Can post memo to both transaction and payment |
| Statement Charges | Creates ReceivePayment Record | Payment memo only                             |
| Sales Receipts    | Updates existing record       | Sets memo and Payment method (Visa)           |
  
> ****Note:**** You must select specific transactions before clicking payment buttons. If no transactions are selected, the tool will display a warning. Multi-select is supported.
---
## Running from Source

If you're modifying the tool:

***Requirements:***
- Python 3.11 or higher (****32-bit version required**** - QBFC uses 32-bit COM)
- Windows (required for COM access to QuickBooks)
- ***QBFC 13.0*** (QuickBooks Foundation Classes) - See installation instructions below
> ****Important:**** You must use 32-bit Python. The QBFC SDK registers 32-bit COM components, and 64-bit Python cannot load them. Download the "Windows installer (32-bit)" from python.org.

***Install Python dependencies:***

```bash
pip install pywin32 faker pillow pystray
```


***Install QBFC 13.0:***
 

The tool requires QBFC (QuickBooks Foundation Classes) to be installed and registered on your system.


1. ***Download Intuit's QBFC*** from Intuit Developer Portal:
   - Visit: https://developer.intuit.com/app/developer/qbdesktop/docs/get-started/older-versions-of-the-desktop-sdk
   - Select QBFC13_Installer

***Note:*** You may be prompted to login or create an Intuit Developer account.

2. ****Run QBFC Installer:****

3. ***Verify Installation:***
      ```bash
   python src/qb/qbfc_diagnostic.py
   ```
    
 This diagnostic tool will show which QBFC versions are installed and working.
 
3. ***Run:***
```bash
# Windows (recommended)
run.bat
  
# Or directly with Python
python src/app.py
```
  
QuickBooks needs to be running first, or you'll get COM errors.

  ****Troubleshooting QBFC Installation:****
  
If you see a "Class not registered" error:
1. Run the QBFC diagnostic: `python src/qb/qbfc_diagnostic.py`
2. Install missing QBFC versions as indicated
3. Ensure QuickBooks Desktop is installed (QBFC requires it)
4. Run installers as Administrator if needed
---
## Building the Executable

If you need to build a new exe:

```bash
pip install pyinstaller
pyinstaller --clean QBDTestTool.spec
```

The spec file is already configured. Output goes to `dist/QBDTestTool.exe`.

****Build Options:****
- ****GUI-only (default)****: `console=False` in spec file - no console window appears
- ****With console (debugging)****: Change to `console=True` - shows console for error messages

After building, the executable runs standalone on any Windows 10/11 machine without Python installed.

---

## Troubleshooting
### "QuickBooks is not running" error

QuickBooks needs to be running ****and**** have a company file open before you start the tool. If you launch the tool first, it won't work.

  Fix: Start QuickBooks, open a company file, then run the tool.

### "Access denied" or "Application not authorized"

First time you run this, QuickBooks will ask if you want to allow access. You need to click "Yes, always allow" or it won't work.

If you accidentally clicked "No", you'll need to go into QuickBooks' integrated applications preferences and authorize it manually.

---
## Project Structure

```
src/
├── app.py                      - Main GUI orchestrator
├── actions/                    - Action handlers
│   ├── customer_actions.py     - Customer CRUD operations
│   ├── transaction_actions.py  - Unified transaction creation
│   ├── payment_actions.py      - DEV payment testing
│   ├── monitor_actions.py      - Transaction monitoring actions
│   └── monitor_search_actions.py - Advanced search
├── workers/                    - Background threading workers
│   ├── customer_worker.py      - Customer/job batch creation
│   ├── invoice_worker.py       - Invoice batch creation
│   ├── sales_receipt_worker.py - Sales receipt batch creation
│   ├── charge_worker.py        - Statement charge batch creation
│   ├── monitor_worker.py       - Transaction state monitoring
│   ├── cleanup_worker.py       - Archive/delete operations
│   └── data_loader_worker.py   - QB data loading
├── ui/                         - UI component setup
│   ├── create_tab_setup.py     - Create Data tab with subtabs
│   ├── monitor_tab_setup.py    - Monitor tab interface
│   ├── verify_tab_setup.py     - Verification results display
│   ├── settings_tab_setup.py   - Settings and configuration
│   ├── setup_subtab_setup.py   - Data loading subtab
│   ├── customer_subtab_setup.py - Customer creation form
│   └── transaction_subtab_setup.py - Transaction creation form
├── store/                      - Redux-like state management
│   ├── store.py                - Store class (subscribe/dispatch)
│   ├── state.py                - AppState dataclass definitions
│   ├── actions.py              - Action type constants
│   └── reducers.py             - Pure reducer functions
├── qb/                         - QuickBooks QBFC integration
│   ├── qbfc_connection.py      - QBFC COM wrapper
│   ├── qbfc_operations.py      - QBFC request builders
│   ├── qbfc_response_mapper.py - Map QBFC responses to dicts
│   ├── connection_manager.py   - Separate process manager
│   ├── ipc_client.py           - IPC client for manager
│   └── data_loader.py          - Load customers/items/accounts
├── mock_generation/            - Test data generators
│   ├── customer_generator.py   - Random customer data (Faker)
│   ├── invoice_generator.py    - Invoice with line items
│   ├── sales_receipt_generator.py - Sales receipt data
│   └── charge_generator.py     - Statement charge data
├── trayapp/                    - System tray integration
│   ├── tray_icon.py            - Tray icon implementation
│   └── daemon_actions.py       - Daemon mode actions
├── persistence/                - Session save/load
│   ├── session_manager.py      - JSON session persistence
│   └── change_detector.py      - Detect external QB changes
├── config/                     - Application configuration
│   └── app_config.py           - Config file management
└── app_logging/                - Logging configuration
    └── logging_config.py       - Log level control
```

---
## Dependencies

***Core:***
- `pywin32` - COM access to QuickBooks via QBFC
- `tkinter` - GUI (ships with Python)
  
***Extras:***
- `faker` - Generate random customer names/addresses
- `pillow` - Tray icon graphics
- `pystray` - System tray integration
