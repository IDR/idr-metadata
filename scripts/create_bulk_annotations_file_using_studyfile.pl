#!/usr/bin/perl

# NOTE:  Comments need updating
# TODO: should add a log file which documents any problems like no ontology terms found for a phenotype
# so that I can check everything is as it should be afterwards.



#######################################################################
# create_bulk_annotations_file_using_study_v2.pl                                     #
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
# get inputs from user                                               #
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

     Example:  create_bulk_annotations_file.pl -l libraryFile.csv -p processedData.csv -n 2
     Output :  The output file name is taken from the library file with the extension .BULK_ANNOTATION.csv\n\n";

      exit;

     

}elsif($libraryFile eq ""){
   print "\nERROR: You must provide a library file using the -l option\n"; exit;
}elsif($processedDataFile eq ""){
   print "\nERROR: You must provide a processed data file file using the -p option\n"; exit;
}elsif($screenNumber eq "") {
   print "\nERROR: You must provide a screen number\n"; exit;
}

######################################################################
# read in the study, library and processed data files                       #
######################################################################

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

# process the study file
# 1. find the right screen
# 2. find which column to combine on
# 3. get the phenotypes and the ontology mappings
# 4. get the URIS for the ontologies and for the Gene Identifiers etc

# get all the rows for the screen we are making the bulk annotation file for

my $screenRows_ref = getScreenRows($study, $screenNumber);

my @screenRows = @$screenRows_ref;

my @screenNameRow = split ("\t", $screenRows[1]); 
print "The screen name is $screenNameRow[1]\n";

$columnTitleToCombineOn = getColumnToCombineOn(\@screenRows);
print "The column to combine on is $columnTitleToCombineOn\n";

# Now create a hash of the submitter phenotypes and their ontology sources, terms and accessions
# There may be more than one ontology term so structures will be like
# submitted_phenotype1 => CMPO, CMPO_term, CMPO_acccession
# submitted_phenotype2 => CMPO, CMPO_term, CMPO_acccession, CMPO, CMPO_term, CMPO_acccession

my $phenotype_ontologyArray_ref = getPhenotypes(\@screenRows);
my %phenotype_ontologyArray = %$phenotype_ontologyArray_ref;

my $columnName_URIs_ref = getIdentifierURIs(\@screenRows);
my %columnName_URI = %$columnName_URIs_ref;


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

my @libraryHeaderRow = split("\t", $libraryFile[0]);


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

my @processedHeaderRow = split("\t", $processedFile[0]);

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
     my @thisRow = split("\t", $processedFile[$row], -1); # the -1 means that trailing empty cells are kept as part of @thisRow

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

# Ontology Mappings and Adding Links to Column Names!


# find which are the phenotype columns from the processed file
# when get a phenotype column, find out what its in it, then get mapping
# store which ontology with the phenotype to add link in header
# then add the header rows
# then go through and add the mappings


# first clone the hash of arrays with the identifier and the columns so can
# move through all the columns in the original file without the column numbers
# jumping due to column insertions

 my %Identifier_otherColumnsWithOntology = %{ dclone(\%Identifier_otherColumns) };

print "At start old header row is @{$Identifier_otherColumns{$columnTitleToCombineOn}}\n";
print "At start new header row is @{$Identifier_otherColumnsWithOntology{$columnTitleToCombineOn}}\n";

my $b = 0;
my $numberOntologyColumnsAdded = 0;

