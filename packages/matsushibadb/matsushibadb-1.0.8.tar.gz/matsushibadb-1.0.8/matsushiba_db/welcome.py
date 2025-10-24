#!/usr/bin/env python3
"""
MatsushibaDB Welcome Module
Shows welcome message and checks for updates
"""

import json
import urllib.request
import urllib.error
import sys
from pathlib import Path


def show_welcome():
    """Display welcome message."""
    print('\n' + '🎉' * 25)
    print('🎉 Welcome to MatsushibaDB!')
    print('\n🚀 Next-Generation SQL Database by Matsushiba Systems')
    print('🔧 Inbuilt SQL Standalone - No External Dependencies!')
    
    print('\n📖 Quick Start:')
    print('  matsushiba-db server    # Start server')
    print('  matsushiba-db help       # Show help')
    print('  matsushiba-db init       # Initialize project')
    print('  matsushiba-db welcome    # Show this message')
    
    print('\n🌐 Documentation: https://db.matsushiba.co')
    print('🆘 Support: https://db.matsushiba.co/support')
    
    print('\n✨ Thank you for choosing MatsushibaDB!')
    print('🎉' * 25 + '\n')


def check_for_updates():
    """Check for package updates."""
    try:
        # Get current version
        package_path = Path(__file__).parent.parent / 'package.json'
        if package_path.exists():
            with open(package_path, 'r') as f:
                package_data = json.load(f)
                current_version = package_data.get('version', '1.0.8')
        else:
            current_version = '1.0.8'
        
        print('🔍 Checking for updates...')
        
        # Check PyPI for latest version
        try:
            url = 'https://pypi.org/pypi/matsushibadb/json'
            with urllib.request.urlopen(url) as response:
                data = json.loads(response.read())
                latest_version = data['info']['version']
                
                if compare_versions(latest_version, current_version) > 0:
                    print('\n🔄 Update available!')
                    print(f'   Current: {current_version}')
                    print(f'   Latest:  {latest_version}')
                    print('   Run: pip install --upgrade matsushibadb\n')
                else:
                    print('✅ You have the latest version!\n')
        except (urllib.error.URLError, KeyError, json.JSONDecodeError):
            print('ℹ️  Could not check for updates\n')
            
    except Exception:
        print('ℹ️  Could not check for updates\n')


def compare_versions(a, b):
    """Compare version strings."""
    a_parts = [int(x) for x in a.split('.')]
    b_parts = [int(x) for x in b.split('.')]
    
    for i in range(max(len(a_parts), len(b_parts))):
        a_part = a_parts[i] if i < len(a_parts) else 0
        b_part = b_parts[i] if i < len(b_parts) else 0
        
        if a_part > b_part:
            return 1
        elif a_part < b_part:
            return -1
    
    return 0


def show_tips():
    """Show pro tips."""
    print('💡 Pro Tips:')
    print('  • Use --enable-audit for audit logging')
    print('  • Use --enable-encryption for file encryption')
    print('  • Use --enable-rbac for role-based access control')
    print('  • Use --ssl-cert and --ssl-key for HTTPS')
    print('')


def main():
    """Main function."""
    show_welcome()
    check_for_updates()
    show_tips()


if __name__ == '__main__':
    main()
