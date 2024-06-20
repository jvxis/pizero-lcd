import requests
import logging
import sys
import random
from PIL import Image, ImageDraw, ImageFont
import config
import ST7789
import time
from datetime import datetime

logging.basicConfig(level=logging.DEBUG)

# Initialize 240x240 display with hardware SPI
disp = ST7789.ST7789()
disp.Init()
disp.clear()
disp.bl_DutyCycle(50)  # Set backlight to 50%

def fetch_data():
    url = "http://jvx-minibolt.local/status/json"
    response = requests.get(url)
    return response.json()

# Fetch initial JSON data from the URL
data = fetch_data()

# Define fonts
font_large = ImageFont.truetype("Font/ShareTech-Regular.ttf", size=24)
font_small = ImageFont.truetype("Font/ShareTech-Regular.ttf", size=18)
font_bounce = ImageFont.truetype("Font/ShareTech-Regular.ttf", size=30)
font_nerd_runner = ImageFont.truetype("Font/ShareTech-Regular.ttf", size=32)
font_smaller = ImageFont.truetype("Font/ShareTech-Regular.ttf", size=14)

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
    draw.rectangle([(node_alias_x - 10, node_alias_y - 5), (node_alias_x + node_alias_width + 10, node_alias_y + 30)], fill="ORANGE")
    draw.text((node_alias_x, node_alias_y), node_alias, font=font_large, fill="WHITE")
    
    # Display menu options with background rectangles
    menu_options = ['1. Bitcoin', '2. LND', '3. Exit']
    line_height = 40
    for i, option in enumerate(menu_options):
        draw.rectangle([(10, 80 + i * line_height - 5), (230, 80 + i * line_height + 30)], fill="DARKBLUE")
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
    draw.rectangle([(10, 10), (230, 40)], fill="ORANGE")
    draw.text(((240 - title_width) // 2, 10), title, font=font_large, fill="WHITE")
    
    # Display information
    y_position = 50
    for line in info.split('\n'):
        color = "WHITE"
        if "Pruned:" in line:
            value = line.split(":")[1].strip()
            color = "RED" if value == "True" else "LIGHTGREEN" if value == "False" else "WHITE"
        elif "Synced to Chain:" in line:
            value = line.split(":")[1].strip()
            color = "LIGHTGREEN" if value == "True" else "RED" if value == "False" else "WHITE"
        elif "Synced to Graph:" in line:
            value = line.split(":")[1].strip()
            color = "LIGHTGREEN" if value == "True" else "RED" if value == "False" else "WHITE"
        elif "Sync %:" in line:
            value = line.split(":")[1].strip()
            color = "LIGHTGREEN" if value == "100.00%" else "YELLOW"
        elif "Inactive Channels:" in line:
            value = line.split(":")[1].strip()
            color = "LIGHTGREEN" if value == "0" else "YELLOW"
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
        f"Channels: {data['number_of_channels']}\n"
        f"Inactive Channels: {data['num_inactive_channels']}\n"
        f"$ Total: {data['total_balance']:.0f} sats\n"
        f"$ Wallet: {data['wallet_balance']:.0f} sats\n"
        f"$ Channel: {data['channel_balance']:.0f} sats\n"
    )
    return "LND Info", lnd_info

def bounce_texts(texts):
    colors = ["BLUE", "RED", "GREEN", "YELLOW", "ORANGE", "WHITE", "GRAY"]
    while True:
        if disp.digital_read(disp.GPIO_KEY3_PIN) != 0:
            display_menu()
            break
        random.shuffle(texts)  # Shuffle texts to display in a random order
        for text in texts:
            # Create image buffer
            image = Image.new("RGB", (240, 240), "BLACK")
            draw = ImageDraw.Draw(image)
            
            # Draw the text at a random position with a random color
            text_bbox = font_bounce.getbbox(text)
            text_width = text_bbox[2] - text_bbox[0]
            text_height = text_bbox[3] - text_bbox[1]
            
            # Ensure the text width and height are within the display bounds
            if text_width > 240:
                text_width = 240
            if text_height > 240:
                text_height = 240
            
            x = random.randint(0, 240 - text_width)
            y = random.randint(0, 240 - text_height)
            color = random.choice(colors)
            draw.text((x, y), text, font=font_bounce, fill=color)
            
            # Update display
            disp.ShowImage(image)
            
            # Wait for 2 seconds or exit if key3 is pressed
            start_time = time.time()
            while time.time() - start_time < 2:
                if disp.digital_read(disp.GPIO_KEY3_PIN) != 0:
                    display_menu()
                    return
                time.sleep(0.1)

def display_nerd_runner(initial_data):
    while True:
        data = initial_data
        image = Image.new("RGB", (240, 240), "BLACK")
        draw = ImageDraw.Draw(image)
        
        # Current Date and Time
        current_time = datetime.now().strftime("%d/%m/%Y - %H:%M")
        draw.text((10, 10), current_time, font=font_small, fill="WHITE")
        
        # NERD RUNNER text
        nerd_runner_text = "NERD RUNNER"
        nerd_runner_bbox = font_nerd_runner.getbbox(nerd_runner_text)
        nerd_runner_width = nerd_runner_bbox[2] - nerd_runner_bbox[0]
        nerd_runner_x = (240 - nerd_runner_width) // 2
        nerd_runner_y = 50
        draw.rounded_rectangle([(nerd_runner_x - 10, nerd_runner_y - 5), (nerd_runner_x + nerd_runner_width + 10, nerd_runner_y + 30)], radius=10, fill="YELLOW")
        draw.text((nerd_runner_x, nerd_runner_y), nerd_runner_text, font=font_nerd_runner, fill="BLACK")
        
        # Bitcoin Core and Block Height
        bitcoin_text = f"Bitcoin Core \n{100 if data['sync_percentage'] > 99.99 else data['sync_percentage']:.2f}%"
        bitcoin_color = "LIGHTGREEN" if data['sync_percentage'] > 99.99 else "YELLOW"
        block_height_text = f"\nBlock Height \n{data['current_block_height']}"
        draw.rounded_rectangle([(20, 100), (120, 200)], radius=10, fill="BLUE")
        draw.text((30, 110), bitcoin_text, font=font_small, fill=bitcoin_color)
        draw.text((30, 140), block_height_text, font=font_small, fill="ORANGE")
        
        # LND $ Total and Wallet
        lnd_total_text = f"LND $ Total \n{data['total_balance']:.0f} sats"
        lnd_wallet_text = f"\nLND $ Wallet  \n{data['wallet_balance']:.0f} sats"
        draw.rounded_rectangle([(130, 100), (230, 200)], radius=10, fill="ORANGE")
        draw.text((140, 110), lnd_total_text, font=font_small, fill="BLUE")
        draw.text((140, 140), lnd_wallet_text, font=font_small, fill="BLUE")
        
        # Fee information
        fastest_fee_text = f"Fast: {data['fastestFee']} sat/vB"
        half_hour_fee_text = f"30m Fee: {data['halfHourFee']} sat/vB"
        hour_fee_text = f"Hour Fee: {data['hourFee']} sat/vB"
        draw.rounded_rectangle([(10, 210), (230, 230)], radius=10, fill="YELLOW")
        draw.text((15, 212), fastest_fee_text, font=font_smaller, fill="BLACK")
        draw.text((100, 212), half_hour_fee_text, font=font_smaller, fill="BLACK")
        draw.text((200, 212), hour_fee_text, font=font_smaller, fill="BLACK")
        
        # Update display
        disp.ShowImage(image)
        
        start_time = time.time()
        while time.time() - start_time < 15 * 60:  # 15 minutes
            if disp.digital_read(disp.GPIO_KEY3_PIN) != 0:
                display_menu()
                return
            time.sleep(1)
        # Fetch new data after 15 minutes    
        data = fetch_data()
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
    elif disp.digital_read(disp.GPIO_KEY_PRESS_PIN) != 0:
        # Joystick button pressed: Show bouncing texts
        bounce_texts([
            f"Fastest Fee: {data['fastestFee']} sat/vB",
            f"Half Hour Fee: {data['halfHourFee']} sat/vB",
            f"Hour Fee: {data['hourFee']} sat/vB",
            f"Bitcoin Version: {data['subversion']}",
            f"LND Version: {data['node_lnd_version']}",
            f"Total Channels: {data['number_of_channels']}",
            f"$ Total: {data['total_balance']:.0f} sats",
            f"Block Height: {data['current_block_height']}"
        ])
    elif disp.digital_read(disp.GPIO_KEY_UP_PIN) != 0:
        # Joystick up: Show NERD RUNNER screen
        display_nerd_runner(data)
