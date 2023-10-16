import aiosqlite

# Define the path for the SQLite database
db_path = "database/database69.db"

async def initialize_db():
    try:
        async with aiosqlite.connect(db_path) as db:
            cursor = await db.cursor()
          
            #Check if the whitelist_claims table exists and drop it
            #await cursor.execute("""
                #DROP TABLE IF EXISTS translations;
            #""")
          
            #Check if the whitelist table exists and drop it
            #await cursor.execute("""
                #DROP TABLE IF EXISTS translation_settings;
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
                    WL_image TEXT,  -- New column
                    FOREIGN KEY (guild_id) REFERENCES guild_memberships(guild_id),
                    UNIQUE (WL_ID, guild_id, wl_name, type)
                );
            """)
          
            await cursor.execute("""
                CREATE TABLE IF NOT EXISTS whitelist_claims (
                    claim_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    WL_ID INTEGER NOT NULL,
                    guild_id TEXT NOT NULL,
                    user_id TEXT NOT NULL,
                    user_roles TEXT NOT NULL,
                    address TEXT NOT NULL,
                    no_mints INTEGER,
                    FOREIGN KEY (WL_ID) REFERENCES whitelist(WL_ID),
                    FOREIGN KEY (guild_id) REFERENCES guild_memberships(guild_id),
                    UNIQUE (WL_ID, user_id)
                );
            """)

            await cursor.execute("""
                CREATE TABLE IF NOT EXISTS translate_settings (
                    guild_id TEXT PRIMARY KEY NOT NULL,
                    base_language TEXT,
                    channel_1 TEXT,
                    channel_2 TEXT,
                    channel_3 TEXT,
                    FOREIGN KEY (guild_id) REFERENCES guild_memberships(guild_id)
                );
            """)

            await cursor.execute("""
                CREATE TABLE IF NOT EXISTS translations (
                    guild_id TEXT NOT NULL,
                    translation TEXT NOT NULL,
                    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                    original_message_id TEXT NOT NULL UNIQUE,
                    PRIMARY KEY (guild_id, original_message_id),
                    FOREIGN KEY (guild_id) REFERENCES guild_memberships(guild_id)
                );
            """)


            await db.commit()
    except aiosqlite.Error as e:
        print(f"Database error: {e}")


######################
# TRANSLATION TABLES #
######################

async def add_replace_translation_settings(guild_id, channel_1, channel_2, channel_3, base_language=None):
    """Insert or update translation settings for a guild."""
    try:
        async with aiosqlite.connect(db_path) as db:
            cursor = await db.cursor()
            await cursor.execute("""
                INSERT INTO translate_settings (guild_id, channel_1, channel_2, channel_3, base_language)
                VALUES (?, ?, ?, ?, ?)
                ON CONFLICT (guild_id)
                DO UPDATE SET channel_1 = excluded.channel_1, channel_2 = excluded.channel_2, channel_3 = excluded.channel_3, base_language = excluded.base_language;
            """, (guild_id, channel_1, channel_2, channel_3, base_language))
            await db.commit()
    except aiosqlite.Error as e:
        print(f"Database error: {e}")

async def delete_translation_settings(guild_id):
    """Delete translation settings for a guild."""
    try:
        async with aiosqlite.connect(db_path) as db:
            cursor = await db.cursor()
            await cursor.execute("""
                DELETE FROM translate_settings WHERE guild_id = ?;
            """, (guild_id,))
            await db.commit()
    except aiosqlite.Error as e:
        print(f"Database error: {e}")

async def retrieve_translation_settings(guild_id):
    """Retrieve translation settings for a guild."""
    try:
        async with aiosqlite.connect(db_path) as db:
            cursor = await db.cursor()
            await cursor.execute("""
                SELECT channel_1, channel_2, channel_3, base_language FROM translate_settings WHERE guild_id = ?;
            """, (guild_id,))
            row = await cursor.fetchone()
            if row:
                return row
            else:
                return None
    except aiosqlite.Error as e:
        print(f"Database error: {e}")


async def insert_translation(guild_id, translation, original_message_id):
    """Insert a new translation into the database."""
    try:
        async with aiosqlite.connect(db_path) as db:
            cursor = await db.cursor()
            await cursor.execute(
                "INSERT OR REPLACE INTO translations (guild_id, translation, original_message_id) VALUES (?, ?, ?)", 
                (guild_id, translation, original_message_id))
            await db.commit()
    except aiosqlite.Error as e:
        print(f"Database error: {e}")

async def retrieve_translation(guild_id, original_message_id):
    """Retrieve a translation from the database based on the guild_id and original_message_id."""
    try:
        async with aiosqlite.connect(db_path) as db:
            cursor = await db.cursor()
            await cursor.execute("SELECT translation FROM translations WHERE guild_id = ? AND original_message_id = ?", (guild_id, original_message_id))
            translation = await cursor.fetchone()
            return translation[0] if translation else None
    except aiosqlite.Error as e:
        print(f"Database error: {e}")

async def delete_old_translations(guild_id, hours=24):
    """Delete translations that are older than the specified number of hours for a given guild."""
    try:
        async with aiosqlite.connect(db_path) as db:
            cursor = await db.cursor()
            await cursor.execute("DELETE FROM translations WHERE guild_id = ? AND timestamp < datetime('now', '-{} hours')".format(hours), (guild_id,))
            await db.commit()
    except aiosqlite.Error as e:
        print(f"Database error: {e}")

async def retrieve_all_translations(guild_id):
    """Retrieve all translations for a specific guild_id from the database."""
    try:
        async with aiosqlite.connect(db_path) as db:
            cursor = await db.cursor()
            await cursor.execute("SELECT original_message_id, translation FROM translations WHERE guild_id = ?", (guild_id,))
            translations = await cursor.fetchall()
            return translations if translations else None
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

async def edit_guild(guild_id, membership_type=None, expiry_date=None):
    """Edit an existing guild membership in the database or return an error if it doesn't exist."""
    try:
        async with aiosqlite.connect(db_path) as db:
            cursor = await db.cursor()

            # Check if the guild_id exists in the database
            await cursor.execute("SELECT 1 FROM guild_memberships WHERE guild_id = ?", (guild_id,))
            existing_guild = await cursor.fetchone()

            if not existing_guild:
                return "Guild does not exist in the database"

            # Prepare the SQL update query and values based on the provided arguments
            update_columns = []
            values = []
            if membership_type is not None:
                update_columns.append("membership_type = ?")
                values.append(membership_type)
            if expiry_date is not None:
                update_columns.append("expiry_date = ?")
                values.append(expiry_date)
            if not update_columns:
                return "No updates specified"

            update_query = f"UPDATE guild_memberships SET {', '.join(update_columns)} WHERE guild_id = ?"
            values.append(guild_id)

            # Execute the update query
            await cursor.execute(update_query, values)
            await db.commit()

            return "Guild successfully updated in the database"
    except aiosqlite.Error as e:
        return f"Database error: {e}"

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

