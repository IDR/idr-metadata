#!/usr/bin/perl
use warnings;
use strict;

use Getopt::Long;

######################################################################
# identifyMissingWellsAndAddAsEmpty.pl                               #
# Eleanor Williams 2015-06-20                                        #
# Specific script for mitocheck data set which has no empty wells    #
# listed in the library file. This script identifies which of the    #
# 384 wells are not listed and adds them to the library file as      #
# lines with the siRNA identifier as 'empty'.                        # 
######################################################################


# TO DOs:  To make the script more general it would be good to      #
# identify the plate, well numbers and siRNA identifier columns in  #
# in the library file from the headers rather than assume which     #
# columns they are in. Would also be good to work out how many tabs #
# that are needed to be added for the 'empty' rows from the number  #
# of header rows.                                                   #
# Could also make the number of expected wells - 96 or 384 as an    #
# input from the user.                                              #

my $libraryFile = "";
my $numberOfWells = "";
my $help = "";


######################################################################
# get inputs from user                                               #
######################################################################

GetOptions(
	   "l=s" => \$libraryFile,
	   "n=s" => \$numberOfWells,
        "h"   => \$help
	   );


if ($help){
   print "Script to add missing 'empty' well locations to a library file.  It takes a tab-delimited 'library' file as input and uses well numbers to identify the missing wells. Number of wells can be either 384 or 96. Usage identifyMissingWellsAndAddAsEmpty.pl -l LibraryFile.txt -n 384\n";
   exit;
}elsif($libraryFile eq ""){
  print "\nERROR: You must provide a library file using the -l option\n";
  exit;
}elsif($numberOfWells eq ""){
  print "\nERROR: You must provide the number of wells on the plate using the -n option\n";
  exit;
}

######################################################################
# read in the existing libary file and see what wells we already     #
# have info for                                                      #                  
######################################################################



my @libraryFile;

if ($libraryFile ne ""){
    open (LIBRARY, "<$libraryFile")|| die "cannot open library file $libraryFile for reading: $!";
    @libraryFile = <LIBRARY>;
    close(LIBRARY);
}


my $headerRow = shift @libraryFile;


# PUT PLATE AND WELL NUMBERS INTO A HASH OF ARRAYS WITH PLATES AS THE KEYS
# ASSUMES THAT PLATE NAMES ARE IN FIRST ELEMENT AND WELL NUMBERS IN SECOND BUT COULD
# FIGURE THIS OUT FROM HEADER ROW


my @row;
my %plate_wellNumberArray;

foreach my $line (@libraryFile){

   @row = split("\t", $line);

   push (@{$plate_wellNumberArray{$row[0]}}, $row[1]);

}

my $outfile = $libraryFile;
$outfile =~ s/\.txt/_withEmptyWells\.txt/;

open (OUT, ">$outfile");
print OUT "$headerRow";


# for each plate need to find out what are the missing wells
# then add a row for each of them into the outfile
# and print the original rows to the outfile as well


foreach my $plate (keys %plate_wellNumberArray){

 # print "looking at plate $plate\n";
  for (my $wellNumber=1; $wellNumber<=$numberOfWells; $wellNumber++){
  #  print "at well $wellNumber\n";
    if (grep {$_ eq $wellNumber} @{$plate_wellNumberArray{$plate}}){
   #   print "found $plate and $wellNumber - all ok\n";
     # do nothing	
    }else{
    #  print "$plate has no well number $wellNumber.\n";
     
      #print OUT "$plate\t$wellNumber\tempty\t\t\tempty\t\t\t\tempty\n";
      print OUT "$plate\t$wellNumber\t\tempty\tempty\tempty\t\t\tempty\n";
    }
  }

}

# NOW PRINT OUT THE ORIGINAL ROWS AGAIN

foreach my $row (@libraryFile){

 print OUT "$row";

}

close (OUT);








