ml load scib-pipeline &&

cd $EBROOTSCIBMINPIPELINE/pipeline/ &&

python data/generate_data.py &&

snakemake --configfile configs/test_data-R4.0.yaml -n &&

snakemake --configfile configs/test_data-R4.0.yaml --cores 8 > test_pipeline.log 2>&1