async def add_token_wl(guild_id, channel_id, blockchain, wl_name, supply, wl_description, token_role_1, token_role_2=None, expiry_date=None, total_wl_spots=None, mint_sale_date='TBA', WL_image=None):
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
                (guild_id, channel_id, blockchain, wl_name, supply, wl_description, mint_sale_date, type, token_role_1, token_role_2, expiry_date, total_wl_spots, WL_image) 
                VALUES (?, ?, ?, ?, ?, ?, ?, 'TOKEN', ?, ?, ?, ?, ?)
            """, (guild_id, channel_id, blockchain, wl_name, supply, wl_description, mint_sale_date, token_role_1, token_role_2, expiry_date, total_wl_spots, WL_image))
            await db.commit()
            return "Token whitelist entry added successfully."
    except aiosqlite.Error as e:
        return f"Database error: {e}"

async def add_nft_wl(guild_id, channel_id, blockchain, wl_name, supply, wl_description, claim_all_roles, nft_role_mint_1, nft_role_mint_2=None, nft_role_mint_3=None, expiry_date=None, total_wl_spots=None, mint_sale_date='TBA', WL_image=None):
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
                (guild_id, channel_id, blockchain, wl_name, supply, wl_description, mint_sale_date, type, claim_all_roles, nft_role_mint_1, nft_role_mint_2, nft_role_mint_3, expiry_date, total_wl_spots, WL_image) 
                VALUES (?, ?, ?, ?, ?, ?, ?, 'NFT', ?, ?, ?, ?, ?, ?, ?)
            """, (guild_id, channel_id, blockchain, wl_name, supply, wl_description, mint_sale_date, claim_all_roles, nft_role_mint_1, nft_role_mint_2, nft_role_mint_3, expiry_date, total_wl_spots, WL_image))
            await db.commit()
            return "NFT whitelist entry added successfully."
    except aiosqlite.Error as e:
        return f"Database error: {e}"

