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
#include <unistd.h>
#include <stdlib.h>
#include <fstream>
#include <string> 
#include <iostream>
#include <gatb/gatb_core.hpp>

#include "lordec-gen.hpp"

#define TO_STR2(x) #x
#define STR(x) TO_STR2(x)
#define LORDECSTRVERSION STR(LORDECVERSION)
#define GATBSTRVERSION STR(GATBVERSION)

// FLAGS
bool DEBUG = true;

//////////////////////////////////////////////////
// constant for parameters
#define CMD_LINE_PARAM_NB 10

// usage
void usage(char *prog) {
  std::cerr << "LoRDEC v" << LORDECSTRVERSION << std::endl;
  std::cerr << "using GATB v" << GATBSTRVERSION << std::endl;
  std::cerr << "website : " << "http://www.atgc-montpellier.fr/lordec/" << std::endl;
  std::cerr << "FAQ : " << "https://www.lirmm.fr/~rivals/lordec/FAQ/" << std::endl << std::endl;
  std::cerr << "Usage :" << std::endl << std::endl;
  std::cerr << prog << " -i <long read FASTA/Q file> -2 <short read FASTA/Q file(s)> -k <k-mer size> -s <solid k-mer abundance threshold> -S <out statistics file> [-T <threads>]" << std::endl;
  std::cerr << "         reads the <FASTA/Q file(s)> of short reads, then builds and save their de Bruijn graph for k-mers of length <k-mer size> and occurring at least <abundance threshold> time" << std::endl;
}

void oldUsage(char *prog) {
  std::cerr << prog << " <FASTA file> <k-mer size> <abundance threshold> <PacBio FASTA file> <output stat file>" << std::endl;
}