for my $a (0 .. $#{$Identifier_otherColumns{$columnTitleToCombineOn}}) { # going through column headings of original array
  print "We are position $a in original row.\n";
  print "We are at position $b in new row\n";
 

       if( ${$Identifier_otherColumns{$columnTitleToCombineOn}}[$a] =~ m/^Phenotype\s?\d*$/){
	 print "This is a phenotype column\n";

	 my @mapping = ();
         my $numberOfMappings = 0;
	 my @ontologiesUsed = ();

	 # FIRST TIME ROUND - JUST FIND OUT FOR THIS PHENOTYPE IF THERE IS A MAPPING, AND IF SO IS IT ONE OR TWO TERMS
	 # AND WHAT ONTOLOGIES ARE THEY FROM
	 
         foreach my $identifier (keys %Identifier_otherColumns){
           print "First time round: identifier is $identifier\n";
	   
	   if (($Identifier_otherColumns{$identifier}[$a] =~ m/\w+/) && ($identifier ne $columnTitleToCombineOn))  { # if the value matches a word character but is not the column heading
	     # see if this phenotype has an ontology mapping
	     print "Phenotype is $Identifier_otherColumns{$identifier}[$a] ";
             @mapping = @{$phenotype_ontologyArray{$Identifier_otherColumns{$identifier}[$a]}};
	     print "and mapping is @mapping and length is ", scalar(@mapping), "\n";	     
    
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
	   } # if there is a value and its not the column heading
	 } # foreach identifier

         print "For this phenotype there are $numberOfMappings mappings\n";
	 print "For this phenotype the ontologies used are @ontologiesUsed \n";

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
	                  print "Second time round, 1 mapping, identifier is $identifier\n";
		         @mapping = @{$phenotype_ontologyArray{$Identifier_otherColumns{$identifier}[$a]}};
                         print "inserting mapping terms $mapping[1] and $mapping[2] \n";
	                 splice @{$Identifier_otherColumnsWithOntology{$identifier}}, $b+1, 0, $mapping[1], $mapping[2];
		      
		       }elsif($identifier eq $columnTitleToCombineOn){ # column title
			 print "Second time round, 1 mapping, identifier is $identifier - column title\n";
                           if(${$Identifier_otherColumns{$columnTitleToCombineOn}}[$a] =~ m/^Phenotype\s?(\d+)$/){# if column name has a number e.g. Phenotype 1
			     my $number = $1;
			     my $termName = "Phenotype Term Name ".$number;
			     my $termAcc = "Phenotype Term Accession ".$number." %% url=".$ontology_URI{$ontologiesUsed[0]}."%s";
			     
			     splice @{$Identifier_otherColumnsWithOntology{$columnTitleToCombineOn}}, $b+1, 0, $termName, $termAcc;
			     $numberOntologyColumnsAdded = $numberOntologyColumnsAdded + 2;
          	           }else{
			     my $termAcc =  "Phenotype Term Accession %% url=".$ontology_URI{$ontologiesUsed[0]}."%s";
                           splice @{$Identifier_otherColumnsWithOntology{$columnTitleToCombineOn}}, $b+1, 0, 'Phenotype Term Name', $termAcc;
	                   }   

		       }else{ # no value
			 print "Second time round, 1 mapping, identifier is $identifier - no value in Phenotype column\n";
                         print "inserting two spaces \n";
	                 splice @{$Identifier_otherColumnsWithOntology{$identifier}}, $b+1, 0,"", "";
		      
                    }
               } # foreach identifier
         $b=$b+3;
	 }elsif($numberOfMappings == 2){
                # for each identifier, if there is a value - put in the two mappings, if heading, put in column titles, if no value put in 4 tabs

	      foreach my $identifier (keys %Identifier_otherColumns){
		if (($Identifier_otherColumns{$identifier}[$a] =~ m/\w+/) && ($identifier ne $columnTitleToCombineOn))  { # if the value matches a word character but is not the column heading
		   print "Second time round, 2 mappings, identifier is $identifier\n";
		        @mapping = @{$phenotype_ontologyArray{$Identifier_otherColumns{$identifier}[$a]}};
                        print "inserting mapping terms $mapping[1], $mapping[2], $mapping[4], $mapping[5] \n";
	                splice @{$Identifier_otherColumnsWithOntology{$identifier}}, $b+1, 0, $mapping[1], $mapping[2], $mapping[4], $mapping[5];
		      
		 }elsif($identifier eq $columnTitleToCombineOn){ # column title
		   print "Second time round, 2 mappings, identifier is $identifier - column title\n";
                          if(${$Identifier_otherColumns{$columnTitleToCombineOn}}[$a] =~ m/^Phenotype\s?(\d+)$/){# if column name has a number e.g. Phenotype 1
		             my $number = $1;
                             my $termNameA = "Phenotype Term Name ".$number."a";
			     my $termAccA = "Phenotype Term Accession ".$number."a %% url=".$ontology_URI{$ontologiesUsed[0]}."%s";
 	                     my $termNameB = "Phenotype Term Name ".$number."b";
			     my $termAccB = "Phenotype Term Accession ".$number."b %% url=".$ontology_URI{$ontologiesUsed[1]}."%s";		   
                             splice @{$Identifier_otherColumnsWithOntology{$columnTitleToCombineOn}}, $b+1, 0, $termNameA, $termAccA, $termNameB, $termAccB;
			   }else{
                             my $termAccA = "Phenotype Term Accession a %% url=".$ontology_URI{$ontologiesUsed[0]}."%s";
                             my $termAccB = "Phenotype Term Accession b %% url=".$ontology_URI{$ontologiesUsed[1]}."%s";			     
                             splice @{$Identifier_otherColumnsWithOntology{$columnTitleToCombineOn}}, $b+1, 0, 'Phenotype Term Name a', $termAccA, 'Phenotype Term Name b', $termAccB;
	                  }   
                 $numberOntologyColumnsAdded = $numberOntologyColumnsAdded + 4;
		 }else{ # no value
		         print "Second time round, no value, identifier is $identifier -\n";
                         print "inserting four spaces \n";
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

print "At end old header row is @{$Identifier_otherColumns{$columnTitleToCombineOn}}\n";
print "At end new header row is @{$Identifier_otherColumnsWithOntology{$columnTitleToCombineOn}}\n";
print "Total number of columns added due to ontologies is $numberOntologyColumnsAdded\n";

# add on the number of columns added for ontologies to the list of columns to be added if there is no processed data

for (my $x=0; $x<$numberOntologyColumnsAdded; $x++){
$blankColumnsIfNoProcessedData = $blankColumnsIfNoProcessedData.",";
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
#$outfile =~ s/-library\.txt/-annotation\.csv/g;
$outfile =~ s/-library\.txt/-annotation\.txt/g;
open (OUT, ">$outfile");

######################################################################
# 7. go through each line in the library file and print out          #
#    adding processed file info if needed                            #

my $v=0;
foreach my $libRow (@libraryFile){
  chomp($libRow);

  # if it is first row then check to see if any of the column headings need a URL added
  # TODO:  But columns with links are identified in the processed file ****************
  if ($v == 0){
    my @columnNames = split("\t", $libRow);

      foreach my $name (@columnNames){
        if (exists $columnName_URI{$name}){
	  $name = $name." %% url=".$columnName_URI{$name}."%s";
	  print "Column is now $name\n";	  
	}
      }
    $libRow = join("\t", @columnNames);   
  }
  
  
  $libRow =~ s/\t/\,/g; # change tabs to commas as want output file to be comma separated
  print OUT "$libRow\,";  

  my @libraryRow = split ("\,", $libRow, -1);  



 # add processed data if there is any or blank columns if not        #

  # if it is first row and column name for matching to processed data has had URL added, need to find it without the URL
 # print "We are looking at identifier $libraryRow[$indexOfLibraryFileColumnForMatching]\n";
  
  if ($v == 0){
     print "we are at the first row of library file\n";
    if ($libraryRow[$indexOfLibraryFileColumnForMatching] =~ m/http/){
      # temporarily remove the link and match the header row in the processed file and print out
      my $columnNameWithoutLink = $libraryRow[$indexOfLibraryFileColumnForMatching];
      $columnNameWithoutLink =~ /^(.*)\ %%.*/;
      $columnNameWithoutLink = $1;
      $libraryRow[$indexOfLibraryFileColumnForMatching] = $columnNameWithoutLink;
      my $processedRow = join("\,", @{$Identifier_otherColumnsWithOntology{$libraryRow[$indexOfLibraryFileColumnForMatching]}});
      print OUT "$processedRow";
      print "Printing out $processedRow\n";

    }else{ # just match as normal
         if (exists ($Identifier_otherColumnsWithOntology{$libraryRow[$indexOfLibraryFileColumnForMatching]})) {
             my $processedRow = join("\,", @{$Identifier_otherColumnsWithOntology{$libraryRow[$indexOfLibraryFileColumnForMatching]}});
             print OUT "$processedRow";
         }else{
             print OUT "$blankColumnsIfNoProcessedData";
             }   

    }
  }else{
    
    if (exists ($Identifier_otherColumnsWithOntology{$libraryRow[$indexOfLibraryFileColumnForMatching]})) {
      my $processedRow = join("\,", @{$Identifier_otherColumnsWithOntology{$libraryRow[$indexOfLibraryFileColumnForMatching]}});
      print OUT "$processedRow";
    }else{
      print OUT "$blankColumnsIfNoProcessedData";
    }   
 } # else not the first row
   print OUT "\n";

  $v++;
}

close (OUT);





   

sub getScreenRows{
  my ($studyFile, $screenNumber) = @_;

  # split the studyFile on "Screen Number"
  my @sections = split ("Screen Number", $studyFile);
  print "There are ", scalar(@sections) ," sections in this study file\n";

  # first section [0] is the study top level info then each following section is a screen
  # get the rows for the screen we want
  my @screenRows = split("\n", $sections[$screenNumber]);
  return \@screenRows;
  
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

   return $columnToCombine;
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

       # check it ends in a forward slash, if not add one
       if($wantedURI !~ /.*\/$/){
       $wantedURI = $wantedURI."/";
       }
       return $wantedURI;
  
}

sub getIdentifierURIs{
  # Find out what identifiers should have a URI link
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
	  print "we have some second ontology terms\n";
	  @termSource2 = split("\t", $screenRows[$n+6], -1);
	  @termNames2 = split("\t", $screenRows[$n+7], -1);
	  @termAccs2 = split("\t", $screenRows[$n+8], -1);
	}


     } # if phenotype row
					     					      
   } # for

         print "Getting the phenotypes from the library file: \n";
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



