from redis import Redis
import uuid
from fastapi import FastAPI, Request
from fastapi.responses import StreamingResponse
from typing import AsyncGenerator
import asyncio
import json

from fastapi.middleware.cors import CORSMiddleware
from typing import Optional, Dict
import aiosqlite
from datetime import datetime, timedelta
import re

app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],  # Your React app's URL
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

redis_client = Redis(host='localhost', port=6379, db=0)

from dataclasses import dataclass
@dataclass
class TreeNode:
    song: dict
    left: Optional['TreeNode'] = None
    right: Optional['TreeNode'] = None

class SessionManager:
    def __init__(self, redis_client):
        self.redis = redis_client
        self.expire_time = 3600  # 1 hour

    async def create_session(self, search_id: str, artist: str, tree: TreeNode):
        session_data = {
            "artist": artist,
            "tree": self._serialize_tree(tree),
            # "current_path": [],
            # "vote_history": []
        }
        self.redis.setex(
            f"session:{search_id}",
            self.expire_time,
            json.dumps(session_data)
        )

    async def get_session(self, search_id: str) -> Optional[dict]:
        """Retrieve session data from Redis"""
        data = self.redis.get(f"session:{search_id}")
        if not data:
            return None
        return json.loads(data)

    async def update_session(self, search_id: str, session_data: dict):
        """Update session data in Redis"""
        self.redis.setex(
            f"session:{search_id}",
            self.expire_time,
            json.dumps(session_data)
        )
    def _serialize_tree(self, node: TreeNode) -> Optional[dict]:
        if node is None:
            return None
        return {
            "song": node.song,
            "left": self._serialize_tree(node.left) if node.left else None,
            "right": self._serialize_tree(node.right) if node.right else None
        }

    async def get_current_song(self, search_id: str, vote_history: list) -> Optional[ dict ]:
        session_data = json.loads(self.redis.get(f"session:{search_id}"))
        node = session_data["tree"]

        # Navigate to current position in tree
        for vote in vote_history:
            node = node["right"] if vote else node["left"]
            if node is None:
                return None

        return node["song"]

session_manager = SessionManager(redis_client)

async def create_decision_tree(artist_name: str) -> TreeNode:
    """Create decision tree based on artist's songs"""
    table_name = await sanitize_table_name(artist_name)

    async with aiosqlite.connect('songs.db') as db:
        # Get all songs for artist
        cursor = await db.execute(f'SELECT * FROM {table_name}')
        songs = await cursor.fetchall()

        # For now, create mock tree structure
        # Later, implement actual recommendation logic here
        return create_mock_decision_tree(artist_name=artist_name)

# Add these utility functions
async def sanitize_table_name(artist_name: str) -> str:
    """Convert artist name to valid table name"""
    # Remove special characters, replace spaces with underscore
    safe_name = re.sub(r'[^\w\s-]', '', artist_name.lower())
    return f"songs_{safe_name.replace(' ', '_')}"

async def init_db():
    """Initialize the database with artists table"""
    async with aiosqlite.connect('songs.db') as db:
        await db.execute('''
            CREATE TABLE IF NOT EXISTS artists (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT UNIQUE,
                table_name TEXT UNIQUE,
                last_updated TIMESTAMP
            )
        ''')
        await db.commit()

# Add to FastAPI app
@app.on_event("startup")
async def startup_event():
    await init_db()

async def ensure_artist_table(db, artist_name: str, table_name: str):
    """Create artist-specific table if it doesn't exist"""
    await db.execute(f'''
        CREATE TABLE IF NOT EXISTS {table_name} (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT,
            spotify_id TEXT UNIQUE,
            album TEXT,
            popularity INTEGER
        )
    ''')
    await db.commit()


def create_mock_decision_tree(artist_name: str) -> TreeNode:
    """Create a mock decision tree 5 levels deep"""
    return TreeNode(
        song={"title": "Root Song", "artist": artist_name, "id": "1"},
        left=TreeNode(
            song={"title": "No Song 1", "artist": artist_name, "id": "2"},
            left=TreeNode(song={"title": "No-No Song", "artist": artist_name, "id": "4"}),
            right=TreeNode(song={"title": "No-Yes Song", "artist": artist_name, "id": "5"})
        ),
        right=TreeNode(
            song={"title": "Yes Song 1", "artist": artist_name, "id": "3"},
            left=TreeNode(song={"title": "Yes-No Song", "artist": artist_name, "id": "6"}),
            right=TreeNode(song={"title": "Yes-Yes Song", "artist": artist_name, "id": "7"})
        )
    )

def get_next_song(tree: TreeNode, vote_history: list) -> Optional[dict]:
    """Navigate tree based on vote history"""
    current = tree
    for vote in vote_history:
        if vote:
            current = current.right
        else:
            current = current.left
        if current is None:
            return None
    return current.song

# Store active searches (in a real app, use Redis or another suitable database)
active_searches = {}

