import json
from pathlib import Path
from tempfile import TemporaryDirectory

from experiments.runtime_v5_0_compiled_surface_skill.compiler import compile_skill
from experiments.runtime_v5_0_output_fidelity_mega_campaign.instance import RichSurfaceInstance
from experiments.runtime_v5_0_output_fidelity_mega_campaign.model import canonical_bytes


ROOT = Path(__file__).resolve().parents[3]
FIXTURES = Path(__file__).resolve().parents[1] / "fixtures"


def test_disposable_instance_realizes_and_replays_markdown() -> None:
    field = json.loads((FIXTURES / "rich-surface-field-en-1.0.json").read_text())
    compilation = compile_skill((FIXTURES / "markdown-structure" / "SKILL.md").read_text(), field)
    thresholds = json.loads((ROOT / "config/v5.0/grounding-en-1.0.json").read_text())["thresholds"]
    prompt = "Direct courier lacks cold storage. Direct courier has road permit. Direct courier can meet the deadline. Backup courier has refrigeration. Backup courier has road permit. Backup courier can meet the deadline. Validate the proposed plan and select a replacement."
    with TemporaryDirectory() as temporary:
        instance = RichSurfaceInstance(
            Path(temporary) / "candidate",
            project_root=ROOT,
            field=field,
            compilations={"MARKDOWN_STRUCTURE": compilation},
            thresholds=thresholds,
        )
        package = instance.query(prompt, "Return a Markdown table.")
        assert package["artifact"]["mode"] == "MARKDOWN_TABLE"
        assert instance.replay(package["archive"]) == canonical_bytes(package["archive"])
        assert instance.store_path != ROOT / "data/store-5.0.sqlite3"

