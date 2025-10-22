# t-sql

A lightweight SQL templating library that leverages Python 3.14's t-strings (PEP 750).
(Note: This library has absolutely nothing to do with Microsoft SQLServer)

t-sql provides a safe way to write SQL queries using Python's template strings (t-strings) while preventing SQL injection attacks through multiple parameter styling options.

## ⚠️ Python Version Requirement
This library requires Python 3.14+

t-sql is built specifically to take advantage of the new t-string feature introduced in PEP 750, which is only available in Python 3.14+.

## Installing

```bash
# with pip
pip install t-sql

# with uv
uv add t-sql
```

## Quick Start

```python
import tsql

# Basic usage
name = 'billy'
query = t'select * from users where name={name}'

# Render with default QMARK style
sql, params = tsql.render(query)
# ('select * from users where name = ?', ['billy'])

# Or use a different parameter style
sql, params = tsql.render(query, style=tsql.styles.NUMERIC_DOLLAR)
# ('select * from users where name = $1', ['billy'])
```

## Parameter Styles

- **QMARK** (default): Uses `?` placeholders
- **NUMERIC**: Uses `:1`, `:2`, etc. placeholders
- **NAMED**: Uses `:name` placeholders
- **FORMAT**: Uses `%s` placeholders
- **PYFORMAT**: Uses `%(name)s` placeholders
- **NUMERIC_DOLLAR**: Uses `$1`, `$2`, etc. (PostgreSQL native)
- **ESCAPED**: Escapes values directly into SQL (no parameters)

## Core Features

### SQL Injection Prevention

```python
# SQL injection prevention works automatically
name = "billy ' and 1=1 --"
sql, params = tsql.render(t'select * from users where name={name}')
# Even with ESCAPED style, quotes are properly escaped
sql, _ = tsql.render(t'select * from users where name={name}', style=tsql.styles.ESCAPED)
# ("select * from users where name = 'billy '' and 1=1 --'", [])
```

### Format-spec helpers

#### Literal

For table/column names that can't be parameterized:

```python
table = "users"
col = "name"
val = "billy"
query = t'select * from {table:literal} where {col:literal}={val}'
sql, params = tsql.render(query)
# ('select * from users where name = ?', ['billy'])
```

#### unsafe

For cases where you need to bypass safety (use with extreme caution):

```python
dynamic_where = "age > 18 AND active = true"
sql, params = tsql.render(t"SELECT * FROM users WHERE {dynamic_where:unsafe}")
```

#### as_values

Formats a dictionary for INSERT statements:

```python
values = {'id': 'abc123', 'name': 'bob', 'email': 'bob@example.com'}
sql, params = tsql.render(t"INSERT INTO users {values:as_values}")
# ('INSERT INTO users (id, name, email) VALUES (?, ?, ?)', ['abc123', 'bob', 'bob@example.com'])
```

#### as_set

Formats a dictionary for UPDATE statements:

```python
values = {'name': 'joe', 'email': 'joe@example.com'}
sql, params = tsql.render(t"UPDATE users SET {values:as_set} WHERE id='abc123'")
# ('UPDATE users SET name = ?, email = ? WHERE id='abc123'', ['joe', 'joe@example.com'])
```

### Helper Functions

t-sql provides several convenience functions for common SQL operations:

#### t_join

Joins multiple t-strings together:

```python
import tsql

min_age = 18
parts = [t"SELECT *", t"FROM users", t"WHERE age > {min_age}"]
query = tsql.t_join(t" ", parts)
sql, params = tsql.render(query)
# ('SELECT * FROM users WHERE age > ?', [18])
```

#### select

Quick SELECT queries:

```python
# Select all columns
query = tsql.select('users')
sql, params = query.render()
# ('SELECT * FROM users', [])

# Select specific columns
query = tsql.select('users', columns=['name', 'email'])
sql, params = query.render()
# ('SELECT name, email FROM users', [])

# With WHERE clause
query = tsql.select('users', columns=['name', 'email'], where={'age': 18})
sql, params = query.render()
# ('SELECT name, email FROM users WHERE age = ?', [18])
```

