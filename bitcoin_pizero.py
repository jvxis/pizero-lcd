import logging
import sys
import time
from datetime import datetime
from typing import Dict, Optional, Tuple

import requests
from PIL import Image, ImageDraw, ImageFont

import ST7789

# Endpoints
MEMPOOL_FEES_URL = "https://mempool.space/api/v1/fees/recommended"
MEMPOOL_PRICE_URL = "https://mempool.space/api/v1/prices"
MEMPOOL_BLOCK_HEIGHT_URL = "https://mempool.space/api/blocks/tip/height"
USD_BRL_URL = "https://economia.awesomeapi.com.br/last/USD-BRL"

# Timing
FETCH_INTERVAL_SECONDS = 300  # 5 minutes
SLEEP_LOOP_SECONDS = 1

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")

# Display init
disp = ST7789.ST7789()
disp.Init()
disp.clear()
disp.bl_DutyCycle(60)


def load_font(size: int) -> ImageFont.FreeTypeFont:
    try:
        return ImageFont.truetype("Font/ShareTech-Regular.ttf", size=size)
    except IOError:
        logging.warning("Font/ShareTech-Regular.ttf nao encontrada. Usando fonte padrao.")
        return ImageFont.load_default()


font_title = load_font(24)
font_block = load_font(36)
font_body = load_font(18)
font_small = load_font(14)


def fetch_fees() -> Dict[str, int]:
    resp = requests.get(MEMPOOL_FEES_URL, timeout=15)
    resp.raise_for_status()
    data = resp.json()
    return {
        "fastest": int(data.get("fastestFee", 0)),
        "half_hour": int(data.get("halfHourFee", 0)),
        "hour": int(data.get("hourFee", 0)),
    }


def fetch_prices() -> Tuple[float, Optional[float]]:
    resp = requests.get(MEMPOOL_PRICE_URL, timeout=15)
    resp.raise_for_status()
    price_usd = float(resp.json().get("USD", 0.0))
    price_brl = None
    try:
        fx = requests.get(USD_BRL_URL, timeout=15)
        fx.raise_for_status()
        fx_data = fx.json()
        usd_brl = float(fx_data["USDBRL"]["bid"])
        price_brl = price_usd * usd_brl
    except Exception as exc:
        logging.warning("Falha ao buscar USD/BRL: %s", exc)
    return price_usd, price_brl


def fetch_block_height() -> int:
    resp = requests.get(MEMPOOL_BLOCK_HEIGHT_URL, timeout=15)
    resp.raise_for_status()
    return int(resp.text.strip())


def draw_screen(block_height: int, fees: Dict[str, int], price_usd: float, price_brl: Optional[float], updated_at: datetime) -> None:
    image = Image.new("RGB", (240, 240), "BLACK")
    draw = ImageDraw.Draw(image)

    # Header
    draw.rectangle([(0, 0), (239, 48)], fill="ORANGE")
    header = "₿ Bitcoin Desk"
    header_w = font_title.getbbox(header)[2] - font_title.getbbox(header)[0]
    draw.text(((240 - header_w) // 2, 12), header, font=font_title, fill="BLACK")

    # Block height
    block_text = f"Bloco {block_height}"
    block_w = font_block.getbbox(block_text)[2] - font_block.getbbox(block_text)[0]
    draw.text(((240 - block_w) // 2, 60), block_text, font=font_block, fill="WHITE")

    # Fees
    fee_y = 110
    draw.rounded_rectangle([(10, fee_y - 6), (230, fee_y + 44)], radius=10, fill="#1E3A5F")
    fee_text = f"🚀 {fees['fastest']} | 🚗 {fees['half_hour']} | 🕒 {fees['hour']} sat/vB"
    draw.text((18, fee_y), fee_text, font=font_body, fill="ORANGE")

    # Prices
    price_y = 160
    draw.rounded_rectangle([(10, price_y - 6), (230, price_y + 54)], radius=10, fill="#0F2A1E")
    usd_text = f"USD {price_usd:,.0f}"
    draw.text((18, price_y), usd_text, font=font_body, fill="#00FFA3")
    if price_brl:
        brl_text = f"BRL {price_brl:,.0f}"
        draw.text((18, price_y + 26), brl_text, font=font_body, fill="#00FFA3")
    else:
        draw.text((18, price_y + 26), "BRL indisponivel", font=font_body, fill="#00FFA3")

    # Footer
    ts = updated_at.strftime("%H:%M:%S")
    footer = f"Atualizado {ts}  •  KEY3 sair"
    draw.text((10, 214), footer, font=font_small, fill="WHITE")

    disp.ShowImage(image)


def main() -> None:
    last_fetch = 0.0
    data: Dict[str, object] = {
        "block": 0,
        "fees": {"fastest": 0, "half_hour": 0, "hour": 0},
        "usd": 0.0,
        "brl": None,
        "updated": datetime.now(),
    }

    while True:
        now = time.time()
        if now - last_fetch >= FETCH_INTERVAL_SECONDS or data["block"] == 0:
            try:
                fees = fetch_fees()
                usd, brl = fetch_prices()
                block_height = fetch_block_height()
                data = {
                    "block": block_height,
                    "fees": fees,
                    "usd": usd,
                    "brl": brl,
                    "updated": datetime.now(),
                }
                last_fetch = now
                logging.info("Dados atualizados: bloco %s, fees %s, USD %.0f", block_height, fees, usd)
            except Exception as exc:
                logging.warning("Falha ao atualizar dados: %s", exc)

        draw_screen(
            block_height=int(data["block"]),
            fees=data["fees"],  # type: ignore[arg-type]
            price_usd=float(data["usd"]),
            price_brl=data["brl"],  # type: ignore[arg-type]
            updated_at=data["updated"],  # type: ignore[arg-type]
        )

        # Exit on KEY3 or Ctrl+C
        try:
            for _ in range(FETCH_INTERVAL_SECONDS):
                if disp.digital_read(disp.GPIO_KEY3_PIN) != 0:
                    disp.module_exit()
                    sys.exit(0)
                time.sleep(SLEEP_LOOP_SECONDS)
                now = time.time()
                if now - last_fetch >= FETCH_INTERVAL_SECONDS:
                    break
        except KeyboardInterrupt:
            disp.module_exit()
            sys.exit(0)


if __name__ == "__main__":
    main()
