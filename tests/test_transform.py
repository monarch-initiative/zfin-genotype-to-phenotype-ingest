"""
Test file for the ZFIN genotype to phenotype transform.

Uses Koza 2.x KozaRunner pattern with PassthroughWriter.
"""

import importlib.util
from pathlib import Path
from typing import Any

import pytest
from koza import KozaTransform
from koza.io.writer.passthrough_writer import PassthroughWriter
from koza.runner import KozaRunner, load_transform

# Define the transform script path
TRANSFORM_SCRIPT = Path(__file__).parent.parent / "src" / "transform.py"

# Define map file paths
MAP_DIR = Path(__file__).parent.parent / "src"


def load_module_from_path(path: Path):
    """Load a Python module from a file path."""
    spec = importlib.util.spec_from_file_location(path.stem, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def run_transform_with_mappings(rows: list[dict], mappings: dict[str, dict[str, dict[str, str]]]) -> list:
    """Run the transform on given rows with provided mappings and return entities."""
    module = load_module_from_path(TRANSFORM_SCRIPT)
    hooks = load_transform(module)
    writer = PassthroughWriter()

    # Create a custom KozaTransform with the mappings
    # We need to manually run the transform since KozaRunner doesn't accept mappings directly
    from koza.runner import KozaTransformHooks

    hooks_obj = hooks.get(None)
    if hooks_obj is None:
        raise ValueError("No hooks found")

    koza_transform = KozaTransform(
        mappings=mappings,
        writer=writer,
        extra_fields={},
    )

    # Run the transform_record functions on each row
    for row in rows:
        for transform_fn in hooks_obj.transform_record:
            result = transform_fn(koza_transform, row)
            if result is not None:
                writer.write(result)

    writer.finalize()
    return writer.data


@pytest.fixture
def mappings():
    """Provide test mapping data in the format expected by KozaTransform."""
    return {
        "eqe2zp": {
            "0-0-GO:0007519-PATO:0002302-0-0-0": {"iri": "ZP:0008064"},
        },
        "pub2pubmed": {
            "ZDB-PUB-131119-10": {"pubmed": "24131632"},
        },
        "pheno_environment_fish": {
            "ZDB-EXP-140122-5": {"ZECO Term ID (ZECO:ID)": "ZECO:0000103"},
        },
    }


@pytest.fixture
def row():
    """Provide an example row to test."""
    return {
        "Fish ID": "ZDB-FISH-150901-10",
        "Fish Name": "AB/TU + MO1-itga7",
        "Start Stage ID": "ZDB-STAGE-010723-35",
        "Start Stage Name": "Larval:Day 4",
        "End Stage ID": "ZDB-STAGE-010723-35",
        "End Stage Name": "Larval:Day 4",
        "Affected Structure or Process 1 subterm ID": "",
        "Affected Structure or Process 1 subterm Name": "",
        "Post-composed Relationship ID": "",
        "Post-composed Relationship Name": "",
        "Affected Structure or Process 1 superterm ID": "GO:0007519",
        "Affected Structure or Process 1 superterm Name": "skeletal muscle tissue development",
        "Phenotype Keyword ID": "PATO:0002302",
        "Phenotype Keyword Name": "decreased process quality",
        "Phenotype Tag": "abnormal",
        "Affected Structure or Process 2 subterm ID": "",
        "Affected Structure or Process 2 subterm name": "",
        "Post-composed Relationship (rel) ID": "",
        "Post-composed Relationship (rel) Name": "",
        "Affected Structure or Process 2 superterm ID": "",
        "Affected Structure or Process 2 superterm name": "",
        "Publication ID": "ZDB-PUB-131119-10",
        "Environment ID": "ZDB-EXP-140122-5",
    }


def test_row(row, mappings):
    """Test that the transform produces the expected output."""
    # Reset seen_records for this test
    import src.transform as transform_module
    transform_module.seen_records = {}

    entities = run_transform_with_mappings([row], mappings)
    assert len(entities) == 1
    entity = entities[0]
    assert entity.category == ["biolink:GenotypeToPhenotypicFeatureAssociation"]
    assert entity.subject == "ZFIN:ZDB-FISH-150901-10"
    assert entity.predicate == "biolink:has_phenotype"
    assert entity.object == "ZP:0008064"
    assert entity.publications == ["PMID:24131632"]


def test_normal_phenotype_skipped(row, mappings):
    """Test that normal phenotypes are skipped."""
    import src.transform as transform_module
    transform_module.seen_records = {}

    row["Phenotype Tag"] = "normal"
    entities = run_transform_with_mappings([row], mappings)
    assert len(entities) == 0


def test_non_standard_condition_skipped(row, mappings):
    """Test that non-standard conditions are skipped."""
    import src.transform as transform_module
    transform_module.seen_records = {}

    # Create a copy of mappings with modified environment
    test_mappings = {
        "eqe2zp": mappings["eqe2zp"].copy(),
        "pub2pubmed": mappings["pub2pubmed"].copy(),
        "pheno_environment_fish": {
            "ZDB-EXP-140122-5": {"ZECO Term ID (ZECO:ID)": "ZECO:0000001"},
        },
    }
    entities = run_transform_with_mappings([row], test_mappings)
    assert len(entities) == 0


def test_missing_zp_term_skipped(row, mappings):
    """Test that rows with missing ZP terms are skipped."""
    import src.transform as transform_module
    transform_module.seen_records = {}

    # Use a ZP key that doesn't exist in the map
    row["Affected Structure or Process 1 superterm ID"] = "GO:9999999"
    entities = run_transform_with_mappings([row], mappings)
    assert len(entities) == 0


def test_publication_fallback_to_zfin(row, mappings):
    """Test that publication falls back to ZFIN ID when no PubMed mapping exists."""
    import src.transform as transform_module
    transform_module.seen_records = {}

    # Use a publication ID that doesn't exist in the map
    row["Publication ID"] = "ZDB-PUB-000000-00"
    # Create mappings with empty pubmed for this ID
    test_mappings = {
        "eqe2zp": mappings["eqe2zp"].copy(),
        "pub2pubmed": {
            "ZDB-PUB-000000-00": {"pubmed": ""},
        },
        "pheno_environment_fish": mappings["pheno_environment_fish"].copy(),
    }
    entities = run_transform_with_mappings([row], test_mappings)
    assert len(entities) == 1
    assert entities[0].publications == ["ZFIN:ZDB-PUB-000000-00"]
