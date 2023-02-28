ml load scib-pipeline

cd $EBROOTSCIBMINPIPELINE/pipeline/

python data/generate_data.py

# dry run
snakemake --configfile configs/test_data-R4.0.yaml -n

# readme example
snakemake --configfile configs/test_data-R4.0.yaml --cores 8 > test_pipeline.log 2>&1

# github pipeline (one of)
snakemake metrics --configfile configs/test_data-R4.0_small.yaml -kc1 --cores 8 > test_pipeline.log 2>&1
