"""
QuickBooks Desktop connection manager using QBFC 13.0 (COM objects).

Replaces the QBXML-based connection with QBFC SessionManager.
"""

import win32com.client
from typing import Optional
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class QBFCConnectionError(Exception):
    """Exception raised for QBFC connection errors."""
    pass


def _parse_qbfc_error(error) -> str:
    """
    Parse QuickBooks QBFC error and return user-friendly message.

    Args:
        error: The exception object from COM

    Returns:
        User-friendly error message
    """
    error_str = str(error)

    # Check error codes using match with guards
    match error_str:
        case s if '-2147220472' in s or '0x80040408' in s:
            return (
                "QuickBooks Desktop is not running or no company file is open.\n\n"
                "Please:\n"
                "1. Start QuickBooks Desktop\n"
                "2. Open a company file\n"
                "3. Try again"
            )
        case s if '-2147220464' in s or '0x80040410' in s:
            return (
                "QuickBooks file mode mismatch.\n\n"
                "Please:\n"
                "1. Make sure QuickBooks Desktop is running\n"
                "2. Ensure a company file is open\n"
                "3. Try closing and reopening QuickBooks\n"
                "4. If the issue persists, check if another application is connected to QuickBooks"
            )
        case s if '-2147220445' in s or '0x80040423' in s:
            return (
                "QuickBooks Desktop is not set to allow access.\n\n"
                "Please:\n"
                "1. Open QuickBooks Desktop\n"
                "2. Go to Edit > Preferences > Integrated Applications\n"
                "3. Make sure this application is authorized"
            )
        case s if '-2147467259' in s or '0x80004005' in s:
            return (
                "QuickBooks access denied or file is locked.\n\n"
                "Please:\n"
                "1. Make sure QuickBooks Desktop is not in use by another application\n"
                "2. Close any other applications that might be accessing QuickBooks\n"
                "3. Try again"
            )
        case s if 'Could not start QuickBooks' in s:
            return (
                "Could not connect to QuickBooks Desktop.\n\n"
                "Please:\n"
                "1. Make sure QuickBooks Desktop is running\n"
                "2. Open a company file\n"
                "3. Grant permission when prompted"
            )
        case s if 'user cancelled' in s.lower():
            return "Connection cancelled by user."
        case _:
            return f"QuickBooks connection error:\n{error_str}"


class QBFCConnection:
    """
    Manages connections to QuickBooks Desktop using QBFC 13.0.

    Follows the pattern of opening/closing connections after each action or batch
    to allow other applications to connect to QuickBooks.
    """

    def __init__(self, app_name: str = "QBDTestTool", app_id: str = ""):
        """
        Initialize QBFC connection manager.

        Args:
            app_name: Application name for QB connection
            app_id: Application ID (optional, can be empty for testing)
        """
        self.app_name = app_name
        self.app_id = app_id
        self.session_manager = None
        self.connection_open = False
        self.session_open = False

    def connect(self, company_file: Optional[str] = None) -> bool:
        """
        Open connection to QuickBooks using QBFC.

        Args:
            company_file: Path to company file (None = currently open file)

        Returns:
            True if connected successfully

        Raises:
            QBFCConnectionError: If connection fails
        """
        # Try multiple QBFC versions (based on official SDK documentation)
        # Per Stack Overflow and SDK docs: Even when using QBFC13, older versions
        # (especially QBFC11) may be required for backward compatibility
        progids = [
            ("QBFC13.QBSessionManager", "QBFC 13.0"),
            ("QBFC12.QBSessionManager", "QBFC 12.0"),
            ("QBFC11.QBSessionManager", "QBFC 11.0"),
        ]

        last_error = None
        for progid, version_name in progids:
            try:
                # Attempt to create the QBFC SessionManager object
                logger.debug(f"Attempting to instantiate {version_name}...")
                self.session_manager = win32com.client.Dispatch(progid)
                logger.info(f"Successfully created {version_name} SessionManager")

                # Open connection to QuickBooks
                # Parameters: AppID, AppName, ConnectionType (1 = qbFileOpenLocalQBD)
                self.session_manager.OpenConnection2(self.app_id, self.app_name, 1)
                self.connection_open = True
                logger.info(f"QBFC connection opened: {self.app_name}")

                # Begin session
                # Parameters: CompanyFile (empty string = currently open), OpenMode
                # OpenMode constants from QBFC:
                #   0 = qbFileOpenDoNotCare (recommended - works with any mode)
                #   1 = qbFileOpenSingleUser
                #   2 = qbFileOpenMultiUser
                #   3 = qbFileOpenOnlineMode
                if company_file:
                    self.session_manager.BeginSession(company_file, 0)  # qbFileOpenDoNotCare
                else:
                    self.session_manager.BeginSession("", 0)  # qbFileOpenDoNotCare

                self.session_open = True
                logger.info(f"QBFC session started using {version_name}")
                return True

            except Exception as e:
                last_error = e
                # If this was a "Class not registered" or "Invalid class string" error, try next version
                error_str = str(e)
                if ('-2147221164' in error_str or '0x80040154' in error_str or 'Class not registered' in error_str or
                    '-2147221005' in error_str or '0x800401f3' in error_str or 'Invalid class string' in error_str):
                    logger.debug(f"{version_name} not available: {error_str}")
                    continue
                else:
                    # Different error (QB not running, etc.) - stop trying
                    logger.error(f"Failed to connect with {version_name}: {str(e)}")
                    friendly_message = _parse_qbfc_error(e)
                    raise QBFCConnectionError(friendly_message)

        # All QBFC versions failed - provide installation guidance
        logger.error("No QBFC version could be instantiated")
        raise QBFCConnectionError(
            "QBFC SDK not found or not properly installed.\n\n"
            "QuickBooks Foundation Classes (QBFC) is required but not registered.\n\n"
            "Solutions:\n"
            "1. Install QBFC SDK from QuickBooks SDK installer\n"
            "2. Run QBFC installer: C:\\Program Files (x86)\\Intuit\\QBSDK13\\Installers\\QBFC*Installer.exe\n"
            "3. Download SDK from: https://developer.intuit.com/\n"
            "4. Note: Installing QBFC 11.0 may be required even when using QB 2020+\n\n"
            f"Technical error: {str(last_error)}"
        )

    def disconnect(self) -> bool:
        """
        Close connection to QuickBooks.

        Returns:
            True if disconnected successfully
        """
        try:
            if self.session_manager and self.session_open:
                self.session_manager.EndSession()
                self.session_open = False
                logger.info("QBFC session ended")

            if self.session_manager and self.connection_open:
                self.session_manager.CloseConnection()
                self.connection_open = False
                logger.info("QBFC connection closed")

            self.session_manager = None
            return True

        except Exception as e:
            logger.error(f"Error during QBFC disconnect: {str(e)}")
            return False

    def get_session_manager(self):
        """
        Get the QBFC SessionManager object for operations.

        Returns:
            QBFC SessionManager COM object

        Raises:
            QBFCConnectionError: If not connected
        """
        if not self.session_manager or not self.session_open:
            raise QBFCConnectionError("Not connected to QuickBooks. Call connect() first.")

        return self.session_manager

    def __enter__(self):
        """Context manager support for batch operations."""
        self.connect()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager cleanup."""
        self.disconnect()
        return False
