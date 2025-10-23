# ⚡ SoketDB v1 — Zero-Setup, AI-Smart JSON Database

> **No switch to turn on.**  
> SoketDB is a lightweight, offline-first, AI-powered database that runs instantly — no setup, no dependencies, no servers.

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

git clone https://github.com/alexaustindev/soketdb.git
cd soketdb
python setup.py install


---

🏁 Quick Start

from soketdb import database

# Initialize a new or existing SoketDB project
db = database("my_project")

# Create a table
db.execute("CREATE TABLE users (username TEXT, password TEXT)")

# Insert records
db.execute("""
INSERT INTO users DATA=[
  {"username": "alex", "password": "1234"},
  {"username": "ben", "password": "abcd"}
]
""")

# Query users
print(db.execute("SELECT username FROM users WHERE password='1234'"))


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