#### insert

Quick INSERT queries:

```python
query = tsql.insert('users', id='abc123', name='bob', email='bob@example.com')
sql, params = query.render()
# ('INSERT INTO users (id, name, email) VALUES (?, ?, ?)', ['abc123', 'bob', 'bob@example.com'])
```

#### update

Quick UPDATE queries:

```python
# Update by ID
query = tsql.update('users', 'abc123', email='new@example.com')
sql, params = query.render()
# ('UPDATE users SET email = ? WHERE id = ?', ['new@example.com', 'abc123'])
```

#### delete

Quick DELETE queries:

```python
# Delete by ID
query = tsql.delete('users', id_value='abc123')
sql, params = query.render()
# ('DELETE FROM users WHERE id = ?', ['abc123'])

# Delete with custom WHERE
query = tsql.delete('users', where={'age': 18})
sql, params = query.render()
# ('DELETE FROM users WHERE age = ?', [18])
```

**Note:** These helper functions return query builder objects, so you can chain additional methods:

```python
query = tsql.select('users').where(t'age > {min_age}').limit(10)
sql, params = query.render()
```

# Query Builder

For a more structured approach, t-sql includes an optional query builder with a fluent interface and type-safe column references.

## Basic Usage

```python
from tsql.query_builder import Table, Column

class Users(Table):
    id: Column
    username: Column
    email: Column
    age: Column

# Simple SELECT
query = Users.select(Users.id, Users.username)
sql, params = query.render()
# ('SELECT users.id, users.username FROM users', [])

# With WHERE clause
query = Users.select().where(Users.age > 18)
sql, params = query.render()
# ('SELECT * FROM users WHERE users.age > ?', [18])

# Multiple conditions (ANDed together)
query = (Users.select(Users.username, Users.email)
         .where(Users.age > 18)
         .where(Users.email != None))
```

**Table Names:** The table name defaults to the lowercase class name. To specify a custom name:

```python
class UserAccount(Table, table_name='user_accounts'):
    id: Column
    username: Column
```

## Joins

```python
class Posts(Table):
    id: Column
    user_id: Column
    title: Column

# INNER JOIN
query = (Posts.select(Posts.title, Users.username)
         .join(Users, on=Posts.user_id == Users.id)
         .where(Posts.id > 100))

# LEFT JOIN
query = (Posts.select()
         .left_join(Users, on=Posts.user_id == Users.id))
```

## Query Features

### Selecting All Columns from a Table

Use `Table.ALL` to select all columns from a specific table:

```python
# Select all columns from posts
query = Posts.select(Posts.ALL)
# ('SELECT posts.* FROM posts', [])

# Select all columns from posts + specific columns from joined tables
query = (Posts.select(Posts.ALL, Users.username, Users.email)
         .join(Users, Posts.user_id == Users.id))
# ('SELECT posts.*, users.username, users.email FROM posts INNER JOIN users ON ...', [])

# Select all columns from multiple tables
query = Posts.select(Posts.ALL, Users.ALL).join(Users, Posts.user_id == Users.id)
# ('SELECT posts.*, users.* FROM posts INNER JOIN users ON ...', [])
```

This is particularly useful when joining tables where you want all columns from one table but only specific columns from others.

### NULL Checks and Other Operators

