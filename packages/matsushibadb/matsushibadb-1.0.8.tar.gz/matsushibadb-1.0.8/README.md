# matsushiba-db

<div align="center">
  <img src="https://db.matsushiba.co/assets/images/logo.svg" alt="MatsushibaDB" width="120" height="120">
  <h1>MatsushibaDB</h1>
  <p><strong>Next-Generation SQL Database by Matsushiba Systems</strong></p>
  <p>A powerful Python package that provides both <strong>client and server functionality</strong> with <strong>inbuilt SQLite standalone</strong> - no external dependencies required!</p>
</div>

## 🚀 Installation

```bash
pip install matsushiba-db
```

## 📖 Quick Start

### **Start Server (Inbuilt SQLite)**
```bash
# Start MatsushibaDB server with inbuilt SQLite
matsushiba-db --host localhost --port 8000

# Or with all enterprise features
matsushiba-db --enable-audit --enable-encryption --enable-rbac --enable-rate-limit
```

### **Use as Client**
```python
from matsushiba_db import MatsushibaDBClient

# Create HTTP client
client = MatsushibaDBClient('http://localhost:8000')

# Query database
result = client.query('SELECT * FROM users')
print(result['data'])
```

## 📦 **Package Features**

### **✅ Standalone SQLite Database**
- **🔧 Inbuilt SQLite**: No external database installation required
- **📦 Self-Contained**: Everything included in the Python package
- **🚀 Zero Configuration**: Works out of the box
- **💾 File-Based**: Simple database files, no server setup needed

### **✅ Server Mode**
- **Standalone SQLite Database Server**
- **Multi-Protocol Support**: HTTP, HTTPS, WebSocket, TCP
- **Enterprise Security**: Rate limiting, CORS, Helmet security
- **High Performance**: Optimized SQLite settings
- **SSL/HTTPS Support**: Built-in SSL certificate support

### **✅ Client Mode**
- **HTTP/HTTPS Client**: REST API client
- **WebSocket Client**: Real-time bidirectional communication
- **TCP Client**: Low-latency TCP connections
- **Promise-based API**: Modern async/await support

## 🛠 **Usage**

### **Server Mode**

#### **Start Server**
```bash
# Basic server
matsushiba-db

# Custom port and database
matsushiba-db --port 9000 --database myapp.db

# SSL/HTTPS server
matsushiba-db --ssl-cert cert.pem --ssl-key key.pem
```

#### **Server Options**
- `--host HOST`: Server host (default: localhost)
- `--port PORT`: Server port (default: 8000)
- `--database FILE`: Database file (default: matsushiba.db)
- `--ssl-cert FILE`: SSL certificate file
- `--ssl-key FILE`: SSL private key file
- `--enable-audit`: Enable audit logging
- `--enable-encryption`: Enable file encryption
- `--enable-rbac`: Enable role-based access control
- `--enable-rate-limit`: Enable rate limiting

#### **Server Endpoints**
- `GET /`: Server information
- `GET /health`: Health check
- `POST /api/query`: Execute SELECT queries
- `POST /api/execute`: Execute INSERT/UPDATE/DELETE
- `POST /api/batch`: Execute multiple queries
- `POST /api/transaction`: Execute ACID transactions
- `GET /api/tables`: List all tables
- `GET /api/table/:name`: Get table schema
- `POST /api/table/:name`: Create table
- `DELETE /api/table/:name`: Drop table
- `GET /api/users`: List users (admin)
- `POST /api/users`: Create user (admin)
- `GET /api/audit`: Get audit logs (admin)
- `GET /api/metrics`: Get performance metrics

### **Client Mode**

#### **HTTP Client**
```python
from matsushiba_db import MatsushibaDBClient

# Create client
client = MatsushibaDBClient('http://localhost:8000')

# Authenticate
response = client.post('/api/auth/login', json={
    'username': 'admin',
    'password': 'admin123'
})
token = response.json()['token']

# Set authorization header
client.headers['Authorization'] = f'Bearer {token}'

# Query data
result = client.post('/api/query', json={
    'sql': 'SELECT * FROM users WHERE age > ?',
    'params': [18]
})
print(result.json()['data'])

# Execute statements
result = client.post('/api/execute', json={
    'sql': 'INSERT INTO users (name, age) VALUES (?, ?)',
    'params': ['John', 25]
})
print(result.json()['changes'])
```

#### **Batch Operations**
```python
# Execute multiple queries
result = client.post('/api/batch', json={
    'queries': [
        {'sql': 'INSERT INTO users (name) VALUES (?)', 'params': ['Alice']},
        {'sql': 'INSERT INTO users (name) VALUES (?)', 'params': ['Bob']},
        {'sql': 'SELECT COUNT(*) as total FROM users'}
    ]
})
print(result.json()['results'])
```

