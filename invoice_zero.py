import logging
import sys
import time
from textwrap import shorten
from typing import List, Optional, Tuple

import qrcode
import requests
from PIL import Image, ImageDraw, ImageFont

import ST7789

API_URL = "https://wallet.br-ln.com/api/v1/payments"
API_KEY = "0efbe93958fc40a396effe783291a369"
DEFAULT_AMOUNT_USD = 5
DEFAULT_MEMO = "Pi Zero LCD Invoice"
DEFAULT_EXPIRY_SECONDS = 900  # 15 minutes
MEMPOOL_PRICE_URL = "https://mempool.space/api/v1/prices"

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")

# Initialize the LCD as soon as the script starts.
disp = ST7789.ST7789()
disp.Init()
disp.clear()
disp.bl_DutyCycle(60)


def load_font(size: int) -> ImageFont.FreeTypeFont:
    """Load preferred font and fall back to PIL default if missing."""
    try:
        return ImageFont.truetype("Font/ShareTech-Regular.ttf", size=size)
    except IOError:
        logging.warning("Font/ShareTech-Regular.ttf not found. Falling back to default font.")
        return ImageFont.load_default()


font_title = load_font(24)
font_body = load_font(18)
font_small = load_font(14)


def show_message(title: str, lines: List[str], background: str = "BLACK", text_color: str = "WHITE") -> None:
    """Render a simple message screen."""
    image = Image.new("RGB", (240, 240), background)
    draw = ImageDraw.Draw(image)

    # Title bar
    draw.rectangle([(0, 0), (239, 44)], fill="ORANGE")
    title_bbox = font_title.getbbox(title)
    title_width = title_bbox[2] - title_bbox[0]
    draw.text(((240 - title_width) // 2, 10), title, font=font_title, fill="WHITE")

    y = 60
    for line in lines:
        draw.text((12, y), line, font=font_body, fill=text_color)
        y += 24

    disp.ShowImage(image)


def fetch_btc_price_usd() -> float:
    """Fetch current BTC price in USD from mempool.space."""
    response = requests.get(MEMPOOL_PRICE_URL, timeout=10)
    response.raise_for_status()
    data = response.json()
    return float(data["USD"])


def usd_to_sats(amount_usd: float) -> Tuple[int, float]:
    """Convert USD amount to sats using live price from mempool.space."""
    price = fetch_btc_price_usd()
    sats = max(int((amount_usd / price) * 100_000_000), 1)
    return sats, price


def create_invoice(amount_sats: int, memo: str, expiry_seconds: int) -> Tuple[str, Optional[str]]:
    """Call the wallet API to create a Lightning invoice."""
    payload = {
        "out": False,
        "amount": int(amount_sats),
        "memo": memo,
        "expiry": int(expiry_seconds),
        "unit": "sat",
    }
    headers = {
        "X-Api-Key": API_KEY,
        "Content-type": "application/json",
    }

    logging.info("Solicitando invoice: %s sats (memo: %s)", amount_sats, memo)
    response = requests.post(API_URL, json=payload, headers=headers, timeout=20)
    response.raise_for_status()
    invoice = response.json()
    return invoice["payment_request"], invoice.get("payment_hash")


def show_invoice_info(amount_usd: float, amount_sats: int, btc_price: float, memo: str) -> None:
    """Show amount and price info before the QR screen."""
    lines = [
        f"{amount_usd:.2f} USD",
        f"~ {amount_sats} sats",
        f"BTC: ${btc_price:,.2f}",
    ]
    if memo:
        lines.append(shorten(memo, width=26, placeholder="..."))
    show_message("Invoice pronta", lines, background="BLACK")
    time.sleep(1.5)


def render_invoice_fullscreen(payment_request: str) -> None:
    """Draw only the QR code, filling the 240x240 display."""
    qr = qrcode.QRCode(
        error_correction=qrcode.constants.ERROR_CORRECT_Q,
        box_size=10,
        border=1,
    )
    qr.add_data(payment_request)
    qr.make(fit=True)
    qr_img = qr.make_image(fill_color="black", back_color="white").convert("RGB")
    base_size = qr_img.size[0]
    scale = max(1, 240 // base_size)
    target_size = base_size * scale
    qr_img = qr_img.resize((target_size, target_size), Image.NEAREST)

    canvas = Image.new("RGB", (240, 240), "WHITE")
    offset = ((240 - target_size) // 2, (240 - target_size) // 2)
    canvas.paste(qr_img, offset)
    disp.ShowImage(canvas)


def wait_for_exit() -> None:
    """Keep the invoice visible until KEY3 is pressed or Ctrl+C."""
    logging.info("Invoice exibida. Pressione KEY3 ou Ctrl+C para sair.")
    try:
        while True:
            if disp.digital_read(disp.GPIO_KEY3_PIN) != 0:
                break
            time.sleep(0.2)
    finally:
        disp.module_exit()


def main() -> None:
    amount = DEFAULT_AMOUNT_USD
    memo = DEFAULT_MEMO

    # Optional CLI overrides: python invoice_zero.py 10 "meu memo"
    if len(sys.argv) > 1:
        try:
            amount = float(sys.argv[1])
        except ValueError:
            logging.warning("Valor invalido informado. Usando padrao de %.2f USD.", DEFAULT_AMOUNT_USD)
            amount = DEFAULT_AMOUNT_USD
    if len(sys.argv) > 2:
        memo = " ".join(sys.argv[2:])

    try:
        amount_sats, btc_price = usd_to_sats(amount)
    except Exception as exc:
        logging.exception("Nao foi possivel obter o preco BTC/USD")
        show_message("Erro preco", [shorten(str(exc), width=32)], background="RED")
        sys.exit(1)

    show_message(
        "Lightning",
        [
            "Gerando invoice",
            f"{amount:.2f} USD ~ {amount_sats} sats",
            f"BTC: ${btc_price:,.2f} (mempool.space)",
            memo,
        ],
    )

    try:
        payment_request, payment_hash = create_invoice(amount_sats, memo, DEFAULT_EXPIRY_SECONDS)
    except requests.HTTPError as exc:
        detail = exc.response.text if exc.response is not None else str(exc)
        logging.error("Erro da API: %s", detail)
        show_message("Erro API", [shorten(detail, width=32)], background="RED")
        sys.exit(1)
    except Exception as exc:
        logging.exception("Falha ao gerar invoice")
        show_message("Erro", [str(exc)], background="RED")
        sys.exit(1)

    show_invoice_info(amount, amount_sats, btc_price, memo)
    render_invoice_fullscreen(payment_request)
    logging.info("Invoice pronta: %s", payment_request)
    wait_for_exit()


if __name__ == "__main__":
    main()
