"""The published handbook must follow the current CLI and have usable entry links."""
from pathlib import Path
import re
import runpy
from urllib.parse import unquote, urlsplit

ROOT = Path(__file__).resolve().parents[1]


def test_reference_pages_match_current_commands_and_configuration():
    generate = runpy.run_path(str(ROOT / "scripts/generate_references.py"))["reference_pages"]
    for language in ("en", "zh"):
        for path, expected in generate(language):
            actual = path.read_text(encoding="utf-8")
            # argparse versions vary wrapping and repeat metavars before aliases.
            actual = re.sub(r"(--[\w-]+) [A-Z_]+(?=, --)", r"\1", actual)
            expected = re.sub(r"(--[\w-]+) [A-Z_]+(?=, --)", r"\1", expected)
            assert actual.split() == expected.split(), f"Refresh {path.name} with scripts/generate_references.py"


def test_bilingual_guide_links_resolve_in_the_distribution_source():
    guide = ROOT / "docs/guide"
    assert {p.name for p in (guide / "en").glob("*.md")} == {p.name for p in (guide / "zh-CN").glob("*.md")}
    pages = [ROOT / "README.md", ROOT / "README.zh-CN.md", ROOT / "docs/desktop.md", *guide.rglob("*.md")]
    for page in pages:
        for target in re.findall(r"\]\(([^\s)]+)\)", page.read_text(encoding="utf-8")):
            url = urlsplit(target)
            if url.scheme:
                prefixes = ("/konbakuyomu/smartsearch/blob/main/", "/konbakuyomu/smartsearch/tree/main/")
                prefix = next((p for p in prefixes if url.path.startswith(p)), None)
                if url.netloc != "github.com" or prefix is None:
                    continue
                destination = ROOT / unquote(url.path[len(prefix):])
            else:
                destination = page.parent / unquote(url.path)
            assert destination.exists(), f"{page.relative_to(ROOT)}: missing {target}"