```python
# NULL checks
query = Users.select().where(Users.email.is_null())
query = Users.select().where(Users.email.is_not_null())

# IN clause
query = Users.select().where(Users.id.in_([1, 2, 3]))
query = Users.select().where(Users.id.not_in([1, 2, 3]))

# LIKE clause
query = Users.select().where(Users.username.like('%john%'))
query = Users.select().where(Users.username.not_like('%john%'))
query = Users.select().where(Users.username.ilike('%JOHN%'))  # case-insensitive
query = Users.select().where(Users.username.not_ilike('%JOHN%'))

# BETWEEN clause
query = Users.select().where(Users.age.between(18, 65))
query = Users.select().where(Users.age.not_between(18, 65))

# ORDER BY
query = Posts.select().order_by(Posts.id)  # defaults to ASC
query = Posts.select().order_by(Posts.id.desc())
query = Posts.select().order_by(Posts.created_at.asc(), Posts.id.desc())

# LIMIT and OFFSET
query = Posts.select().limit(10).offset(20)

# GROUP BY and HAVING
query = (Posts.select()
         .group_by(Posts.user_id)
         .having(t'COUNT(*) > {min_count}'))
```

## Write Operations

The query builder supports INSERT, UPDATE, and DELETE with database-agnostic conflict handling.

### INSERT

```python
# Basic insert
query = Users.insert(id='abc123', username='john', email='john@example.com')
sql, params = query.render()
# ('INSERT INTO users (id, username, email) VALUES (?, ?, ?)', ['abc123', 'john', 'john@example.com'])

# INSERT with RETURNING (Postgres/SQLite)
query = Users.insert(id='abc123', username='john', email='john@example.com').returning()
sql, params = query.render()
# ('INSERT INTO users (id, username, email) VALUES (?, ?, ?) RETURNING *', [...])

# INSERT IGNORE (MySQL)
query = Users.insert(id='abc123', username='john', email='john@example.com').ignore()
sql, params = query.render()
# ('INSERT IGNORE INTO users (id, username, email) VALUES (?, ?, ?)', [...])

# ON CONFLICT DO NOTHING (Postgres/SQLite)
query = Users.insert(id='abc123', username='john', email='john@example.com').on_conflict_do_nothing()
# ('INSERT INTO users (...) VALUES (...) ON CONFLICT DO NOTHING', [...])

# ON CONFLICT DO NOTHING with specific conflict target (Postgres/SQLite)
query = Users.insert(id='abc123', username='john', email='john@example.com').on_conflict_do_nothing(conflict_on='email')
# ('INSERT INTO users (...) VALUES (...) ON CONFLICT (email) DO NOTHING', [...])

# ON CONFLICT DO UPDATE (Postgres/SQLite upsert)
query = Users.insert(id='abc123', username='john', email='john@example.com').on_conflict_update(conflict_on='id')
# ('INSERT INTO users (...) VALUES (...)
#   ON CONFLICT (id) DO UPDATE SET username = EXCLUDED.username, email = EXCLUDED.email', [...])

# ON CONFLICT with custom update
query = Users.insert(id='abc123', username='john', email='john@example.com').on_conflict_update(
    conflict_on='id',
    update={'username': 'updated_name'}
)

# ON DUPLICATE KEY UPDATE (MySQL)
query = Users.insert(id='abc123', username='john', email='john@example.com').on_duplicate_key_update()
# ('INSERT INTO users (...) VALUES (...)
#   ON DUPLICATE KEY UPDATE id = VALUES(id), username = VALUES(username), ...', [...])

# Chain multiple modifiers
query = (Users.insert(id='abc123', username='john', email='john@example.com')
         .on_conflict_update(conflict_on='id')
         .returning('id', 'username'))
```

### UPDATE

```python
# UPDATE requires WHERE clause or explicit .all_rows() for safety
query = Users.update(email='newemail@example.com')
# ❌ Raises UnsafeQueryError: UPDATE without WHERE requires .all_rows()

# UPDATE with WHERE
query = Users.update(email='newemail@example.com').where(Users.id == 'abc123')
sql, params = query.render()
# ('UPDATE users SET email = ? WHERE users.id = ?', ['newemail@example.com', 'abc123'])

# Multiple WHERE conditions
query = (Users.update(email='newemail@example.com')
         .where(Users.id == 'abc123')
         .where(Users.age > 18))

# Explicitly update all rows (use with caution!)
query = Users.update(status='inactive').all_rows()
sql, params = query.render()
# ('UPDATE users SET status = ?', ['inactive'])

# With RETURNING (Postgres/SQLite)
query = (Users.update(email='new@example.com')
         .where(Users.id == 'abc123')
         .returning())
# ('UPDATE users SET email = ? WHERE users.id = ? RETURNING *', [...])
```

