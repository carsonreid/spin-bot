from typing import List, Optional

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field

from src.core.db import get_db

router = APIRouter(prefix="/selections", tags=["selections"])


class SelectionCreate(BaseModel):
    class_name: str = Field(..., min_length=1, max_length=200)
    studio_name: Optional[str] = Field(default=None, max_length=200)
    weekday: int = Field(..., ge=0, le=6, description="0=Monday .. 6=Sunday")
    start_time: str = Field(
        ..., pattern=r"^\d{2}:\d{2}$", description="24-hour format HH:MM"
    )
    week_offset: int = Field(default=1, ge=0, le=8)
    active: bool = True
    notes: Optional[str] = Field(default=None, max_length=500)


class SelectionUpdate(BaseModel):
    class_name: Optional[str] = Field(default=None, min_length=1, max_length=200)
    studio_name: Optional[str] = Field(default=None, max_length=200)
    weekday: Optional[int] = Field(default=None, ge=0, le=6)
    start_time: Optional[str] = Field(default=None, pattern=r"^\d{2}:\d{2}$")
    week_offset: Optional[int] = Field(default=None, ge=0, le=8)
    active: Optional[bool] = None
    notes: Optional[str] = Field(default=None, max_length=500)


class SelectionOut(BaseModel):
    id: int
    class_name: str
    studio_name: Optional[str]
    weekday: int
    start_time: str
    week_offset: int
    active: bool
    notes: Optional[str]
    created_at: str
    updated_at: str


def _row_to_selection(row) -> SelectionOut:
    return SelectionOut(
        id=row["id"],
        class_name=row["class_name"],
        studio_name=row["studio_name"],
        weekday=row["weekday"],
        start_time=row["start_time"],
        week_offset=row["week_offset"],
        active=bool(row["active"]),
        notes=row["notes"],
        created_at=row["created_at"],
        updated_at=row["updated_at"],
    )


@router.get("", response_model=List[SelectionOut])
def list_selections(active_only: bool = Query(default=False)) -> List[SelectionOut]:
    query = "SELECT * FROM booking_selections"
    params = []
    if active_only:
        query += " WHERE active = ?"
        params.append(1)
    query += " ORDER BY weekday ASC, start_time ASC, id ASC"

    with get_db() as conn:
        rows = conn.execute(query, params).fetchall()
    return [_row_to_selection(row) for row in rows]


@router.post("", response_model=SelectionOut, status_code=201)
def create_selection(selection: SelectionCreate) -> SelectionOut:
    with get_db() as conn:
        cursor = conn.execute(
            """
            INSERT INTO booking_selections
                (class_name, studio_name, weekday, start_time, week_offset, active, notes)
            VALUES
                (?, ?, ?, ?, ?, ?, ?)
            """,
            (
                selection.class_name,
                selection.studio_name,
                selection.weekday,
                selection.start_time,
                selection.week_offset,
                int(selection.active),
                selection.notes,
            ),
        )
        conn.commit()
        row = conn.execute(
            "SELECT * FROM booking_selections WHERE id = ?", (cursor.lastrowid,)
        ).fetchone()
    return _row_to_selection(row)


@router.put("/{selection_id}", response_model=SelectionOut)
def update_selection(selection_id: int, update: SelectionUpdate) -> SelectionOut:
    fields = update.model_dump(exclude_unset=True)
    if not fields:
        raise HTTPException(status_code=400, detail="No fields provided to update")

    set_parts = []
    params = []
    for key, value in fields.items():
        if key == "active":
            value = int(value)
        set_parts.append(f"{key} = ?")
        params.append(value)

    set_parts.append("updated_at = CURRENT_TIMESTAMP")
    params.append(selection_id)

    with get_db() as conn:
        existing = conn.execute(
            "SELECT id FROM booking_selections WHERE id = ?", (selection_id,)
        ).fetchone()
        if not existing:
            raise HTTPException(status_code=404, detail="Selection not found")

        conn.execute(
            f"UPDATE booking_selections SET {', '.join(set_parts)} WHERE id = ?",
            params,
        )
        conn.commit()
        row = conn.execute(
            "SELECT * FROM booking_selections WHERE id = ?", (selection_id,)
        ).fetchone()

    return _row_to_selection(row)


@router.delete("/{selection_id}", status_code=204)
def delete_selection(selection_id: int) -> None:
    with get_db() as conn:
        cursor = conn.execute(
            "DELETE FROM booking_selections WHERE id = ?", (selection_id,)
        )
        conn.commit()
    if cursor.rowcount == 0:
        raise HTTPException(status_code=404, detail="Selection not found")
