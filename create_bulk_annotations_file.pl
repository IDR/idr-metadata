#!usr/bin/perl

#######################################################################
# create_bulk_annotations_file.pl                                     #
#                                                                     #
# Eleanor Williams 2015-06-08                                         #
#                                                                     #
# Script to read in standard library file and processed data file     #
# for a High Content Screen and output a .csv file that can be        #
# used as a bulk annotation of the screen in omero.                   #
#                                                                     #
#######################################################################

#######################################################################
# what it does                                                        #
#                                                                     #
# A. reads in a library file and processed data file (hit list)       #
# plus the name of the column in the two files that the data          #
# should be joined on. e.g. siRNA_ID or Entity_ID                     #
# B. from the library file find out which column contains the         #
# identifier that is going to match the library and processed file    #
# information.                                                        #
# C. find out if there are columns duplicated between the library and #
# processed files e.g. gene name.  Don't want to repeat them in the   #
# output file. Remove them from the processed fil                     #
# D. print out data to an output file. It contains all the library    #
# information plus the processed data if there is any for the well    #
#######################################################################


#######################################################################
# things to be careful of                                             #
#                                                                     #
# 1. watch out for mac line endings in the files - needs to be        #
# unix line endings.                                                  #
#######################################################################

use warnings;
use strict;
use Getopt::Long;

my $libraryFile = "";
my $processedDataFile = "";
my $columnTitleToCombineOn = "";
my $help = 0;
my @libraryFile;
my @processedFile;


######################################################################
# get inputs from user                                               #
######################################################################

GetOptions(
        "l=s" => \$libraryFile,
	"p=s" => \$processedDataFile,
	"c=s" => \$columnTitleToCombineOn,   
        "h"   => \$help
	   );


if ($help){
   print "\n Creates a bulk annotation file for a HCS in Omero from a library file and processed data file.

     Options: -l library file (required)
              -p processed data file (hit list) (required)
              -c column title to use to combine the library file and processed data file on (required)
              -h help information

     Example:  create_bulk_annotations_file.pl -l libraryFile.csv -p processedData.csv -c siRNA_ID
     Output :  The output file name is taken from the library file with the extension .BULK_ANNOTATION.csv\n\n";

      exit;

     

}elsif($libraryFile eq ""){
   print "\nERROR: You must provide a library file using the -l option\n"; exit;
}elsif($processedDataFile eq ""){
   print "\nERROR: You must provide a processed data file file using the -p option\n"; exit;
}elsif($columnTitleToCombineOn eq ""){
   print "\nERROR: You must provide a column title that is in both the library and processed data files that should be used for combining the data\n"; exit;
}

######################################################################
# read in the library and processed data files                       #
######################################################################


if ($libraryFile ne ""){
    open (LIBRARY, "<$libraryFile")|| die "cannot open library file $libraryFile for reading: $!";
    @libraryFile = <LIBRARY>;
    close(LIBRARY);
}


if ($processedDataFile ne ""){
    open (PROCESSED, "<$processedDataFile")|| die "cannot open processed data file $processedDataFile for reading: $!";
    @processedFile = <PROCESSED>;
    close(PROCESSED);
}


######################################################################
# process the library file                                           #
# 1. find out which column contains the identifier which is going to #
#    match up with the processed file                                #
# 2. find out which columns appear in both the library and processed #
#    files? We don't want them repeated twice in the final output    #
#    file.                                                           #
# 3. if a well in the library file has no processed data information #
#    then we will need to add a number of empty columns to that row  #
#    in the output file so that table has same number of columns for #
#    each row.  So work out how many blank columns to add.           #
######################################################################

######################################################################
# 1. which column in library file has identifier to match column in
# processed file

my $indexOfLibraryFileColumnForMatching;

my @libraryHeaderRow = split("\,", $libraryFile[0]);


my $n=0;
foreach my $column (@libraryHeaderRow){
  if ($column =~ /^$columnTitleToCombineOn$/){
    $indexOfLibraryFileColumnForMatching = $n;
    last;
  }
  $n++;
}

######################################################################
# 2. which columns appear in both the library and processed files?   

