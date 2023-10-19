# Fetch Sheet Command User Guide for Beginners

## What Does This Command Do?

Are you new to Discord bots and wondering what the `fetch_sheet` command is all about? In simple terms, this command enables you to generate a .csv file containing all the user entries for a specific token or NFT whitelist. You need to have Administrator permissions to use this command.

## How to Use This Command?

To execute the `fetch_sheet` command, type:

/admin fetch_sheet [wl_id]

### Arguments

- **wl_id**: This is the ID number of the whitelist you wish to fetch. Be cautious with this number!

### After You Run the Command

1. **CSV File Generation**: The bot will create a .csv file featuring details like usernames, roles, and addresses.
2. **Download the File**: The bot will send you a message with the .csv file attached. Just click to download.

### What If No Entries Are Found?

If the bot can't find any entries for the specified wl_id, it will inform you. No worries!

### What Will the .CSV File Contain?

The .csv file may contain different columns depending on the type of whitelist:

- **For a TOKEN Whitelist**:
  - `User`: Discord usernames
  - `Roles`: Roles that the user has
  - `Address`: User's blockchain address
  
- **For an NFT Whitelist**:
  - `User`: Discord usernames
  - `Roles`: Roles that the user has
  - `Address`: User's blockchain address
  - `Number of Mints`: The number of mints a user is allowed

### Quick Tips

- Verify the wl_id to ensure you're getting data for the correct whitelist.
- Confirm you have the necessary permissions to execute this command.

