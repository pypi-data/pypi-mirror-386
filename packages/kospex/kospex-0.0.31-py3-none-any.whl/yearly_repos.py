#!/usr/bin/env python3
import sqlite3
import json
import sys
from concurrent.futures import ThreadPoolExecutor, ProcessPoolExecutor
from rich.console import Console
import kospex_utils as KospexUtils
from kospex_utils import KospexTimer

console = Console()

def create_memory_db_from_disk(disk_db_path):
    """Load disk database into memory"""
    # Connect to disk database
    disk_conn = sqlite3.connect(disk_db_path)

    # Create in-memory database
    memory_conn = sqlite3.connect(':memory:')

    # Copy schema and data
    disk_conn.backup(memory_conn)
    disk_conn.close()

    return memory_conn

def batch_process_all_developers(memory_conn):
    """Process all developers in batch"""
    # Get all unique emails
    emails_query = "SELECT DISTINCT author_email FROM commits"
    emails = [row[0] for row in memory_conn.execute(emails_query).fetchall()]

    results = {}
    stats_query = """
        SELECT
            CAST(strftime('%Y', author_when) AS INTEGER) AS year,
            COUNT(DISTINCT _repo_id) AS unique_repo_count
        FROM commits
        WHERE author_email = ?
        GROUP BY CAST(strftime('%Y', author_when) AS INTEGER)
        ORDER BY year
    """

    for email in emails:
        cursor = memory_conn.execute(stats_query, (email,))
        with KospexTimer("Processing all developers") as dev_timer:
            results[email] = cursor.fetchall()
        console.log(f"Processed {dev_timer} -- {email}")
        console.log(results[email])

    return results

if sys.argv[1]:
    print(f"{sys.argv[1]}")
    console.log("Starting developer analysis...")
    db_path = KospexUtils.get_kospex_db_path()
    console.log(f"Database path: {db_path}")
else:
    exit(1)


console.log("Starting developer analysis...")
db_path = KospexUtils.get_kospex_db_path()
console.log(f"Database path: {db_path}")

memdb = None
with KospexTimer("Loading database into memory db") as timed:
    memdb = create_memory_db_from_disk(db_path)
console.log(timed)

memdb = sqlite3.connect(db_path)

with KospexTimer("Processing all developers") as timed:
    results = batch_process_all_developers(memdb)
console.log(timed)

with open('developer_analysis_results.json', 'w') as f:
    json.dump(results, f)
