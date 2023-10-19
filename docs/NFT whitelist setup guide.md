# NFT Whitelist Command User Guide for Beginners

## What is this All About?

If you're new to Discord bots, you're probably wondering what an NFT whitelist is. In simple terms, this is a special list that allows certain members in your Discord server to have exclusive access to mint (or create) Non-Fungible Tokens (NFTs). NFTs are unique digital assets verified using blockchain technology.

The `nft_wl` command helps you set up this special list. It's a part of a larger `setup` command and allows you to specify a lot of details, like which roles in your Discord server can mint these NFTs, how many they can mint, and so on.

## Do I Need Special Access?

Yes, you need to have Administrator permissions in your Discord server to use this command.

## How Do I Use This Command?

Type the following into a Discord channel where the bot is active:

/setup nft_wl [arguments]

Arguments are the extra bits of information that the command needs. Here's what each one means:

### Required Info

- **channel_mention**: Tell the bot which channel to use for displaying information about the NFT whitelist. Simply '@' mention the channel.
  
- **blockchain**: Specify the blockchain that the NFT is part of. The bot will give you choices for this.
  
- **wl_name**: What's the name of your NFT collection? Type it here.
  
- **wl_description**: Give some more details about your NFT collection.
  
- **days_available**: How many days should this whitelist be open? Type a number.
  
- **mints_for_all_roles**: Do you want to allow all roles to mint the NFT or just a primary role? Type 'Yes' for all roles, and 'No' for just the primary role.
  
- **primary_role**: Which role is the main one that can mint the NFT? '@' mention the role here.

### Extra Info (Optional)

- **no_mints_primary**: How many NFTs can the primary role mint? (Optional)
  
- **secondary_role**: Is there a second role that can mint? '@' mention it here. (Optional)
  
- **no_mints_secondary**: How many NFTs can the secondary role mint? (Optional)
  
- **tertiary_role**: Is there a third role that can mint? '@' mention it here. (Optional)
  
- **no_mints_tertiary**: How many NFTs can the tertiary role mint? (Optional)
  
- **supply**: Total number of NFTs to be made. (Optional)
  
- **total_wl_spots_available**: Total number of whitelist spots. (Optional)
  
- **mint_sale_date**: When will the NFT go on sale? Use the format YYYY:MM:DD HH:MM. (Optional)

### Picture Time!

After you type the command, the bot will ask you to upload an image. This is going to be the image for the NFT whitelist. You'll have 60 seconds to do this, so have the image ready.

### What if Something Goes Wrong?

Don't worry, the bot will tell you if something didn't work and why.

### How Will I Know It Worked?

If everything is successful, the bot will send a message saying the NFT whitelist has been added.

