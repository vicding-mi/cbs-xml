# CBS data

This repository contains scripts to process CBS metadata for ingesting into Dataverse.
Please use `Python 3.7` for best compatibility. Newer versions should work, but not tested. 

### Sample configuration
```python
dataverse_name = 'dataverse_or_subdataverse_name'
cbs_data_path = '/fullpath/to/metadata'
cbs_mapping_file = '/fullpath/to/mapping.csv'
```
### There are 3 working files
 * 01 cbs schema flat `python 01_cbs_schema_flat.py`
 * 02 import dataset `python 02_import_dataset.py`
 * 03 publish ds `python 03_publish_ds.py`

### Work flow listed below: 
 * 01/ Flatten its XSD in order to get a mapping file, the mapping file will be CSV. The generated file contains full path for each field. The mapping information could be filled by data manager.
   * the first column is the full XPATH of each xsd element 
   * the second column is the block name
   * the third column is the parent field, if available, otherwise should be ""
   * the forth column is the multiple value allowed indicator 0 or 1 of parent field
   * the fifth column is the field name
   * the sixth column is the multiple value allowed indicator of field
   * the seventh column is the type of the field ('primitive', 'controlledVocabulary')
 * 02/ Convert XSD file, according to the mapping, to JSON
   * No JSON file will be generated on the disk, only json structure on the fly
 * 02/ Import JSON into Dataverse by using old API or the new semantic API
   * This step is combined with the previous step
 * 03/ Publish after checking
