#!/usr/bin/perl

#######################################################################
# check_tab_columns.pl                                                #
#                                                                     #
# Eleanor Williams 2015-06-08                                         #
#                                                                     #
# script to check that each row has the same number of columns in a   #
# tab delimited file and to identify and remove trailing spaces       #
#                                                                     #
#######################################################################

# TO DO:
# Note: if you select 'y' for changing the file it will output a new  #
# file even if there has been nothing to change                       #


use warnings;
use strict;
use Getopt::Long;

my $file = "";
my $change = "n";
my $help = 0;



######################################################################
# get inputs from user                                               #
######################################################################

GetOptions(
	   "f=s" => \$file,
	   "c=s" => \$change,
	   "h"   => \$help
	   );


if ($help){
   print "\n Counts the number of columns in each row of a tab separated file.

     Options: -f file for checking (required)
              -c if a changed/fixed version of the file should be created or not (y or n)
              -h help information

     Example:  check_tab_columns.pl -f fileToCheck.txt
     Output :  Output is to screen of the number of rows with each column count\n\n";

      exit;

}elsif($file eq ""){
   print "\nERROR: You must provide a file for checking using the -f option\n"; exit;
 }elsif($change ne "y" && $change ne "n"){
   print "\nERROR: You must say if the file should be changed (y or n) or not using the -c option\n"; exit;
 }



# create this outfile if we need it
if ($change eq "y"){
 my $outfile = $file;
 $outfile =~ s/\.txt/_noTrailingSpaces\.txt/;
 open (OUT, ">$outfile"); 
}   



######################################################################
# read in the file and check it                                                 #
######################################################################

my @file;
my %columns_count;

if ($file ne ""){
    open (FILE, "<$file")|| die "cannot open library file $file for reading: $!";
    @file = <FILE>;
    close(FILE);
}

my $rowNumber = 1;

foreach my $row (@file){
  chomp($row);
  my @fields = split ("\t",$row, -1);

  
  	# now keep a add one to the count of rows with that number of columns
	if (exists ($columns_count{scalar(@fields)}) ){
           $columns_count{scalar(@fields)} = $columns_count{scalar(@fields)} + 1;
	}else{
         $columns_count{scalar(@fields)} = 1;
        }

       # check for trailing spaces
       foreach my $cell (@fields){
	  if ($cell =~ /\s+$/){
	    print ";$cell; contains a trailing empty space in row $rowNumber\n";
	    if($change eq "y"){
	      	$cell =~ s/\s+$//;
	        print "value is now ;$cell;\n";
	     }
          } 
          if ($cell =~ /\s+\"$/){
            print ";$cell; contains a trailing empty space in row $rowNumber - replacing\n";
	    if ($change eq "y"){
	      $cell =~ s/\s+"$/\"/;
	      print "value is now ;$cell;\n";
	    }
	  }

	}

  # if want to create a new file then join the row again and print out
  if ($change eq "y"){
    my $newRow = join("\t", @fields);
    print OUT "$newRow\n";
  }
  

    $rowNumber++;


}


print "Columns\tNumber of Rows\n";
foreach my $columns (keys %columns_count){
print "$columns\t$columns_count{$columns}\n";
}


if ($change eq "y"){
  close (OUT);
}








