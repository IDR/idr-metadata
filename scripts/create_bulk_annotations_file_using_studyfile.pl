#!/usr/bin/perl

#######################################################################
# create_bulk_annotations_file_using_study.pl                         
#                                                                     
# Eleanor Williams 2015-06-08                                         
#                                                                     
# Script to read in study, library file and processed data   
# files for a High Content Screen and output a comma separated file that can be  
# used as a bulk annotation of the screen in omero.                   
#                                                                     
#######################################################################

#######################################################################
# what it does                                                        
#
# A. reads in a study, library and processed data file (hit list)     
# plus the number of the screen that you want to generate the bulk    
# annotation file for e.g. 1, 2, 3.                                   
# Usually screenA = 1, screenB = 2, screenC = 3 etc                   
#                                                                     
# B. from the study file the screen get:
#   - the rows relating to the screen in question
#   - the column heading to be used to combine the library and
#     processed data files e.g. Gene Identifier
#   - the phenotypes (if any)
#   - the URIs that should be added to the bulk annotation column headings
#                     
# C. from the library file find out:
#   - which column contains the identifier that is going to be used to
#     combined the data with the the processed file
#
# D. from the library and processed data files:
#   - how many columns are in common between the library and processed file
#   - work out how many blank columns will need to be added if there is
#   processed data for a well
#                                                       
# E. from the processed file: 
#    - find out which column contains the identifier which is going to 
#    match up with the library file                                  
#    - remove the columns from the processed file that are already in  
#    the library file as don't need them twice in the final bulk annotation
#    file
#    - for each phenotype in the processed file find out what the
#    associated ontology mappings are (if any)
#
# F. print out data to an output file.
#    - goes through each line of the library file
#    - and adds in the processed data with the ontology mappings added (if there is any)
#    - if there is no processed data then adds blank columns
#    - prints out each line to an output file
# 
#######################################################################

#######################################################################
# Things to be careful of                                             
#                                                                     
# Line Endings
# Watch out for mac line endings in the files. Needs to be unix line
# endings.
#
# Column Heading URLS (apart from ontology ones) e.g. Gene Identifier
# The column heading URLS are added to the columns from the library file
# but they come from the processed file!  This is because
# - we don't collect info about library file column headings (maybe we should?)
# - duplicate columns between the library and processed files are removed
#   from the processed file
# - so far all column headings that need a URL have been in both the
#   library and processed files
# This could be a problem in future though and so the script needs a
# rewrite once we decide if we need to collect info about library file columns
#
#######################################################################

#######################################################################
# TODOs
#
# - if join on Plate_Well then remove this column from the bulk annoation
#   as don't really need it there.
# - put a lot more into subroutines esp the phenotype ontology mapping
#   part. 
# - could do a lot more checking of values e.g. check URIs and
#   ontology accessions are correct format etc. 
# - probably lots of things could be simplified and improved on
# 
#######################################################################

use warnings;
use strict;
use Getopt::Long;
use Data::Dumper;
use Storable qw(dclone);

my $libraryFile = "";
my $processedDataFile = "";
my $studyFile;
my $help = 0;

# variables used throughout
my $columnTitleToCombineOn = "";
my $screenNumber = "";
my $study;
my @libraryFile;
my @processedFile;


######################################################################
# A. get inputs from user and open the files                                          
######################################################################

GetOptions(
	"s=s" => \$studyFile,
        "l=s" => \$libraryFile,
	"p=s" => \$processedDataFile,
	"n=s" => \$screenNumber,   
        "h"   => \$help
	   );


