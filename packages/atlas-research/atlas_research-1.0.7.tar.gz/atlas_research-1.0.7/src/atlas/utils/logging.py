import logging, os

LOG_DIR = "logs"
os.makedirs(LOG_DIR, exist_ok=True)

logging.basicConfig(
    filename=os.path.join(LOG_DIR, "atlas.log"),
    level=logging.INFO,
    format="[%(asctime)s] [%(levelname)s] %(message)s",
)

logger = logging.getLogger("atlas")
