# zfin-genotype-to-phenotype-ingest

Koza ingest for ZFIN (Zebrafish Information Network) genotype-to-phenotype data, transforming zebrafish phenotype annotations into Biolink model format.

## Data Source

[ZFIN](https://zfin.org/) is the central repository for zebrafish genetic, genomic, phenotypic, and developmental data.

Data is downloaded from:
- `https://zfin.org/downloads/phenotype_fish.txt` - Main phenotype data
- `https://raw.githubusercontent.com/obophenotype/zebrafish-phenotype-ontology/master/src/curation/id_map_zfin.tsv` - EQE to ZP mapping
- `https://zfin.org/downloads/pheno_environment_fish.txt` - Environment data
- `https://zfin.org/downloads/pub_to_pubmed_id_translation.txt` - Publication mappings

## Output

This ingest produces:
- **Genotype-to-phenotype associations** - Links zebrafish genotypes (fish) to phenotypic features using ZP terms

## Usage

```bash
# Install dependencies
just install

# Run full pipeline
just run

# Or run steps individually
just download      # Download ZFIN data files
just transform-all # Run Koza transform
just test          # Run tests
```

## Requirements

- Python 3.10+
- [uv](https://github.com/astral-sh/uv) package manager
- [just](https://github.com/casey/just) command runner

## License

MIT