#### **ACID Transactions**
```python
# Execute transaction
result = client.post('/api/transaction', json={
    'queries': [
        {'sql': 'UPDATE accounts SET balance = balance - 100 WHERE id = 1'},
        {'sql': 'UPDATE accounts SET balance = balance + 100 WHERE id = 2'}
    ]
})
print(result.json()['success'])  # True if all succeeded, False if rolled back
```

## 🔧 **API Reference**

### **Client Methods**

#### **query(sql, params)**
Execute a SELECT query and return results.

```python
result = client.post('/api/query', json={
    'sql': 'SELECT * FROM users WHERE age > ?',
    'params': [18]
})
# Returns: {'success': True, 'data': [...], 'count': number}
```

#### **execute(sql, params)**
Execute INSERT/UPDATE/DELETE statements.

```python
result = client.post('/api/execute', json={
    'sql': 'INSERT INTO users (name) VALUES (?)',
    'params': ['John']
})
# Returns: {'success': True, 'changes': number, 'lastID': number}
```

### **Server Configuration**

#### **Environment Variables**
```bash
MATSUSHIBADB_HOST=localhost
MATSUSHIBADB_PORT=8000
MATSUSHIBADB_DATABASE=matsushiba.db
MATSUSHIBADB_SSL_CERT=cert.pem
MATSUSHIBADB_SSL_KEY=key.pem
```

## 🔒 **Security Features**

- **Rate Limiting**: Prevents request spam (1000 requests/hour)
- **CORS Support**: Configurable cross-origin requests
- **JWT Authentication**: Secure token-based authentication
- **Password Hashing**: bcrypt password hashing
- **Input Validation**: SQL injection protection
- **SSL/HTTPS**: Encrypted connections
- **RBAC**: Role-based access control (admin, user, readonly, guest)
- **Audit Logging**: Complete operation logging
- **File Encryption**: AES-256-CBC encryption for database files

## 📊 **Performance**

- **WAL Mode**: Write-Ahead Logging for better concurrency
- **Connection Pooling**: Efficient connection management
- **Compression**: Gzip compression for responses
- **Caching**: Optimized SQLite cache settings
- **Inbuilt SQLite**: No external database dependencies

## 🌐 **Multi-Protocol Support**

| Protocol | Use Case | Performance | Features |
|----------|----------|-------------|----------|
| HTTP/HTTPS | Web APIs, REST | Good | CORS, SSL, Compression |
| WebSocket | Real-time apps | Excellent | Bidirectional, Low latency |
| TCP | High-performance | Best | Minimal overhead |

## 📝 **Examples**

### **Complete Application (Standalone)**
```python
from matsushiba_db import MatsushibaDBServer
import asyncio

# Start server with inbuilt SQLite
server = MatsushibaDBServer(
    host='localhost',
    port=8000,
    database='myapp.db',
    enable_audit_log=True,
    enable_encryption=True,
    enable_rbac=True,
    enable_rate_limit=True
)

# Start server
asyncio.run(server.start())

# Client usage
from matsushiba_db import MatsushibaDBClient

client = MatsushibaDBClient('http://localhost:8000')

# Authenticate
response = client.post('/api/auth/login', json={
    'username': 'admin',
    'password': 'admin123'
})
token = response.json()['token']
client.headers['Authorization'] = f'Bearer {token}'

# Create table
client.post('/api/table/users', json={
    'sql': '''
        CREATE TABLE users (
            id INTEGER PRIMARY KEY,
            name TEXT NOT NULL,
            email TEXT UNIQUE
        )
    '''
})

# Insert data
client.post('/api/execute', json={
    'sql': 'INSERT INTO users (name, email) VALUES (?, ?)',
    'params': ['John', 'john@example.com']
})

# Query data
result = client.post('/api/query', json={
    'sql': 'SELECT * FROM users'
})
print(result.json()['data'])
```

## 🚀 **Deployment**

### **Production Server (Standalone)**
```bash
# Install globally
pip install matsushiba-db

# Start production server with inbuilt SQLite
matsushiba-db --host 0.0.0.0 --port 80 --database /var/lib/matsushiba/production.db
```

### **Docker**
```dockerfile
FROM python:3.11
RUN pip install matsushiba-db
EXPOSE 8000
CMD ["matsushiba-db", "--host", "0.0.0.0", "--port", "8000"]
```

## 📄 **License**

MatsushibaDB is proprietary software by **Matsushiba Systems**.
See [License Terms](https://db.matsushiba.co/license) for full details.

## 🆘 **Support**

- **Email**: support@matsushiba.co
- **Documentation**: https://db.matsushiba.co/docs
- **Community**: https://db.matsushiba.co/support
- **Issues**: https://github.com/matsushiba/matsushibadb/issues

---

<div align="center">
  <p><strong>MatsushibaDB</strong> - The future of SQL databases is here! 🚀</p>
  <p><em>Part of Matsushiba Systems</em></p>
</div>