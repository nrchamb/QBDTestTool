"""
QBFC Installation Diagnostic Utility.

Helps users identify which QBFC versions are installed and registered.
"""

import winreg
import win32com.client
from typing import List, Tuple, Dict


def check_qbfc_registry() -> List[int]:
    """
    Check which QBFC versions are registered in Windows registry.

    Returns:
        List of QBFC version numbers found (e.g., [11, 12, 13])
    """
    versions = []

    # Check common QBFC versions
    for ver in range(1, 17):  # Check QBFC 1.0 through 16.0
        try:
            with winreg.OpenKey(winreg.HKEY_CLASSES_ROOT, f"QBFC{ver}.QBSessionManager") as key:
                # If key exists, this version is registered
                versions.append(ver)
        except FileNotFoundError:
            pass  # Version not installed
        except Exception:
            pass  # Other registry errors

    return versions


def test_qbfc_instantiation() -> List[Tuple[int, bool, str]]:
    """
    Attempt to instantiate each QBFC version to verify it works.

    Returns:
        List of tuples: (version, success, error_message)
    """
    results = []

    for ver in range(1, 17):
        progid = f"QBFC{ver}.QBSessionManager"
        try:
            # Try to create the COM object
            session_manager = win32com.client.Dispatch(progid)
            results.append((ver, True, "OK"))
            # Clean up
            del session_manager
        except Exception as e:
            error_msg = str(e)
            # Extract just the error type
            if ('Class not registered' in error_msg or '-2147221164' in error_msg or
                'Invalid class string' in error_msg or '-2147221005' in error_msg):
                results.append((ver, False, "Not registered"))
            else:
                results.append((ver, False, f"Error: {error_msg[:50]}"))

    return results


def diagnose_qbfc_installation() -> Dict[str, any]:
    """
    Complete diagnostic of QBFC installation.

    Returns:
        Dictionary with diagnostic results
    """
    print("=" * 60)
    print("QBFC Installation Diagnostic")
    print("=" * 60)
    print()

    # Check registry
    print("Checking Windows Registry...")
    registry_versions = check_qbfc_registry()

    if registry_versions:
        print(f"✓ Found {len(registry_versions)} QBFC version(s) in registry:")
        for ver in registry_versions:
            print(f"  - QBFC {ver}.0")
    else:
        print("✗ No QBFC versions found in registry")
    print()

    # Test instantiation
    print("Testing COM Instantiation...")
    test_results = test_qbfc_instantiation()
    working_versions = [ver for ver, success, _ in test_results if success]

    if working_versions:
        print(f"✓ {len(working_versions)} QBFC version(s) can be instantiated:")
        for ver in working_versions:
            print(f"  - QBFC {ver}.0: Working")
    else:
        print("✗ No QBFC versions can be instantiated")
        print("\nVersions checked:")
        for ver, success, msg in test_results:
            if not success and msg != "Not registered":
                print(f"  - QBFC {ver}.0: {msg}")
    print()

    # Summary and recommendations
    print("=" * 60)
    print("Summary")
    print("=" * 60)

    if working_versions:
        print(f"✓ QBFC is properly installed")
        print(f"  Available versions: {', '.join([str(v) + '.0' for v in working_versions])}")
        print(f"  Recommended: Use QBFC {max(working_versions)}.0 (highest available)")
    else:
        print("✗ QBFC is NOT properly installed")
        print()
        print("Solutions:")
        print("1. Install QuickBooks SDK from Intuit Developer Portal")
        print("   Download: https://developer.intuit.com/")
        print()
        print("2. Run QBFC installer from SDK:")
        print("   C:\\Program Files (x86)\\Intuit\\QBSDK13\\Installers\\QBFC*Installer.exe")
        print()
        print("3. If using QuickBooks 2020+, install QBFC 11.0, 12.0, AND 13.0")
        print("   (Multiple versions may be required for backward compatibility)")
        print()
        print("4. Ensure QuickBooks Desktop is installed on this machine")

    print()

    return {
        'registry_versions': registry_versions,
        'working_versions': working_versions,
        'test_results': test_results,
    }


if __name__ == "__main__":
    # Run diagnostic when executed directly
    diagnose_qbfc_installation()