### DELETE

```python
# DELETE requires WHERE clause or explicit .all_rows() for safety
query = Users.delete()
# ❌ Raises UnsafeQueryError: DELETE without WHERE requires .all_rows()

# DELETE with WHERE
query = Users.delete().where(Users.id == 'abc123')
sql, params = query.render()
# ('DELETE FROM users WHERE users.id = ?', ['abc123'])

# Multiple conditions
query = Users.delete().where(Users.age < 18).where(Users.active == False)

# Explicitly delete all rows (use with extreme caution!)
query = Users.delete().all_rows()
sql, params = query.render()
# ('DELETE FROM users', [])

# With RETURNING (Postgres/SQLite)
query = Users.delete().where(Users.id == 'abc123').returning()
# ('DELETE FROM users WHERE users.id = ? RETURNING *', ['abc123'])
```

## Database Compatibility

The query builder is database-agnostic - all methods are available regardless of which database you're using. It's your responsibility to use the appropriate methods for your database:

**PostgreSQL:**
- ✅ `.returning()` - RETURNING clause
- ✅ `.on_conflict_do_nothing()` - ON CONFLICT DO NOTHING
- ✅ `.on_conflict_update()` - ON CONFLICT DO UPDATE with EXCLUDED.*
- ❌ `.ignore()` - Not supported
- ❌ `.on_duplicate_key_update()` - Not supported

**MySQL:**
- ❌ `.returning()` - Not supported (MySQL limitation)
- ✅ `.ignore()` - INSERT IGNORE
- ✅ `.on_duplicate_key_update()` - ON DUPLICATE KEY UPDATE with VALUES()
- ❌ `.on_conflict_do_nothing()` - Not supported
- ❌ `.on_conflict_update()` - Not supported

**SQLite:**
- ✅ `.returning()` - RETURNING clause (SQLite 3.35+)
- ✅ `.on_conflict_do_nothing()` - ON CONFLICT DO NOTHING
- ✅ `.on_conflict_update()` - ON CONFLICT DO UPDATE
- ❌ `.ignore()` - Not supported
- ❌ `.on_duplicate_key_update()` - Not supported

If you use an unsupported method, your database will raise a syntax error when you execute the query.

## Mixing Query Builder with T-Strings

You can combine the query builder with raw t-strings for complex logic:

```python
from tsql.query_builder import Table, Column

class Users(Table):
    id: Column
    name: Column
    age: Column
    email: Column

# Start with query builder
query = Users.select(Users.id, Users.name, Users.email)

# Add structured condition
query = query.where(Users.age > 18)

# Add complex t-string condition for OR logic
search_term = "john"
name_col = str(Users.name)
email_col = str(Users.email)
complex_condition = t"{name_col:literal} LIKE '%' || {search_term} || '%' OR {email_col:literal} LIKE '%' || {search_term} || '%'"
query = query.where(complex_condition)

sql, params = query.render()
# SELECT users.id, users.name, users.email FROM users
# WHERE users.age > ? AND (users.name LIKE '%' || ? || '%' OR users.email LIKE '%' || ? || '%')
# params: [18, 'john', 'john']
```

Note: T-string conditions passed to `.where()` are automatically wrapped in parentheses to ensure proper operator precedence.

## SQLAlchemy & Alembic Integration

The query builder can integrate with SQLAlchemy's metadata system for alembic autogenerate:

```bash
pip install t-sql[sqlalchemy]
# or
uv add t-sql --optional sqlalchemy
```

### Two Ways to Define Columns

**1. Simple Column annotations** (for query builder only):

```python
from tsql.query_builder import Table, Column

class Users(Table):
    id: Column
    name: Column
    age: Column
```

**2. SQLAlchemy with SAColumn wrapper** (recommended for type checkers):

```python
from sqlalchemy import MetaData, Integer, String
from tsql.query_builder import Table, SAColumn

metadata = MetaData()

class Users(Table, metadata=metadata):
    id = SAColumn(Integer, primary_key=True)
    email = SAColumn(String(255), unique=True, nullable=False)
    name = SAColumn(String(100))
    age = SAColumn(Integer)

# Use for alembic
target_metadata = metadata

# Use for queries
query = Users.select().where(Users.age > 18)
```

The `SAColumn` wrapper tells type checkers it returns a tsql `Column`, while at runtime it creates a SQLAlchemy `Column`. This gives you proper IDE completions for methods like `.is_null()`, `.like()`, etc.

### Table Constraints

For Alembic migrations, you can define table-level constraints using the `constraints` attribute:

```python
from sqlalchemy import MetaData, String, UniqueConstraint, CheckConstraint, Index
from tsql.query_builder import Table, SAColumn

metadata = MetaData()

class Clients(Table, table_name='clients', metadata=metadata):
    id = SAColumn(String, primary_key=True)
    tenant_id = SAColumn(String)
    email = SAColumn(String, nullable=False)

    # Define table-level constraints
    constraints = [
        UniqueConstraint('tenant_id', 'email', name='uq_clients_tenant_email'),
        CheckConstraint('length(email) > 0', name='ck_clients_email_not_empty'),
        Index('ix_clients_tenant', 'tenant_id')
    ]
```

The `constraints` attribute accepts both lists and tuples, and supports all SQLAlchemy constraint types:
- `UniqueConstraint` - Multi-column unique constraints
- `CheckConstraint` - Table-level check constraints
- `Index` - Multi-column indexes
- `ForeignKeyConstraint` - Table-level foreign keys

**Note:** Single-column constraints like unique indexes and foreign keys can still be defined directly on `SAColumn` (e.g., `SAColumn(String, unique=True, index=True)`).

### Table Comments

Add database-level documentation with the `comment` parameter:

```python
class Users(Table, metadata=metadata, comment='Application user accounts'):
    id = SAColumn(Integer, primary_key=True)
    email = SAColumn(String(255), nullable=False)
```

Table comments appear in database introspection tools and migration files, making your schema self-documenting.

### Type Processors

Type processors enable automatic value transformation when reading from and writing to the database, similar to SQLAlchemy's `TypeDecorator`. This is useful for encryption, serialization, and custom data transformations.

