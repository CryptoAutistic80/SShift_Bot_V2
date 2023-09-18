import aiosqlite

# Define the path for the SQLite database
db_path = "database/database69.db"

async def initialize_db():
    """Initialize the database and create tables if they don't exist."""
    try:
        async with aiosqlite.connect(db_path) as db:
            cursor = await db.cursor()
            await cursor.execute("""
                CREATE TABLE IF NOT EXISTS guild_memberships (
                    guild_id TEXT PRIMARY KEY NOT NULL,
                    guild_name TEXT,
                    membership_type TEXT NOT NULL,
                    expiry_date DATETIME
                );
            """)
            
            await cursor.execute("""
                CREATE TABLE IF NOT EXISTS guild_settings (
                    guild_id TEXT PRIMARY KEY NOT NULL,
                    verify_channel TEXT,
                    verified_role TEXT,
                    FOREIGN KEY (guild_id) REFERENCES guild_memberships(guild_id)
                );
            """)
            await db.commit()
    except aiosqlite.Error as e:
        print(f"Database error: {e}")

#####################
# Guild Memberships #
#####################

async def add_guild(guild_id, guild_name, membership_type, expiry_date):
    """Insert a new guild membership into the database or return an error if it already exists."""
    try:
        async with aiosqlite.connect(db_path) as db:
            cursor = await db.cursor()
            
            # Check if the guild_id already exists in the database
            await cursor.execute("SELECT 1 FROM guild_memberships WHERE guild_id = ?", (guild_id,))
            existing_guild = await cursor.fetchone()
            
            if existing_guild:
                return "Guild already exists in the database"
            
            # Insert the new guild membership
            await cursor.execute(
                "INSERT INTO guild_memberships (guild_id, guild_name, membership_type, expiry_date) VALUES (?, ?, ?, ?)", 
                (guild_id, guild_name, membership_type, expiry_date))
            await db.commit()
            return "Guild successfully added to the database"
    except aiosqlite.Error as e:
        return f"Database error: {e}"

async def remove_guild(guild_id):
    """Remove a guild membership from the database based on the guild_id and return feedback on the operation."""
    try:
        async with aiosqlite.connect(db_path) as db:
            cursor = await db.cursor()
            await cursor.execute("DELETE FROM guild_memberships WHERE guild_id = ?", (guild_id,))
            
            # Check if any row was deleted without using await
            changes = db.total_changes
            await db.commit()
            
            if changes > 0:
                return "Guild successfully removed from the database"
            else:
                return "Guild not found in the database"
    except aiosqlite.Error as e:
        return f"Database error: {e}"

async def edit_guild(guild_id, membership_type, expiry_date):
    """Update an existing guild membership's details based on the guild_id."""
    try:
        async with aiosqlite.connect(db_path) as db:
            cursor = await db.cursor()
            await cursor.execute(
                "UPDATE guild_memberships SET membership_type = ?, expiry_date = ? WHERE guild_id = ?", 
                (membership_type, expiry_date, guild_id))
            await db.commit()
    except aiosqlite.Error as e:
        print(f"Database error: {e}")

async def retrieve_guild_membership(guild_id):
    """Retrieve all guild membership details from the database based on the guild_id."""
    try:
        async with aiosqlite.connect(db_path) as db:
            cursor = await db.cursor()
            await cursor.execute("SELECT * FROM guild_memberships WHERE guild_id = ?", (guild_id,))
            membership_details = await cursor.fetchone()
            if membership_details:
                return {
                    "guild_name": membership_details[1],
                    "guild_id": membership_details[0],
                    "membership_type": membership_details[2],
                    "expiry_date": membership_details[3]
                }
            return None
    except aiosqlite.Error as e:
        print(f"Database error: {e}")

########################
# Verification Channel #
########################

async def add_verification(guild_id, verify_channel, verified_role):
    """Insert or update a verification setting into the database."""
    try:
        async with aiosqlite.connect(db_path) as db:
            cursor = await db.cursor()
            
            # Check if the guild_id exists in the guild_memberships table
            await cursor.execute("SELECT 1 FROM guild_memberships WHERE guild_id = ?", (guild_id,))
            existing_guild = await cursor.fetchone()
            
            if not existing_guild:
                return "Guild does not have a membership entry, setup cannot proceed."
            
            # Insert or replace the guild settings based on the guild_id
            await cursor.execute("""
                INSERT OR REPLACE INTO guild_settings 
                (guild_id, verify_channel, verified_role) 
                VALUES (?, ?, ?)
            """, (guild_id, verify_channel, verified_role))
            
            await db.commit()
    except aiosqlite.Error as e:
        return f"Database error: {e}"

async def delete_verification(guild_id):
    """Remove a verification setting from the database based on the guild_id."""
    try:
        async with aiosqlite.connect(db_path) as db:
            cursor = await db.cursor()
            await cursor.execute("DELETE FROM guild_settings WHERE guild_id = ?", (guild_id,))
            changes = db.total_changes
            await db.commit()
            if changes > 0:
                return "Verification setting successfully removed from the database"
            else:
                return "Verification setting not found in the database"
    except aiosqlite.Error as e:
        return f"Database error: {e}"
      
async def retrieve_verification(guild_id):
    """Retrieve the verification settings for a specified guild_id from the database."""
    try:
        async with aiosqlite.connect(db_path) as db:
            cursor = await db.cursor()
            await cursor.execute("SELECT verify_channel, verified_role FROM guild_settings WHERE guild_id = ?", (guild_id,))
            verification_details = await cursor.fetchone()
            if verification_details:
                return {
                    "verify_channel": verification_details[0],
                    "verified_role": verification_details[1]
                }
            else:
                return None
    except aiosqlite.Error as e:
        return None

