def test_project_context_exists() -> None:
    from pathlib import Path

    root = Path(__file__).resolve().parents[3]
    assert (root / "docs" / "project-context.md").exists()
