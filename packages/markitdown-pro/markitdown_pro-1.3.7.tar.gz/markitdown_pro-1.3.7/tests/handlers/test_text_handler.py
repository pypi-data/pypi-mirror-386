import logging
from pathlib import Path

import pytest

from markitdown_pro.common.utils import ensure_minimum_content
from markitdown_pro.handlers.text_handler import TextHandler
from tests.fixtures import data_path, pretty_id
from tests.utils import list_files

log = logging.getLogger(__name__)

TEST_FILES_PATH = data_path()
ALL_FILES = list_files(
    TEST_FILES_PATH, include_ext=TextHandler.SUPPORTED_EXTENSIONS, recursive=True
)
log.info(f"Found {len(ALL_FILES)} test files in {TEST_FILES_PATH}.")


@pytest.mark.asyncio
@pytest.mark.parametrize("file_path", ALL_FILES, ids=[pretty_id(p) for p in ALL_FILES])
async def test_files(file_path: Path, text_handler: TextHandler):
    log.info(f"{TextHandler.__name__}: Testing file {file_path}")

    markdown_text = await text_handler.handle(str(file_path))
    assert markdown_text is not None, f"Conversion returned None for {file_path.name}"
    assert isinstance(markdown_text, str), f"Output type is not str for {file_path.name}"
    assert ensure_minimum_content(markdown_text), f"Output is empty for {file_path.name}"
