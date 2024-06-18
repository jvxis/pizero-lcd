import requests
import logging
import time
import sys
from PIL import Image, ImageDraw, ImageFont
import config
import ST7789

logging.basicConfig(level=logging.DEBUG)

# Initialize 240x240 display with hardware SPI
disp = ST7789.ST7789()
disp.Init()
disp.clear()
disp.bl_DutyCycle(50)  # Set backlight to 50%

# Fetch JSON data from the URL
url = "http://jvx-minibolt.local/status/json"
response = requests.get(url)
data = response.json()

# Define fonts
font_large = ImageFont.truetype("Font/Font02.ttf", size=24)
font_small = ImageFont.truetype("Font/Font02.ttf", size=18)


# Calculate node_alias width
node_alias = data['node_alias']
node_alias_width = 70

# Center coordinates for node_alias
node_alias_x = (240 - node_alias_width) // 2
node_alias_y = 20


 
while True: 

    # Create image buffer
    image = Image.new("RGB", (240, 240), "BLACK")
    draw = ImageDraw.Draw(image)
    
    # Display node_alias centered
    draw.text((node_alias_x, node_alias_y), node_alias, font=font_large, fill="WHITE")
    
    # Display menu options
    menu_options = ['1. Bitcoin', '2. LND', '3. Exit']
    line_height = 40
    for i, option in enumerate(menu_options):
        draw.text((10, 80 + i * line_height), option, font=font_small, fill="WHITE")
    
    # Update display
    disp.ShowImage(image)
    # Wait for key press
    while True:
        if disp.digital_read(disp.GPIO_KEY1_PIN) != 0:
            # Key 1 pressed: Show Bitcoin info
            bitcoin_info = f"{node_alias} - Bitcoin\n"
            bitcoin_info += f"Subversion: {data['subversion']}\n"
            bitcoin_info += f"Sync Percentage: {100 if data['sync_percentage'] > 99.99 else data['sync_percentage']:.2f}%\n"
            bitcoin_info += f"Current Block Height: {data['current_block_height']}\n"
            bitcoin_info += f"Chain: {data['chain']}\n"
            bitcoin_info += f"Pruned: {data['pruned']}\n"
            bitcoin_info += f"Fastest Fee: {data['fastestFee']} sat/vB\n"
            bitcoin_info += f"Half Hour Fee: {data['halfHourFee']} sat/vB\n"
            bitcoin_info += f"Hour Fee: {data['hourFee']} sat/vB\n"
            
            # Clear display and show Bitcoin info
            draw.rectangle([(0, 0), (240, 240)], fill="BLACK")
            draw.text((10, 10), bitcoin_info, font=font_small, fill="WHITE")
            disp.ShowImage(image)
            while True:
                if disp.digital_read(disp.GPIO_KEY3_PIN) != 0:
                    break
        
        elif disp.digital_read(disp.GPIO_KEY2_PIN) != 0:
            # Key 2 pressed: Show LND info
            lnd_info = f"{node_alias} - LND\n"
            lnd_info += f"Node LND Version: {data['node_lnd_version']}\n"
            lnd_info += f"Synced to Chain: {data['synced_to_chain']}\n"
            lnd_info += f"Synced to Graph: {data['synced_to_graph']}\n"
            lnd_info += f"Number of Channels: {data['number_of_channels']}\n"
            lnd_info += f"Number of Inactive Channels: {data['num_inactive_channels']}\n"
            lnd_info += f"Total Balance: {data['total_balance']:.2f} sats\n"
            lnd_info += f"Wallet Balance: {data['wallet_balance']:.2f} sats\n"
            lnd_info += f"Channel Balance: {data['channel_balance']:.2f} sats\n"
            
            # Clear display and show LND info
            draw.rectangle([(0, 0), (240, 240)], fill="BLACK")
            draw.text((10, 10), lnd_info, font=font_small, fill="WHITE")
            disp.ShowImage(image)
            while True:
                if disp.digital_read(disp.GPIO_KEY3_PIN) != 0:
                    break
        
        elif disp.digital_read(disp.GPIO_KEY3_PIN) != 0:
            # Key 3 pressed: Exit the application
            disp.module_exit()
            sys.exit()
