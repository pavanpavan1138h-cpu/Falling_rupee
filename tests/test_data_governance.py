"""Validation checks for the POME EL data governance and experiment foundation."""

from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

REQUIRED_DOCS = (
    "reports/data_audit/DATASET_REGISTRY.md",
    "reports/data_audit/DATA_DICTIONARY_TEMPLATE.md",
    "reports/data_audit/DATA_VALIDATION_PROTOCOL.md",
    "reports/research/FEATURE_INVENTORY.md",
    "reports/research/TIME_SERIES_VALIDATION_PROTOCOL.md",
    "reports/experiments/EXPERIMENT_PROTOCOL.md",
)

REQUIRED_CONTRACTS = (
    "exchange_rate",
    "crude_oil",
    "indian_cpi",
    "rbi_policy_rate",
    "neer_reer",
    "indian_wpi",
    "macro_controls",
)


def _read_text(relative_path: str) -> str:
    return (ROOT / relative_path).read_text(encoding="utf-8")


def _check_yaml_structure() -> None:
    text = _read_text("config/data_contracts.yaml")
    non_comment_lines = [
        line for line in text.splitlines() if line.strip() and not line.lstrip().startswith("#")
    ]

    assert non_comment_lines[0].startswith("version:"), "YAML must define a version field."
    assert any(line.strip() == "contracts:" for line in non_comment_lines), (
        "YAML must define contracts."
    )

    contract_starts = [
        idx
        for idx, line in enumerate(non_comment_lines)
        if line.lstrip().startswith("- dataset_id:")
    ]
    assert contract_starts, "At least one contract entry is required."

    for idx, start_index in enumerate(contract_starts):
        end_index = (
            contract_starts[idx + 1] if idx + 1 < len(contract_starts) else len(non_comment_lines)
        )
        current_block = non_comment_lines[start_index:end_index]
        assert any("dataset_id:" in line for line in current_block), (
            "Contract block missing dataset_id."
        )
        assert any("category:" in line for line in current_block), (
            "Contract block missing category."
        )
        assert any("expected_frequency:" in line for line in current_block), (
            "Contract block missing expected_frequency."
        )
        assert any("validation_requirements:" in line for line in current_block), (
            "Contract block missing validation_requirements."
        )

    assert len(contract_starts) == len(REQUIRED_CONTRACTS), (
        "Contract count does not match the expected major categories."
    )

    dataset_ids = []
    for line in non_comment_lines:
        if line.lstrip().startswith("- dataset_id:"):
            dataset_ids.append(line.split(":", 1)[1].strip())
    assert len(dataset_ids) == len(set(dataset_ids)), "Dataset identifiers must be unique."


def test_required_governance_documents_exist() -> None:
    for relative_path in REQUIRED_DOCS:
        assert (ROOT / relative_path).exists(), (
            f"Missing required governance document: {relative_path}"
        )


def test_required_directories_exist() -> None:
    required_dirs = (
        ROOT / "reports" / "data_audit",
        ROOT / "reports" / "research",
        ROOT / "reports" / "experiments",
        ROOT / "config",
    )
    for directory in required_dirs:
        assert directory.exists(), f"Missing required directory: {directory}"


def test_data_contract_structure_is_consistent() -> None:
    _check_yaml_structure()
    contract_text = _read_text("config/data_contracts.yaml")
    for dataset_id in REQUIRED_CONTRACTS:
        assert f"dataset_id: {dataset_id}" in contract_text, (
            f"Missing contract declaration: {dataset_id}"
        )


def test_document_headers_are_present() -> None:
    headers = {
        "reports/data_audit/DATASET_REGISTRY.md": "# POME EL Dataset Registry",
        "reports/data_audit/DATA_DICTIONARY_TEMPLATE.md": ("# POME EL Data Dictionary Template"),
        "reports/data_audit/DATA_VALIDATION_PROTOCOL.md": ("# POME EL Data Validation Protocol"),
        "reports/research/FEATURE_INVENTORY.md": "# POME EL Feature Inventory",
        "reports/research/TIME_SERIES_VALIDATION_PROTOCOL.md": (
            "# POME EL Time-Series Validation and Leakage Prevention Protocol"
        ),
        "reports/experiments/EXPERIMENT_PROTOCOL.md": ("# POME EL Experiment Protocol"),
    }
    for relative_path, header in headers.items():
        assert header in _read_text(relative_path), f"Header missing from: {relative_path}"
