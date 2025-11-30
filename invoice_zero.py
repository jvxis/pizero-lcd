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
FIAT_PRICE_URL = "https://api.coindesk.com/v1/bpi/currentprice/USD.json"

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
    """Fetch current BTC price in USD."""
    response = requests.get(FIAT_PRICE_URL, timeout=10)
    response.raise_for_status()
    data = response.json()
    return float(data["bpi"]["USD"]["rate_float"])


def usd_to_sats(amount_usd: float) -> Tuple[int, float]:
    """Convert USD amount to sats using a live price feed."""
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


def render_invoice(
    payment_request: str,
    payment_hash: Optional[str],
    amount_usd: float,
    memo: str,
    amount_sats: Optional[int],
) -> None:
    """Draw the QR code and supporting text on the LCD."""
    qr = qrcode.QRCode(
        error_correction=qrcode.constants.ERROR_CORRECT_Q,
        box_size=3,
        border=2,
    )
    qr.add_data(payment_request)
    qr.make(fit=True)
    qr_img = qr.make_image(fill_color="black", back_color="white").convert("RGB")

    qr_size = 150
    qr_img = qr_img.resize((qr_size, qr_size), Image.NEAREST)

    image = Image.new("RGB", (240, 240), "WHITE")
    draw = ImageDraw.Draw(image)

    # Header with amount
    header_text = f"{amount_usd:.2f} USD"
    header_width = font_title.getbbox(header_text)[2] - font_title.getbbox(header_text)[0]
    draw.rectangle([(0, 0), (239, 64)], fill="BLACK")
    draw.text(((240 - header_width) // 2, 8), header_text, font=font_title, fill="WHITE")
    if amount_sats is not None:
        sats_text = f"~ {amount_sats} sats"
        draw.text((10, 32), sats_text, font=font_small, fill="WHITE")

    # Memo just under the header
    if memo:
        memo_text = shorten(memo, width=26, placeholder="...")
        draw.text((12, 48), memo_text, font=font_small, fill="WHITE")

    # Center the QR code
    qr_x = (240 - qr_size) // 2
    qr_y = 70
    image.paste(qr_img, (qr_x, qr_y))

    # Footer with abbreviated invoice info
    short_invoice = f"{payment_request[:12]}...{payment_request[-12:]}"
    draw.rectangle([(0, 220), (239, 239)], fill="BLACK")
    draw.text((10, 222), short_invoice, font=font_small, fill="WHITE")
    if payment_hash:
        hash_text = f"hash: {payment_hash[:12]}..."
        draw.text((10, 206), hash_text, font=font_small, fill="BLACK")

    disp.ShowImage(image)


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
        show_message("Erro", [str(exc)], background="RED")
        sys.exit(1)

    show_message(
        "Lightning",
        [
            "Gerando invoice",
            f"{amount:.2f} USD ~ {amount_sats} sats",
            f"BTC: ${btc_price:,.2f}",
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

    render_invoice(payment_request, payment_hash, amount, memo, amount_sats)
    logging.info("Invoice pronta: %s", payment_request)
    wait_for_exit()


if __name__ == "__main__":
    main()
