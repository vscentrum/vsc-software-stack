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
#include <fstream>  // for ifstream class
#include <iostream>

#include <gatb/gatb_core.hpp>
#include "lordec-gen.hpp"

#define TO_STR2(x) #x
#define STR(x) TO_STR2(x)
#define LORDECSTRVERSION STR(LORDECVERSION)
#define GATBSTRVERSION STR(GATBVERSION)

void usage(char *prog) {
  std::cerr << "LoRDEC v" << LORDECSTRVERSION << std::endl;
  std::cerr << "using GATB v" << GATBSTRVERSION << std::endl;
  std::cerr << "website : " << "http://www.atgc-montpellier.fr/lordec/" << std::endl;
  std::cerr << "FAQ : " << "https://www.lirmm.fr/~rivals/lordec/FAQ/" << std::endl << std::endl;
  std::cerr << "Usage :" << std::endl << std::endl;
  std::cerr << prog << " -i <FASTA-file> -o <output-file>" << std::endl;
}

/********************************************************************************/
/*                      Trim lower case letters from read ends                  */
/********************************************************************************/
int main (int argc, char* argv[])
{

    extern char *optarg; 
    extern int optind; 
    extern int opterr;
    opterr = 1;

    std::string
      pacbioFile,
      outReadFile;

    int
      c = 0,
      iFlag = 0, 
      oFlag = 0; 

    // check nb of compulsory arguments (-i and -o followed by FASTA file URIs).
    if (argc < 5)
    {
      usage(argv[0]);
      return EXIT_FAILURE;
    }

    while ((c = getopt(argc, argv, "i:o:")) != -1) {
      switch (c) { 
      case 'i': 
	if (iFlag){
	  std::cerr << "Option -i <long reads FASTA-file> should be used only once." << std::endl;
	  usage(argv[0]);
	  return EXIT_FAILURE; 	  
	}
	iFlag = 1; 
	pacbioFile = optarg; 
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

      case '?': 				// getopt_long already printed an error message.
	break; 
      default:
	usage(argv[0]);
	return EXIT_FAILURE;
      } 
    }

    // Check for required arguments
    if (!iFlag || !oFlag) {
      usage(argv[0]);
      return EXIT_FAILURE;
    }

    // check accessibility of pacbioFile
    if ( !is_readable( pacbioFile ) ) {
      std::cerr << "Cannot access the FASTA file for PacBio reads: " << pacbioFile << std::endl;
      return EXIT_FAILURE;
    }

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

    // We get a handle on a FASTA bank for the PacBio reads
    // v105 ???
    // BankFasta bank(pacbioFile);
    try{
      // OLD v105
      // BankFasta bank(pacbioFile);
      // ER essai
      IBank* bank = Bank::open(pacbioFile);

      // Create the output bank
      BankFasta output(outReadFile);
      
      // allocate buffer
      char *buffer = new char[max_read_len];

    // Go over the PacBio reads one by one
    // OLD
    Iterator<Sequence> *itSeq = bank->iterator();
    // BankFasta::Iterator *itSeq (bank); // ER essai
 
    for (itSeq->first(); !itSeq->isDone(); itSeq->next())
      {
	char *read = (*itSeq)->getDataBuffer();
	int read_len = (*itSeq)->getDataSize();
	int firstUC=-1, lastUC=-1; // first and last position of uppercase nuc in the input seq
	for(int i = 0; i < read_len; i++) { // seek the first uppercase letter from start
	  if (isupper(read[i])) {
	    firstUC = i;
	    break;
	  }
	}
	if (firstUC < 0) // no uppercase letter found: go to next input seq
	  continue;

	for (int i = read_len-1; i >= 0; i--) { // seek last uppercase letter from the end
	  if (isupper(read[i])) {
	    lastUC = i;
	    break;
	  }
	}
	// copy desired region of the read to buffer
	// TODO: check the buffer limit !!!
	for(int i = firstUC; i <= lastUC; i++) {
	  buffer[i-firstUC] = read[i];
	}
	buffer[lastUC-firstUC+1] = '\0';

	// create a output sequence from the buffer
	Sequence s(buffer);
	s._comment = (*itSeq)->getComment();
	// insert the output sequence in output file
	output.insert(s);
      }
    output.flush();
    delete [] buffer;

    }// end of try
    catch (Exception& e){
      std::cerr << "EXCEPTION: " << e.getMessage() << std::endl;
    }

    return EXIT_SUCCESS;
}
