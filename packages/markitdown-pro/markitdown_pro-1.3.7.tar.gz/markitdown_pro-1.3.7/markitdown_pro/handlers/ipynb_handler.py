from typing import Optional

import nbformat

from ..common.logger import logger
from .base_handler import BaseHandler


class IpynbHandler(BaseHandler):
    """Handler for Jupyter notebooks (.ipynb)."""

    SUPPORTED_EXTENSIONS = frozenset([".ipynb"])

    async def handle(self, file_path: str, *args, **kwargs) -> Optional[str]:
        logger.info(f"IpynbHandler: Processing notebook: {file_path}")
        try:
            nb = nbformat.read(file_path, as_version=4)
            cells_content = []
            for cell in nb.cells:
                if cell.cell_type == "markdown":
                    cells_content.append(cell.source)
                elif cell.cell_type == "code":
                    cells_content.append("```python\n" + cell.source + "\n```")
            result = "\n\n".join(cells_content)
            return result
        except Exception as e:
            logger.error(f"IpynbHandler: Error processing notebook {file_path}: {e}")
            return None