my @columnsToLooseFromProcessedFile;
my $numberOfColumnsUniqueToProcessedFile=0;
my $blankColumnsIfNoProcessedData = "";

my @processedHeaderRow = split("\,", $processedFile[0]);

for (my $index=0; $index<@processedHeaderRow; $index++){ 
  if (grep (/^$processedHeaderRow[$index]$/, @libraryHeaderRow)){
  push @columnsToLooseFromProcessedFile, $index;
  }
}

$numberOfColumnsUniqueToProcessedFile = scalar(@processedHeaderRow) - scalar(@columnsToLooseFromProcessedFile);

######################################################################
# 3. make a string of blank columns equal to the number of columns
#    left in the processed data file after removing columns also in
#    the library file

for (my $blanks=0; $blanks<$numberOfColumnsUniqueToProcessedFile-1; $blanks++){
  $blankColumnsIfNoProcessedData = $blankColumnsIfNoProcessedData.",";
}


######################################################################
# process the processed data file                                    #
# 4. find out which column contains the identifier which is going to #
#    match up with the library file                                  #
# 5. remove the columns from the processed file that are already in  #
#    the library file as don't need them twice in the final file     #
######################################################################

######################################################################
# 4. which column in processed file has identifier to match column in
# library file

my $indexOfProcessedFileColumnForMatching;

my $p=0;
foreach my $column (@processedHeaderRow){
  if ($column =~ /^$columnTitleToCombineOn$/){
    $indexOfProcessedFileColumnForMatching = $p;
    last;
  }
  $p++;
}

######################################################################
# 5. remove the columns from the processed file that are already in  #
#    the library file as don't need them twice in the final file. To #
#    do this need to create a hash of the column numbers and the     #
#    values otherwise as soon as one column is removed all the other #
#    column numbers in the array will change.                        #
#    Then put the remaining row into a hash with the common          #
#    identifier as the key.                                          #


  my %Identifier_otherColumns;


  # get each row of the processed file
for (my $row=0; $row<@processedFile; $row++){
  
     chomp ($processedFile[$row]);  
     my @thisRow = split("\,", $processedFile[$row], -1); # the -1 means that trailing empty cells are kept as part of @thisRow

     # create the hash of with the column number and then column value
     my %columnNumber_columnValue;
     my $count=0;
        foreach my $columnValue (@thisRow){
        $columnNumber_columnValue{$count} = $columnValue;
        $count++;
        }

  #then create new array with just the column values we want to keep
  my @thisRowColumnValuesToKeep;

  my @keysInOrder = sort {$a <=> $b} keys %columnNumber_columnValue;
   
  foreach my $key (@keysInOrder){
    if (grep (/^$key$/, @columnsToLooseFromProcessedFile)){
    # do nothing
    }else{
      push @thisRowColumnValuesToKeep, $columnNumber_columnValue{$key};
     }
    
  }
  
  $Identifier_otherColumns{$thisRow[$indexOfProcessedFileColumnForMatching]} = \@thisRowColumnValuesToKeep;
 
}

######################################################################
# create the output file                                             #
# 6. create the out file name and open it                            #
# 7. the library file contains information for every well, so go     #
#    through each line in it, print out each line, adding            #
#    information from the processed file if there is any.            #
######################################################################

######################################################################
# 6. open the output file

my $outfile = $libraryFile;
$outfile =~ s/LibraryFile\.csv//g;
$outfile = $outfile.".BULK_ANNOTATION.csv";

open (OUT, ">$outfile");

######################################################################
# 7. go through each line in the library file and print out          #
#    adding processed file info if needed                            #

foreach my $libRow (@libraryFile){

  chomp($libRow);
  print OUT "$libRow\,";  

 my @libraryRow = split ("\,", $libRow, -1);
 
 # add processed data if there is any or blank columns if not        #
 
 
 if (exists ($Identifier_otherColumns{$libraryRow[$indexOfLibraryFileColumnForMatching]})) {
   my $processedRow = join("\,", @{$Identifier_otherColumns{$libraryRow[$indexOfLibraryFileColumnForMatching]}});
   print OUT "$processedRow";
 }else{
   print OUT "$blankColumnsIfNoProcessedData";
 }   

   print OUT "\n";

}

close (OUT);







