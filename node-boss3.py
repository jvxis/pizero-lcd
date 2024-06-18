import requests
import logging
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
font_large = ImageFont.truetype("Font/NotoSans-Regular.ttf", size=24)
font_small = ImageFont.truetype("Font/NotoSans-Regular.ttf", size=18)

# Calculate node_alias width
node_alias = data['node_alias']
node_alias_bbox = font_large.getbbox(node_alias)
node_alias_width = node_alias_bbox[2] - node_alias_bbox[0]

# Center coordinates for node_alias
node_alias_x = (240 - node_alias_width) // 2
node_alias_y = 20

def display_menu():
    # Create image buffer
    image = Image.new("RGB", (240, 240), "BLACK")
    draw = ImageDraw.Draw(image)
    
    # Display node_alias centered with background rectangle
    draw.rectangle([(node_alias_x - 10, node_alias_y - 5), (node_alias_x + node_alias_width + 10, node_alias_y + 30)], fill="BLUE")
    draw.text((node_alias_x, node_alias_y), node_alias, font=font_large, fill="WHITE")
    
    # Display menu options with background rectangles
    menu_options = ['1. Bitcoin', '2. LND', '3. Exit']
    line_height = 40
    for i, option in enumerate(menu_options):
        draw.rectangle([(10, 80 + i * line_height - 5), (230, 80 + i * line_height + 30)], fill="DARKGRAY")
        draw.text((20, 80 + i * line_height), option, font=font_small, fill="WHITE")
    
    # Update display
    disp.ShowImage(image)

def display_info(title, info):
    # Create image buffer
    image = Image.new("RGB", (240, 240), "BLACK")
    draw = ImageDraw.Draw(image)
    
    # Display title with background rectangle
    title_bbox = font_large.getbbox(title)
    title_width = title_bbox[2] - title_bbox[0]
    draw.rectangle([(10, 10), (230, 40)], fill="BLUE")
    draw.text(((240 - title_width) // 2, 10), title, font=font_large, fill="WHITE")
    
    # Display information
    #draw.text((10, 50), info, font=font_small, fill="WHITE")
    
    # Display information
    y_position = 50
    for line in info.split('\n'):
        color = "WHITE"
        if "Pruned:" in line:
            value = line.split(":")[1].strip()
            color = "GREEN" if value == "True" else "RED" if value == "False" else "WHITE"
        elif "Synced to Chain:" in line:
            value = line.split(":")[1].strip()
            color = "GREEN" if value == "True" else "RED" if value == "False" else "WHITE"
        elif "Synced to Graph:" in line:
            value = line.split(":")[1].strip()
            color = "GREEN" if value == "True" else "RED" if value == "False" else "WHITE"
        draw.text((10, y_position), line, font=font_small, fill=color)
        y_position += 20
    
    # Update display
    disp.ShowImage(image)

def get_bitcoin_info():
    bitcoin_info = (
        f"Version: {data['subversion']}\n"
        f"Sync %: {100 if data['sync_percentage'] > 99.99 else data['sync_percentage']:.2f}%\n"
        f"Block Height: {data['current_block_height']}\n"
        f"Chain: {data['chain']}\n"
        f"Pruned: {data['pruned']}\n"
        f"Fastest Fee: {data['fastestFee']} sat/vB\n"
        f"Half Hour Fee: {data['halfHourFee']} sat/vB\n"
        f"Hour Fee: {data['hourFee']} sat/vB\n"
    )
    return "Bitcoin Info", bitcoin_info

def get_lnd_info():
    lnd_info = (
        f"Version: {data['node_lnd_version']}\n"
        f"Synced to Chain: {data['synced_to_chain']}\n"
        f"Synced to Graph: {data['synced_to_graph']}\n"
        f"Num. of Channels: {data['number_of_channels']}\n"
        f"Num. of Inactive Channels: {data['num_inactive_channels']}\n"
        f"Total Balance: {data['total_balance']:.2f} sats\n"
        f"Wallet Balance: {data['wallet_balance']:.2f} sats\n"
        f"Channel Balance: {data['channel_balance']:.2f} sats\n"
    )
    return "LND Info", lnd_info

display_menu()

while True:
    if disp.digital_read(disp.GPIO_KEY1_PIN) != 0:
        # Key 1 pressed: Show Bitcoin info
        title, info = get_bitcoin_info()
        display_info(title, info)
        while True:
            if disp.digital_read(disp.GPIO_KEY3_PIN) != 0:
                display_menu()
                break
    elif disp.digital_read(disp.GPIO_KEY2_PIN) != 0:
        # Key 2 pressed: Show LND info
        title, info = get_lnd_info()
        display_info(title, info)
        while True:
            if disp.digital_read(disp.GPIO_KEY3_PIN) != 0:
                display_menu()
                break
    elif disp.digital_read(disp.GPIO_KEY3_PIN) != 0:
        # Key 3 pressed: Exit the application
        disp.module_exit()
        sys.exit()
