# ⚡ Soket Database

**Soket Database (SoketDB)** is a lightweight, file-based JSON database designed for developers who value **speed, simplicity, and flexibility**.  
Unlike traditional SQL engines, SoketDB stores your data directly in JSON, providing instant access with no external dependencies — yet it still supports **SQL-like commands** and even **natural language queries** powered by an AI-to-SQL translator.

---

## 🚀 Features

- 🧩 **JSON-Native Storage** – All data is stored in structured JSON files.  
- ⚡ **Zero Setup** – No server, no SQL engine, just import and start using.  
- 🗣️ **AI Query Support** – Convert plain English queries into SQL with `query()`.  
- 🔒 **Secure & Thread-Safe** – Uses internal locks to ensure safe concurrent access.  
- ☁️ **Cloud Sync (Hugging Face)** – Optionally sync your data with Hugging Face datasets for backup or collaboration.  
- 🧠 **Built-in SQL Engine** – Supports `CREATE`, `INSERT`, `SELECT`, `UPDATE`, `DELETE`, and `DROP TABLE`.  
- ⚙️ **Fast & Portable** – Ideal for microservices, local apps, and prototypes.  

---

## 📦 Installation

```bash
pip install soketdb

🧰 Usage Example

from soketdb import database

# Initialize project
db = database("my_project")

# Create a table
print(db.execute("CREATE TABLE users (name, age, city)"))

# Insert data
print(db.execute("INSERT INTO users DATA = [{'name': 'Alex', 'age': 25, 'city': 'London'}]"))

# Query data with SQL
print(db.execute("SELECT name, age FROM users WHERE age > 20"))

# Query data with natural English
print(db.query("show all users older than 20"))

# Update records
print(db.execute("UPDATE users SET city = 'Paris' WHERE name = 'Alex'"))

# Delete records
print(db.execute("DELETE FROM users WHERE age < 18"))

# Drop table
print(db.execute("DROP TABLE users"))


---

🤖 Natural Language Queries

You can query your data without writing SQL:

db.query("show all users living in Paris")
# 🤖 AI Translated: SELECT * FROM users WHERE city = 'Paris'


---

☁️ Syncing to Hugging Face (Optional)

You can enable cloud backup:

db = database(
    project_name="my_project",
    storage="huggingface",
    token="your_hf_token",
    path="username/dataset_name"
)

Your tables will automatically sync to the Hugging Face dataset repo.


---

🧩 Supported SQL Commands

Command	Description

CREATE TABLE	Create a new table with columns
INSERT INTO	Insert new JSON data
SELECT ... FROM	Query data with optional WHERE, JOIN, and LIMIT
UPDATE	Modify existing records
DELETE FROM	Remove rows
DROP TABLE	Delete a table entirely



---

🔐 Thread Safety

All SQL operations are protected with a re-entrant lock (RLock), allowing safe concurrent access from multiple threads.


---

🧠 AI Query Translator

The built-in function ai_to_sql() converts natural text into simple SQL, making SoketDB beginner-friendly and intuitive for quick data exploration.

Example:

db.query("show names and ages of users in London older than 25")
# Output:
# 🤖 AI Translated: SELECT name, age FROM users WHERE city = 'London' AND age > 25


---

🪶 Lightweight Design

No dependencies beyond Python standard libraries.

Optional Hugging Face integration for syncing.

Data is human-readable and portable (.json + .meta files).



---

📂 Project Structure

Each project is self-contained inside ./soketDB:

soketDB/
├── my_project/
│   ├── users.json
│   ├── users.json.meta
│   └── jobs.json


---

🧾 License

MIT License © 2025 Soket Database


---

✨ Author

Created by Alex Austin
Full-stack developer & cybersecurity engineer
💡 “A database that’s as fast and flexible as your code.”

---