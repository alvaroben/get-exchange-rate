import re
import os
import logging
from bs4 import BeautifulSoup
import requests
from dotenv import load_dotenv

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

load_dotenv()

URL = "https://dgii.gov.do/estadisticas/tasaCambio/Paginas/default.aspx"


def update_alegra_rate(rate_value):
    logger.info(f"Starting Alegra API update with exchange rate: {rate_value}")

    alegra_api = f"https://api.alegra.com/api/v1/currencies/USD"
    alegra_api_token = os.getenv("ALEGRA_API_TOKEN")

    if not alegra_api_token:
        logger.error("ALEGRA_API_TOKEN not found in environment variables")
        raise ValueError("Missing ALEGRA_API_TOKEN")

    alegra_headers = {
        "accept": "application/json",
        "content-type": "application/json",
        "authorization": f"Basic {alegra_api_token}"
    }
    payload = {"exchangeRate": rate_value}

    logger.info(f"Sending PUT request to Alegra API: {alegra_api}")

    try:
        alegra_response = requests.put(alegra_api, json=payload, headers=alegra_headers)
        alegra_response.raise_for_status()
        logger.info(f"Successfully updated Alegra exchange rate. Status code: {alegra_response.status_code}")
    except requests.exceptions.RequestException as e:
        logger.error(f"Failed to update Alegra exchange rate: {str(e)}")
        raise


def get_rate():
    logger.info(f"Starting exchange rate retrieval from DGII website: {URL}")

    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36"
    }

    logger.info("Sending GET request to DGII website")
    response = requests.get(URL, headers=headers, timeout=15)
    response.raise_for_status()
    logger.info(f"Successfully received response from DGII. Status code: {response.status_code}")

    logger.info("Parsing HTML content with BeautifulSoup")
    soup = BeautifulSoup(response.text, 'html.parser')
    scripts = soup.find_all("script")
    logger.info(f"Found {len(scripts)} script tags in the page")

    logger.info("Searching for script containing 'Dólar' keyword")
    script_con_data = ""
    for s in scripts:
        if s.string and "Dólar" in s.string:
            script_con_data = s.string
            logger.info("Found script with exchange rate data")
            break

    if not script_con_data:
        logger.error("No script containing 'Dólar' keyword was found")

    logger.info("Extracting exchange rate value using regex pattern")
    match = re.search(r"RD\$\s*([\d\.]+)", script_con_data)

    if match:
        rate_value = float(match.group(1))
        rate_value = int(rate_value * 100) / 100
        logger.info(f"Successfully extracted exchange rate: {rate_value} DOP/USD")
        os.environ["USD_EXCHANGE_RATE"] = rate_value
        update_alegra_rate(rate_value)
        logger.info("Exchange rate retrieval and update process completed successfully")
        return rate_value

    return None


if __name__ == "__main__":
    get_rate()
