import mysql.connector
import csv
import json
from datetime import datetime
from pathlib import Path

def clean_record(record):
    # Limpieza simple de ejemplo
    try:
        if record.get("quantity", 0) < 0:
            record["quantity"] = 0
        if "name" in record and record["name"] is not None:
            record["name"] = record["name"].strip().title()
        else:
            record["name"] = ""
    except Exception:
        # Si algo sale mal en limpieza, devolvemos el registro tal cual
        pass
    return record

def main():
    # Conexión a MySQL
    conn = mysql.connector.connect(
        host="localhost", user="root", password="Mariana1.", database="gym_inventory"
    )
    cursor = conn.cursor(dictionary=True)

    cursor.execute("SELECT * FROM inventory_raw")
    raw_data = cursor.fetchall()

    cleaned_data = [clean_record(dict(row)) for row in raw_data]

    # Rutas de backups en la RAÍZ del proyecto (gym_inventory_project_improved/backups)
    project_root = Path(__file__).resolve().parents[2]
    backups_dir = project_root / "backups"
    backups_dir.mkdir(parents=True, exist_ok=True)

    timestamp = datetime.now().strftime("%Y%m%d%H%M%S")

    # Backups: si no hay datos, igual generamos headers vacíos correctos
    raw_csv = backups_dir / f"raw_{timestamp}.csv"
    cleaned_csv = backups_dir / f"cleaned_{timestamp}.csv"
    log_json = backups_dir / f"log_{timestamp}.json"

    # RAW
    with raw_csv.open("w", newline="", encoding="utf-8") as raw_file:
        if raw_data:
            writer = csv.DictWriter(raw_file, fieldnames=list(raw_data[0].keys()))
            writer.writeheader()
            writer.writerows(raw_data)
        else:
            writer = csv.DictWriter(raw_file, fieldnames=["id", "name", "quantity"])
            writer.writeheader()

    # CLEANED
    with cleaned_csv.open("w", newline="", encoding="utf-8") as clean_file:
        if cleaned_data:
            writer = csv.DictWriter(clean_file, fieldnames=list(cleaned_data[0].keys()))
            writer.writeheader()
            writer.writerows(cleaned_data)
        else:
            writer = csv.DictWriter(clean_file, fieldnames=["id", "name", "quantity"])
            writer.writeheader()

    # Insertar en tabla CLEANED (truncate lógico)
    cursor.execute("DELETE FROM inventory_cleaned")
    for item in cleaned_data:
        cursor.execute(
            "INSERT INTO inventory_cleaned (id, name, quantity) VALUES (%s, %s, %s)",
            (item.get("id"), item.get("name"), item.get("quantity")),
        )

    # Log
    log = {
        "timestamp": timestamp,
        "records_read": len(raw_data),
        "records_cleaned": len(cleaned_data),
        "raw_backup": str(raw_csv),
        "cleaned_backup": str(cleaned_csv),
    }
    with log_json.open("w", encoding="utf-8") as log_file:
        json.dump(log, log_file, indent=4, ensure_ascii=False)

    conn.commit()
    cursor.close()
    conn.close()

if __name__ == "__main__":
    main()
