import sys, os
sys.path.append(os.path.abspath("."))
from src.database.db import _connect

with _connect() as conn:
    conn.execute("DELETE FROM optimization_runs")
    conn.commit()
print("optimization_runs table cleared.")