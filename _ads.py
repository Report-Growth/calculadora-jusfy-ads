"""Cliente Google Ads com as mesmas credenciais do conector local (somente leitura)."""
import os
from pathlib import Path
from dotenv import load_dotenv
from google.ads.googleads.client import GoogleAdsClient

# Pasta do conector Google Ads (com o .env das credenciais). Defina GOOGLE_ADS_CONECTOR_DIR
# ou coloque um .env nesta pasta.
CONECTOR = Path(os.getenv("GOOGLE_ADS_CONECTOR_DIR", Path(__file__).parent))
load_dotenv(CONECTOR / ".env")


def client(login=None):
    return GoogleAdsClient.load_from_dict({
        "developer_token": os.getenv("GOOGLE_ADS_DEVELOPER_TOKEN"),
        "client_id": os.getenv("GOOGLE_ADS_CLIENT_ID"),
        "client_secret": os.getenv("GOOGLE_ADS_CLIENT_SECRET"),
        "refresh_token": os.getenv("GOOGLE_ADS_REFRESH_TOKEN"),
        "login_customer_id": login or os.getenv("GOOGLE_ADS_LOGIN_CUSTOMER_ID"),
        "use_proto_plus": True,
    })


def default_cid():
    return os.getenv("GOOGLE_ADS_CUSTOMER_ID")
