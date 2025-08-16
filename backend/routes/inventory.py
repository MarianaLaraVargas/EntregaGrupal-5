# backend/routes/inventory.py
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, StringConstraints
from typing import Annotated, Optional
import os
import mysql.connector

router = APIRouter(prefix="/api", tags=["Inventory"])

# ---------- DB ----------
def get_db():
    return mysql.connector.connect(
        host=os.getenv("DB_HOST", "localhost"),
        user=os.getenv("DB_USER", "root"),
        password=os.getenv("DB_PASSWORD", ""),
        database=os.getenv("DB_NAME", "gym_inventory"),
        port=int(os.getenv("DB_PORT", "3306")),
    )

# ---------- Modelos (Pydantic v2) ----------
NameStr = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1, max_length=100)]

class RawItem(BaseModel):
    id: Optional[int] = None
    name: NameStr
    quantity: int

class RawItemUpdate(BaseModel):
    name: Optional[NameStr] = None
    quantity: Optional[int] = None

# ---------- Helpers ----------
def get_next_raw_id(conn) -> int:
    cur = conn.cursor()
    try:
        cur.execute("SELECT COALESCE(MAX(id), 0) + 1 FROM inventory_raw")
        return int(cur.fetchone()[0])
    finally:
        cur.close()

# ---------- Endpoints ----------
@router.get("/cleaned")
def get_cleaned_inventory():
    conn = get_db()
    try:
        cur = conn.cursor(dictionary=True)
        cur.execute("SELECT id, name, quantity FROM inventory_cleaned ORDER BY id")
        return cur.fetchall()
    finally:
        cur.close(); conn.close()

@router.get("/raw")
def get_raw_inventory():
    conn = get_db()
    try:
        cur = conn.cursor(dictionary=True)
        cur.execute("SELECT id, name, quantity FROM inventory_raw ORDER BY id")
        return cur.fetchall()
    finally:
        cur.close(); conn.close()

@router.post("/raw")
def add_raw(item: RawItem):
    """Inserta en inventory_raw. Si no viene 'id', calcula MAX(id)+1."""
    conn = get_db()
    try:
        cur = conn.cursor()
        new_id = item.id if item.id is not None else get_next_raw_id(conn)
        cur.execute(
            "INSERT INTO inventory_raw (id, name, quantity) VALUES (%s, %s, %s)",
            (new_id, item.name, item.quantity),
        )
        conn.commit()
        return {"id": new_id, "name": item.name, "quantity": item.quantity}
    except mysql.connector.errors.IntegrityError:
        raise HTTPException(status_code=409, detail=f"El id {item.id} ya existe.")
    except mysql.connector.Error as e:
        print("MySQL error on POST /api/raw:", e)
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        try: cur.close(); conn.close()
        except: pass

@router.put("/raw/{item_id}")
def update_raw(item_id: int, patch: RawItemUpdate):
    """Actualiza name/quantity del RAW. Permite actualización parcial."""
    if patch.name is None and patch.quantity is None:
        raise HTTPException(status_code=400, detail="No hay campos para actualizar.")

    conn = get_db()
    try:
        cur = conn.cursor()
        fields, values = [], []
        if patch.name is not None:
            fields.append("name=%s"); values.append(patch.name)
        if patch.quantity is not None:
            fields.append("quantity=%s"); values.append(patch.quantity)

        sql = f"UPDATE inventory_raw SET {', '.join(fields)} WHERE id=%s"
        values.append(item_id)
        cur.execute(sql, tuple(values))
        conn.commit()

        if cur.rowcount == 0:
            raise HTTPException(status_code=404, detail="Ítem no encontrado.")
        return {"id": item_id, "updated": True}
    except mysql.connector.Error as e:
        print("MySQL error on PUT /api/raw:", e)
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        try: cur.close(); conn.close()
        except: pass

@router.delete("/raw/{item_id}")
def delete_raw(item_id: int):
    conn = get_db()
    try:
        cur = conn.cursor()
        cur.execute("DELETE FROM inventory_raw WHERE id=%s", (item_id,))
        conn.commit()
        if cur.rowcount == 0:
            raise HTTPException(status_code=404, detail="Ítem no encontrado.")
        return {"id": item_id, "deleted": True}
    except mysql.connector.Error as e:
        print("MySQL error on DELETE /api/raw:", e)
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        try: cur.close(); conn.close()
        except: pass
