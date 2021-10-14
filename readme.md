# CBS data

This repository contains scripts to process CBS metadata for ingesting into Dataverse.

CBS metadata is of DSC type, which is XML with XSD as its schema. We have to 
 * Flatten its XSD in order to get a mapping file, the mapping file will be CSV, the first column is the full XPATH of each xsd element and the second column will be the corresponding field name in Dataverse. This file can be easily created by the script and then filled in by Data managers. 
 * Convert XSD file, according to the mapping, to JSON or JSON-LD
 * Import JSON or JSON-LD into Dataverse by using old API or the new semantic API

