"""
An example test file for the transform script.

It uses pytest fixtures to define the input data and the mock koza transform.
The test_example function then tests the output of the transform script.

See the Koza documentation for more information on testing transforms:
https://koza.monarchinitiative.org/Usage/testing/
"""

import pytest

# Define the ingest name and transform script path
INGEST_NAME = "zfin_genotype_to_phenotype"
TRANSFORM_SCRIPT = "./src/zfin_genotype_to_phenotype_ingest/transform.py"


@pytest.fixture
def map_cache():
    eqe2zp = {'0-0-GO:0007519-PATO:0002302-0-0-0': {'iri': 'ZP:0008064'}}
    pub2pubmed = {'ZDB-PUB-131119-10': {'pubmed': '24131632'}}
    pheno_environment_fish = {'ZDB-EXP-140122-5': {'ZECO Term ID (ZECO:ID)': 'ZECO:0000103'}}
    return {"eqe2zp": eqe2zp, "pub2pubmed": pub2pubmed, "pheno_environment_fish": pheno_environment_fish}


# Define an example row to test (as a dictionary)
@pytest.fixture
def row():
    return {
        'Fish ID': 'ZDB-FISH-150901-10',
        'Fish Name': 'AB/TU + MO1-itga7',
        'Start Stage ID': 'ZDB-STAGE-010723-35',
        'Start Stage Name': 'Larval:Day 4',
        'End Stage ID': 'ZDB-STAGE-010723-35',
        'End Stage Name': 'Larval:Day 4',
        'Affected Structure or Process 1 subterm ID': '',
        'Affected Structure or Process 1 subterm Name': '',
        'Post-composed Relationship ID': '',
        'Post-composed Relationship Name': '',
        'Affected Structure or Process 1 superterm ID': 'GO:0007519',
        'Affected Structure or Process 1 superterm Name': 'skeletal muscle tissue development',
        'Phenotype Keyword ID': 'PATO:0002302',
        'Phenotype Keyword Name': 'decreased process quality',
        'Phenotype Tag': 'abnormal',
        'Affected Structure or Process 2 subterm ID': '',
        'Affected Structure or Process 2 subterm name': '',
        'Post-composed Relationship (rel) ID': '',
        'Post-composed Relationship (rel) Name': '',
        'Affected Structure or Process 2 superterm ID': '',
        'Affected Structure or Process 2 superterm name': '',
        'Publication ID': 'ZDB-PUB-131119-10',
        'Environment ID': 'ZDB-EXP-140122-5',
    }


# Define the mock koza transform
@pytest.fixture
def entities(mock_koza, row, map_cache):
    # Returns [entity_a, entity_b, association] for a single row
    return mock_koza(
        INGEST_NAME,
        row,
        TRANSFORM_SCRIPT,
        map_cache=map_cache,
    )


def test_row(entities):
    assert len(entities) == 1
    entity = entities[0]
    assert entity.category == ['biolink:GenotypeToPhenotypicFeatureAssociation']
    assert entity.subject == 'ZFIN:ZDB-FISH-150901-10'
    assert entity.predicate == 'biolink:has_phenotype'
    assert entity.object == 'ZP:0008064'
    assert entity.publications == ['PMID:24131632']
