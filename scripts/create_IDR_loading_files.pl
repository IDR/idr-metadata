#!/usr/bin/perl
use warnings;
use strict;

use Getopt::Long;

######################################################################
#           #
######################################################################

my $infile = "";
my $help = "";


######################################################################
# get inputs from user                                               #
######################################################################

GetOptions(
        "f=s" => \$infile,
	   "h"   => \$help
	   );


if ($help){
   print "Script to read in a file with a list of plates and directory listings for the images related to the plate\n";
   exit;
}elsif($infile eq ""){
  print "\nERROR: You must provide a input file using the -f option\n";
  exit;
}

######################################################################
# read in the ptdump file                                            #               
######################################################################

my @in;

if ($infile ne ""){
    open (IN, "<$infile")|| die "cannot open input file $infile for reading: $!";
    @in = <IN>;
    close(IN);
}

# for each row, create a file with the plate name and put the directory path in the contents of the file



for (my $n=0; $n<@in; $n++){
  chomp($in[$n]);

  my ($plate, $path) = split("\t", $in[$n]);
  print "plate is $plate and path is $path\n";

  my $outfile = $plate;

open (OUT, ">$outfile");
print OUT "$path\n";
close (OUT); 

}