async def check_artist_status(artist_name: str, debug: bool = False) -> tuple[bool, str]:
    """
    Check if we need to update songs for this artist
    Returns: (needs_update, table_name)
    """
    table_name = await sanitize_table_name(artist_name)

    async with aiosqlite.connect('songs.db') as db:
        cursor = await db.execute(
            'SELECT last_updated FROM artists WHERE name = ?',
            (artist_name,)
        )
        result = await cursor.fetchone()

        if result is None:
            # New artist - create entry and table
            await db.execute(
                'INSERT INTO artists (name, table_name, last_updated) VALUES (?, ?, ?)',
                (artist_name, table_name, datetime.now().isoformat())
            )
            await ensure_artist_table(db, artist_name, table_name)
            return True, table_name

        last_updated = datetime.fromisoformat(result[0])
        two_weeks_ago = datetime.now() - timedelta(weeks=2)

        return last_updated < two_weeks_ago, table_name

async def update_artist_songs(artist_name: str, songs: list):
    """Store or update songs for an artist"""
    table_name = await sanitize_table_name(artist_name)

    async with aiosqlite.connect('songs.db') as db:
        # Update last_updated timestamp
        await db.execute(
            'UPDATE artists SET last_updated = ? WHERE name = ?',
            (datetime.now().isoformat(), artist_name)
        )

        # Ensure table exists
        await ensure_artist_table(db, artist_name, table_name)

        # Clear existing songs (optional, depends on your update strategy)
        await db.execute(f'DELETE FROM {table_name}')

        # Insert new songs
        for song in songs:
            await db.execute(f'''
                INSERT OR REPLACE INTO {table_name}
                (title, spotify_id, album, popularity)
                VALUES (?, ?, ?, ?)
            ''', (
                song['title'],
                song.get('spotify_id'),
                song.get('album'),
                song.get('popularity', 0)
            ))

        await db.commit()


async def search_songs_for_artist(artist_name: str, debug = False) -> list:
    """Search for songs, updating database if necessary"""
    if debug:
        print(f"Checking artist status for {artist_name=}")
    needs_update, table_name = await check_artist_status(artist_name)
    if debug:
        print(f"Finished checking artist status for {artist_name=}")

    if needs_update:
        # In real implementation, call Spotify API here
        songs = [
            {
                "title": "Song 1",
                "spotify_id": "abc123",
                "album": "Album 1",
                "popularity": 75
            },
            {
                "title": "Song 2",
                "spotify_id": "def456",
                "album": "Album 1",
                "popularity": 80
            },
        ]
        await update_artist_songs(artist_name, songs)

    # Retrieve songs from database
    async with aiosqlite.connect('songs.db') as db:
        cursor = await db.execute(f'''
            SELECT title, spotify_id, album, popularity
            FROM {table_name}
        ''')

        rows = await cursor.fetchall()
        return [
            {
                "title": row[0],
                "spotify_id": row[1],
                "album": row[2],
                "popularity": row[3],
                "artist": artist_name
            }
            for row in rows
        ]


async def event_generator(search_id: str) -> AsyncGenerator[str, None]:
    """Generate SSE events"""
    debug = False
    try:
        # Send initial searching status
        yield f"data: {json.dumps({'status': 'searching', 'progress': 0})}\n\n"
        if debug:
            print("Yielded intitial response")

        # Process artist and create decision tree
        artist_name = active_searches[search_id]['artist']
        await search_songs_for_artist(artist_name,debug=True)  # Get/update songs in DB
        if debug:
            print(f"Finished searching songs for artist {artist_name=}")
        tree = await create_decision_tree(artist_name)  # Create recommendation tree
        if debug:
            print(f"Finished creating decision tree for {artist_name=}")

        # Store tree in Redis
        await session_manager.create_session(search_id, artist_name, tree)
        print(f"Created session in Redis for {search_id=} {artist_name=}")

        # Send completion status with first song
        yield f"data: {json.dumps({
            'status': 'completed',
            'song': tree.song
        })}\n\n"

    except Exception as e:
        yield f"data: {json.dumps({'status': 'error', 'message': str(e)})}\n\n"

    # Cleanup
    if search_id in active_searches:
        del active_searches[search_id]

active_sessions = {}

@app.post("/api/vote")
async def record_vote(request: Request):
    data = await request.json()
    artist_name = data['artist']
    vote_history = data['vote_history']

    # Create/get tree and navigate to next song
    tree = create_mock_decision_tree(artist_name)
    next_song = get_next_song(tree, vote_history)

    if next_song is None:
        return {"status": "complete"}

    return {
        "status": "continue",
        "song": next_song
    }

@app.post("/api/start-search")
async def start_search(request: Request):
    data = await request.json()
    search_id = str(uuid.uuid4())
    artist_name = data['artist']

    # Store in active_searches for SSE updates
    active_searches[search_id] = {'artist': artist_name}

    return {"searchId": search_id}

@app.get("/api/search-updates/{search_id}")
async def search_updates(search_id: str):
    if search_id not in active_searches:
        return {"error": "Search not found"}

    return StreamingResponse(
        event_generator(search_id),
        media_type="text/event-stream"
    )

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000, reload=True)
