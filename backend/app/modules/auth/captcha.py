import hmac
import random
import string
from base64 import b64encode
from html import escape

from app.core.config import get_settings

CAPTCHA_ALPHABET = "".join(
    character for character in string.ascii_uppercase + string.digits if character not in "O0I1"
)


def normalize_captcha_code(code: str) -> str:
    return code.strip().upper()


def generate_captcha_code(length: int = 4) -> str:
    return "".join(random.SystemRandom().choice(CAPTCHA_ALPHABET) for _ in range(length))


def hash_captcha_code(code: str) -> str:
    settings = get_settings()
    return hmac.digest(
        settings.captcha_secret_key.encode("utf-8"),
        normalize_captcha_code(code).encode("utf-8"),
        "sha256",
    ).hex()


def verify_captcha_code(code: str, code_hash: str) -> bool:
    return hmac.compare_digest(hash_captcha_code(code), code_hash)


def create_captcha_image_data_url(code: str) -> str:
    safe_code = escape(normalize_captcha_code(code))
    svg = f"""<svg xmlns="http://www.w3.org/2000/svg" width="160" height="64" viewBox="0 0 160 64">
  <rect width="160" height="64" rx="14" fill="#fbfff7"/>
  <path d="M12 45 C42 22, 76 56, 148 18"
    stroke="#9fcf95" stroke-width="3" fill="none" opacity="0.7"/>
  <text x="50%" y="53%" dominant-baseline="middle" text-anchor="middle"
    font-family="Arial, sans-serif" font-size="30" font-weight="700"
    letter-spacing="7" fill="#2f7b2e">{safe_code}</text>
</svg>"""
    encoded = b64encode(svg.encode("utf-8")).decode("ascii")
    return f"data:image/svg+xml;base64,{encoded}"
