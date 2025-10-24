#!/usr/bin/env python3
"""
MatsushibaDB Project Initializer
Creates new projects with templates
"""

import os
import json
import argparse
from pathlib import Path


# Project templates
TEMPLATES = {
    'basic': {
        'name': 'Basic Project',
        'description': 'Simple MatsushibaDB project with basic configuration'
    },
    'api': {
        'name': 'API Project',
        'description': 'REST API project with MatsushibaDB backend'
    },
    'webapp': {
        'name': 'Web Application',
        'description': 'Full-stack web application with MatsushibaDB'
    },
    'microservice': {
        'name': 'Microservice',
        'description': 'Microservice architecture with MatsushibaDB'
    }
}


def create_main_file(template):
    """Create main application file based on template."""
    templates = {
        'basic': '''#!/usr/bin/env python3
"""
MatsushibaDB Basic Project
"""

from matsushiba_db import MatsushibaDBServer
import asyncio

async def main():
    # Start MatsushibaDB server
    server = MatsushibaDBServer(
        host='localhost',
        port=8000,
        database='app.db',
        enable_audit_log=True,
        enable_encryption=True,
        enable_rbac=True
    )
    
    print('🚀 Starting MatsushibaDB server...')
    await server.start()

if __name__ == '__main__':
    asyncio.run(main())
''',

        'api': '''#!/usr/bin/env python3
"""
MatsushibaDB API Project
"""

from flask import Flask, request, jsonify
from matsushiba_db import MatsushibaDBClient
import asyncio

app = Flask(__name__)
db = MatsushibaDBClient('http://localhost:8000')

@app.route('/api/users', methods=['GET'])
async def get_users():
    try:
        result = await db.query('SELECT * FROM users')
        return jsonify(result)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/users', methods=['POST'])
async def create_user():
    try:
        data = request.get_json()
        name = data.get('name')
        email = data.get('email')
        
        result = await db.execute(
            'INSERT INTO users (name, email) VALUES (?, ?)',
            [name, email]
        )
        return jsonify({'id': result['lastID'], 'name': name, 'email': email})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    print('🚀 API server starting...')
    print('📊 Make sure MatsushibaDB server is running on port 8000')
    app.run(host='0.0.0.0', port=3000, debug=True)
''',

        'webapp': '''#!/usr/bin/env python3
"""
MatsushibaDB Web Application
"""

from flask import Flask, request, jsonify, render_template_string
from matsushiba_db import MatsushibaDBClient
import asyncio

app = Flask(__name__)
db = MatsushibaDBClient('http://localhost:8000')

# HTML template
HTML_TEMPLATE = '''
<!DOCTYPE html>
<html>
<head>
    <title>MatsushibaDB Web App</title>
    <style>
        body { font-family: Arial, sans-serif; margin: 40px; }
        .container { max-width: 800px; margin: 0 auto; }
        .form-group { margin: 20px 0; }
        input, textarea { width: 100%; padding: 8px; margin-bottom: 10px; }
        button { background: #007bff; color: white; padding: 10px 20px; border: none; cursor: pointer; }
        .data-item { border: 1px solid #ddd; padding: 15px; margin: 10px 0; }
    </style>
</head>
<body>
    <div class="container">
        <h1>🚀 MatsushibaDB Web App</h1>
        
        <h2>Add Data</h2>
        <form id="dataForm">
            <div class="form-group">
                <label>Title:</label>
                <input type="text" id="title" required>
            </div>
            <div class="form-group">
                <label>Content:</label>
                <textarea id="content" rows="4" required></textarea>
            </div>
            <button type="submit">Add Data</button>
        </form>
        
        <h2>Data List</h2>
        <div id="dataList"></div>
    </div>
    
    <script>
        document.getElementById('dataForm').addEventListener('submit', async (e) => {
            e.preventDefault();
            const data = {
                title: document.getElementById('title').value,
                content: document.getElementById('content').value
            };
            
            try {
                const response = await fetch('/api/data', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify(data)
                });
                
                if (response.ok) {
                    document.getElementById('dataForm').reset();
                    loadData();
                }
            } catch (error) {
                console.error('Error:', error);
            }
        });
        
        async function loadData() {
            try {
                const response = await fetch('/api/data');
                const data = await response.json();
                
                const dataList = document.getElementById('dataList');
                dataList.innerHTML = data.map(item => 
                    `<div class="data-item">
                        <h3>${item.title}</h3>
                        <p>${item.content}</p>
                    </div>`
                ).join('');
            } catch (error) {
                console.error('Error loading data:', error);
            }
        }
        
        loadData();
    </script>
</body>
</html>
'''

@app.route('/')
def index():
    return render_template_string(HTML_TEMPLATE)

@app.route('/api/data', methods=['GET'])
async def get_data():
    try:
        result = await db.query('SELECT * FROM data')
        return jsonify(result)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/data', methods=['POST'])
async def create_data():
    try:
        data = request.get_json()
        title = data.get('title')
        content = data.get('content')
        
        result = await db.execute(
            'INSERT INTO data (title, content) VALUES (?, ?)',
            [title, content]
        )
        return jsonify({'id': result['lastID'], 'title': title, 'content': content})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    print('🌐 Web app starting...')
    print('📊 Make sure MatsushibaDB server is running on port 8000')
    app.run(host='0.0.0.0', port=3000, debug=True)
''',

        'microservice': '''#!/usr/bin/env python3
"""
MatsushibaDB Microservice
"""

from flask import Flask, jsonify
from matsushiba_db import MatsushibaDBClient
import os

app = Flask(__name__)
service_name = os.getenv('SERVICE_NAME', 'matsushiba-service')
db = MatsushibaDBClient('http://localhost:8000')

@app.route('/health')
def health():
    return jsonify({
        'service': service_name,
        'status': 'healthy',
        'timestamp': '2024-01-01T00:00:00Z'
    })

@app.route('/api/service/data')
async def get_service_data():
    try:
        result = await db.query('SELECT * FROM service_data')
        return jsonify(result)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    port = int(os.getenv('PORT', 3000))
    print(f'🔧 {service_name} starting on port {port}...')
    print('📊 Make sure MatsushibaDB server is running on port 8000')
    app.run(host='0.0.0.0', port=port)
'''
    }
    
    return templates.get(template, templates['basic'])


def create_requirements_file(template):
    """Create requirements.txt file."""
    base_requirements = [
        'matsushibadb>=1.0.8',
        'flask>=2.3.0'
    ]
    
    if template == 'api':
        base_requirements.extend([
            'flask-cors>=4.0.0',
            'flask-limiter>=3.0.0'
        ])
    elif template == 'webapp':
        base_requirements.extend([
            'flask-cors>=4.0.0',
            'flask-limiter>=3.0.0'
        ])
    elif template == 'microservice':
        base_requirements.extend([
            'flask-cors>=4.0.0',
            'gunicorn>=21.0.0'
        ])
    
    return '\n'.join(base_requirements)


def create_readme(project_name, template):
    """Create README.md file."""
    return f'''# {project_name}

{TEMPLATES[template]['description']}

## 🚀 Quick Start

1. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

2. **Start MatsushibaDB server:**
   ```bash
   matsushiba-db server
   ```

3. **Start your application:**
   ```bash
   python main.py
   ```

## 📖 Documentation

- [MatsushibaDB Documentation](https://db.matsushiba.co)
- [API Reference](https://db.matsushiba.co/docs)
- [Examples](https://db.matsushiba.co/examples)

## 🆘 Support

- [GitHub Issues](https://github.com/matsushibaco/matsushibadb/issues)
- [Email Support](mailto:support@matsushiba.co)
- [Community](https://db.matsushiba.co/support)

## 📄 License

This project is licensed under the MIT License.

---

**MatsushibaDB** - Next-Generation SQL Database by Matsushiba Systems
'''


def create_gitignore():
    """Create .gitignore file."""
    return '''# Python
__pycache__/
*.py[cod]
*$py.class
*.so
.Python
build/
develop-eggs/
dist/
downloads/
eggs/
.eggs/
lib/
lib64/
parts/
sdist/
var/
wheels/
*.egg-info/
.installed.cfg
*.egg

# Database files
*.db
*.sqlite
*.sqlite3

# Environment variables
.env
.env.local
.env.development.local
.env.test.local
.env.production.local

# IDE
.vscode/
.idea/
*.swp
*.swo

# OS
.DS_Store
Thumbs.db

# Logs
*.log
logs/
'''


def init_project(project_name, template='basic'):
    """Initialize a new MatsushibaDB project."""
    print('🚀 Initializing MatsushibaDB project...\n')
    
    project_dir = Path(project_name or 'matsushiba-project')
    
    # Check if directory exists
    if project_dir.exists():
        print(f'❌ Directory \'{project_name}\' already exists!')
        print('Please choose a different name or remove the existing directory.\n')
        return
    
    try:
        # Create project directory
        project_dir.mkdir(parents=True, exist_ok=True)
        print(f'📁 Created project directory: {project_name}')
        
        # Create main.py
        main_content = create_main_file(template)
        (project_dir / 'main.py').write_text(main_content)
        print('📄 Created main.py')
        
        # Create requirements.txt
        requirements_content = create_requirements_file(template)
        (project_dir / 'requirements.txt').write_text(requirements_content)
        print('📦 Created requirements.txt')
        
        # Create README.md
        readme_content = create_readme(project_name or 'matsushiba-project', template)
        (project_dir / 'README.md').write_text(readme_content)
        print('📖 Created README.md')
        
        # Create .gitignore
        gitignore_content = create_gitignore()
        (project_dir / '.gitignore').write_text(gitignore_content)
        print('🔒 Created .gitignore')
        
        # Create config.py
        config_content = '''# MatsushibaDB Configuration
HOST = 'localhost'
PORT = 8000
DATABASE = 'app.db'

# Security Settings
ENABLE_AUDIT_LOG = True
ENABLE_ENCRYPTION = True
ENABLE_RBAC = True
ENABLE_RATE_LIMIT = True

# Performance Settings
MAX_CONNECTIONS = 100
CONNECTION_POOL_SIZE = 20

# JWT Settings
JWT_SECRET = 'your-secret-key'

# Encryption Key
ENCRYPTION_KEY = 'your-encryption-key'
'''
        (project_dir / 'config.py').write_text(config_content)
        print('⚙️  Created config.py')
        
        print('\n✅ Project initialized successfully!')
        print('\n📋 Next steps:')
        print(f'   cd {project_name}')
        print('   pip install -r requirements.txt')
        print('   matsushiba-db server  # In another terminal')
        print('   python main.py')
        print('\n🌐 Documentation: https://db.matsushiba.co')
        print('🆘 Support: https://db.matsushiba.co/support\n')
        
    except Exception as e:
        print(f'❌ Error initializing project: {e}')
        return


def show_templates():
    """Show available templates."""
    print('📋 Available project templates:\n')
    for key, template in TEMPLATES.items():
        print(f'  {key:<12} - {template["name"]}')
        print(f'  {" " * 12}   {template["description"]}\n')


def main():
    """Main function."""
    parser = argparse.ArgumentParser(description='MatsushibaDB Project Initializer')
    parser.add_argument('project_name', nargs='?', help='Project name')
    parser.add_argument('template', nargs='?', default='basic', 
                       choices=list(TEMPLATES.keys()),
                       help='Project template')
    parser.add_argument('--list-templates', action='store_true',
                       help='List available templates')
    
    args = parser.parse_args()
    
    if args.list_templates:
        show_templates()
        return
    
    if not args.project_name:
        print('🚀 MatsushibaDB Project Initializer\n')
        print('Usage: matsushiba-init [project-name] [template]\n')
        show_templates()
        print('Examples:')
        print('  matsushiba-init                    # Basic project')
        print('  matsushiba-init my-app             # Basic project named "my-app"')
        print('  matsushiba-init my-api api         # API project')
        print('  matsushiba-init my-webapp webapp   # Web application')
        print('  matsushiba-init my-service microservice # Microservice\n')
        return
    
    init_project(args.project_name, args.template)


if __name__ == '__main__':
    main()
