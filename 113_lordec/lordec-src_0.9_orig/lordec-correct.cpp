// Copyright Leena Salmela and Eric Rivals 2014
//
// leena.salmela@cs.helsinki.fi
// rivals@lirmm.fr
//
// This software is a computer program whose purpose is to correct
// sequencing errors in PacBio reads using highly accurate short reads
// (e.g. Illumina).
//
// This software is governed by the CeCILL license under French law and
// abiding by the rules of distribution of free software. You can use,
// modify and/ or redistribute the software under the terms of the CeCILL
// license as circulated by CEA, CNRS and INRIA at the following URL
// "http://www.cecill.info".
//
// As a counterpart to the access to the source code and rights to copy,
// modify and redistribute granted by the license, users are provided only
// with a limited warranty and the software's author, the holder of the
// economic rights, and the successive licensors have only limited
// liability.
//
// In this respect, the user's attention is drawn to the risks associated
// with loading, using, modifying and/or developing or reproducing the
// software by the user in light of its specific status of free software,
// that may mean that it is complicated to manipulate, and that also
// therefore means that it is reserved for developers and experienced
// professionals having in-depth computer knowledge. Users are therefore
// encouraged to load and test the software's suitability as regards their
// requirements in conditions enabling the security of their systems and/or
// data to be ensured and, more generally, to use and operate it in the
// same conditions as regards security.
//
// The fact that you are presently reading this means that you have had
// knowledge of the CeCILL license and that you accept its terms.

#include "utils.hpp"
#include "lordec-correct.h"

//////////////////////////////////////////////////
// MAIN

