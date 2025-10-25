import json
import os
from typing import Optional

import yaml
from bs4 import BeautifulSoup

try:
    import chardet
except ImportError:
    chardet = None

from ..common.logger import logger
from .base_handler import BaseHandler


class MarkupHandler(BaseHandler):
    """Handler for .html, .xml, .json, .ndjson, .yaml, .yml files."""

    SUPPORTED_EXTENSIONS = frozenset([".html", ".htm", ".xml", ".json", ".ndjson", ".yaml", ".yml"])

    async def handle(self, file_path: str, *args, **kwargs) -> Optional[str]:
        logger.info(f"MarkupHandler: Processing markup file: {file_path}")
        try:
            ext = os.path.splitext(file_path)[1].lower()

            # Detect encoding
            encoding = "utf-8"  # Default
            if chardet:
                with open(file_path, "rb") as f:
                    raw_data = f.read()
                    result = chardet.detect(raw_data)
                    encoding = result["encoding"]
                    logger.debug(f"MarkupHandler: Detected encoding: {encoding}")
            else:
                logger.warning("MarkupHandler: chardet not available, assuming UTF-8 encoding.")

            with open(file_path, "r", encoding=encoding) as f:
                content = f.read()

            if ext in [".html", ".htm"]:
                soup = BeautifulSoup(content, "html.parser")
                text = soup.get_text(separator="\n")
            elif ext == ".xml":
                soup = BeautifulSoup(content, "xml")
                text = soup.get_text(separator="\n")
            elif ext in [".json", ".ndjson"]:
                try:
                    # Attempt to parse as complete JSON
                    data = json.loads(content)
                    text = json.dumps(data, indent=2, ensure_ascii=False)
                except Exception:
                    # If not, process line by line (ndjson case)
                    lines = content.splitlines()
                    parsed_lines = []
                    for line in lines:
                        try:
                            obj = json.loads(line)
                            parsed_lines.append(json.dumps(obj, indent=2, ensure_ascii=False))
                        except Exception:
                            parsed_lines.append(line)
                    text = "\n".join(parsed_lines)
            elif ext in [".yaml", ".yml"]:
                data = yaml.safe_load(content)
                text = yaml.dump(data, allow_unicode=True)
            else:
                text = content

            return text
        except Exception as e:
            logger.error(f"MarkupHandler: Error processing markup file {file_path}: {e}")
            return None