async def retrieve_whitelist_entry_by_id(guild_id, WL_ID):
    """Fetch a specific whitelist entry based on guild_id and WL_ID."""
    try:
        async with aiosqlite.connect(db_path) as db:
            cursor = await db.cursor()
            await cursor.execute(
                "SELECT * FROM whitelist WHERE guild_id = ? AND WL_ID = ?",
                (guild_id, WL_ID)
            )
            entry = await cursor.fetchone()
            if entry:
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
                    "token_role_1": entry[10],
                    "token_role_2": entry[11],
                    "nft_role_mint_1": entry[12],
                    "nft_role_mint_2": entry[13],
                    "nft_role_mint_3": entry[14],
                    "expiry_date": entry[15],
                    "total_wl_spots": entry[16],
                    "WL_image": entry[17]
                }
            else:
                return None
    except aiosqlite.Error as e:
        print(f"Database error: {e}")
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
                        "token_role_1": entry[10],
                        "token_role_2": entry[11],
                        "nft_role_mint_1": entry[12],
                        "nft_role_mint_2": entry[13],
                        "nft_role_mint_3": entry[14],
                        "expiry_date": entry[15],
                        "total_wl_spots": entry[16],
                        "WL_image": entry[17]
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

 
####################
# Whitelist claims #
####################

# Add or update a whitelist claim
async def upsert_whitelist_claim(WL_ID, guild_id, user_id, user_roles, address, no_mints):
    async with aiosqlite.connect(db_path) as db:
        cursor = await db.cursor()
        await cursor.execute("""
            INSERT OR REPLACE INTO whitelist_claims 
            (WL_ID, guild_id, user_id, user_roles, address, no_mints) 
            VALUES (?, ?, ?, ?, ?, ?)
        """, (WL_ID, guild_id, user_id, user_roles, address, no_mints))
        await db.commit()

# Delete a whitelist claim
async def delete_whitelist_claim(WL_ID, user_id):
    async with aiosqlite.connect(db_path) as db:
        cursor = await db.cursor()
        await cursor.execute("""
            DELETE FROM whitelist_claims WHERE WL_ID = ? AND user_id = ?
        """, (WL_ID, user_id))
        await db.commit()

# Retrieve a whitelist claim
async def retrieve_whitelist_claim(WL_ID, user_id):
    async with aiosqlite.connect(db_path) as db:
        cursor = await db.cursor()
        await cursor.execute("""
            SELECT * FROM whitelist_claims WHERE WL_ID = ? AND user_id = ?
        """, (WL_ID, user_id))
        claim_details = await cursor.fetchone()
        if claim_details:
            return {
                "claim_id": claim_details[0],
                "WL_ID": claim_details[1],
                "guild_id": claim_details[2],
                "user_id": claim_details[3],
                "user_roles": claim_details[4],  # Updated to reflect new schema
                "address": claim_details[5],
                "no_mints": claim_details[6]  # Updated index due to new column
            }
        return None

# Retrieve all whitelist claims for specfic user
async def retrieve_all_claims_for_user(user_id):
    async with aiosqlite.connect(db_path) as db:
        cursor = await db.cursor()
        await cursor.execute("""
            SELECT * FROM whitelist_claims WHERE user_id = ?
        """, (user_id,))
        
        claim_details_list = await cursor.fetchall()
        if not claim_details_list:
            return None

        claims = []
        for claim_details in claim_details_list:
            claim_dict = {
                "claim_id": claim_details[0],
                "WL_ID": claim_details[1],
                "guild_id": claim_details[2],
                "user_id": claim_details[3],
                "user_roles": claim_details[4],
                "address": claim_details[5],
                "no_mints": claim_details[6]
            }
            claims.append(claim_dict)

        return claims


async def fetch_user_entries_for_wl(guild_id, WL_ID):
    async with aiosqlite.connect(db_path) as db:
        cursor = await db.cursor()
        await cursor.execute("""
            SELECT whitelist_claims.*, whitelist.wl_name, whitelist.type  -- Assuming type is in the whitelist table
            FROM whitelist_claims 
            JOIN whitelist ON whitelist_claims.WL_ID = whitelist.WL_ID 
            WHERE whitelist_claims.guild_id = ? AND whitelist_claims.WL_ID = ?
        """, (guild_id, WL_ID))
        user_entries = await cursor.fetchall()
        if user_entries:
            results = []
            for entry in user_entries:
                results.append({
                    "claim_id": entry[0],
                    "WL_ID": entry[1],
                    "guild_id": entry[2],
                    "user_id": entry[3],
                    "user_roles": entry[4],
                    "address": entry[5],
                    "no_mints": entry[6],
                    "wl_name": entry[7],  # wl_name is now included
                    "type": entry[8]  # type is now included
                })
            return results
        return None

