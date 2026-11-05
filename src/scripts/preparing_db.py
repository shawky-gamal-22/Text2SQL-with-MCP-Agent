import pathlib
import requests
import sqlite3

from config.settings import get_settings


def downloading_data():
    url = "https://storage.googleapis.com/benchmarks-artifacts/chinook/Chinook.db"
    local_path = pathlib.Path(get_settings().DB_PATH)

    if local_path.exists():
        print(f"{local_path} already exists, skipping download.")
    else:
        response = requests.get(url, timeout=60)
        if response.status_code == 200:
            local_path.write_bytes(response.content)
            print(f"File downloaded and saved as {local_path}")
        else:
            print(f"Failed to download file. Status code: {response.status_code}")


def main():
    downloading_data()

    con = sqlite3.connect(get_settings().DB_PATH)
    cursor = con.cursor()

    cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
    tables = [row[0] for row in cursor.fetchall() if not row[0].startswith("sqlite_")]

    print("Dialect: sqlite")
    print(f"Available tables: {tables}")

    cursor.execute("SELECT * FROM Artist LIMIT 5;")
    print(f"Sample output: {cursor.fetchall()}")
    con.close()


if __name__ == "__main__":
    main()
