# PriceBot-2.0
* Price bot for discord made in python.
* Bot updates price every 5mins (300seconds)
* This bot utilizes CMC charts using playwright to take a screen shot of the website
* Bot shows price on nickname, if you adjust the speed of the updates be aware of discord rules as they may ban your bot if you are too aggressive.
* Status Green or Red shows the direction of the coin based on the 24 hour % of the coin
* An up or down arrow is included to show direction based on the percentage

# Bot Commands
* !tetsuo          - Show current TETSUO price information - 60 second cooldown
* !sol             - Show current Solana price information - 60 second cooldown
* !chart tetsuo    - Show TETSUO price chart - 15 second cooldown
* !chart sol       - Show Solana price chart - 15 second cooldown
* !help

# Bot ADMIN COMMANDS (MUST HAVE THE PROPER ROLE "owner = default role")
* TBD for future options

# Things you must do
* create .env file - edit the file -> DISCORD_TOKEN= 'YOUR_BOT_TOKEN_HERE'  <- put that in the .env file and put your token in there
* Invite your bot with proper permissions https://discord.com/oauth2/authorize?client_id=BOTIDGOESHERE&scope=bot&permissions=572023139200064  <-- if you don't like this permission you can control it with roles
* Create the role owner - If you don't like this role you can edit help.py and change the name of the role to whatever you like - the permissions sets the bot up for future commands that require deleting or updating older messages


# Update package list
sudo apt update
sudo apt upgrade -y

# Install Python 3.8+ and required packages
sudo add-apt-repository ppa:deadsnakes/ppa
sudo apt update
sudo apt install python3.8 python3.8-venv python3.8-dev screen -y
sudo apt-get install python3-dev build-essential
python -m pip install --upgrade pip
pip install wheel setuptools
pip install contourpy
pip install matplotlib
pip install mplfinance

# Create project directory
mkdir discord_price_bot
cd discord_price_bot

# Create requirements.txt file
echo "discord.py>=2.4.0" > requirements.txt
echo "requests>=2.31.0" >> requirements.txt

# Create and activate virtual environment
python3.8 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Create bot.py file (copy the code into this file)
touch bot.py

# Running the bot
# For testing:
python bot.py

# For production (using screen):
screen -S discord_bot
python bot.py
# Use Ctrl+A then D to detach from screen

# To reattach to screen session:
screen -r discord_bot

# To list screen sessions:
screen -ls

# To kill screen session:
screen -X -S discord_bot quit
