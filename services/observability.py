import logging
from langfuse import Langfuse
from config import LANGFUSE_PUBLIC_KEY, LANGFUSE_SECRET_KEY, LANGFUSE_HOST

logger = logging.getLogger(__name__)

# Initialize Langfuse
if LANGFUSE_PUBLIC_KEY and LANGFUSE_SECRET_KEY:
    langfuse = Langfuse(
        public_key=LANGFUSE_PUBLIC_KEY,
        secret_key=LANGFUSE_SECRET_KEY,
        host=LANGFUSE_HOST
    )
    logger.info("Langfuse Observability initialized.")
else:
    langfuse = None
    logger.warning("Langfuse keys missing. Observability disabled.")

def safe_flush():
    if langfuse:
        langfuse.flush()
