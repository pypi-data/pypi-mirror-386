from __future__ import annotations

import pytest

import os, tempfile
from pathlib import Path

from baseprinter import cli


BASEPRINT_CASE_DIR = Path(__file__).parent / "cases" / "baseprint"
BASEPRINT_CASES = os.listdir(BASEPRINT_CASE_DIR)
if os.getenv("BASEPRINTER_JATS") != "OFF":
    BASEPRINT_CASES = ["empty", "meta_title_tags", "hello", "author1"]


def _run(args) -> int:
    if isinstance(args, str):
        args = args.split()
    return cli.main(args)


@pytest.mark.parametrize("case", BASEPRINT_CASES)
def test_baseprint_output(case):
    expect_xml = BASEPRINT_CASE_DIR / case / "expect/article.xml"
    src_dir = BASEPRINT_CASE_DIR / case / "src"
    src_files = os.listdir(src_dir)
    assert len(src_files), f"Source files missing from {src_dir}"
    if len(src_files) == 1:
        args = src_files[0]
    else:
        args = "-d pandocin.yaml"
    os.chdir(src_dir)
    with tempfile.TemporaryDirectory() as tmp:
        assert 0 == _run(f"{args} -b {tmp}/baseprint")
        got = Path(f"{tmp}/baseprint/article.xml").read_text()
    assert got == expect_xml.read_text()
