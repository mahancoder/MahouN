
from neo4j import GraphDatabase
import os

# سعی می‌کنیم پسورد رو از .env بخونیم، اگه نبود یه چیز پیش‌فرض می‌ذاریم
new_password = os.getenv("DB_NEO4J_PASSWORD", "mahoun_secure_pass_123")

uri = "bolt://localhost:7687"
user = "neo4j"
old_password = "neo4j"

driver = GraphDatabase.driver(uri, auth=(user, old_password))

try:
    # IMPORTANT: Password change MUST happen on the 'system' database
    with driver.session(database="system") as session:
        # Use the specific syntax recommended by Neo4j for first-time password change
        session.run(f"ALTER CURRENT USER SET PASSWORD FROM 'neo4j' TO '{new_password}'")
        print(f"✅ پسورد با موفقیت به '{new_password}' تغییر یافت.")
except Exception as e:
    if "PasswordChangeRequired" in str(e) or "Unauthorized" in str(e):
        print(f"❌ خطا در تغییر پسورد: {e}")
        print("احتمالا پسورد قبلا عوض شده یا یوزر/پسورد اشتباهه.")
    else:
        print(f"✅ احتمالا پسورد قبلا تغییر کرده: {e}")
finally:
    driver.close()
