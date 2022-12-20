wget ftp://ftp.ensemblgenomes.org/pub/plants/release-49/fasta/arabidopsis_thaliana/dna/Arabidopsis_thaliana.TAIR10.dna_sm.toplevel.fa.gz && 
gunzip Arabidopsis_thaliana.TAIR10.dna_sm.toplevel.fa.gz && 
cp $EBROOTFINDER/example/Arabidopsis_thaliana_metadata.csv ./ &&
cp -r $EBROOTFINDER/example/raw_data/ ./ &&
sed -i "s|/home/ubuntu/Finder/example/|$PWD/|g" Arabidopsis_thaliana_metadata.csv && 
touch genemark.lic && 
run_finder -no_cleanup -mf $PWD/Arabidopsis_thaliana_metadata.csv -n 2 -om PLANTS -gm $EBROOTGENEMARKMINET \
-gml $PWD/genemark.lic -out_dir FINDER_test_ARATH -g $PWD/Arabidopsis_thaliana.TAIR10.dna_sm.toplevel.fa -p uniprot_ARATH.fasta -preserve 1> $PWD/FINDER_test_ARATH.output 2> $PWD/FINDER_test_ARATH.error 
