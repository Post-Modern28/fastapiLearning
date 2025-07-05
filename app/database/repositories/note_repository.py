import asyncpg

class NoteRepository:
    def __init__(self, db: asyncpg.Connection):
        self.db = db

    async def create_note(self, title: str, description: str, user_id: int):
        return await self.db.fetchrow(
            """
            INSERT INTO ThingsToDo(title, description, user_id)
            VALUES ($1, $2, $3)
            RETURNING *
            """,
            title, description, user_id
        )

    async def delete_note(self, note_id: int):
        return await self.db.execute(
            "DELETE FROM ThingsToDo WHERE id = $1", note_id
        )

    async def get_note_owner(self, note_id: int) -> int:
        row = await self.db.fetchrow(
            "SELECT user_id FROM ThingsToDo WHERE id = $1",
            note_id,
        )
        if row is None:
            return -1
            # raise HTTPException(status_code=404, detail="Note not found")
        return row["user_id"]