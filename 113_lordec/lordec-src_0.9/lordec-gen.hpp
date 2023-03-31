

// constants limits for parameters
#define MIN_KMER_LEN 4
#define MIN_SOLID_THR 1

#define MIN_ERROR_RATE 0.0
#define MAX_ERROR_RATE 0.5

#define MIN_TRIALS 1
#define MAX_TRIALS 100

#define MIN_NB_BRANCH 1
#define MAX_NB_BRANCH 10000

#define MIN_THREADS 0
#define MAX_THREADS 64


// other constants
//#define MAX_READ_LEN 500000
#define MAX_PATH_LEN 1000

// default values for correction
#define DEF_ERROR_RATE 0.40
#define DEF_MAX_BRANCH 200
#define DEF_TRIALS 5
#define DEF_THREADS 0
#define DEF_MAX_ABUNDANCE 2147483647

// alignment scores
#define ALIGN_MATCH 1
#define ALIGN_MISMATCH -3
#define ALIGN_INDEL -2

// Constants for trimming and splitting
#define DEF_MIN_REGION_LG 100

// Constants for statistics
#define STAT_FOUND 0
#define STAT_FOUND_LEN1 1
#define STAT_TOOLONG 2
#define STAT_EXPLOSION 3
#define STAT_NOPATH 4

#define STAT_TAIL "TAIL"
#define STAT_END2END "END2END"
#define STAT_GAPEXTEND "GAPEXTEND"

// File extensions
#define HDF5_EXT ".h5"
#define FASTA_EXT ".fa"
#define FASTQ_EXT ".fq"

// Utilities 

// min macro
#define MIN(a,b) ((a) < (b) ? (a) : (b))

// max macro
#define MAX(a,b) ((a) > (b) ? (a) : (b))


//////////////////////////////////////////////////
// check wheter a file is present and readable 
bool is_readable( const std::string & file ) 
{ 
    std::ifstream fichier( file.c_str() ); 
    return !fichier.fail(); 
} 
