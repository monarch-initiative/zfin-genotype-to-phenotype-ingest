"""ZFIN Genotype to Phenotype Transform."""

import uuid
from typing import Any

import koza
from biolink_model.datamodel.pydanticmodel_v2 import (
    AgentTypeEnum,
    GenotypeToPhenotypicFeatureAssociation,
    KnowledgeLevelEnum,
)
from koza import KozaTransform
from koza.utils.exceptions import MapItemException
from loguru import logger

STANDARD_CONDITION = "ZECO:0000103"  # ZECO ID for the standard condition

seen_records: dict[str, str] = {}


@koza.transform_record()
def transform(koza_transform: KozaTransform, row: dict[str, Any]):
    """Transform a ZFIN phenotype row into a GenotypeToPhenotypicFeatureAssociation."""
    global seen_records

    # Only want abnormal phenotype here
    if row["Phenotype Tag"] == "normal":
        return

    # Pull out our key elements
    zp_key_elements = [
        row["Affected Structure or Process 1 subterm ID"],
        row["Post-composed Relationship ID"],
        row["Affected Structure or Process 1 superterm ID"],
        row["Phenotype Keyword ID"],
        row["Affected Structure or Process 2 subterm ID"],
        row["Post-composed Relationship (rel) ID"],
        row["Affected Structure or Process 2 superterm ID"],
    ]

    zp_key = "-".join([element or "0" for element in zp_key_elements])

    # Look up ZP term - lookup returns the value for the column, or the key if not found (warning mode)
    try:
        zp_term = koza_transform.lookup(zp_key, "iri", map_name="eqe2zp")
        # If lookup returns the key itself, it means the lookup failed (warning mode default)
        if zp_term == zp_key:
            logger.debug(f"ZP concatenation {zp_key} did not match a ZP term")
            return
    except MapItemException:
        logger.debug(f"ZP concatenation {zp_key} did not match a ZP term")
        return

    if not zp_term:
        logger.debug(f"ZP concatenation {zp_key} did not match a ZP term")
        return

    # Look up environment
    env_id = row["Environment ID"]
    try:
        zeco_term = koza_transform.lookup(env_id, "ZECO Term ID (ZECO:ID)", map_name="pheno_environment_fish")
        if zeco_term == env_id:
            logger.debug(f"Environment ID {env_id} not found in pheno_environment_fish map")
            return
    except MapItemException:
        logger.debug(f"Environment ID {env_id} not found in pheno_environment_fish map")
        return

    if zeco_term != STANDARD_CONDITION:
        logger.debug("ZP Environment not standard condition")
        return

    # This data has multiple "life stages" of the animal so we don't want to have duplicates
    key = "-".join([row["Fish ID"], row["Publication ID"], zp_term])
    if key in seen_records:
        logger.debug(
            f"Duplicate record found presumably for differences in life stages, Record={key}, LifeStage={row['End Stage Name']}"
        )
        return
    else:
        seen_records[key] = ""

    zdb_pub_id = row["Publication ID"]

    # Look up PubMed ID
    try:
        pubmed_id = koza_transform.lookup(zdb_pub_id, "pubmed", map_name="pub2pubmed")
        if pubmed_id and pubmed_id != zdb_pub_id:
            publication_id = "PMID:" + pubmed_id
        else:
            publication_id = "ZFIN:" + zdb_pub_id
    except MapItemException:
        publication_id = "ZFIN:" + zdb_pub_id

    association = GenotypeToPhenotypicFeatureAssociation(
        id=str(uuid.uuid1()),
        subject="ZFIN:" + row["Fish ID"],
        predicate="biolink:has_phenotype",
        object=zp_term,
        publications=[publication_id],
        aggregator_knowledge_source=["infores:monarchinitiative"],
        primary_knowledge_source="infores:zfin",
        knowledge_level=KnowledgeLevelEnum.knowledge_assertion,
        agent_type=AgentTypeEnum.manual_agent,
    )
    koza_transform.write(association)