/********************************************************************************/
/*    Create deBruijn graph from a FASTA (bank) file and compute statistics     */
/********************************************************************************/
int main (int argc, char* argv[])
{

    extern char *optarg; 
    extern int optind; 
    extern int opterr;
    opterr = 1;

    int
      c = 0,
      dFlag = 0,
      iFlag = 0,
      kFlag = 0,
      sFlag = 0,
      SFlag = 0,
      TFlag = 0;

    // parameters
    int 
      kmer_len = MIN_KMER_LEN, 
      solid_kmer_thr = MIN_SOLID_THR,
      threads = DEF_THREADS;

    std::string
      kmer_len_str = "4", 
      solid_kmer_thr_str = "1",
      pacbioFile,
      illuminaFile,
      outStatFile;

    // We check that the user provides at least one option (supposed to be a FASTA file URI).
    if (argc < CMD_LINE_PARAM_NB)
    {
      usage(argv[0]);
      return EXIT_FAILURE;
    }

    while ((c = getopt(argc, argv, "2:i:k:s:S:")) != -1) {
      switch (c) { 
      case '2': 
	if (dFlag){
	  std::cerr << "Option -i <short reads FASTA-file> should be used only once." << std::endl;
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

      case 'S': 
	if (SFlag){
	  std::cerr << "Option -S <out statistics file> should be used at most once." << std::endl;
	  usage(argv[0]);
	  return EXIT_FAILURE; 	  
	}
	SFlag = 1; 
	outStatFile = optarg; 
	break; 
	
      case 'T':
	if (TFlag){
	  std::cerr << "Option -T <threads> should be used at most once." << std::endl;
	  usage(argv[0]);
	  return EXIT_FAILURE; 	  
	}
	TFlag = 1; 
	threads = atoi(optarg); 
	break; 

      case '?': 				// getopt_long already printed an error message.
	break; 

      default:
	usage(argv[0]);
	return EXIT_FAILURE;
      } 
    }

    // Check for required arguments
    if (!dFlag || !iFlag || !kFlag || !sFlag || !SFlag) {
      usage(argv[0]);
      return EXIT_FAILURE;
    }


    // parameters
    // int kmer_len = atoi(argv[2]);
    // int solid_kmer_thr = atoi(argv[3]);
    // std::string illuminaFile = argv[1];
    // std::string pacbioFile   = argv[4];
    // std::string outStatFile   = argv[5];

    std::string illuminaGraph;
    // // an alternative way of resizing the string and concatenating an extension
    // illuminaGraph.reserve(illuminaFile.length() + 4);
    // illuminaGraph = strcat(argv[1], ".h5");
    illuminaGraph = illuminaFile + ".h5";


    // print parameters for debugging
    if (DEBUG){
      for (int i=1; i < argc; i++){
	std::cerr << argv[i]  << std::endl;
      }
      std::cerr << "illumina: " << illuminaFile << " " << illuminaGraph << " pacbioFile: " << pacbioFile << std::endl;
      std::cerr << "kmer_len: " << kmer_len << " solid_kmer_thr: " << solid_kmer_thr << std::endl;
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

    // check the presence of input files : decide between stored graph and seq file
    bool 
      bRefSeq   = false,
      bRefGraph = false;

    // Not needed anymore as we can give the list of Illumina files to Bank directly
    // Array of illumina files
    // char **illFiles = NULL;
    // int filecount=0;

    // check the presence of input files
    if ( !is_readable( illuminaGraph ) ) 
    { 
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
    if ( !is_readable( pacbioFile ) ) 
    { 
      std::cerr << "Cannot access the FASTA file for PacBio reads: " << pacbioFile << std::endl;
      return EXIT_FAILURE;
    } 

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
	// for (int i = 0; i < filecount; i++) {
	//   std::cerr << illFiles[i] << std::endl;
	// }
      }

      // We create the graph with from file and other options
      try{
	// v106: open IBank from 1/ list of filenames 2/ a file of filenames
	IBank *b = Bank::open(illuminaFile);
	// v106: read a BankAlbum from a vector of filenames: works
	//	IBank *b = new BankAlbum(illFilesVec);

	// v106: graph creation interface -abundance-min instead of -abundance
	// v106: graph creation interface if classical construction neede use:  -bloom cache -debloom original -debloom-impl basic
	// v106: graph creation interface otherwise do not use parameters  -bloom -debloom -debloom-impl basic
	graph = Graph::create (b, (const char *)"-kmer-size %d -abundance-min %d -bloom cache -debloom original -debloom-impl basic -nb-cores %d", kmer_len, solid_kmer_thr, threads);
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

    // // version with exception catching
    // Graph graph;
    // try{
    //   graph = Graph::create ((char const *)"-in %s -kmer-size %d -nks %d", illuminaFile.c_str(), kmer_len, solid_kmer_thr);
    // }
    // // catch (gatb::core::system::ExceptionErrno & graphExc){
    // catch (gatb::core::system::Exception & graphExc){
    //   std::cout << "Error message graph creation " << graphExc.getMessage () << std::endl;
    //   return EXIT_FAILURE;
    // }
    // We dump some information about the graph.
    std::cout << graph.getInfo() << std::endl;
    if (DEBUG)
      std::cerr << "Graph information dumped" << std::endl;
    
    // Note: Graph::create will take care about 'bank' object and will delete it if nobody else needs it.
    // In other words: there is no need here to call 'delete' on 'bank' here.

    // We get a handle on a FASTA bank for the PacBio reads
    IBank *ptrBankPB = NULL;
    // Bank *ptrBankPB = NULL;
    try{
#ifdef OLD_GATB
#ifdef VERY_OLD_GATB
      ptrBankPB =  BankRegistery::singleton().getFactory()->createBank(pacbioFile);
#else
      // v104 version open Pacbio file with  gatb-core-1.0.4
      ptrBankPB =  BankRegistery::singleton().createBank(pacbioFile);
      // v100 version open Pacbio file with  gatb-core-1.0.0
      // ptrBankPB = new Bank(pacbioFile); // argv[4]
#endif
#else
      // CURRENT VERSION
      // v106 simplified Bank interface (no BankRegistery anymore)// new in gatb-core-1.0.6
      ptrBankPB =  Bank::open(pacbioFile);
#endif
    }
    catch (gatb::core::system::Exception & bankPBExc){
      std::cerr << "Error message PacBio bank " << bankPBExc.getMessage () << std::endl;
      return EXIT_FAILURE;
    }

    // Go over the PacBio reads one by one and extract k-mers
    // Bank::Iterator itSeq(bankPB);
    Iterator<Sequence> *itSeq = ptrBankPB->iterator();
    // Bank::Iterator itSeq(*ptrBankPB);
#ifdef OLD_GATB
    Kmer<>::Model model(kmer_len);
    Kmer<>::Model::Iterator itKmer(model);
#else
    Kmer<>::ModelDirect model(kmer_len);
    Kmer<>::ModelDirect::Iterator itKmer(model);
#endif
    // Model<LargeInt<1> > model(kmer_len);
    // Model<LargeInt<1> >::Iterator itKmer(model);

    // Create the output file
    IFile *output = System::file().newFile(outStatFile, "w");
    if (DEBUG)
      std::cerr << "Output Stat file open " << outStatFile << std::endl;

    for (itSeq->first(); !itSeq->isDone(); itSeq->next())
      {
	if ((*itSeq)->getDataSize() >= kmer_len) {

	  // We set the data from which we want to extract kmers.
	  itKmer.setData ((*itSeq)->getData());

	  // We iterate the kmers.
	  int len=0;
	  int count=0;
	  int head=-1;
	  int tail=-1;
	  
	  for (itKmer.first(); !itKmer.isDone(); itKmer.next())   {  
#ifdef OLD_GATB
	    Data data((char *)(model.toString(*itKmer).c_str()));
#else
	    Data data((char *)(model.toString(itKmer->value()).c_str()));
#endif
	    Node node = graph.buildNode(data);
	    if (graph.contains(node) && graph.indegree(node) >= 1 && graph.outdegree(node)>=1) {
	      count++;
	      if (head == -1)
		head = len;
	      tail = len;
	    }
	    len++;
	  }
	  output->print("%d %d %d %d", count, len, head, len-tail-1);

	  int run = 0;
	  for (itKmer.first(); !itKmer.isDone(); itKmer.next())   {  
#ifdef OLD_GATB
	    Data data((char *)(model.toString(*itKmer).c_str()));
#else
	    Data data((char *)(model.toString(itKmer->value()).c_str()));
#endif
	    Node node = graph.buildNode(data);
	    if (graph.contains(node) && graph.indegree(node) >= 1 && graph.outdegree(node)>=1) {
	      run++;
	    } else {
	      if (run > 0)
		output->print(" %d", run);
	      run = 0;
	    }
	  }
	  if (run > 0)
	    output->print(" %d\n", run);
	  else
	    output->print("\n");
	}
      }
    output->flush();
    delete output;
    
    return EXIT_SUCCESS;
}
