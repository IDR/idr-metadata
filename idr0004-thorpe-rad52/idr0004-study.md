Generic Information
===================

Section with generic information about the study including title,
description, publication details (if applicable) and contact details.


Study
-----

**Study Title:** Genome-wide analysis of Rad52 foci reveals diverse
mechanisms impacting recombination.

**Study Type:** high content screen

**Study Type Term Source REF:**

**Study Type Term Accession Number:**

**Study Description:** To investigate the DNA damage response, we
undertook a genome-wide study in Saccharomyces cerevisiae and
identified 86 gene deletions that lead to increased levels of
spontaneous Rad52 foci in proliferating diploid cells. More than half
of the genes are conserved across species ranging from yeast to
humans. Along with genes involved in DNA replication, repair, and
chromatin remodeling, we found 22 previously uncharacterized open
reading frames. Analysis of recombination rates and synthetic genetic
interactions with rad52Delta suggests that multiple mechanisms are
responsible for elevated levels of spontaneous Rad52 foci, including
increased production of recombinogenic lesions, sister chromatid
recombination defects, and improper focus assembly/disassembly. Our
cell biological approach demonstrates the diversity of processes that
converge on homologous recombination, protect against spontaneous DNA
damage, and facilitate efficient repair.

**Study Organism:** Saccharomyces cerevisiae

**Study Organism Term Source REF:** ncbi_taxonomy

**Study Organism Term Accession Number:**
http://purl.obolibrary.org/obo/NCBITaxon_4932

**Study Screens Number:** 1

**Study External URL:**

**Study Public Release Date:** 2015-05-01


Study Publication
-----------------

**Study PubMed ID:** 21893595: 18085829

**Study Publication Title:** Bringing Rad52 foci into focus.: Genome-wide
analysis of Rad52 foci reveals diverse mechanisms impacting
recombination.

**Study Author List:** Thorpe PH, Alvaro D, Lisby M, Rothstein R.":
"Alvaro D, Lisby M, Rothstein R.


Study Contacts
--------------

**Study Person Last Name:** Peter

**Study Person First Name:** Thorpe

**Study Person Email:** peter.thorpe@crick.ac.uk

**Study Person Address:** The Francis Crick Institute, London, UK.

**Study Person Roles:** submitter

**Term Source Name:** ncbi_taxonomy: EFO: CMPO

**Term Source File:** http://purl.obolibrary.org/obo/ncbitaxon.owl:
http://www.ebi.ac.uk/efo/efo.owl: http://www.ebi.ac.uk/cmpo/cmpo.owl


Screens
=======

Section containing all information relative to each screen in the
study including materials used, protocols names and description,
phenotype names and description. For multiple assays this section
should be repeated.


Screen
------

This section should be repeated if a study contains multiple screens.


**Screen Number:** 1

**Screen Technology Type:** gene deletion screen

**Screen Technology Term Source REF:**

**Screen Technology Term Accession Number:**

**Screen Type:** primary

**Screen Target Organism:** Saccharomyces cerevisiae


Study Materials
---------------

**Cell Line or Strain:** BY4739: BY4742

**Cell Line of Strain Term Source REF:**

**Cell Line of Strain Term Accession Number:**



Library
=======

Library section. The library file should be supplied separately and it
should contain the reagents description including, at the absolute
minimum: reagent ID, sequences and position in the layout (= plate +
position in the plate)

**Library File Name:** JCBRad52LibraryFile.txt

**Library Type:** diploid homozygous deletion library

**Library Type Term Source REF:**

**Library Type Term Accession Number:**

