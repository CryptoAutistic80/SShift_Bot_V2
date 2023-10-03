import aiosqlite

# Define the path for the SQLite database
db_path = "database/database69.db"

async def initialize_db():
    try:
        async with aiosqlite.connect(db_path) as db:
            cursor = await db.cursor()
          
            #Check if the whitelist table exists and drop it
            #await cursor.execute("""
                #DROP TABLE IF EXISTS whitelist;
            #""")
            
            # Table for guild memberships
            await cursor.execute("""
                CREATE TABLE IF NOT EXISTS guild_memberships (
                    guild_id TEXT PRIMARY KEY NOT NULL,
                    guild_name TEXT,
                    membership_type TEXT NOT NULL,
                    expiry_date DATETIME
                );
            """)

            # Table for guild verifications
            await cursor.execute("""
                CREATE TABLE IF NOT EXISTS guild_verifications (
                    guild_id TEXT PRIMARY KEY NOT NULL,
                    verify_channel TEXT,
                    verified_role TEXT,
                    FOREIGN KEY (guild_id) REFERENCES guild_memberships(guild_id)
                );
            """)

            # Table for guild role reactions
            await cursor.execute("""
                CREATE TABLE IF NOT EXISTS guild_reactions (
                    reaction_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    guild_id TEXT NOT NULL,
                    reaction_channel TEXT,
                    emoji TEXT,
                    description TEXT,
                    role_id TEXT,
                    FOREIGN KEY (guild_id) REFERENCES guild_memberships(guild_id)
                );
            """)

            # New table for guild welcome messages
            await cursor.execute("""
                CREATE TABLE IF NOT EXISTS guild_welcome (
                    guild_id TEXT PRIMARY KEY NOT NULL,
                    channel_id TEXT,
                    message TEXT,
                    FOREIGN KEY (guild_id) REFERENCES guild_memberships(guild_id)
                );
            """)
          
            await cursor.execute("""
                CREATE TABLE IF NOT EXISTS whitelist (
                    WL_ID INTEGER PRIMARY KEY AUTOINCREMENT,
                    guild_id TEXT NOT NULL,
                    channel_id TEXT,
                    blockchain TEXT, 
                    wl_name TEXT,
                    supply INTEGER,
                    wl_description TEXT,
                    mint_sale_date TEXT,
                    type TEXT CHECK (type IN ('TOKEN', 'NFT')),
                    claim_all_roles TEXT CHECK (claim_all_roles IN ('YES', 'NO') OR claim_all_roles IS NULL),
                    token_role_1 TEXT,
                    token_role_2 TEXT DEFAULT NULL,
                    nft_role_mint_1 TEXT DEFAULT NULL,
                    nft_role_mint_2 TEXT DEFAULT NULL,
                    nft_role_mint_3 TEXT DEFAULT NULL,
                    expiry_date TEXT,
                    total_wl_spots INTEGER,
                    FOREIGN KEY (guild_id) REFERENCES guild_memberships(guild_id),
                    UNIQUE (WL_ID, guild_id, wl_name, type)
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
                INSERT OR REPLACE INTO guild_verifications 
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
            await cursor.execute("DELETE FROM guild_verifications WHERE guild_id = ?", (guild_id,))
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
            await cursor.execute("SELECT verify_channel, verified_role FROM guild_verifications WHERE guild_id = ?", (guild_id,))
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

########################
# Guild Role Reactions #
########################

# Add a reaction entry
async def upsert_reaction(guild_id, reaction_channel, emoji, description, role_id):
    try:
        async with aiosqlite.connect(db_path) as db:
            cursor = await db.cursor()
            await cursor.execute("""
                INSERT INTO guild_reactions 
                (guild_id, reaction_channel, emoji, description, role_id) 
                VALUES (?, ?, ?, ?, ?)
            """, (guild_id, reaction_channel, emoji, description, role_id))
            await db.commit()
    except aiosqlite.IntegrityError:
        return "An entry with these parameters already exists."
    except aiosqlite.Error as e:
        return f"Database error: {e}"


# Retrieve all reactions for a guild
async def retrieve_reactions(guild_id):
    try:
        async with aiosqlite.connect(db_path) as db:
            cursor = await db.cursor()
            await cursor.execute("SELECT reaction_channel, emoji, description, role_id FROM guild_reactions WHERE guild_id = ?", (guild_id,))
            reactions = await cursor.fetchall()
            return reactions
    except aiosqlite.Error as e:
        return None

# Delete all reactions for a guild
async def delete_reactions(guild_id):
    try:
        async with aiosqlite.connect(db_path) as db:
            cursor = await db.cursor()
            await cursor.execute("DELETE FROM guild_reactions WHERE guild_id = ?", (guild_id,))
            await db.commit()
    except aiosqlite.Error as e:
        return f"Database error: {e}" 


#########################
# Guild Welcome Message #
#########################

async def upsert_welcome_message(guild_id, channel_id, message):
    """
    Insert or update a welcome message into the database.
    If an entry with the given guild_id exists, it updates the existing entry.
    Otherwise, it inserts a new entry.
    """
    try:
        async with aiosqlite.connect(db_path) as db:
            cursor = await db.cursor()
            
            # Insert or replace the welcome message based on the guild_id
            await cursor.execute("""
                INSERT OR REPLACE INTO guild_welcome 
                (guild_id, channel_id, message) 
                VALUES (?, ?, ?)
            """, (guild_id, channel_id, message))
            
            await db.commit()
    except aiosqlite.Error as e:
        return f"Database error: {e}"

async def retrieve_welcome_message(guild_id):
    """Retrieve the welcome message settings for a specified guild_id from the database."""
    try:
        async with aiosqlite.connect(db_path) as db:
            cursor = await db.cursor()
            await cursor.execute("SELECT channel_id, message FROM guild_welcome WHERE guild_id = ?", (guild_id,))
            welcome_details = await cursor.fetchone()
            if welcome_details:
                return {
                    "channel_id": welcome_details[0],
                    "message": welcome_details[1]
                }
            else:
                return None
    except aiosqlite.Error as e:
        return None

async def delete_welcome_message(guild_id):
    """Remove a welcome message setting from the database based on the guild_id."""
    try:
        async with aiosqlite.connect(db_path) as db:
            cursor = await db.cursor()
            await cursor.execute("DELETE FROM guild_welcome WHERE guild_id = ?", (guild_id,))
            changes = db.total_changes
            await db.commit()
            if changes > 0:
                return "Welcome message setting successfully removed from the database"
            else:
                return "Welcome message setting not found in the database"
    except aiosqlite.Error as e:
        return f"Database error: {e}"


###################
# Guild Whitelist #
###################

async def add_token_wl(guild_id, channel_id, blockchain, wl_name, supply, wl_description, token_role_1, token_role_2=None, expiry_date=None, total_wl_spots=None, mint_sale_date='TBA'):
    """Insert a new token whitelist entry into the database."""
    try:
        async with aiosqlite.connect(db_path) as db:
            cursor = await db.cursor()
            await cursor.execute("SELECT 1 FROM whitelist WHERE guild_id = ? AND wl_name = ? AND type = 'TOKEN'", (guild_id, wl_name))
            existing_entry = await cursor.fetchone()
            
            if existing_entry:
                return "An entry with these parameters already exists."
            
            await cursor.execute("""
                INSERT INTO whitelist 
                (guild_id, channel_id, blockchain, wl_name, supply, wl_description, mint_sale_date, type, token_role_1, token_role_2, expiry_date, total_wl_spots) 
                VALUES (?, ?, ?, ?, ?, ?, ?, 'TOKEN', ?, ?, ?, ?)
            """, (guild_id, channel_id, blockchain, wl_name, supply, wl_description, mint_sale_date, token_role_1, token_role_2, expiry_date, total_wl_spots))
            await db.commit()
            return "Token whitelist entry added successfully."
    except aiosqlite.Error as e:
        return f"Database error: {e}"

async def add_nft_wl(guild_id, channel_id, blockchain, wl_name, supply, wl_description, claim_all_roles, nft_role_mint_1, nft_role_mint_2=None, nft_role_mint_3=None, expiry_date=None, total_wl_spots=None, mint_sale_date='TBA'):
    """Insert a new NFT whitelist entry into the database."""
    try:
        async with aiosqlite.connect(db_path) as db:
            cursor = await db.cursor()
            await cursor.execute("SELECT 1 FROM whitelist WHERE guild_id = ? AND wl_name = ? AND type = 'NFT'", (guild_id, wl_name))
            existing_entry = await cursor.fetchone()
            
            if existing_entry:
                return "An entry with these parameters already exists."
            
            await cursor.execute("""
                INSERT INTO whitelist 
                (guild_id, channel_id, blockchain, wl_name, supply, wl_description, mint_sale_date, type, claim_all_roles, nft_role_mint_1, nft_role_mint_2, nft_role_mint_3, expiry_date, total_wl_spots) 
                VALUES (?, ?, ?, ?, ?, ?, ?, 'NFT', ?, ?, ?, ?, ?, ?)
            """, (guild_id, channel_id, blockchain, wl_name, supply, wl_description, mint_sale_date, claim_all_roles, nft_role_mint_1, nft_role_mint_2, nft_role_mint_3, expiry_date, total_wl_spots))
            await db.commit()
            return "NFT whitelist entry added successfully."
    except aiosqlite.Error as e:
        return f"Database error: {e}"

async def retrieve_whitelist_entry(guild_id, wl_name):
    """Fetch a specific whitelist entry based on guild_id and wl_name."""
    try:
        async with aiosqlite.connect(db_path) as db:
            cursor = await db.cursor()
            await cursor.execute("SELECT * FROM whitelist WHERE guild_id = ? AND wl_name = ?", (guild_id, wl_name))
            entry = await cursor.fetchone()
            if entry:
                role_mints = [entry[10], entry[11], entry[12]]
                token_roles = [entry[9], entry[10]]
                return {
                    "WL_ID": entry[0],
                    "guild_id": entry[1],
                    "channel_id": entry[2],
                    "blockchain": entry[3],
                    "wl_name": entry[4],
                    "supply": entry[5],
                    "wl_description": entry[6],
                    "mint_sale_date": entry[7],
                    "type": entry[8],
                    "claim_all_roles": entry[9],
                    "token_roles": token_roles,
                    "nft_role_mints": role_mints,
                    "expiry_date": entry[13],
                    "total_wl_spots": entry[14]
                }
            else:
                return None
    except aiosqlite.Error as e:
        return None

async def retrieve_all_whitelists_for_guild(guild_id):
    """Fetch all whitelist entries for a specific guild ID."""
    try:
        async with aiosqlite.connect(db_path) as db:
            cursor = await db.cursor()
            await cursor.execute("SELECT * FROM whitelist WHERE guild_id = ?", (guild_id,))
            whitelist_entries = await cursor.fetchall()
            if whitelist_entries:
                results = []
                for entry in whitelist_entries:
                    role_mints = [entry[10], entry[11], entry[12]]
                    token_roles = [entry[9], entry[10]]
                    results.append({
                        "WL_ID": entry[0],
                        "guild_id": entry[1],
                        "channel_id": entry[2],
                        "blockchain": entry[3],
                        "wl_name": entry[4],
                        "supply": entry[5],
                        "wl_description": entry[6],
                        "mint_sale_date": entry[7],
                        "type": entry[8],
                        "claim_all_roles": entry[9],
                        "token_roles": token_roles,
                        "nft_role_mints": role_mints,
                        "expiry_date": entry[13],
                        "total_wl_spots": entry[14]
                    })
                return results
            else:
                return None
    except aiosqlite.Error as e:
        return None

async def delete_whitelist_entry(guild_id: str, wl_type: str):
    """Delete a specific whitelist entry based on guild_id and wl_type."""
    try:
        async with aiosqlite.connect(db_path) as db:
            cursor = await db.cursor()
            await cursor.execute(
                "DELETE FROM whitelist WHERE guild_id = ? AND type = ?", 
                (guild_id, wl_type)
            )
            await db.commit()
    except aiosqlite.Error as e:
        return f"Database error: {e}"

