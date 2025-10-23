import os
import re
import json
import threading
from huggingface_hub import upload_file
from typing import List, Dict, Any, Optional, Union

DATABASE = "./soketDB"
TABLE_EXT = ".json"

lock = threading.RLock()


def ai_to_sql(prompt: str):
    """
    Convert natural English queries into SQL-like syntax.
    Generates only SQL that the database supports.
    """

    text = prompt.lower().strip()

    # Detect table name
    if "user" in text:
        table = "users"
    elif "job" in text:
        table = "jobs"
    elif "order" in text:
        table = "orders"
    else:
        table = "users"  # Default to users

    # Detect columns (select fields)
    select_columns = ["*"]  # Default to all columns
    
    # Extract specific columns if mentioned
    if "name" in text and "age" in text:
        select_columns = ["name", "age"]
    elif "name" in text and "city" in text:
        select_columns = ["name", "city"]
    elif "name" in text:
        select_columns = ["name"]
    elif "age" in text:
        select_columns = ["age"]
    elif "city" in text:
        select_columns = ["city"]
    elif "title" in text:
        select_columns = ["title"]
    elif "salary" in text:
        select_columns = ["salary"]

    # For specific column requests
    if "show" in text or "display" in text or "list" in text:
        if "name" in text and "age" in text:
            select_columns = ["name", "age"]
        elif "name" in text and "city" in text:
            select_columns = ["name", "city"]
        elif "name" in text:
            select_columns = ["name"]
        elif "age" in text:
            select_columns = ["age"]
        elif "city" in text:
            select_columns = ["city"]
        elif "title" in text:
            select_columns = ["title"]
        elif "salary" in text:
            select_columns = ["salary"]

    # --- WHERE conditions ---
    where_conditions = []

    # Age conditions
    if "age" in text:
        if "age is 30" in text or "age = 30" in text:
            where_conditions.append("age = 30")
        elif "age is 24" in text or "age = 24" in text:
            where_conditions.append("age = 24")
        elif "age greater than 25" in text or "age > 25" in text:
            where_conditions.append("age > 25")
        elif "age less than 30" in text or "age < 30" in text:
            where_conditions.append("age < 30")
        elif "age between 20 and 35" in text:
            where_conditions.append("age > 20")
            where_conditions.append("age < 35")

    # Salary conditions
    if "salary" in text:
        if "salary more than 48000" in text or "salary > 48000" in text:
            where_conditions.append("salary > 48000")
        elif "salary less than 60000" in text or "salary < 60000" in text:
            where_conditions.append("salary < 60000")

    # City conditions (simple equality only - no LIKE support)
    if "city" in text:
        if "london" in text:
            where_conditions.append("city = 'London'")
        elif "paris" in text:
            where_conditions.append("city = 'Paris'")
        elif "berlin" in text:
            where_conditions.append("city = 'Berlin'")

    # Name conditions (simple equality only)
    if "name" in text:
        if "alex" in text:
            where_conditions.append("name = 'Alex'")
        elif "jane" in text:
            where_conditions.append("name = 'Jane'")
        elif "bob" in text:
            where_conditions.append("name = 'Bob'")

    # --- Build SQL ---
    sql = f"SELECT {', '.join(select_columns)} FROM {table}"
    
    # Add WHERE clause if we have conditions
    if where_conditions:
        sql += f" WHERE {' AND '.join(where_conditions)}"

    # Handle LIMIT (simple cases only)
    if "top 2" in text or "first 2" in text:
        sql += " LIMIT 2"

    return sql