/********************************************************************************/
/*    Create deBruijn graph from a FASTA (bank) file and do error correction    */
/********************************************************************************/
int main (int argc, char* argv[]) {
  try {
    extern char *optarg;
    extern int optind;
    extern int opterr;
    opterr = 1;

    int
      c = 0,
      dFlag = 0,
      iFlag = 0,
      kFlag = 0,
      oFlag = 0,
      sFlag = 0,
      SFlag = 0,
      tFlag = 0,
      bFlag = 0,
      eFlag = 0,
      TFlag = 0,
      cFlag = 0,
      gFlag = 0,
      aFlag = 0,
      OFlag = 0,
      pFlag = 0;

    // parameters
    int
      kmer_len = MIN_KMER_LEN,
      solid_kmer_thr = MIN_SOLID_THR,
      max_abundance_thr = DEF_MAX_ABUNDANCE;  // defaut maximal authorized abundance for any k-mer

    std::string
      kmer_len_str = "4",
      solid_kmer_thr_str = "1",
      pacbioFile,
      illuminaFile,
      outReadFile,
      outStatFile,
      outTmpPath = "";

    std::string prog = argv[0];

    // getopt
    static struct option long_options[] =
    {
      // These options don't set a flag.
      // We distinguish them by their indices.
      // mandatory arguments
      {"short_reads",    required_argument, 0, '2'},	// FASTA input file (short read sequences)
      {"long_reads",     required_argument, 0, 'i'},	// FASTA input file (long read sequences)
      {"kmer_len",       required_argument, 0, 'k'},	// integer > 4 : kmer length
      {"corrected_read_file",    required_argument, 0, 'o'},	// output file for the corrected long reads
      {"solid_threshold",required_argument, 0, 's'},	// integer solidity abundance threshold for kmers
      {"stat_file",      required_argument, 0, 'S'},	// output statistics file
      // optional arguments
      {"trials",         required_argument, 0, 't'},	// integer in [1, 100] : max nb of trials from a kmer
      {"branch",         required_argument, 0, 'b'},	// integer in [1, 1000] : max nb of branch to explore in graph
      {"errorrate",      required_argument, 0, 'e'},	// real in ]0, 0.5] maximum error rate in long reads
#ifdef _OPENMP
      {"threads",     required_argument, 0, 'T'},	// number of threads
#endif
      {"complete_search", no_argument, 0, 'c'},         // do not correct an area if all options have not been explored
      {"graph_named_like_output", no_argument, 0, 'g'},    // try to read previously generated graph near output rather than near input, write it near output also
      {"progress", no_argument, 0, 'p'},    // try to read previously generated graph near output rather than near input, write it near output also
      {"abundance-max", required_argument, 0, 'a'},     // set the maximal abundance threshold for a k-mer; this option is passed to graphCreate
      {"out-tmp", required_argument, 0, 'O'},     // change GATB graph build temporary files location
      {0, 0, 0, 0}
    };
    // getopt_long stores the option index here.
    int option_index = 0;

    while ((c = getopt_long (argc, argv, "2:i:k:o:s:S:t:b:e:T:a:cgO:ph", long_options, &option_index)) != -1) {
      switch (c) {
        case 'h':
          usage(argv[0]);
          return EXIT_SUCCESS;
          break;

        case '2':
          if (dFlag){
            std::cerr << "Option -2 <short reads FASTA-file> should be used only once." << std::endl;
            usage(argv[0]);
            return EXIT_FAILURE;
          }
          dFlag = 1;
          illuminaFile = optarg;
          break;

        case 'i':
          if (iFlag){
            std::cerr << "Option -i <long reads FASTA-file> should be used only once." << std::endl;
            usage(argv[0]);
            return EXIT_FAILURE;
          }
          iFlag = 1;
          pacbioFile = optarg;
          break;

        case 'k':
          if (kFlag){
            std::cerr << "Option -k <k-mer size> should be used only once." << std::endl;
            usage(argv[0]);
            return EXIT_FAILURE;
          }
          kFlag = 1;
          kmer_len_str = optarg;
          kmer_len = atoi(optarg);
          break;

        case 'o':
          if (oFlag){
            std::cerr << "Option -o <output-file> should be used only once." << std::endl;
            usage(argv[0]);
            return EXIT_FAILURE;
          }
          oFlag = 1;
          outReadFile = optarg;
          break;

        case 's':
          if (sFlag){
            std::cerr << "Option -s <solid k-mer abundance threshold> should be used only once." << std::endl;
            usage(argv[0]);
            return EXIT_FAILURE;
          }
          sFlag = 1;
          solid_kmer_thr_str = optarg;
          solid_kmer_thr = atoi(optarg);
          break;

          // optional arguments
        case 'S':
          if (SFlag){
            std::cerr << "Option -S <out statistics file> should be used at most once." << std::endl;
            usage(argv[0]);
            return EXIT_FAILURE;
          }
          SFlag = 1;
          outStatFile = optarg;
          break;

        case 't':
          if (tFlag){
            std::cerr << "Option -t <max trials from a k-mer> should be used only once." << std::endl;
            usage(argv[0]);
            return EXIT_FAILURE;
          }
          tFlag = 1;
          //	max_trials_str = optarg;
          max_trials = atoi(optarg);
          break;

        case 'b':
          if (bFlag){
            std::cerr << "Option -b <max nb branches to explore> should be used only once." << std::endl;
            usage(argv[0]);
            return EXIT_FAILURE;
          }
          bFlag = 1;
          //	max_branch_str = optarg;
          max_branch = atoi(optarg);
          break;

        case 'e':
          if (eFlag){
            std::cerr << "Option -e <error_rate> should be used only once." << std::endl;
            usage(argv[0]);
            return EXIT_FAILURE;
          }
          eFlag = 1;
          //	max_error_rate_str = optarg;
          max_error_rate = atof(optarg);
          break;

        case 'T':
          if (TFlag){
            std::cerr << "Option -T <nb threads> should be used only once." << std::endl;
            usage(argv[0]);
            return EXIT_FAILURE;
          }
          TFlag = 1;
          threads = atoi(optarg);
          break;

        case 'c':
          if (cFlag){
            std::cerr << "Option -c should be used only once." << std::endl;
            usage(argv[0]);
            return EXIT_FAILURE;
          }
          std::cout << "Using strict mode" << std::endl;
          cFlag = 1;
          strict_mode = 1;
          break;

        case 'g':
          if (gFlag){
            std::cerr << "Option -g should be used only once." << std::endl;
            usage(argv[0]);
            return EXIT_FAILURE;
          }
          gFlag = 1;
          break;

        case 'p':
          if (pFlag){
            std::cerr << "Option -p should be used only once." << std::endl;
            usage(argv[0]);
            return EXIT_FAILURE;
          }
          pFlag = 1;
          break;

        case 'a':
          if (aFlag){
            std::cerr << "Option -a should be used only once." << std::endl;
            usage(argv[0]);
            return EXIT_FAILURE;
          }
          aFlag = 1;
          // max_abundance_thr_str = optarg;    // UNUSED string of parameter value
          max_abundance_thr = atoi(optarg);     // integer var with parameter value
          break;

        case 'O':
          if (OFlag){
            std::cerr << "Option -O should be used only once." << std::endl;
            usage(argv[0]);
            return EXIT_FAILURE;
          }
          OFlag = 1;
          outTmpPath = outTmpPath + "-out-tmp ";
          outTmpPath = outTmpPath + optarg;
          break;

        case '?': 				// getopt_long already printed an error message.
          break;

        default:
          usage(argv[0]);
          return EXIT_FAILURE;
      }
    }

    // check that the user provides all mandatory options
    if (!dFlag || !iFlag || !kFlag || !oFlag || !sFlag) {
      usage(prog);
      return EXIT_FAILURE;
    }


    //////////////////////////////////////////////////
    // OLD parameters checking
    // parameters
    // while(argc > CMD_LINE_PARAM_NB) {
    //   std::cerr << argv[1] << std::endl;
    //   if (strcmp(argv[1], "-trials") == 0) {
    // 	max_trials = atoi(argv[2]);
    // 	argc -= 2;
    // 	argv += 2;
    //   } else if (strcmp(argv[1], "-branch") == 0) {
    // 	max_branch = atoi(argv[2]);
    // 	argc -= 2;
    // 	argv += 2;
    //   } else if (strcmp(argv[1], "-errorrate") == 0) {
    // 	max_error_rate = atof(argv[2]);
    // 	argc -= 2;
    // 	argv += 2;
    //   } else if (strcmp(argv[1], "-threads") == 0) {
    // 	threads = atoi(argv[2]);
    // 	argc -= 2;
    // 	argv += 2;
    //   } else {
    // 	usage(prog);
    // 	return EXIT_FAILURE;
    //   }
    // }
    //
    //
    // int kmer_len = atoi(argv[2]);
    // int solid_kmer_thr = atoi(argv[3]);
    // std::string illuminaFile = argv[1];
    // std::string pacbioFile   = argv[4];

    //////// Count reads in input file
    BankFasta bsize(pacbioFile);
    BankFasta::Iterator itSeqSize(bsize);
    size_t max_read_len = 0;
    size_t seqSize;
    long long nbSeq = 0;
    for (itSeqSize.first(); !itSeqSize.isDone(); itSeqSize.next()) {
      seqSize = itSeqSize->getDataSize();
      if (seqSize > max_read_len) {
        max_read_len = seqSize;
      }
      nbSeq++;
    }
    max_read_len = max_read_len * 1.25;
    ////////////////////////////////////////////////// MANAGE GRAPH FILE PATH
    std::string illuminaGraph;
    int comaPosition = std::string::npos;
    // -g option means graph file path is based on output file path
    if (gFlag) {
      illuminaGraph = outReadFile;
    }
    // we use the short read file as a basis for the graph file path
    else {
      // if there is just one SR file or if user uses a meta file with SR files paths :
      illuminaGraph = illuminaFile;
      comaPosition = illuminaGraph.find(",");
      // if there is a coma in SR path, we take the first and add "_multi" suffix
      if (comaPosition != std::string::npos) {
        illuminaGraph = illuminaGraph.substr(0, comaPosition) + "_multi";
      }
    }
    illuminaGraph = illuminaGraph + "_k" + kmer_len_str + "_s" + solid_kmer_thr_str + ".h5";

    // check if we have write access to graph file
    std::string dirn = dirname(illuminaGraph);
    int writeGraphPossible;
    if (dirn == "") {
      writeGraphPossible = access("./", W_OK);
    }
    else {
      writeGraphPossible = access(dirn.c_str(), W_OK);
    }
    // if it's not possible : we put/read it in the output directory
    if (writeGraphPossible != 0) {
      std::cout << "Impossible to write in " << dirname(illuminaGraph) << "\n";
      illuminaGraph = dirname(outReadFile) + basename(illuminaGraph);
      std::cout << "Graph will be written in output directory : " << illuminaGraph << "\n";
    }
    ////////////////////////////////////////////////// END MANAGE GRAPH FILE PATH
    //     std::string outReadFile   = argv[5];
    // #ifdef STATS
    //     std::string outStatFile   = argv[6];
    // #endif
    //////////////////////////////////////////////////
    // print parameters for debugging
    if (DEBUG){
      for (int i=1; i < argc; i++){
        std::cerr << argv[i]  << std::endl;
      }
      std::cerr << "illumina: " << illuminaFile << " " << illuminaGraph << " pacbioFile: " << pacbioFile << std::endl;
      std::cerr << "kmer_len: " << kmer_len << " solid_kmer_thr: " << solid_kmer_thr << std::endl;
      std::cerr << "max_trials: " << max_trials << " max_error_rate: " << max_error_rate << " max_branch: " << max_branch << std::endl;
      std::cerr << "abundance_max: " << max_abundance_thr << std::endl;
      if (strict_mode)
        std::cerr << "using strict mode" << std::endl;
    }

    // check some parameters
    if ( kmer_len < MIN_KMER_LEN ) {
      std::cerr << "Parameter <k-mer size> must be larger than or equal to " << MIN_KMER_LEN << std::endl;
      return EXIT_FAILURE;
    }

    if ( solid_kmer_thr < MIN_SOLID_THR ) {
      std::cerr << "Parameter <abundance threshold> must be strictly positive" << std::endl;
      return EXIT_FAILURE;
    }

    if ( max_error_rate < MIN_ERROR_RATE || max_error_rate > MAX_ERROR_RATE ) {
      std::cerr << "Parameter <max_error_rate> must be strictly positive and less than " << MAX_ERROR_RATE << std::endl;
      return EXIT_FAILURE;
    }

    if ( max_trials < MIN_TRIALS || max_trials > MAX_TRIALS ) {
      std::cerr << "Parameter <max_trials> must be at least 1 and less than 100" << std::endl;
      return EXIT_FAILURE;
    }

    if ( max_branch < MIN_NB_BRANCH || max_branch > MAX_NB_BRANCH ) {
      std::cerr << "Parameter <max_branch> must be at least 1 and less than 10000" << std::endl;
      return EXIT_FAILURE;
    }

    if ( threads < MIN_THREADS || threads > MAX_THREADS ) {
      std::cerr << "Parameter <threads> must be at least 0 and less than 65" << std::endl;
    }

    if ( max_abundance_thr <= solid_kmer_thr || max_abundance_thr > DEF_MAX_ABUNDANCE ) {
      std::cerr << "Parameter <abundance_max> must be larger than <solid_kmer_thr> and smaller than " << DEF_MAX_ABUNDANCE << std::endl;
      std::cerr << "Currently <abundance_max> is set to " << max_abundance_thr << " and <solid_kmer_thr> to " << solid_kmer_thr << std::endl;
      return EXIT_FAILURE;
    }

    // check the presence of input files : decide between stored graph and seq file
    bool
      bRefSeq   = false,
      bRefGraph = false;

    // Not needed anymore as we can give the list of Illumina files to Bank directly
    // Array of illumina files
    // char **illFiles = NULL;
    // int filecount=0;

    // check the presence of input files
    if ( !is_readable( illuminaGraph ) ) {
      std::cerr << "Cannot access the graph file for reference reads: " << illuminaGraph << std::endl;

      // Not needed anymore as we can give the list of Illumina files to Bank directly
      // filecount = 1;
      // // Tokenize reads file (list of files separated by ,)
      // char *ifcstr = (char *)illuminaFile.c_str();
      // for(int i = 0; i < strlen(ifcstr); i++) {
      // 	if (ifcstr[i] == ',')
      // 	  filecount++;
      // }

      // illFiles = new char*[filecount];
      // illFiles[0] = ifcstr;
      // int j = 1;
      // int l = strlen(ifcstr);
      // for (int i = 0; i < l; i++) {
      // 	if (ifcstr[i] == ','){
      // 	  ifcstr[i] = '\0';
      // 	  illFiles[j] = &ifcstr[i+1];
      // 	  if ( !is_readable( illFiles[j-1]) ) {
      // 	    std::cerr << "Cannot access the FASTA file for reference reads: " << illFiles[j-1] << std::endl;
      // 	    return EXIT_FAILURE;
      // 	  }
      // 	  j++;
      // 	}
      // }

      // if ( !is_readable( illFiles[j-1] ) ) {
      // 	std::cerr << "Cannot access the FASTA file for reference reads: " << illFiles[j-1] << std::endl;
      // 	return EXIT_FAILURE;
      // }

      bRefSeq = true;
    }
    else {
      bRefGraph = true;
    }
    if (DEBUG){
      std::cerr << "bRefGraph: " << bRefGraph << std::endl;
      std::cerr << "bRefSeq: "   << bRefSeq   << std::endl;
    }

    // check accessibility of pacbioFile
    if ( !is_readable( pacbioFile ) ) {
      std::cerr << "Cannot access the FASTA file for PacBio reads: " << pacbioFile << std::endl;
      return EXIT_FAILURE;
    }

    //// if the graph is not a valid HDF5 file, delete it
    //if(bRefGraph && !H5::H5File::isHdf5(illuminaGraph.c_str())) {
    //  std::cerr << "EXISTING GRAPH FILE IS NOT VALID. remove it and create a new one.\n";
    //  std::remove(illuminaGraph.c_str());
    //  bRefGraph = false;
    //}

    // Exception gatb::core::system::ExceptionErrno
    Graph graph;
    if ( bRefGraph ){
      if (DEBUG){
        std::cerr << "loading the graph: " << illuminaGraph << std::endl;
      }
      graph = Graph::load (illuminaGraph);
      if (kmer_len != graph.getKmerSize()) {
        std::cerr << "k-mer length of DBG (" << graph.getKmerSize() << ") and -k option (" << kmer_len << ") do not match" << std::endl;
        return (EXIT_FAILURE);
      }
    }
    else{
      if (DEBUG){
        std::cerr << "creating the graph from file(s): " << illuminaFile << std::endl;
        // v105 version after tokenization of all Illumina files
        // std::cerr << "creating the graph from file(s): " << std::endl;
        // for (int i = 0; i < filecount; i++) {
        //   std::cerr << illFiles[i] << std::endl;
        // }
      }

      // v106: put all SR filenames in a vector, required by interface of BankAlbum(), // new in gatb-core-1.0.6
      // std::vector<std::string> illFilesVec;
      // for (int i=0; i<filecount; i++)  { illFilesVec.push_back (illFiles[i]); }


      // We create the graph with from file and other options
      ///////////////////////////////
      // LS: 1st version
      //      graph = Graph::create ((char const *)"-in %s -kmer-size %s -nks %s", argv[1], argv[2], argv[3]);
      ///////////////////////////////
      // v105 version open Illumina files with  gatb-core-1.0.5
      // BankFasta *b = new BankFasta(filecount, illFiles);
      ///////////////////////////////
      // v106 takes as parameter either a comma-separated list of filenames OR a text filename of a file containing filenames (one per line)// new in gatb-core-1.0.6
      // IBank *b = new BankAlbum(illuminaFile);
      // after vectorisation
      try{
        // v106: open IBank from 1/ list of filenames 2/ a file of filenames
        IBank *b = Bank::open(illuminaFile);
        // v106: read a BankAlbum from a vector of filenames: works
        //	IBank *b = new BankAlbum(illFilesVec);
        // v106: graph creation interface -abundance-min instead of -abundance
        // v106: graph creation interface if classical construction neede use:  -bloom cache -debloom original -debloom-impl basic
        // v106: graph creation interface otherwise do not use parameters  -bloom -debloom -debloom-impl basic
        //	graph = Graph::create (b, (const char *)"-kmer-size %d -abundance-min %d -bloom neighbor -debloom cascading -debloom-impl minimizer -nb-cores %d", kmer_len, solid_kmer_thr, threads);

        graph = Graph::create (b, (const char *)"%s -out %s -kmer-size %d -abundance-min %d -bloom cache -debloom original -debloom-impl basic -nb-cores %d -abundance-max %d", outTmpPath.c_str(), illuminaGraph.c_str(), kmer_len, solid_kmer_thr, threads, max_abundance_thr);
        // TODO check that
        //delete b;
        //b->~IBank();

        if (is_readable(illuminaGraph)) {
          std::cerr << "!!! file present : "<< illuminaGraph<<std::endl;
        }
        else {
          std::cerr << "!!! file NOT present : "<< illuminaGraph<<std::endl;
        }
        // v104
        // graph = Graph::create ((char const *)"-in %s -kmer-size %d -nks %d", illuminaFile.c_str(), kmer_len, solid_kmer_thr);

      }
      catch (Exception& e){
        std::cerr << "EXCEPTION: " << e.getMessage() << std::endl;
        return EXIT_FAILURE;
      }

      if (DEBUG){
        std::cerr << "graph created" << std::endl;
      }

    }

    // precomputeAdjacency is not benefic at all
    // compatible with GATB >= 1.2.0
//#if defined(GATB_V122) || defined(GATB_V130) || defined(GATB_V140) || defined(GATB_V141)
//    graph.precomputeAdjacency();
//#endif
//#if defined(GATB_V122) || defined(GATB_V130) || defined(GATB_V140) || defined(GATB_V141)
//    graph.simplify();
//#endif
    ////////////////////////////////////////////////////////////
    // LS first version, create graph
    // We get a handle on a FASTA bank.
    //    IBank *bank = new Bank(argv[1]);
    // We create the graph with the bank and other options
    // Graph graph = Graph::create ((char const *)"-in %s -kmer-size %s -nks %s", argv[1], argv[2], argv[3]);
    ///////////////////////////////
    // We dump some information about the graph.
    std::cout << graph.getInfo() << std::endl;

    // Note: Graph::create will take care about 'bank' object and will delete it if nobody else needs it.
    // In other words: there is no need here to call 'delete' on 'bank' here.

    // We get a handle on a FASTA bank for the PacBio reads
    IBank *ptrBankPB = NULL;
    // Bank *ptrBankPB = NULL;
    try{
      // v106 simplified Bank interface (no BankRegistery anymore)// new in gatb-core-1.0.6
      ptrBankPB =  Bank::open(pacbioFile);
      // v104 version open Pacbio file with  gatb-core-1.0.4
      // ptrBankPB =  BankRegistery::singleton().createBank(pacbioFile);
      // v100 version open Pacbio file with  gatb-core-1.0.0
      // ptrBankPB = new Bank(pacbioFile); // argv[4]
    }
    catch (gatb::core::system::Exception & bankPBExc){
      std::cout << "Error message PacBio bank " << bankPBExc.getMessage () << std::endl;
      return EXIT_FAILURE;
    }
    // return EXIT_SUCCESS;

    ///////////////////////////////
    // // LS : 1st version
    // We get a handle on a FASTA bank for the PacBio reads
    //Bank bankPB(argv[4]);
    // Bank::Iterator itSeq(bankPB);
    ///////////////////////////////

    // Go over the PacBio reads one by one and extract k-mers
    Iterator<Sequence> *itSeq = ptrBankPB->iterator();
    // Bank::Iterator itSeq(*ptrBankPB);

    // Create the output bank
    BankFasta output(outReadFile); //argv[5]
    // Bank output(outReadFile); //argv[5]

    IFile *statFile = NULL;
    ISynchronizer *syncStat = NULL;
    if (SFlag) {
      // Create a file for path statistics
      statFile = System::file().newFile(outStatFile, "w"); //argv[6]
      syncStat = System::thread().newSynchronizer();
    }

    cout << "Found " << nbSeq << " reads.\n";
    cout << "Correcting reads...\n";

    // progress
    long long nbSeqProcessed = 0;
    ProgressManager *pmCorrect = new ProgressManager(nbSeq, "reads");

    // Access to the output file must be synchronized
    ISynchronizer *sync = System::thread().newSynchronizer();
    ISynchronizer *syncCount = System::thread().newSynchronizer();
    IDispatcher::Status status = Dispatcher(threads).iterate(itSeq, [&] (const Sequence& seq) {

      if (seq.getDataSize() >= kmer_len) {
        char *read = new char[max_read_len];
        int read_len=0;
        char *buffer = new char[max_read_len];

        if (seq.getDataSize() > max_read_len) {
          std::cout << "Too long read" << std::endl;
          exit(EXIT_FAILURE);
        }

        // Correct the read backward
        copy_upper_case(buffer, seq.getDataBuffer(), seq.getDataSize());
        buffer[seq.getDataSize()] = '\0';
        reverse(read, buffer, strlen(buffer));
        Sequence seq1(read);
        seq1._comment = seq.getComment();
        read_len = correct_one_read(seq1, buffer, graph, statFile, syncStat, kmer_len, max_read_len);

        // Correct the read forward
        copy_upper_case(read, buffer, read_len);
        buffer[read_len] = '\0';
        reverse(buffer, read, read_len);
        Sequence seq2(buffer);
        seq2._comment = seq.getComment();
        read_len = correct_one_read(seq2, read, graph, statFile, syncStat, kmer_len, max_read_len);

        read[read_len]='\0';
        Sequence s(read);
        s._comment = seq.getComment();
        {
          LocalSynchronizer local(sync);
          output.insert(s);
        }
        delete [] read;
        delete [] buffer;
      }
      // display progress if -p option set
      if (pFlag) {
        LocalSynchronizer local(syncCount);
        // no need for __sync_fetch_and_add because all the surrounding block is a critical section
        //__sync_fetch_and_add (&nbSeqProcessed, 1);
        nbSeqProcessed++;
        pmCorrect->updateProgress(nbSeqProcessed);
      }

    });

    std::cout << std::endl;
    delete pmCorrect;

    output.flush();

    delete ptrBankPB;
    delete sync;
    delete syncCount;

    if (statFile != NULL) {
      statFile->flush();
      delete statFile;

      delete syncStat;

      std::cout << "Path statistics:" << std::endl;
      std::cout << "Path found: " << path_found << std::endl;
      std::cout << "Path (of length 1) found: " << path_len1 << std::endl;
      std::cout << "No path found: " << path_nopath << std::endl;
      std::cout << "Combinatorial explosion: " << path_explosion << std::endl;
      std::cout << "K-mers too distant: " << path_toolong << std::endl;

      std::cout << std::endl << "Total: " << (path_found+path_len1+path_nopath+path_explosion+path_toolong) << std::endl;
    }

    return EXIT_SUCCESS;
  } catch (gatb::core::system::Exception & e){
    std::cout << "Error message " << e.getMessage () << std::endl;
    return EXIT_FAILURE;
  }
}
//////////////////////////////////////////////////

