# Architecture & Database Documentation

This document explains the design choices of the School Management Portal, database engine features, limitations, and the migration strategy to scale the portal.

---

## 1. Why Flask?

Flask was selected as the application framework due to the following key design advantages:
* **Micro-framework Flexibility**: Unlike Django, Flask does not impose a rigid directory structure or database setup. It allows us to design clean, modular Blueprints and separate files for database models, config, and decorators.
* **Granular Control**: Flask allows us to write custom request-handling filters, auth decorators, and global context variables (`g.user`) easily.
* **Lightweight Footprint**: Ideal for deploying on school servers or running locally on low-resource machines.
* **Ecosystem Integration**: Seamless integration with SQLAlchemy (`Flask-SQLAlchemy`) and authentication utilities.

---

## 2. Why SQLite?

SQLite is used as the default database engine for the following reasons:
* **Zero Configuration**: SQLite requires no separate server setup, daemon process, or service management. It writes directly to a single file on disk (`school_portal.db`).
* **High Efficiency**: Extremely fast read-heavy operations, suitable for schools where records are viewed frequently (attendance reports, grades, announcements).
* **Portability**: The entire database can be backed up or moved by copying the single `.db` file.
* **Developer Velocity**: Simplifies development and initial installation processes.

---

## 3. SQLite Limitations

While SQLite is excellent for small to medium deployments, it has key limitations:
1. **Concurrency Controls (Write Locks)**: SQLite locking locks the entire database file during writes. If multiple teachers are marking attendance at the exact same moment, database locks (`database is locked` error) can occur.
2. **Network Limitations**: SQLite is not designed to be accessed over network file shares (NFS/SMB) due to file-locking latency and risk of corruption.
3. **Lack of User Authentication**: Access control is handled at the application level. Anyone with access to the server disk can read or write to the database file directly.
4. **No Native Replication**: Lacks built-in support for master-slave replication or active-active clustering, making high-availability setups complex.

---

## 4. Migration Strategy for PostgreSQL/MySQL

Because this project utilizes **SQLAlchemy ORM** instead of raw SQL queries, migrating the backend database to a enterprise-grade system like PostgreSQL or MySQL is highly streamlined. 

### Step-by-Step Migration Plan

#### Step 1: Install Database Drivers
Install the database adapter for Python in the server environment:
* For PostgreSQL: `pip install psycopg2-binary`
* For MySQL: `pip install pymysql`

#### Step 2: Update Configuration File (`config.py`)
Modify the `SQLALCHEMY_DATABASE_URI` connection string to point to the new server. SQLAlchemy handles dialect differences under the hood automatically:
```python
# PostgreSQL
SQLALCHEMY_DATABASE_URI = 'postgresql://db_user:secure_password@localhost:5432/school_db'

# MySQL
SQLALCHEMY_DATABASE_URI = 'mysql+pymysql://db_user:secure_password@localhost:3306/school_db'
```

#### Step 3: Database Schema Initialization
With the target database server running:
1. Create the database (`school_db`) on the target server.
2. Initialize the tables using SQLAlchemy's create command inside a Flask shell:
   ```bash
   flask shell
   >>> from database import db
   >>> db.create_all()
   ```

#### Step 4: Data Migration (SQLite to Target DB)
To migrate existing data from `school_portal.db` to the new database, run a script to copy rows table-by-table. A Python migration script using SQLAlchemy:
```python
# pseudo-code migration helper
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import models

sqlite_engine = create_engine('sqlite:///school_portal.db')
target_engine = create_engine('postgresql://user:pass@host/db')

# Dump all models sequentially from SQLite and load into Target DB
# Session-to-session copying
```
Alternatively, database migration tools like `pgloader` (for PostgreSQL) or standard ETL scripts can migrate the schemas and records directly while maintaining key relationships.

#### Step 5: Database Schema Upgrades (Flask-Migrate)
Integrate `Flask-Migrate` (which wraps Alembic) to manage future schema upgrades seamlessly:
```bash
pip install flask-migrate
```
Add to `app.py`:
```python
from flask_migrate import Migrate
migrate = Migrate(app, db)
```
Initialize migrations:
```bash
flask db init
flask db migrate -m "Initial schema migration"
flask db upgrade
```
