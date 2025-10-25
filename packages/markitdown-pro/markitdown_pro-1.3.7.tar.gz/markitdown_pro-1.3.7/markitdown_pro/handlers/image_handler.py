import contextlib
from pathlib import Path
from typing import List, Optional

from ..common.logger import logger
from ..common.utils import detect_extension
from ..converters.gpt_vision_wrapper import GPTVisionWrapper
from .base_handler import BaseHandler


class ImageHandler(BaseHandler):
    SUPPORTED_EXTENSIONS = GPTVisionWrapper.SUPPORTED_EXTENSIONS

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.gpt_vision_4_1_mini = GPTVisionWrapper(model_name="gpt-4.1-mini")
        self.gpt_vision_4_1 = GPTVisionWrapper(model_name="gpt-4.1")

        self.pipeline: List[GPTVisionWrapper] = [self.gpt_vision_4_1_mini, self.gpt_vision_4_1]

        self._max_retries = kwargs.get("max_retries", 2)
        self._base_delay = kwargs.get("base_delay", 0.5)
        self._max_delay = kwargs.get("max_delay", 10.0)

    async def handle(self, file_path, *args, **kwargs) -> Optional[str]:
        """
        Handles image files by converting them to Markdown using GPT Vision.

        Args:
            file_path: Path to the image file.

        Returns:
            Markdown string representing the image content (OCR and analysis),
            or an error message.
        """
        for handler in self.pipeline:
            try:
                logger.info(f"ImageHandler: Trying handler {handler.name} for file '{file_path}'")
                md_content = await handler.convert(
                    file_path,
                    max_retries=self._max_retries,
                    base_delay=self._base_delay,
                    max_delay=self._max_delay,
                )
                if md_content:
                    return md_content
            except Exception as e:
                logger.error(
                    f"ImageHandler: Handler {handler.name} failed for file '{file_path}': {e}"
                )
            finally:
                # Prevent "Event loop is closed" from httpx finalizers during pytest teardown
                with contextlib.suppress(Exception):
                    if hasattr(handler, "gpt_vision"):
                        await handler.gpt_vision.aclose()

        logger.error(f"ImageHandler: All handlers failed for file '{file_path}'")
        return None

    async def get_page_count(self, file_path: str | Path) -> Optional[int]:
        """
        Determines the number of pages in the given image file.
        """
        p = Path(file_path)
        ext = detect_extension(str(p.absolute()))
        if ext not in self.SUPPORTED_EXTENSIONS:
            logger.warning(f"ImageHandler: Unsupported file format: {ext}")
            return None

        if ext in {".tif", ".tiff"}:
            try:
                from PIL import Image, ImageSequence  # optional dependency

                with Image.open(str(p)) as im:
                    return sum(1 for _ in ImageSequence.Iterator(im)) or 1
            except Exception as e_tiff:
                logger.warning(f"ImageHandler: local TIFF page count failed for '{p}': {e_tiff}")
        else:
            return 1

    async def aclose(self) -> None:
        for handler in self.pipeline:
            if hasattr(handler, "gpt_vision") and handler.gpt_vision:
                await handler.gpt_vision.aclose()