```python
from tsql import TypeProcessor
from tsql.query_builder import Table, SAColumn
from sqlalchemy import Integer, String, MetaData
import json

metadata = MetaData()

# Define custom type processors
class EncryptedString(TypeProcessor):
    def __init__(self, key):
        self.key = key

    def process_bind_param(self, value):
        """Transform Python value -> DB value (encrypt on write)"""
        if value is None:
            return None
        return encrypt(value, self.key)

    def process_result_value(self, value):
        """Transform DB value -> Python value (decrypt on read)"""
        if value is None:
            return None
        return decrypt(value, self.key)

class JSONType(TypeProcessor):
    def process_bind_param(self, value):
        """Serialize Python dict/list -> JSON string"""
        return json.dumps(value) if value is not None else None

    def process_result_value(self, value):
        """Deserialize JSON string -> Python dict/list"""
        return json.loads(value) if value is not None else None

# Use type processors in table definition
class User(Table, metadata=metadata):
    id = SAColumn(Integer, primary_key=True)
    ssn = SAColumn(String(255), type_processor=EncryptedString(key="secret"))
    metadata_ = SAColumn(String, type_processor=JSONType())
    email = SAColumn(String(255))  # No processor = no transformation

# Write - automatic encryption/serialization
User.insert(ssn="123-45-6789", metadata_={"role": "admin"})
# SQL: INSERT INTO user (ssn, metadata_) VALUES (?, ?)
# Params: [encrypt("123-45-6789", "secret"), '{"role": "admin"}']

User.update(ssn="new-ssn").where(User.id == 1)
# SQL: UPDATE user SET ssn = ? WHERE user.id = ?
# Params: [encrypt("new-ssn", "secret"), 1]

# Where clauses - automatic transformation
User.select().where(User.ssn == "123-45-6789")
# SQL: SELECT * FROM user WHERE user.ssn = ?
# Params: [encrypt("123-45-6789", "secret")]

# Read - manual decryption/deserialization with map_results()
query = User.select().where(User.id == 1)
sql, params = query.render()
rows = await connection.fetch(sql, *params)  # Returns encrypted/serialized data
transformed_rows = query.map_results(rows)   # Applies type processors
# transformed_rows = [{"id": 1, "ssn": "123-45-6789", "metadata_": {"role": "admin"}, ...}]
```

**Key features:**
- **Write-side**: Automatically applied in `INSERT`, `UPDATE`, and `WHERE` clauses
- **Read-side**: Manual via `query.map_results(rows)` - you control when transformation happens
- **NULL handling**: NULL values are passed through to processors (they decide how to handle)
- **Column comparisons**: Type processors are NOT applied when comparing columns to other columns

**Why manual read-side transformation?**
The query builder stays database-agnostic and doesn't execute queries directly. You control when to apply transformations after fetching results from your specific database driver.

## Schema Support

```python
class Users(Table, schema='public'):
    id: Column
    name: Column
```

Or with custom table name and schema:

```python
class Users(Table, table_name='user_accounts', schema='public'):
    id: Column
    name: Column
```

# Rendering Queries

All query types (t-strings, TSQL objects, and QueryBuilder objects) can be rendered using `tsql.render()`:

```python
import tsql
from tsql.query_builder import Table, Column

class Users(Table):
    id: Column
    name: Column

# All of these work with tsql.render():
sql, params = tsql.render(t"SELECT * FROM users WHERE id = {user_id}")
sql, params = tsql.render(Users.select().where(Users.id == user_id))
sql, params = tsql.render(tsql.select('users', user_id))

# Or call .render() directly on TSQL/QueryBuilder objects:
query = Users.select().where(Users.age > 18)
sql, params = query.render()
```

# Type Safety & Preventing SQL Injection

This library should ideally be used in middleware or library code to enforce safe query construction. Use the `TSQLQuery` type to prevent raw strings:

```python
from tsql import TSQLQuery, render

def execute_sql_query(query: TSQLQuery):
    """Only accepts safe, parameterized queries"""
    sql, params = render(query)
    return sql_engine.execute(sql, params)

# Type checker allows these:
execute_sql_query(t"SELECT * FROM users WHERE id = {user_id}")  # ✓
execute_sql_query(Users.select())  # ✓
execute_sql_query(tsql.select('users'))  # ✓

# Type checker rejects raw strings:
execute_sql_query("SELECT * FROM users")  # ✗ Type error!
```

The `TSQLQuery` type is a union of `TSQL`, `Template` (t-strings), and `QueryBuilder`, ensuring all queries are safe from SQL injection.

# Security Considerations

## Overview

SQL injection is one of the most critical web application security risks (OWASP Top 10). This library is designed from the ground up to prevent SQL injection attacks through multiple layers of protection. However, understanding how these protections work—and where they can be bypassed—is essential for secure usage.

## How t-sql Prevents SQL Injection

### 1. Automatic Parameterization (Primary Defense)

By default, all interpolated values in t-strings are converted to parameterized queries:

