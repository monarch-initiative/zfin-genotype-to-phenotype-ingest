# zfin-genotype-to-phenotype-ingest

This is a Koza ingest repository for transforming ZFIN (Zebrafish Information Network) genotype-to-phenotype data into Biolink model format.

## Project Structure

- `download.yaml` - Configuration for downloading ZFIN data files
- `src/` - Transform code and configuration
  - `transform.py` / `transform.yaml` - Main transform for genotype-phenotype associations
  - `eqe2zp.yaml` - Mapping from ZFIN EQE to ZP terms
  - `pheno_environment_fish.yaml` - Mapping from ZFIN environment to ZECO IDs
  - `pub2pubmed.yaml` - Mapping from ZFIN publication IDs to PubMed IDs
- `tests/` - Unit tests for transforms
- `output/` - Generated nodes and edges (gitignored)
- `data/` - Downloaded source data (gitignored)

## Key Commands

- `just run` - Full pipeline (download -> transform)
- `just download` - Download ZFIN data files
- `just transform-all` - Run all transforms
- `just test` - Run tests

## Data Sources

This ingest uses data from:
- `phenotype_fish.txt` - Main phenotype data
- `id_map_zfin.tsv` - EQE to ZP term mapping
- `pheno_environment_fish.txt` - Environment to ZECO mapping
- `pub_to_pubmed_id_translation.txt` - Publication ID mapping