if ($help){
   print "\n Creates a bulk annotation file for a HCS in Omero from a library file and processed data file.

     Options: -s study file (required)
              -l library file (required)
              -p processed data file (hit list) (required)
              -n screen number (1,2,3 etc) 
              -h help information

     Example:  create_bulk_annotations_file_using_studyfile.pl -s idr0000-study.txt -l idr0000-screenB-library.txt -p idr0000-screenB-processed.txt -n 2
     Output :  The output file name is taken from the library file with the extension -annotation.txt rather than -library.txt \n\n";

      exit;

}elsif($studyFile eq ""){
   print "\nERROR: You must provide a study file using the -s option\n"; exit;    
}elsif($libraryFile eq ""){
   print "\nERROR: You must provide a library file using the -l option\n"; exit;
}elsif($processedDataFile eq ""){
   print "\nERROR: You must provide a processed data file file using the -p option\n"; exit;
}elsif($screenNumber eq "") {
   print "\nERROR: You must provide a screen number using the -n option\n"; exit;
}


# read in the study, library and processed data files                       


local $/=undef; # reads in the whole file at once, not line by line. We will split it into sections later
if ($studyFile ne ""){
    open (STUDY, "<$studyFile")|| die "cannot open study file $studyFile for reading: $!";
    $study = <STUDY>;
    close(STUDY);
}

local $/ = "\n"; # back to reading in line by line
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
# B. process the study file                                             
# 1. find the right screen                                           
# 2. find which column to combine on                                  
# 3. get the phenotypes and the ontology mappings
# 4. get the URIS for columns that are in the processed file e.g. Gene Identifiers etc
#####################################################################


# 1. find the right screen 
my $screenRows_ref = getScreenRows($study, $screenNumber);
my @screenRows = @$screenRows_ref;
my @screenNameRow = split ("\t", $screenRows[1]); 
print "Making bulk annotation file for screen $screenNameRow[1]\n";

# 2. find which column to combine on  
$columnTitleToCombineOn = getColumnToCombineOn(\@screenRows);
#print "The column to combine on is $columnTitleToCombineOn\n";

# 3. get the phenotypes and the ontology mappings
# Create a hash of the submitter phenotypes and their ontology sources, terms and accessions
# There may be more than one ontology term so structures will be like
# submitted_phenotype1 => CMPO, CMPO_term, CMPO_acccession
# submitted_phenotype2 => CMPO, CMPO_term, CMPO_acccession, CMPO, CMPO_term, CMPO_acccession

   my $phenotype_ontologyArray_ref = getPhenotypes(\@screenRows);
   my %phenotype_ontologyArray = %$phenotype_ontologyArray_ref;

   unless (%phenotype_ontologyArray){
     warn "WARNING: There are no phenotypes for this screen\n";
   }

# 4. get the URIS for columns that are in the processed file e.g. Gene Identifiers etc
   my $columnName_URIs_ref = getIdentifierURIs(\@screenRows);
   my %columnName_URI = %$columnName_URIs_ref;

   unless (%columnName_URI){
   warn "WARNING: There are no identifiers with URIs for this screen\n";
   } 


######################################################################
# C. process the library file                                           
# 5. find out which column contains the identifier which is going to 
#    match up with the processed file                                
######################################################################


# 5. which column in library file has identifier to match column in
# processed file

my $indexOfLibraryFileColumnForMatching;

my @libraryHeaderRow = split("\t", $libraryFile[0]);


my $n=0;
foreach my $column (@libraryHeaderRow){
  if ($column =~ /^$columnTitleToCombineOn$/){
    $indexOfLibraryFileColumnForMatching = $n;
    last;
  }
  $n++;
}

# remove any new line characters
foreach my $libraryHeader (@libraryHeaderRow){
chomp ($libraryHeader);
}

####################################################################
# D. columns in common between library and processed data files
# (note no effort is made to check the content is the same, just
# the column titles)
#
# 6. find out which columns appear in both the library and processed 
#    files? We don't want them repeated twice in the final output    
#    file.                                                           
# 7. if a well in the library file has no processed data information 
#    then we will need to add a number of empty columns to that row  
#    in the output file so that table has same number of columns for 
#    each row.  So work out how many blank columns to add.           
######################################################################