class database:
    def __init__(self, project_name: str, storage: str = "local", token: Optional[str] = None, path: Optional[str] = None):
        self.project_name = project_name
        self.storage = storage.lower()
        self.token = token
        self.path = path

        # Create project folder locally
        self.project_path = os.path.join(DATABASE, project_name)
        os.makedirs(self.project_path, exist_ok=True)

        if self.storage == "huggingface" and (not token or not path):
            print("⚠️ Missing token or path. Switching to local mode.")
            self.storage = "local"

    # -----------------------------
    # Internal read/write helpers
    # -----------------------------
    def _read_table(self, table: str) -> List[Dict[str, Any]]:
        """Read table data from JSON file."""
        file = f"{table}{TABLE_EXT}"
        path = os.path.join(self.project_path, file)
        if not os.path.exists(path):
            return []
        try:
            with open(path, "r", encoding="utf-8") as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError):
            return []

    def _write_table(self, table: str, data: List[Dict[str, Any]]) -> None:
        """Write table data to JSON file and optionally sync with HuggingFace."""
        file = f"{table}{TABLE_EXT}"
        path = os.path.join(self.project_path, file)
        
        # Ensure directory exists
        os.makedirs(os.path.dirname(path), exist_ok=True)
        
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=4, ensure_ascii=False)
        
        if self.storage == "huggingface" and self.token and self.path:
            try:
                upload_file(
                    path_or_fileobj=path,
                    path_in_repo=f"{self.project_name}/{file}",
                    repo_id=self.path,
                    repo_type="dataset",
                    token=self.token
                )
            except Exception as e:
                print(f"⚠️ Failed to sync with HuggingFace: {e}")

    def _read_metadata(self, table: str) -> Optional[Dict[str, Any]]:
        """Read table metadata."""
        meta_path = os.path.join(self.project_path, f"{table}{TABLE_EXT}.meta")
        if not os.path.exists(meta_path):
            return None
        try:
            with open(meta_path, "r") as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError):
            return None

    def _write_metadata(self, table: str, metadata: Dict[str, Any]) -> None:
        """Write table metadata."""
        meta_path = os.path.join(self.project_path, f"{table}{TABLE_EXT}.meta")
        with open(meta_path, "w") as f:
            json.dump(metadata, f, indent=4)

    # -----------------------------
    # Thread-safe SQL executor
    # -----------------------------
    def execute(self, sql: str) -> Any:
        """Execute SQL query in a thread-safe manner."""
        result_container = {}

        def _worker():
            with lock:
                result_container["result"] = self._run_sql(sql)

        thread = threading.Thread(target=_worker)
        thread.start()
        thread.join()
        return result_container["result"]

    def query(self, prompt: str) -> Any:
        """
        Execute natural language queries by converting them to SQL first.
        Supports both SQL and plain English.
        """
        # Check if it's already SQL
        sql_keywords = ["SELECT", "INSERT", "UPDATE", "DELETE", "CREATE", "DROP", "FROM", "WHERE", "JOIN"]
        is_sql = any(keyword in prompt.upper() for keyword in sql_keywords)
        
        if is_sql:
            return self.execute(prompt)
        else:
            # Convert natural language to SQL
            try:
                sql = ai_to_sql(prompt)
                print(f"🤖 AI Translated: {sql}")
                return self.execute(sql)
            except Exception as e:
                return f"❌ AI translation failed: {e}"

    # -----------------------------
    # SQL Parser Helpers
    # -----------------------------
    def _parse_join_condition(self, join_cond: str) -> tuple[str, str]:
        """Parse JOIN condition and return (left_key, right_key)."""
        if "=" not in join_cond:
            raise ValueError(f"Invalid JOIN condition: {join_cond}")
        
        parts = join_cond.split("=", 1)
        if len(parts) != 2:
            raise ValueError(f"Invalid JOIN condition format: {join_cond}")
        
        left_key = parts[0].strip()
        right_key = parts[1].strip()
        
        # Handle table.column format by removing table prefix
        if "." in left_key:
            left_key = left_key.split(".")[-1]
        if "." in right_key:
            right_key = right_key.split(".")[-1]
            
        return left_key, right_key

    def _parse_where_conditions(self, where_clause: str) -> Dict[str, str]:
        """Parse WHERE conditions into a dictionary."""
        if not where_clause:
            return {}
        
        conditions = {}
        # Split by AND (case insensitive)
        pattern = r'\s+AND\s+'
        cond_parts = re.split(pattern, where_clause, flags=re.I)
        
        for cond in cond_parts:
            cond = cond.strip()
            if "=" in cond:
                key, value = cond.split("=", 1)
                key = key.strip()
                value = value.strip().strip("'\"")
                conditions[key] = value
                
        return conditions

    def _parse_set_clause(self, set_clause: str) -> Dict[str, str]:
        """Parse SET clause for UPDATE statements."""
        updates = {}
        # More robust parsing that handles quoted values
        pattern = r'(\w+)\s*=\s*("[^"]*"|\'[^\']*\'|[^,]+)'
        matches = re.findall(pattern, set_clause)
        
        for key, value in matches:
            value = value.strip().strip("'\"")
            updates[key.strip()] = value
            
        return updates

    def _parse_select_columns(self, cols: str, left_table: str, right_table: str = None) -> List[str]:
        """Parse SELECT columns and handle table prefixes."""
        if cols.strip() == "*":
            return ["*"]
        
        columns = []
        for col in cols.split(","):
            col = col.strip()
            # Handle table.column format
            if "." in col:
                table_name, column_name = col.split(".", 1)
                columns.append((table_name.strip(), column_name.strip()))
            else:
                columns.append(col)
        return columns

    def _compare_values(self, actual_value: Any, condition_value: str, operator: str = "=") -> bool:
        """Compare values with type awareness for numbers."""
        try:
            # Try to convert both values to numbers for comparison
            actual_num = float(actual_value) if actual_value is not None else None
            condition_num = float(condition_value) if condition_value else None
            
            if actual_num is not None and condition_num is not None:
                # Numeric comparison
                if operator == "=":
                    return actual_num == condition_num
                elif operator == ">":
                    return actual_num > condition_num
                elif operator == "<":
                    return actual_num < condition_num
                elif operator == ">=":
                    return actual_num >= condition_num
                elif operator == "<=":
                    return actual_num <= condition_num
                elif operator == "!=":
                    return actual_num != condition_num
        except (ValueError, TypeError):
            pass
        
        # Fall back to string comparison
        actual_str = str(actual_value) if actual_value is not None else ""
        condition_str = str(condition_value) if condition_value else ""
        
        if operator == "=":
            return actual_str == condition_str
        elif operator == ">":
            return actual_str > condition_str
        elif operator == "<":
            return actual_str < condition_str
        elif operator == ">=":
            return actual_str >= condition_str
        elif operator == "<=":
            return actual_str <= condition_str
        elif operator == "!=":
            return actual_str != condition_str
        
        return False

    def _parse_where_conditions_advanced(self, where_clause: str) -> List[tuple]:
        """Parse WHERE conditions with support for operators: =, !=, >, <, >=, <="""
        if not where_clause:
            return []
        
        conditions = []
        # Split by AND (case insensitive)
        pattern = r'\s+AND\s+'
        cond_parts = re.split(pattern, where_clause, flags=re.I)
        
        for cond in cond_parts:
            cond = cond.strip()
            # Match operators: =, !=, >, <, >=, <=
            operator_pattern = r'(\w+\.?\w*)\s*(=|!=|>|<|>=|<=)\s*("[^"]*"|\'[^\']*\'|\S+)'
            match = re.match(operator_pattern, cond)
            
            if match:
                key, operator, value = match.groups()
                value = value.strip().strip("'\"")
                conditions.append((key.strip(), operator, value))
            elif "=" in cond:
                # Fallback for simple equals
                key, value = cond.split("=", 1)
                conditions.append((key.strip(), "=", value.strip().strip("'\"")))
                
        return conditions

    # -----------------------------
    # Enhanced INSERT data parsing
    # -----------------------------
    def _parse_insert_data(self, data_str: str) -> List[Dict[str, Any]]:
        """Parse INSERT DATA with support for both proper JSON and Python-like dicts."""
        data_str = data_str.strip()
        
        # Try to parse as proper JSON first
        try:
            return json.loads(data_str)
        except json.JSONDecodeError:
            pass
        
        # If JSON fails, try to parse Python-like dict syntax
        try:
            # Replace single quotes with double quotes for JSON compatibility
            data_str = re.sub(r"'([^']*)'", r'"\1"', data_str)
            return json.loads(data_str)
        except json.JSONDecodeError as e:
            raise ValueError(f"Invalid data format: {e}")

    # -----------------------------
    # SQL Engine
    # -----------------------------
    def _run_sql(self, sql: str) -> Any:
        sql = re.sub(r'\s+', ' ', sql.strip())  # Normalize whitespace
        
        try:
            # ---------------------
            # CREATE TABLE - IMPROVED ERROR MESSAGES
            # ---------------------
            if match := re.match(r"CREATE TABLE (\w+)\s*\((.+)\)", sql, re.I):
                table, cols = match.groups()
                path = os.path.join(self.project_path, f"{table}{TABLE_EXT}")
                
                # Check if table already exists
                if os.path.exists(path):
                    existing_columns = []
                    meta = self._read_metadata(table)
                    if meta:
                        existing_columns = meta.get("columns", [])
                    return f"❌ Table '{table}' already exists. Existing columns: {existing_columns}"
                
                columns = [c.strip().split()[0] for c in cols.split(",")]  # Get only column names
                
                # Check for duplicate columns
                if len(columns) != len(set(columns)):
                    duplicates = [col for col in columns if columns.count(col) > 1]
                    return f"❌ Duplicate column names found: {list(set(duplicates))}"
                
                self._write_table(table, [])
                meta = {"columns": columns}
                self._write_metadata(table, meta)
                return f"✅ Table '{table}' created with columns {columns}"

            # ---------------------
            # INSERT INTO - IMPROVED ERROR MESSAGES
            # ---------------------
            if match := re.match(r"INSERT INTO (\w+)\s+DATA\s*=\s*(.+)", sql, re.I | re.S):
                table, payload = match.groups()
                path = os.path.join(self.project_path, f"{table}{TABLE_EXT}")
                
                # Check if table exists
                if not os.path.exists(path):
                    available_tables = self.list_tables()
                    return f"❌ Table '{table}' not found. Available tables: {available_tables}"
                
                data = self._read_table(table)
                try:
                    rows = self._parse_insert_data(payload)
                except ValueError as e:
                    return f"❌ Invalid data format: {e}"
                
                if isinstance(rows, dict): 
                    rows = [rows]

                meta = self._read_metadata(table)
                if not meta:
                    return f"❌ Metadata for table '{table}' not found. Table may be corrupted."
                
                valid_cols = set(meta["columns"])

                # Check for invalid columns with better error messages
                invalid_cols_found = set()
                valid_rows = []
                
                for r in rows:
                    row_cols = set(r.keys())
                    invalid_cols = row_cols - valid_cols
                    if invalid_cols:
                        invalid_cols_found.update(invalid_cols)
                    else:
                        valid_rows.append(r)
                
                if invalid_cols_found:
                    return f"❌ Invalid column(s) {list(invalid_cols_found)} in table '{table}'. Valid columns are: {list(valid_cols)}"

                # Avoid duplicate full-row insertions
                new_rows = []
                for r in valid_rows:
                    if r not in data:
                        new_rows.append(r)

                if not new_rows:
                    existing_sample = data[0] if data else "No existing data"
                    return f"⚠️ No new data to insert (duplicates skipped). All rows already exist in table '{table}'. Sample existing row: {existing_sample}"

                data.extend(new_rows)
                self._write_table(table, data)
                return f"✅ {len(new_rows)} unique row(s) inserted into '{table}'. Total rows: {len(data)}"

            # ---------------------
            # SELECT (with JOIN/WHERE/LIMIT) - IMPROVED WITH BETTER WHERE
            # ---------------------
            select_pattern = r"SELECT (.+?) FROM (\w+)(?:\s+JOIN\s+(\w+)\s+ON\s+(.+?))?(?:\s+WHERE\s+(.+?))?(?:\s+LIMIT\s+(\d+))?$"
            if match := re.match(select_pattern, sql, re.I):
                cols, table, join_table, join_cond, where, limit = match.groups()
                
                # Check if table exists
                if not os.path.exists(os.path.join(self.project_path, f"{table}{TABLE_EXT}")):
                    available_tables = self.list_tables()
                    return f"❌ Table '{table}' not found. Available tables: {available_tables}"
                
                data = self._read_table(table)

                # JOIN processing
                if join_table and join_cond:
                    # Check if join table exists
                    if not os.path.exists(os.path.join(self.project_path, f"{join_table}{TABLE_EXT}")):
                        return f"❌ Join table '{join_table}' not found."
                    
                    try:
                        right_data = self._read_table(join_table)
                        left_key, right_key = self._parse_join_condition(join_cond)
                        
                        joined = []
                        for left_row in data:
                            for right_row in right_data:
                                # Convert to string for comparison to handle different data types
                                left_val = str(left_row.get(left_key, ""))
                                right_val = str(right_row.get(right_key, ""))
                                if left_val == right_val and left_val:  # Ensure non-empty match
                                    # Merge rows with prefix handling
                                    merged_row = left_row.copy()
                                    # Add right table data with table prefix to avoid conflicts
                                    for k, v in right_row.items():
                                        merged_row[f"{join_table}.{k}"] = v
                                    joined.append(merged_row)
                        data = joined
                    except Exception as e:
                        return f"❌ JOIN error: {e}"

                # WHERE processing - IMPROVED WITH OPERATORS AND TABLE PREFIX SUPPORT
                if where:
                    conditions = self._parse_where_conditions_advanced(where)
                    if conditions:
                        filtered_data = []
                        for row in data:
                            match_all = True
                            for key, operator, value in conditions:
                                # Handle table-prefixed columns in WHERE clause (e.g., jobs.salary)
                                actual_value = row.get(key)
                                if actual_value is None and '.' not in key and join_table:
                                    # Try with table prefix for join queries
                                    prefixed_key = f"{join_table}.{key}"
                                    actual_value = row.get(prefixed_key)
                                
                                if not self._compare_values(actual_value, value, operator):
                                    match_all = False
                                    break
                            if match_all:
                                filtered_data.append(row)
                        data = filtered_data
                    else:
                        # Fallback to simple equals parsing
                        filters = self._parse_where_conditions(where)
                        data = [r for r in data if all(str(r.get(k, "")) == v for k, v in filters.items())]

                # COLUMNS processing
                if cols.strip() != "*":
                    selected_cols = self._parse_select_columns(cols, table, join_table)
                    processed_data = []
                    
                    for row in data:
                        new_row = {}
                        for col in selected_cols:
                            if isinstance(col, tuple):  # table.column format
                                table_name, col_name = col
                                # Look for prefixed column first, then regular column
                                prefixed_key = f"{table_name}.{col_name}"
                                if prefixed_key in row:
                                    new_row[prefixed_key] = row[prefixed_key]
                                elif col_name in row:
                                    new_row[col_name] = row[col_name]
                            else:  # simple column name
                                if col in row:
                                    new_row[col] = row[col]
                        processed_data.append(new_row)
                    data = processed_data

                # LIMIT processing
                if limit:
                    data = data[:int(limit)]

                return data if data else "⚠️ No data found matching the criteria."

            # ---------------------
            # UPDATE - IMPROVED ERROR MESSAGES
            # ---------------------
            if match := re.match(r"UPDATE (\w+) SET (.+?) WHERE (.+)", sql, re.I):
                table, set_part, where = match.groups()
                
                if not os.path.exists(os.path.join(self.project_path, f"{table}{TABLE_EXT}")):
                    available_tables = self.list_tables()
                    return f"❌ Table '{table}' not found. Available tables: {available_tables}"
                
                data = self._read_table(table)
                
                updates = self._parse_set_clause(set_part)
                conditions = self._parse_where_conditions_advanced(where)
                
                updated = 0
                for r in data:
                    match_all = True
                    for key, operator, value in conditions:
                        actual_value = r.get(key)
                        if not self._compare_values(actual_value, value, operator):
                            match_all = False
                            break
                    
                    if match_all:
                        # Check if update columns exist in table
                        meta = self._read_metadata(table)
                        if meta:
                            valid_cols = set(meta.get("columns", []))
                            invalid_update_cols = set(updates.keys()) - valid_cols
                            if invalid_update_cols:
                                return f"❌ Cannot update non-existent columns: {list(invalid_update_cols)}. Valid columns: {list(valid_cols)}"
                        
                        r.update(updates)
                        updated += 1
                
                self._write_table(table, data)
                return f"✅ {updated} row(s) updated in '{table}'."

            # ---------------------
            # DELETE - IMPROVED ERROR MESSAGES
            # ---------------------
            delete_pattern = r"DELETE FROM (\w+)(?:\s+WHERE\s+(.+))?"
            if match := re.match(delete_pattern, sql, re.I):
                table, where = match.groups()
                
                if not os.path.exists(os.path.join(self.project_path, f"{table}{TABLE_EXT}")):
                    available_tables = self.list_tables()
                    return f"❌ Table '{table}' not found. Available tables: {available_tables}"
                
                data = self._read_table(table)
                
                if not where:
                    count = len(data)
                    self._write_table(table, [])
                    return f"🗑️ {count} row(s) deleted from '{table}'."
                
                conditions = self._parse_where_conditions_advanced(where)
                before = len(data)
                
                if conditions:
                    data = [r for r in data if not all(
                        self._compare_values(r.get(key), value, operator) 
                        for key, operator, value in conditions
                    )]
                else:
                    # Fallback to simple equals
                    conds = self._parse_where_conditions(where)
                    data = [r for r in data if not all(str(r.get(k, "")) == v for k, v in conds.items())]
                
                deleted = before - len(data)
                self._write_table(table, data)
                return f"🗑️ {deleted} row(s) deleted from '{table}'."

            # ---------------------
            # DROP TABLE - IMPROVED ERROR MESSAGES
            # ---------------------
            if match := re.match(r"DROP TABLE (\w+)", sql, re.I):
                table = match.group(1)
                table_path = os.path.join(self.project_path, f"{table}{TABLE_EXT}")
                meta_path = table_path + ".meta"
                
                if not os.path.exists(table_path):
                    available_tables = self.list_tables()
                    return f"❌ Table '{table}' does not exist. Available tables: {available_tables}"
                
                try:
                    os.remove(table_path)
                    if os.path.exists(meta_path):
                        os.remove(meta_path)
                    return f"✅ Table '{table}' dropped successfully."
                except Exception as e:
                    return f"❌ Error dropping table '{table}': {e}"

            return "⚠️ Invalid or unsupported SQL syntax. Supported commands: CREATE TABLE, INSERT INTO, SELECT, UPDATE, DELETE, DROP TABLE"

        except Exception as e:
            return f"⚠️ Error executing SQL: {e}"

    # -----------------------------
    # Utility Methods
    # -----------------------------
    def list_tables(self) -> List[str]:
        """List all tables in the database."""
        tables = []
        if os.path.exists(self.project_path):
            for file in os.listdir(self.project_path):
                if file.endswith(TABLE_EXT) and not file.endswith(".meta"):
                    tables.append(file[:-len(TABLE_EXT)])
        return tables

    def table_info(self, table: str) -> Optional[Dict[str, Any]]:
        """Get information about a table."""
        meta = self._read_metadata(table)
        if not meta:
            return None
        
        data = self._read_table(table)
        return {
            "columns": meta.get("columns", []),
            "row_count": len(data),
            "storage": self.storage
        }