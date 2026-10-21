
import logging
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path

URL = "http://localhost:8080"
TIMEOUT = 5
MAX_ATTEMPTS = 3
RETRY_INTERVAL = 2

LOG_FILE = Path(__file__).resolve().parent / "monitor.log"

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s",
    handlers=[
        logging.FileHandler(LOG_FILE, encoding="utf-8"),
        logging.StreamHandler(),
    ],
)

logger = logging.getLogger(__name__)


def check_service():
    for attempt in range(1, MAX_ATTEMPTS + 1):
        try:
            with urllib.request.urlopen(URL, timeout=TIMEOUT) as response:
                status = response.status

                if status == 200:
                    logger.info(
                        "Serviço disponível | HTTP %s | Tentativa %s",
                        status,
                        attempt,
                    )
                    return True

                logger.warning(
                    "Resposta inesperada | HTTP %s | Tentativa %s",
                    status,
                    attempt,
                )

        except (urllib.error.URLError, TimeoutError) as error:
            logger.error(
                "Falha na conexão | Tentativa %s/%s | %s",
                attempt,
                MAX_ATTEMPTS,
                error,
            )

        if attempt < MAX_ATTEMPTS:
            time.sleep(RETRY_INTERVAL)

    logger.critical("Serviço indisponível após todas as tentativas")
    return False


if __name__ == "__main__":
    sys.exit(0 if check_service() else 1)
