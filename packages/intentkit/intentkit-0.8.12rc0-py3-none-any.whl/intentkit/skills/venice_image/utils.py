import base64
import io
import logging
from typing import Optional

import filetype
import httpx
from PIL import Image
from pydantic import HttpUrl

from intentkit.skills.base import ToolException

logger = logging.getLogger(__name__)


async def fetch_image_as_bytes(image_url: HttpUrl) -> bytes:
    """Fetches image bytes from a given URL. Converts unsupported formats to PNG using Pillow.

    Raises:
        ToolException: If fetching or converting the image fails.
    """
    try:
        async with httpx.AsyncClient(timeout=90) as client:
            response = await client.get(str(image_url), follow_redirects=True)
            response.raise_for_status()

            original_bytes = response.content

            # Guess file type from content
            kind = filetype.guess(original_bytes)
            detected_ext = kind.extension if kind else None
            detected_mime = kind.mime if kind else "unknown"

            if not detected_ext or not detected_mime.startswith("image/"):
                msg = f"URL {image_url} did not return a recognizable image format. Detected: {detected_mime}"
                logger.error(msg)
                raise ToolException(msg)

            if detected_ext in ("jpg", "jpeg", "png"):
                return original_bytes

            # Convert unsupported image to PNG
            try:
                img = Image.open(io.BytesIO(original_bytes)).convert("RGBA")
                with io.BytesIO() as output:
                    img.save(output, format="PNG")
                    logger.info(
                        f"Converted unsupported image type '{detected_ext}' to PNG."
                    )
                    return output.getvalue()
            except Exception as e:
                msg = f"Failed to convert image ({detected_ext}) to PNG: {e}"
                logger.error(msg, exc_info=True)
                raise ToolException(msg) from e

    except httpx.HTTPStatusError as e:
        msg = f"HTTP error fetching image {image_url}: Status {e.response.status_code}"
        logger.error(msg)
        raise ToolException(msg) from e
    except httpx.RequestError as e:
        msg = f"Network error fetching image {image_url}: {e}"
        logger.error(msg)
        raise ToolException(msg) from e
    except Exception as e:
        msg = f"Unexpected error fetching image {image_url}: {e}"
        logger.error(msg, exc_info=True)
        raise ToolException(msg) from e


async def fetch_image_as_base64(image_url: HttpUrl) -> Optional[str]:
    """Fetches an image from the URL and returns the image as a Base64-encoded string."""
    image_bytes = await fetch_image_as_bytes(image_url)

    if image_bytes is None:
        return None

    # Convert image bytes to a Base64-encoded string
    return base64.b64encode(image_bytes).decode("utf-8")
