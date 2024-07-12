import uuid  # For generating UUIDs for associations

from biolink_model.datamodel.pydanticmodel_v2 import (  # Replace * with any necessary data classes from the Biolink Model
    AgentTypeEnum,
    GenotypeToPhenotypicFeatureAssociation,
    KnowledgeLevelEnum,
)
from koza.cli_utils import get_koza_app
from loguru import logger

koza_app = get_koza_app("zfin_genotype_to_phenotype")
eqe2zp = koza_app.get_map("eqe2zp")
pheno_environment_fish = koza_app.get_map("pheno_environment_fish")
pub2pubmed = koza_app.get_map("pub2pubmed")

standard_condition = "ZECO:0000103"  # This is the ZECO ID for the standard condition

seen_records = {}
while (row := koza_app.get_row()) is not None:
    # Code to transform each row of data
    # For more information, see https://koza.monarchinitiative.org/Ingests/transform

    # Only want abonormal phenotype here
    if row["Phenotype Tag"] == "normal":
        continue

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
    zp_term = eqe2zp[zp_key]["iri"]
    zeco_term = pheno_environment_fish[row["Environment ID"]]["ZECO Term ID (ZECO:ID)"]

    if not zp_term:
        logger.debug("ZP concatenation " + zp_key + " did not match a ZP term")
        continue

    if zeco_term != standard_condition:
        logger.debug("ZP Environment not standard condition")
        continue

    ### This data has multiple "life stages" of the animal so we don't want to have duplicates
    key = '-'.join([row["Fish ID"], row["Publication ID"], zp_term])
    if key in seen_records:
        logger.debug(
            "Duplicate record found presumably for differences in life stages, Record={}, LifeStage={}".format(
                key, row["End Stage Name"]
            )
        )
        continue
    else:
        seen_records.update({key: ''})

    publication_id = None
    zdb_pub_id = row["Publication ID"]

    if zdb_pub_id in pub2pubmed and pub2pubmed[zdb_pub_id]["pubmed"]:
        publication_id = "PMID:" + pub2pubmed[zdb_pub_id]["pubmed"]
    else:
        publication_id = "ZFIN:" + zdb_pub_id

    print(row)
    print({zp_key: eqe2zp[zp_key]})
    print({zdb_pub_id: pub2pubmed[zdb_pub_id]})
    print({row["Environment ID"]: pheno_environment_fish[row["Environment ID"]]})
    print("===========================================")

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
    koza_app.write(association)

    ### TO DO - Properly map enviornment ID to ZECO ID from the https://zfin.org/downloads/pheno_environment_fish.txt file then based on the ZECO ID skip or represent the data with the proper biolink association
    ### For now we will just only use standard condition...
    ### Do we want to add "Stages" columns as qualifiers?
