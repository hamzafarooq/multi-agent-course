import psycopg2
from tabulate import tabulate

def display_users():
    try:
        # 1. Connect to your PostgreSQL database
        conn = psycopg2.connect(
            dbname="toolbox_db",
            user="toolbox_user",
            password="mysecretpassword",
            host="127.0.0.1",
            port="5432"
        )
        cur = conn.cursor()

        # 2. Execute the query
        query = "SELECT user_id, email, full_name FROM users;"
        cur.execute(query)
        
        # 3. Fetch data and column names
        rows = cur.fetchall()
        headers = [desc[0] for desc in cur.description]

        # 4. Print using tabulate
        # print("\n--- CUSTOMER DATA REPORT ---\n")
        print(tabulate(rows, headers=headers, tablefmt="grid"))
        # print(f"\nTotal Records: {len(rows)}\n")

        cur.close()
        conn.close()

    except Exception as e:
        print(f"Error: {e}")

def greet_user(user_id):
    try:
        # 1. Connect to your PostgreSQL database
        conn = psycopg2.connect(
            dbname="toolbox_db",
            user="toolbox_user",
            password="mysecretpassword",
            host="127.0.0.1",
            port="5432"
        )
        cur = conn.cursor()
        query = "SELECT full_name, email, is_premium_customer, total_items_purchased FROM users WHERE user_id = %s;"
        cur.execute(query, (user_id,))
        row = cur.fetchone()
        if row[2]:
            return f"Agent: Hello {row[0]}! Welcome to the Customer Support Assistant. How can I help you today? You are a premium customer and have {row[3]} items purchased."
        else:
            return f"Agent: Hello {row[0]}! Welcome to the Customer Support Assistant. How can I help you today?"

    except Exception as e:
        return f"Error: {e}"
    finally:
        cur.close()
        conn.close()


def authenticate_user(email: str, password: str):
    """Authenticate a user by email and password stored in the users table."""
    try:
        conn = psycopg2.connect(
            dbname="toolbox_db",
            user="toolbox_user",
            password="mysecretpassword",
            host="127.0.0.1",
            port="5432",
        )
        cur = conn.cursor()
        query = """
            SELECT user_id, full_name, email, is_premium_customer, total_items_purchased
            FROM users
            WHERE email = %s AND password = %s;
        """
        cur.execute(query, (email, password))
        row = cur.fetchone()
        if not row:
            return None

        return {
            "user_id": row[0],
            "full_name": row[1],
            "email": row[2],
            "is_premium_customer": row[3],
            "total_items_purchased": row[4],
        }
    except Exception:
        return None
    finally:
        try:
            cur.close()
            conn.close()
        except Exception:
            pass


def get_user_actions(email: str):
    """Fetch all actions from actions_log for the given user email.
    Returns a list of dicts with keys: id, timestamp, action_type, parameters.
    Returns empty list on error or if table does not exist.
    """
    try:
        conn = psycopg2.connect(
            dbname="toolbox_db",
            user="toolbox_user",
            password="mysecretpassword",
            host="127.0.0.1",
            port="5432",
        )
        cur = conn.cursor()
        query = """
            SELECT id, timestamp, action_type, parameters
            FROM actions_log
            WHERE user_email = %s
            ORDER BY timestamp DESC;
        """
        cur.execute(query, (email,))
        rows = cur.fetchall()
        cols = [desc[0] for desc in cur.description]
        result = [dict(zip(cols, row)) for row in rows]
        cur.close()
        conn.close()
        return result
    except Exception:
        return []

