# ⚡ SoketDB v1 — Zero-Setup, AI-Smart JSON Database

> **No switch to turn on.**  
> SoketDB is a lightweight, offline-first, AI-powered database that runs instantly — no setup, no servers.

---

## 🧠 Overview

SoketDB is a **plug-and-play JSON database** with an **AI-driven query engine**.  
It lets you store, query, and sync data locally or in the cloud — without needing MySQL, PostgreSQL, or MongoDB.

Built for **developers who just want to build**, SoketDB merges the simplicity of JSON with the power of SQL and AI.

---

## 🚀 Features

- ⚡ **Zero Setup** — Works out of the box, no installations or daemons.  
- 💾 **JSON-Native Storage** — Every table is a readable JSON file.  
- 🧠 **AI Query Engine** — Translate natural language into SQL-like commands.  
- ☁️ **Cloud Backup** — Optional sync to Hugging Face, Google Drive, Dropbox, or AWS S3.  
- 🔐 **Thread-Safe Execution** — Prevents corruption in multi-threaded access.  
- 🧩 **Configurable Storage** — Local, hybrid, or full cloud mode.  
- 🧱 **System Tables** — Built-in logs, meta tracking, and analytics support.  
- 🌍 **Offline-First Philosophy** — Works anywhere, even without the internet.

---

## 🧰 Installation

```bash
pip install soketdb

Or install manually:

git clone https://github.com/pythos-team/soketdb.git
cd soketdb
python setup.py install


---

🏁 Quick Start

from soketdb import database

    # Example 1: Regular database (no encryption)
    print("=== Regular Database ===")
    db_regular = database("my_app")
    db_regular.execute("CREATE TABLE users (id, name, email)")
    db_regular.execute("INSERT INTO users DATA = [{'id': 1, 'name': 'John', 'email': 'john@example.com'}]")
    result = db_regular.query("show all users")
    print(f"Regular DB Result: {result}")
    
    # Example 2: Production database with encryption
    print("\n=== Production Database ===")
    db_production = database("my_secure_app", production=True)
    db_production.execute("CREATE TABLE secure_users (id, name, email, password_hash)")
    db_production.execute("INSERT INTO secure_users DATA = [{'id': 1, 'name': 'Alice', 'email': 'alice@secure.com', 'password_hash': 'hash123'}]")
    result = db_production.query("count secure users")
    print(f"Production DB Result: {result}")
    
    # Example 3: Using existing encryption key
    print("\n=== Using Existing Encryption Key ===")
    # You would use the key that was displayed when you first created the production database
     db_existing = database("my_secure_app", production=True, encryption_key="your_encryption_key_here")


---

💡 Natural Language Queries

db.query("show all users where password is 1234")

✅ AI converts this into:

SELECT * FROM users WHERE password='1234'


---

☁️ Cloud Sync Example

db = database(
    "my_project",
    storage="huggingface",
    token="hf_xxx_your_token",
    path="alex/soketdb_storage"
)

You can also use Google Drive or Dropbox for automatic backups.


---

📊 Folder Structure

my_project/
│
├── users.json
├── plugins.json
├── system_meta.json
└── logs/


---

🧩 Supported Commands

Command	Description

CREATE TABLE	Create a new table
INSERT INTO	Add new JSON data
SELECT	Query records
UPDATE	Modify existing records
DELETE FROM	Delete specific rows
DROP TABLE	Remove a table completely



---

💬 Philosophy

> “Databases shouldn’t require a switch to turn on.
SoketDB runs, stores, and syncs — instantly.”
— Alex Austin, Creator of SoketDB




---

🧱 Use Cases

Offline-first or hybrid AI projects

Local testing without cloud DBs

Quick data persistence for tools, bots, or microservices

Lightweight web apps and scripts

AI/ML experiments needing quick storage



---

🔐 License

Licensed under the MIT License.
Copyright © 2025 Alex Austin


---

🌟 Tagline

> SoketDB — Simple. Smart. Secure.
The database that runs even when everything else is off.



---