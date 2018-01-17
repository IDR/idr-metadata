#!/usr/bin/perl

#######################################################################
# check_csv_columns.pl                                                #
#                                                                     #
# Eleanor Williams 2015-06-08                                         #
#                                                                     #
# script to check that each row has the same number of columns in a   #
# csv file                                                            #
#                                                                     #
#######################################################################


use warnings;
use strict;
use Getopt::Long;
use Text::CSV;

my $file = "";
my $help = 0;



######################################################################
# get inputs from user                                               #
######################################################################

GetOptions(
	   "f=s" => \$file,
	   "h"   => \$help
	   );


if ($help){
   print "\n Counts the number of columns in each row of a comma separated file.

     Options: -f file for checking (required)
              -h help information

     Example:  check_csv_columns.pl -f fileToCheck.csv 
     Output :  Output is to screen of the number of rows with each column count\n\n";

      exit;

}elsif($file eq ""){
  print "\nERROR: You must provide a file for checking using the -f option\n"; exit;
}

######################################################################
# read in the file and check it                                                 #
######################################################################

my $csv = Text::CSV-> new({ sep_char => ',' });
my %columns_count; # keep a record of the number of rows with each column count

if ($file ne ""){
    open (my $data, '<', $file)|| die "cannot open file $file for reading: $!";

    my $rowNumber = 1;
    while (my $line = <$data>){
      chomp $line;

      if ($csv->parse($line)) {

	my @fields = $csv->fields();
	
	# now keep a add one to the count of rows with that number of columns
	if (exists ($columns_count{scalar(@fields)}) ){
           $columns_count{scalar(@fields)} = $columns_count{scalar(@fields)} + 1;
	}else{
         $columns_count{scalar(@fields)} = 1;
	 }

        # check there are no trailing spaces, if there are just report don't change as should be changed
	# in source file
         foreach my $cell (@fields){
	    if ($cell =~ /\s+$/){
	    print ";$cell; contains a trailing empty space in row $rowNumber\n";
            } 
            if ($cell =~ /\s+\"$/){
            print ";$cell; contains a trailing empty space in row $rowNumber\n";
	    }
	    if ($cell =~ /^\s+/){
	    print ";$cell; contains a leading empty space in row $rowNumber\n";
            } 
            if ($cell =~ /^\"\s+/){
            print ";$cell; contains a leading empty space in row $rowNumber\n";
	    }
	 }
	
      }else{

	print "Line could not be parsed: $line\n";

      }
    $rowNumber++;
    }

}

print "Columns\tNumber of Rows\n";
foreach my $columns (keys %columns_count){
print "$columns\t$columns_count{$columns}\n";
}











