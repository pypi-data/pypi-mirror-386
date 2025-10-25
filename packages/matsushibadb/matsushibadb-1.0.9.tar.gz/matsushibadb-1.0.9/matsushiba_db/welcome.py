#!/usr/bin/env python3
"""
MatsushibaDB Python - Welcome System
Shows welcome message and checks for updates
"""

import sys
import os
import json
import urllib.request
import urllib.error
from packaging import version


def show_welcome():
    """Show welcome message"""
    print('\n' + '=' * 50)
    print('Welcome to MatsushibaDB!')
    print('\nNext-Generation SQL Database by Matsushiba Systems')
    print('Inbuilt SQL Standalone - No External Dependencies!')
    
    print('\nQuick Start:')
    print('  matsushiba-server          # Start server')
    print('  matsushiba-db --help       # Show help')
    print('  matsushiba-welcome         # Show this message')
    
    print('\nDocumentation: https://db.matsushiba.co')
    print('Support: https://db.matsushiba.co/support')
    
    print('\nThank you for choosing MatsushibaDB!')
    print('=' * 50 + '\n')


def check_for_updates():
    """Check for updates from PyPI"""
    try:
        print('Checking for updates...')
        
        # Get current version
        current_version = get_current_version()
        
        # Get latest version from PyPI
        latest_version = get_latest_version()
        
        if latest_version and version.parse(latest_version) > version.parse(current_version):
            print('\nUpdate available!')
            print(f'   Current: {current_version}')
            print(f'   Latest:  {latest_version}')
            print('   Run: pip install --upgrade matsushibadb\n')
        else:
            print('You have the latest version!\n')
            
    except Exception as e:
        print('Could not check for updates\n')


def get_current_version():
    """Get current package version"""
    try:
        import matsushibadb
        return matsushibadb.__version__
    except ImportError:
        return "1.0.9"  # Fallback


def get_latest_version():
    """Get latest version from PyPI"""
    try:
        url = 'https://pypi.org/pypi/matsushibadb/json'
        with urllib.request.urlopen(url, timeout=5) as response:
            data = json.loads(response.read().decode())
            return data['info']['version']
    except (urllib.error.URLError, json.JSONDecodeError, KeyError):
        return None


def show_tips():
    """Show pro tips"""
    print('Pro Tips:')
    print('  • Use --enable-audit for audit logging')
    print('  • Use --enable-encryption for file encryption')
    print('  • Use --enable-rbac for role-based access control')
    print('  • Use --ssl-cert and --ssl-key for HTTPS')
    print('')


def main():
    """Main welcome function"""
    show_welcome()
    check_for_updates()
    show_tips()


if __name__ == "__main__":
    main()