import asyncpg


class NoteRepository:
    def __init__(self, db: asyncpg.Connection):
        self.db = db

    async def create_note(self, title: str, description: str, user_id: int):
        return await self.db.fetchrow(
            """
            INSERT INTO things_to_do(title, description, user_id)
            VALUES ($1, $2, $3)
            RETURNING *
            """,
            title,
            description,
            user_id,
        )

    async def get_user_notes(self, user_id: int):
        return await self.db.fetch(
            """
            SELECT * 
            FROM things_to_do
            WHERE user_id = $1
            """,
            user_id,
        )

    async def get_filtered_notes(self, query: str, params: list):
        return await self.db.fetch(query, *params)

    async def get_note_by_id(self, note_id: int):
        return await self.db.fetchrow(
            "SELECT * FROM things_to_do WHERE id = $1", note_id
        )

    async def delete_note(self, note_id: int):
        return await self.db.execute("DELETE FROM things_to_do WHERE id = $1", note_id)

    async def update_note(
        self, note_id: int, title: str, description: str, completed: bool
    ):
        return await self.db.execute(
            """
            UPDATE things_to_do
            SET title = $1, description = $2, completed=$3
            WHERE id = $4
            """,
            title,
            description,
            completed,
            note_id,
        )

    async def bulk_complete(self, note_ids: list[int], completed: bool):
        return await self.db.execute(
            """
            UPDATE things_to_do
            SET completed = $1,
                completed_at = CASE WHEN $1 THEN CURRENT_TIMESTAMP ELSE NULL END
            WHERE id = ANY($2::int[])
            """,
            completed,
            note_ids,
        )

    async def get_analytics(self, timezone: str):
        total = await self.db.fetchval("SELECT COUNT(*) FROM things_to_do")
        status_counts = await self.db.fetch(
            "SELECT completed, COUNT(*) as count FROM things_to_do GROUP BY completed"
        )
        avg_time = await self.db.fetchval(
            """
            SELECT AVG(EXTRACT(EPOCH FROM (completed_at - created_at)) / 3600) 
            FROM things_to_do
            WHERE completed = true
            """
        )
        weekday_raw = await self.db.fetch(
            """
            SELECT
                to_char(created_at AT TIME ZONE $1, 'Day') as weekday,
                EXTRACT(DOW FROM created_at AT TIME ZONE $1) as dow,
                COUNT(*) as count
            FROM things_to_do
            GROUP BY weekday, dow
            ORDER BY dow
            """,
            timezone,
        )
        return total, status_counts, avg_time, weekday_raw

    async def get_note_owner(self, note_id: int) -> int:
        row = await self.db.fetchrow(
            "SELECT user_id FROM things_to_do WHERE id = $1",
            note_id,
        )
        if row is None:
            return -1
        return row["user_id"]