**Library Manufacturer:** Open Biosystems now Dharmacon
(http://dharmacon.gelifesciences.com/non-mammalian-cdna-and-orf/yeast-knockout-collection/)

**Library Version:** Winzeler EA, Shoemaker DD, Astromoff A, et
al. 1999. Functional characterization of the S. cerevisiae genome by
gene deletion and parallel analysis. Science 285(5429): 901-906.

**Library Assembly :** Annotation for library was synced to SGD on 1st Nov 2010

**Library Experimental Conditions:** none

Library Experimental Conditions Term Source REF

Library Experimental Conditions Term Accession Number

**Quality Control Description:** general comments about growth of
individual deletion strains


Protocols
---------

**Protocol Name:** growth protocol: library selection protocol: image
aquistion and feature extraction protocol: hit detection protocol

**Protocol Type:** library selection protocol: image aquistion and feature
extraction protocol: hit detection protocol

**Protocol Type Term Source REF:**

**Protocol Type Term Accession Number:**

**Protocol Description:** Individual deletions of nonessential genes
made in the BY4742 and BY4739 MAT_ strains were obtained from the
Saccharomyces Gene Deletion Project [64]. The conditional chromosome
strains used to create the hybrid LOH strains and the method of
inducing LOH in these strains have been described [12]. Strain BY4742
was used as the wild-type control for the library background. Gene
deletions from the library were backcrossed into the W303 background
to create congenic strains. : "Examination of Rad52-YFP focus levels
by microscopy was performed as previously described [66]. Briefly,
cells were grown overnight in SC-Leu media at 23 �C and exponentially
growing cultures were prepared for microscopy. A single DIC image and
11 YFP images obtained at 0.3-_m intervals along the z-axis were
captured for each frame, and Rad52-YFP foci were counted by inspecting
all focal planes intersecting each cell. For each gene deletion strain
in the screen, 200�400 cells were scored for Rad52-YFP foci.": "n the
focus screen described, 108 mutants were initially identified with
Rad52-YFP foci in greater than 20% of cells examined. Of these 108, 80
gene deletions maintained the focus phenotype following repeat
experiments and were selected for further analysis. After retesting
all uncharacterized ORFs with focus levels between 15%�20% (41), nine
consistently exhibited elevated foci and were added to the set of
deletions. Three hypothetical ORFs were removed from the set after
expression of the wild-type gene failed to complement the focus
phenotype in the gene deletion strain. The remaining 86 gene deletions
were prepared for the additional assays.


Phenotypes
----------

**Phenotype Name:** increased level of spontaneous Rad52-YFP foci

**Phenotype Description:** A gene deletion strain showing a consistently
increased level of RAd52-YFP foci compared to wild type strain BY4742.

**Phenotype Score Type:** manual


Raw Data Files
--------------

**Raw Image Data Type:** image

**Raw Image Data Format:** OpenLab LIFF

**Raw Image Organization:** The primary screen is organised into 52 x
96-well plates.  Images were taken from 6 to 10 fields per well.  Some
images are missing, and in particular there are no images for 6 of the
plates.  These plates are not included in the library or processed
data files.



Feature Level Data Files
========================

Give individual file details unless there is one file per well.

**Feature Level Data File Name:**

**Feature Level Data File Description:**

**Feature Level Data File Format:**

**Feature Level Data Column Name:**

**Feature Level Data Column Description:**


Processed Data Files
====================

**Processed Data File Name:** JCBRad52ProcessedData.txt

**Processed Data File Format:** tab delimited text

**Processed Data File Description:** This file contains information about
the percentage of cells with Rad52-YFP foci found in each deletion
strain and which were identified to have elevated levels of foci
compared to wild type strain BY4742.

**Processed Data Genome Build For Target Genes:**

**Processed Data Column Name:** Plate: Well: Gene Identifier: Gene Symbol:
Number Of Cells: Number of Cells with Foci: Percentage Cells With
Foci: Author Hit: Phenotype

**Processed Data Column Type:** Plate : Well: Entity Identifier: Gene
Symbol: Data: Data: Data: Data: Phenotype

**Processed Data Column Description:** The plate the result comes from:
The well the result comes from: The ORF identifier (from the
Saccharomyces Genome Database (information linked via Ensembl)) for
the deleted gene.: The symbol for the deleted gene.: The number of
cells examined.: The number of cells which contain one or more
Rad52-YFP foci.: The percentage of examined cells which contain
Rad52-YFP foci.: Whether this deletion screen is identified as a gene
of interest for further analysis. : Phenotype observed among cells
with this gene deletion