# 6. which columns appear in both the library and processed files?   

my @columnsToLooseFromProcessedFile;
my $numberOfColumnsUniqueToProcessedFile=0;
my $blankColumnsIfNoProcessedData = "";

my @processedHeaderRow = split("\t", $processedFile[0]);

for (my $index=0; $index<@processedHeaderRow; $index++){
  chomp($processedHeaderRow[$index]);
#  print "Column is ;$processedHeaderRow[$index];\n";
  if (grep (/^\Q$processedHeaderRow[$index]\E$/, @libraryHeaderRow)){ # have to do quotemeta to match if the string has square brackets
                                                                      # e.g. Experimental Condition [genotype]
  push @columnsToLooseFromProcessedFile, $index;
  }
}

$numberOfColumnsUniqueToProcessedFile = scalar(@processedHeaderRow) - scalar(@columnsToLooseFromProcessedFile);


# 7. make a string of blank columns equal to the number of columns
#    left in the processed data file after removing columns also in
#    the library file

for (my $blanks=0; $blanks<$numberOfColumnsUniqueToProcessedFile-1; $blanks++){
  $blankColumnsIfNoProcessedData = $blankColumnsIfNoProcessedData.",";
}


######################################################################
# E. process the processed data file                                    
# 8. find out which column contains the identifier which is going to 
#    match up with the library file                                  
# 9. remove the columns from the processed file that are already in  
#    the library file as don't need them twice in the final file
# 10. For each phenotype in the processed file find out what the
#    associated ontology mappings are (if any)
######################################################################

# 8. which column in processed file has identifier to match column in
# library file

my $indexOfProcessedFileColumnForMatching;

my $p=0;
foreach my $column (@processedHeaderRow){
  if ($column =~ /^$columnTitleToCombineOn$/){
#    print "column to match on is $column\n";
    $indexOfProcessedFileColumnForMatching = $p;
    last;
  }
  $p++;
}


# 9. remove the columns from the processed file that are already in  
#    the library file as don't need them twice in the final file. To 
#    do this need to create a hash of the column numbers and the     
#    values otherwise as soon as one column is removed all the other 
#    column numbers in the array will change.                        
#    Then put the remaining row into a hash with the common          
#    identifier as the key.                                          


  my %Identifier_otherColumns;


  # get each row of the processed file
