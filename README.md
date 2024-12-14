# PriceBot-2.0
* Price bot for discord made in python.
* Bot updates price every 5mins (300seconds)
* Bot shows price on nickname, if you adjust the speed of the updates be aware of discord rules as they may ban your bot if you are too aggressive.
* Status Green or Red shows the direction of the coin based on the 24 hour % of the coin
* An up or down arrow is included to show direction based on the percentage

# Bot Commands
* !price - returns base token based on dexscreener entries located at the top of bot.py (Currently renamed to Tetsuo in the release)
* !sol - returns sol price
Development * !chart - Need to add a basic chart grab to display the 1hr chart for selected coins

# Update package list
sudo apt update
sudo apt upgrade -y

# Install Python 3.8+ and required packages
sudo add-apt-repository ppa:deadsnakes/ppa
sudo apt update
sudo apt install python3.8 python3.8-venv python3.8-dev screen -y

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