```python
# User input (potentially malicious)
user_input = "admin' OR 1=1 --"

# t-sql automatically parameterizes this
sql, params = tsql.render(t"SELECT * FROM users WHERE name = {user_input}")
# Result: ('SELECT * FROM users WHERE name = ?', ["admin' OR 1=1 --"])
```

The malicious SQL becomes **literal string data** in the parameter, not executable SQL code. The database treats it as a string value to match, not as SQL syntax.

**Attack vectors prevented:**
- Classic injection: `' OR 1=1 --`
- Union-based: `' UNION SELECT * FROM secrets --`
- Stacked queries: `'; DROP TABLE users; --`
- Boolean-based blind: `' AND SLEEP(5) --`
- Authentication bypass: `admin'--`

### 2. Literal Validation (Identifier Safety)

For table and column names that cannot be parameterized, use `:literal`:

```python
table = "users"
col = "name"
sql, params = tsql.render(t"SELECT * FROM {table:literal} WHERE {col:literal} = {value}")
```

**Validation rules:**
- Must be valid Python identifiers (`str.isidentifier()`)
- Supports qualified names: `table.column` or `schema.table.column` (max 3 parts)
- Rejects anything with spaces, quotes, or special characters

```python
# These are REJECTED with ValueError:
bad_table = "users; DROP TABLE secrets"  # Contains semicolon
bad_col = "name' OR 1=1"  # Contains quote
bad_schema = "schema.table.column.extra"  # Too many parts

tsql.render(t"SELECT * FROM {bad_table:literal}")  # Raises ValueError
```

**Attack vectors prevented:**
- Table/column injection: `users; DROP TABLE secrets`
- Second-order injection via identifiers
- Schema manipulation

### 3. Escape-based Protection (ESCAPED Style)

For databases or scenarios where parameterization isn't available, the `ESCAPED` style properly escapes values:

```python
malicious = "'; DROP TABLE users; --"
sql, _ = tsql.render(t"SELECT * FROM users WHERE name = {malicious}", style=tsql.styles.ESCAPED)
# Result: "SELECT * FROM users WHERE name = '''; DROP TABLE users; --'"
#         (single quotes are doubled, making it literal data)
```

**Important:** While effective, parameterization is always preferred when available. Use `ESCAPED` only when necessary.

### 4. Query Builder Safety: UPDATE/DELETE Protection

The query builder prevents accidental mass UPDATE/DELETE operations by requiring an explicit WHERE clause or `.all_rows()` call:

```python
from tsql import UnsafeQueryError

# This raises UnsafeQueryError at render time
Users.update(status='inactive').render()  # ❌ Error!
Users.delete().render()  # ❌ Error!

# Must add WHERE clause
Users.update(status='inactive').where(Users.id == user_id).render()  # ✅

# Or explicitly confirm mass operation
Users.update(status='inactive').all_rows().render()  # ✅
Users.delete().all_rows().render()  # ✅
```

This protection catches the most common and dangerous SQL mistake: forgetting the WHERE clause. 

## Danger Zones: Where You Can Still Get Hurt

### The :unsafe Format Spec

The `:unsafe` format spec **bypasses all safety mechanisms**:

```python
# DANGEROUS - no validation or parameterization!
dynamic_sql = "age > 18 OR role = 'admin'"  # If this comes from user input, you're vulnerable
sql, params = tsql.render(t"SELECT * FROM users WHERE {dynamic_sql:unsafe}")
```

**When :unsafe is acceptable:**
- Hard-coded SQL fragments in your own code
- SQL generated by trusted, validated builder logic
- Dynamic ORDER BY clauses (after validation)

**When :unsafe is DANGEROUS:**
- **Never** with user input (even "validated" input)
- Dynamic WHERE clauses from external sources
- Any data from forms, APIs, or databases

**Recommendation:** Treat `:unsafe` like `eval()` in your code reviews. Every usage should be scrutinized and documented.
