import requests
import spidev as SPI
import logging
import ST7789
import time

from PIL import Image,ImageDraw,ImageFont

logging.basicConfig(level=logging.DEBUG)
# 240x240 display with hardware SPI:
disp = ST7789.ST7789()

# Initialize library.
disp.Init()

# Clear display.
disp.clear()

#Set the backlight to 100
disp.bl_DutyCycle(50)

# Create blank image for drawing.
image1 = Image.new("RGB", (disp.width, disp.height), "YELLOW")
draw = ImageDraw.Draw(image1)
font_s = ImageFont.truetype('/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf', 14)

# Fetch the JSON data from the URL
url = "http://jvx-minibolt.local/status/json"
response = requests.get(url)
data = response.json()

# Store the values of the keys into variables
bitcoind = data.get("bitcoind")
chain = data.get("chain")
channel_balance = data.get("channel_balance")
current_block_height = data.get("current_block_height")
economyFee = data.get("economyFee")
fastestFee = data.get("fastestFee")
halfHourFee = data.get("halfHourFee")
hourFee = data.get("hourFee")
message = data.get("message")
minimumFee = data.get("minimumFee")
node_alias = data.get("node_alias")
node_lnd_version = data.get("node_lnd_version")
num_active_channels = data.get("num_active_channels")
num_inactive_channels = data.get("num_inactive_channels")
num_pending_channels = data.get("num_pending_channels")
number_of_channels = data.get("number_of_channels")
number_of_peers = data.get("number_of_peers")
number_of_peers_lnd = data.get("number_of_peers_lnd")
pruned = data.get("pruned")
pub_key = data.get("pub_key")
subversion = data.get("subversion")
sync_percentage = data.get("sync_percentage")
synced_to_chain = data.get("synced_to_chain")
synced_to_graph = data.get("synced_to_graph")
total_balance = data.get("total_balance")
version = data.get("version")
wallet_balance = data.get("wallet_balance")


#logging.info("draw line")
#draw.line([(20, 10),(70, 60)], fill = "RED",width = 1)
#draw.line([(70, 10),(20, 60)], fill = "RED",width = 1)
#draw.line([(170,15),(170,55)], fill = "RED",width = 1)
#draw.line([(150,35),(190,35)], fill = "RED",width = 1)

#logging.info("draw rectangle")

#draw.rectangle([(20,10),(70,60)],fill = "WHITE",outline="BLUE")
#draw.rectangle([(85,10),(130,60)],fill = "BLUE")

#logging.info("draw circle")
#draw.arc((150,15,190,55),0, 360, fill =(0,255,0))
#draw.ellipse((150,65,190,105), fill = (0,255,0))

logging.info("draw text")
Font1 = ImageFont.truetype("Font/Font01.ttf",18)
Font2 = ImageFont.truetype("Font/Font01.ttf",18)
Font3 = ImageFont.truetype("Font/Font02.ttf",18)

draw.rectangle([(2,65),(238,100)],fill = "BLACK")
#draw.text((5, 68), f'Node: {node_alias} | Channels: {number_of_channels}', fill = "WHITE",font=Font3)
draw.text((5, 68), f'Node: {node_alias} | Channels: {number_of_channels}', fill = "WHITE", font=font_s)
draw.rectangle([(2,102),(238,140)],fill = "BLUE")
#draw.text((5, 104), f'Current Height: {current_block_height}', fill = "WHITE",font=Font3)
draw.text((5, 104), f'Current Height: {current_block_height}', fill = "WHITE", font=font_s)
draw.rectangle([(2,142),(238,177)],fill = "RED")
#draw.text((5, 144), f'Fees: FF-{fastestFee} sat/vB | HH-{halfHourFee} sat/vB', fill = "WHITE",font=Font3)
draw.text((5, 144), f'Fees: FF-{fastestFee} sat/vB | HH-{halfHourFee} sat/vB', fill = "WHITE", font=font_s)
#draw.rectangle([(0,115),(190,160)],fill = "RED")
#draw.text((5, 118), 'WaveShare', fill = "WHITE",font=Font2)
#draw.text((5, 160), '1234567890', fill = "GREEN",font=Font3)
#text= u"NODE STATUS - TEST JVX"
#draw.text((5, 200),text, fill = "BLUE",font=Font3)
#im_r=image1.rotate(270)
im_r=image1
disp.ShowImage(im_r)
time.sleep(15)
#logging.info("show image")
#image = Image.open('pic.jpg')
#im_r=image.rotate(270)
#im_r=image
#disp.ShowImage(im_r)
#time.sleep(10)


