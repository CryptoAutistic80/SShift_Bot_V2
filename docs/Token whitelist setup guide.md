# Token Whitelist Command User Guide for Beginners

## What is This About?

New to Discord bots and token whitelists? No worries! A token whitelist is a list that grants certain members in your Discord server special access to claim a specific token. This token could be anything from a utility token to a governance token within a blockchain ecosystem.

The `token_wl` command is a handy tool that helps you set up this whitelist. You'll need Administrator permissions to use it.

## How Do I Use This Command?

To use the `token_wl` command, type:

/setup token_wl [arguments]

### What Do the Arguments Mean?

#### Required Arguments:

- **channel_mention**: Mention the channel where you want the bot to display the whitelist information. 
- **blockchain**: Choose the blockchain on which the token resides.
- **token_name**: Enter the name of the token you're whitelisting.
- **description**: Provide details about what the token is and why it's being whitelisted.
- **days_available**: Specify for how many days the whitelist should be available.
- **primary_role**: Mention the primary role that is eligible to claim the token.

#### Optional Arguments:

- **secondary_role**: You can mention a secondary role that's also eligible, if you want.
- **total_token_supply**: If you know the total supply of the token, you can enter it here.
- **total_wl_spots_available**: Specify the total number of whitelist spots, if you wish.
- **mint_sale_date**: You can also specify the date and time of the token's launch, in YYYY:MM:DD HH:MM format.

### Ready to Upload an Image?

After running the command, the bot will prompt you to upload an image for the token whitelist. Make sure you have it ready, as you'll only have 60 seconds to upload.

### What if I Mess Up?

Don't worry, the bot will tell you if something didn't work, and why.

### How Will I Know if It Worked?

The bot will send a follow-up message confirming the successful addition of the token whitelist.