for (my $row=0; $row<@processedFile; $row++){
  
     chomp ($processedFile[$row]);  
     my @thisRow = split("\t", $processedFile[$row], -1); # the -1 means that trailing empty cells are kept as part of @thisRow

     # create the hash of with the column number and then column value
     my %columnNumber_columnValue;
     my $count=0;
     foreach my $columnValue (@thisRow){
     #   print "Column Number: $count Value: $columnValue\n";
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


# 10. For each phenotype in the processed file find out what the
#    associated ontology mappings are (if any)

# first clone the hash of arrays with the identifier and the columns so can
# move through all the columns in the original file without the column numbers
# jumping due to column insertions

 my %Identifier_otherColumnsWithOntology = %{ dclone(\%Identifier_otherColumns) };

#print "At start old header row is @{$Identifier_otherColumns{$columnTitleToCombineOn}}\n";
#print "At start new header row is @{$Identifier_otherColumnsWithOntology{$columnTitleToCombineOn}}\n";

# if there are any phenotypes then add the ontology to the new header row otherwise it will just stay the same as
# it is

if  (%phenotype_ontologyArray){ # if there are any phenotypes mentioned in the study file for the screen

# find which are the phenotype columns from the processed file
# when get a phenotype column, find out what its in it, then get mapping
# store which ontology with the phenotype to add link in header
# then add the header rows
# then go through and add the mappings
  
my $b = 0;
my $numberOntologyColumnsAdded = 0;

for my $a (0 .. $#{$Identifier_otherColumns{$columnTitleToCombineOn}}) { # going through column headings of original array
  # Reminder: %Identifier_otherColumns has each identifier e.g. Plate_Well or Gene Identfier that is used to combined the 
  # library and processed data files as the key, and all the processed data columns that go with that identifier as the values
  # So here we are going through the column headings row because the key is what ever the column title to combine on is

       if( ${$Identifier_otherColumns{$columnTitleToCombineOn}}[$a] =~ m/^Phenotype\s?\d*$/){  # when we get a phenotype column ...

	 my @mapping = ();
         my $numberOfMappings = 0;
	 my @ontologiesUsed = ();

	 # FIRST TIME ROUND - JUST FIND OUT FOR THIS PHENOTYPE IF THERE IS A MAPPING, AND IF SO IS IT ONE OR TWO TERMS
	 # AND WHAT ONTOLOGIES ARE THEY FROM
	 
         foreach my $identifier (keys %Identifier_otherColumns){ # start going through all the rows in that phenotype column to find one with a value
	   
	   if (($Identifier_otherColumns{$identifier}[$a] =~ m/\w+/) && ($identifier ne $columnTitleToCombineOn))  { # if the value matches a word character but is not the column heading
	     # see if this phenotype has an ontology mapping


             if (grep (/\Q$Identifier_otherColumns{$identifier}[$a]\E/, keys %phenotype_ontologyArray)){ # check the phenotype exists in the study file. Have to use quotemeta in case there is a bracket or other character needing escaping in the phenotype value
	     
                 @mapping = @{$phenotype_ontologyArray{$Identifier_otherColumns{$identifier}[$a]}};	  # this info comes from the study file   
    
	            if(scalar(@mapping) == 3){
		         $numberOfMappings = 1;
		         push @ontologiesUsed, $mapping[0];
                         last;			
	            }elsif(scalar(@mapping) == 6){  
		         $numberOfMappings = 2;
		         push @ontologiesUsed, $mapping[0], $mapping[3];
                         last;
		    }else{
                         $numberOfMappings = 0;
	                last; 
		       }

	       }else{
               die "ERROR: Phenotype '$Identifier_otherColumns{$identifier}[$a]' does not exist in the study file: $!";
	       }
	   } # if there is a value and its not the column heading
	 } # foreach identifier

	 # get the URIs associated with the ontologies used

	 my %ontology_URI;
	 foreach my $ontology (@ontologiesUsed){
	   my $URI = getOntologyURI($ontology, $study);
	   $ontology_URI{$ontology} = $URI;
	 }

	 
         # SECOND TIME ROUND - GO THROUGH EACH IDENTIFIER, IF THERE IS A PHENOTYPE ADD THE MAPPINGS, IF NOT THEN JUST ADD THE SAME NUMBER OF TABS
	 # IF THERE IS A PHENOTYPE BUT THIS PHENOTYPE HAS NO ONTOLOGY MAPPING THEN SKIP TO THE NEXT COLUMN
	 
         if ($numberOfMappings == 1){

              # for each identifier, if there is a value - put in the one mapping, if heading, put in column titles, if no value put in 2 tabs
	   foreach my $identifier (keys %Identifier_otherColumns){
	                
	               if (($Identifier_otherColumns{$identifier}[$a] =~ m/\w+/) && ($identifier ne $columnTitleToCombineOn))  { # if the value matches a word character but is not the column heading

		         @mapping = @{$phenotype_ontologyArray{$Identifier_otherColumns{$identifier}[$a]}};
	                 splice @{$Identifier_otherColumnsWithOntology{$identifier}}, $b+1, 0, $mapping[1], $mapping[2];
		      
		       }elsif($identifier eq $columnTitleToCombineOn){ # column title
                           if(${$Identifier_otherColumns{$columnTitleToCombineOn}}[$a] =~ m/^Phenotype\s?(\d+)$/){# if column name has a number e.g. Phenotype 1
			     my $number = $1;
			     my $termName = "Phenotype ".$number." Term Name";
			     my $termAcc = "Phenotype ".$number." Term Accession %% url=".$ontology_URI{$ontologiesUsed[0]}."%s";
			     
			     splice @{$Identifier_otherColumnsWithOntology{$columnTitleToCombineOn}}, $b+1, 0, $termName, $termAcc;
			     $numberOntologyColumnsAdded = $numberOntologyColumnsAdded + 2;
          	           }else{
			     my $termAcc =  "Phenotype Term Accession %% url=".$ontology_URI{$ontologiesUsed[0]}."%s";
                           splice @{$Identifier_otherColumnsWithOntology{$columnTitleToCombineOn}}, $b+1, 0, 'Phenotype Term Name', $termAcc;
	                   }   

			 }else{ # no value
			 # insert empty column
	                 splice @{$Identifier_otherColumnsWithOntology{$identifier}}, $b+1, 0,"", "";
		      
                    }
               } # foreach identifier
         $b=$b+3;
	 }elsif($numberOfMappings == 2){
                # for each identifier, if there is a value - put in the two mappings, if heading, put in column titles, if no value put in 4 tabs

	      foreach my $identifier (keys %Identifier_otherColumns){
		if (($Identifier_otherColumns{$identifier}[$a] =~ m/\w+/) && ($identifier ne $columnTitleToCombineOn))  { # if the value matches a word character but is not the column heading
		        @mapping = @{$phenotype_ontologyArray{$Identifier_otherColumns{$identifier}[$a]}};
	                splice @{$Identifier_otherColumnsWithOntology{$identifier}}, $b+1, 0, $mapping[1], $mapping[2], $mapping[4], $mapping[5];
		      
		 }elsif($identifier eq $columnTitleToCombineOn){ # column title
                          if(${$Identifier_otherColumns{$columnTitleToCombineOn}}[$a] =~ m/^Phenotype\s?(\d+)$/){# if column name has a number e.g. Phenotype 1
		             my $number = $1;
			     my $termNameA = "Phenotype ".$number." Term Name a";
			     my $termAccA = "Phenotype ".$number." Term Accession a %% url=".$ontology_URI{$ontologiesUsed[0]}."%s";
 	                     my $termNameB = "Phenotype ".$number." Term Name b";
			     my $termAccB = "Phenotype ".$number." Term Accession b %% url=".$ontology_URI{$ontologiesUsed[1]}."%s";		   
                             splice @{$Identifier_otherColumnsWithOntology{$columnTitleToCombineOn}}, $b+1, 0, $termNameA, $termAccA, $termNameB, $termAccB;
			   }else{
                             my $termAccA = "Phenotype Term Accession a %% url=".$ontology_URI{$ontologiesUsed[0]}."%s";
                             my $termAccB = "Phenotype Term Accession b %% url=".$ontology_URI{$ontologiesUsed[1]}."%s";			     
                             splice @{$Identifier_otherColumnsWithOntology{$columnTitleToCombineOn}}, $b+1, 0, 'Phenotype Term Name a', $termAccA, 'Phenotype Term Name b', $termAccB;
	                  }   
                 $numberOntologyColumnsAdded = $numberOntologyColumnsAdded + 4;
		 }else{ # no value
                         # inserting four spaces
	                 splice @{$Identifier_otherColumnsWithOntology{$identifier}}, $b+1, 0,"", "", "", "";		      
                    }

               } # foreach identifier
         $b=$b+5;
	 }else{
	   # must be no mappings for the phenotype so do nothing
	 $b++;
	 }


       }else{ # not a phenotype column so just move to the next column
	 $b++;
       }

} # for each column heading	 




#print "At end old header row is @{$Identifier_otherColumns{$columnTitleToCombineOn}}\n";
#print "At end new header row is @{$Identifier_otherColumnsWithOntology{$columnTitleToCombineOn}}\n";
#print "Total number of columns added due to ontologies is $numberOntologyColumnsAdded\n";

# add on the number of columns added for ontologies to the list of columns to be added if there is no processed data

for (my $x=0; $x<$numberOntologyColumnsAdded; $x++){
$blankColumnsIfNoProcessedData = $blankColumnsIfNoProcessedData.",";
}

} # if there are any phenotypes listed in the study file
 
######################################################################
# F. create the output file                                             #
# 11. create the out file name and open it                            #
# 12. the library file contains information for every well, so go     #
#    through each line in it, print out each line, adding            #
#    information from the processed file if there is any.            #
######################################################################

######################################################################
# 11. open the output file

my $outfile = $libraryFile;
$outfile =~ s/-library\.txt/-annotation\.txt/g; # its comma delimited but
#                                                 make it end in .txt so can
#                                                 open in Excel corrently
open (OUT, ">$outfile");

######################################################################
# 12. go through each line in the library file and print out          #
#    adding processed file info if needed                            #

my $v=0;
foreach my $libRow (@libraryFile){
  chomp($libRow);

  # if it is first row then check to see if any of the column headings need a URL added
  
  # TODO:  But columns with links are identified in the processed file 
  # What if column with link is only in the library file?
  
  if ($v == 0){
    my @columnNames = split("\t", $libRow);

      foreach my $name (@columnNames){
        if (exists $columnName_URI{$name}){
	  $name = $name." %% url=".$columnName_URI{$name}."%s";	  
	}
      }
    $libRow = join("\t", @columnNames);   
  }
  
  
  $libRow =~ s/\t/\,/g; # change tabs to commas as want output file to be comma separated
  print OUT "$libRow\,";  

  my @libraryRow = split ("\,", $libRow, -1);  



 # add processed data if there is any or blank columns if not        #

  # if it is first row and column name for matching to processed data has had URL added, need to find it without the URL  
  if ($v == 0){
    if ($libraryRow[$indexOfLibraryFileColumnForMatching] =~ m/http/){
      # temporarily remove the link and match the header row in the processed file and print out
      my $columnNameWithoutLink = $libraryRow[$indexOfLibraryFileColumnForMatching];
      $columnNameWithoutLink =~ /^(.*)\ %%.*/;
      $columnNameWithoutLink = $1;
      $libraryRow[$indexOfLibraryFileColumnForMatching] = $columnNameWithoutLink;
      my $processedRow = join("\,", @{$Identifier_otherColumnsWithOntology{$libraryRow[$indexOfLibraryFileColumnForMatching]}});
      print OUT "$processedRow";


    }else{ # just match as normal
         if (exists ($Identifier_otherColumnsWithOntology{$libraryRow[$indexOfLibraryFileColumnForMatching]})) {
             my $processedRow = join("\,", @{$Identifier_otherColumnsWithOntology{$libraryRow[$indexOfLibraryFileColumnForMatching]}});
             print OUT "$processedRow";
         }else{
             print OUT "$blankColumnsIfNoProcessedData";
             }   

       }
    
  }else{ # not the first (column heading) row
    
    if (exists ($Identifier_otherColumnsWithOntology{$libraryRow[$indexOfLibraryFileColumnForMatching]})) {
      my $processedRow = join("\,", @{$Identifier_otherColumnsWithOntology{$libraryRow[$indexOfLibraryFileColumnForMatching]}});
      print OUT "$processedRow";
    }else{
      print OUT "$blankColumnsIfNoProcessedData";
    }   
  } # else not the first row

   # put a line ending at the end of every row
   print OUT "\n";

  $v++;
}

close (OUT);



############################################################################################

   

sub getScreenRows{
  my ($studyFile, $screenNumber) = @_;

  if (grep (/Screen Number/, $studyFile)){  
  # split the studyFile on "Screen Number"
    my @sections = split ("Screen Number", $studyFile);
    
     # first section [0] is the study top level info then each following section is a screen
     # get the rows for the screen we want as long as the screen number is valid
        if ( ($screenNumber != 0) && ($screenNumber <= scalar(@sections)-1 ) ){
           my @screenRows = split("\n", $sections[$screenNumber]);
           return \@screenRows;
	 }else{
           die "Screen Number must be the same as one of those specified in the study file; $!";
	 }
	
  }else{
  die "Phrase 'Screen Number' does not exist in the study file so can't get the screen information: $!";
  }
  
}



sub getColumnToCombineOn{
  # Find out which column the library and processed files should be
  # joined on from the study file, screen section
   my $screenRef = shift;

  my $columnToCombine = "none";
  
  foreach my $row (@$screenRef){
    if ($row =~ m/Processed Data Column Link To Library File/) {
      my @cells = split("\t", $row);
       $columnToCombine = $cells[1];
     }
   }

   # if there is no 'Processed Data Column Link to Library File' row or the value is empty then stop here
   if ($columnToCombine eq "none" || $columnToCombine !~ /\w+/){
      die "No column to combine on information for the screen in the study file: $!";
   }else{
     return $columnToCombine;
   }
}


sub getOntologyURI{
  # Find out what the base URIs for the ontologies used
  # these are in the study file, first general section.
  # Ontology name is in one row, URI is on the next
  
  my ($ontologyAskedFor, $studyFile) = @_;
  my %ont_URI; # for storing what we find

  # split the study file on new line character and
  # then find the ontology URI rows
  my @studyRows = split("\n", $studyFile);
  
  # ontology names and URIs
  my @sourceNames;
  my @sourceURIs;
  
  foreach my $row (@studyRows){
    if ($row =~ m/Term Source Name/){
    @sourceNames = split("\t", $row);
    }elsif ($row =~ m/Term Source URI/){
    @sourceURIs = split("\t", $row);
    } 
  }

  # put names and URIs together in one hash
  for my $n (0 .. $#sourceNames){
     $ont_URI{$sourceNames[$n]} = $sourceURIs[$n];      
  }


       # now get the URI we want in this case and return it
       my $wantedURI = $ont_URI{$ontologyAskedFor};

       # if there is no URI for that ontology output a warning and set URI to be blank
       unless ($wantedURI){
	 die "ERROR: There is no URI in the study file for ontology $ontologyAskedFor\n";
       }

       # check it ends in a forward slash, if not add one
       if($wantedURI !~ /.*\/$/){
       $wantedURI = $wantedURI."/";
       }
       return $wantedURI;
  
}

sub getIdentifierURIs{
  
  # Find out what from the study file which identifiers in the processed should have a URI link
  # and what the link should be
  # These are in screen section of the study file with the
  # processed data information
  my $screenRef = shift;

  # find the row with the URIs and column names
  my @URIs;
  my @columnNames;
  
  foreach my $row (@$screenRef){
    if ($row =~ m/Processed Data Column Source Stem URI/) {
      @URIs = split("\t", $row); 
    }elsif($row =~ m/Processed Data Column Name/) {
       @columnNames = split("\t", $row);
     }   
   }

  # find out which columns actually have a URI and then go and
  # and get the corresponding Processed Data Column Name
  my $n = 0;
  my @columnsWithURIs;
  foreach my $URI (@URIs){
    if($URI =~ m/http/){
      push @columnsWithURIs, $n;
    }
    $n++;
  }  
  
  # put results in a hash table
  my %colName_URI;
  foreach my $colNumber(@columnsWithURIs){
    $colName_URI{$columnNames[$colNumber]} = $URIs[$colNumber];  
  }

  return \%colName_URI;

}

sub getPhenotypes{

   my $screenRef = shift;
   my @screenRows = @$screenRef;
   
   my %screenPhenotype_ontologyArray;
   # keep it easy to understand using variables;
   my @phenotypes = ();
   my @termSource1= ();
   my @termNames1 = ();
   my @termAccs1 = ();
   my @termSource2 = ();
   my @termNames2 = ();
   my @termAccs2 = ();
   
   
   # find where the phenotype row is
   # then get the first mappings if there are any
   # then get the second mappings if there are any
   # assuming there are never more than 2 mappings

   for (my $n=0; $n<@screenRows; $n++){

     if ($screenRows[$n] =~ m/Phenotype Name/){

	# split the row and get all the phenotypes + first lot of mappings (always have these rows)
	  @phenotypes = split("\t", $screenRows[$n]);
	  @termSource1 = split("\t", $screenRows[$n+3], -1);  # the -1 keeps trailing columns
	  @termNames1 = split("\t", $screenRows[$n+4], -1);
	  @termAccs1 = split("\t", $screenRows[$n+5], -1);				      

       # then see if we have another lot of ontology terms

	  if ($screenRows[$n+6] =~ m/Phenotype Term Source REF/){
#	  print "we have some second ontology terms\n";
	  @termSource2 = split("\t", $screenRows[$n+6], -1);
	  @termNames2 = split("\t", $screenRows[$n+7], -1);
	  @termAccs2 = split("\t", $screenRows[$n+8], -1);
	}


     } # if phenotype row
					     					      
   } # for

 #        print "Getting the phenotypes from the library file: \n";
         my @mappingsArray =();
         # put it all into the hash of arrays
         my $maxNumberOfOntTerms = 1; # use this to see if we have any phenotypes that map to 2 ontology terms
                                      # like 'abnormal' + 'microtubule structure'
         # go through each column in each row
         for (my $t=1; $t<@phenotypes; $t++){ # first column is 'Phenotype Name' so don't need that
  	  # print "phenotype found is ;$phenotypes[$t];\n";
           # only add values if they have a letter character i.e. not blank
           if ($termSource1[$t] =~ /\w+/){push @mappingsArray, $termSource1[$t];}
   	   if ($termNames1[$t]  =~ /\w+/){push @mappingsArray, $termNames1[$t];}
	   if ($termAccs1[$t]   =~ /\w+/){push @mappingsArray, $termAccs1[$t];}

              if (scalar(@termSource2) > 0){
	         # print "Looking at second mappings\n";
		  $maxNumberOfOntTerms = 2;
                  if ($termSource2[$t] =~ /\w+/){push @mappingsArray, $termSource2[$t];}
   	          if ($termNames2[$t]  =~ /\w+/){push @mappingsArray, $termNames2[$t];}
	          if ($termAccs2[$t]   =~ /\w+/){push @mappingsArray, $termAccs2[$t];}
	      }
	   
	  # print "array is going to be @mappingsArray \n";
	   my @mappingsArrayCopy =  @mappingsArray;
           $screenPhenotype_ontologyArray{$phenotypes[$t]} = \@mappingsArrayCopy;

	   # then reset the mappingsArray to be empty
	   @mappingsArray=();
	   
	 }

  # print Dumper %screenPhenotype_ontologyArray;
	 
   return \%screenPhenotype_ontologyArray;
}


sub havePhenotypes{
   # subroutine to determine whether there are any phenotype values for the screen in the study file
   
   my $screenRef = shift;
   my @screenRows = @$screenRef;
   my $have_phenotypes = "false";

   # find the row that is the Phenotype Name row and see if there are any values
   for (my $n=0; $n<@screenRows; $n++){
        if ($screenRows[$n] =~ m/Phenotype Name/){
           $screenRows[$n] =~ s/Phenotype Name//;
           if($screenRows[$n] =~ /\w/){ # if matches a letter character then we have phenotype values
           $have_phenotypes = "true";
	   }
	last;
	}
    }

   return $have_phenotypes;
   
 }
