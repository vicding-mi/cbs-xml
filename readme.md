# CBS data

This repository contains scripts to process CBS metadata for ingesting into Dataverse.
Please use `Python 3.7` for best compatibility. Newer versions should work, but not tested. 

### Sample configuration file
Copy/rename `dvconfig-sample.py` to `dvconfig.py`. Please see the content below and modify according to your needs. 
```python
base_url = 'https://portal.odissei.nl'
api_token = 'xxx-xxxxxxxxx-xxxx-xxxxxxx'

dataverse_name = 'dataverse_or_subdataverse_name'
cbs_data_path = '/fullpath/to/metadata'
cbs_mapping_file = '/fullpath/to/mapping.csv'
```
### There are 3 working files
 * 01 cbs schema flat `python 01_cbs_schema_flat.py`
 * 02 import dataset `python 02_import_dataset.py`
 * 03 publish ds `python 03_publish_ds.py`

### Work flow listed below: 
 * Step 1) Flatten its XSD in order to get a mapping file, the mapping file will be CSV. The generated file contains full path for each field. The mapping information could be filled by data manager.
   * the first column is the full XPATH of each xsd element 
   * the second column is the block name
   * the third column is the parent field, if available, otherwise should be ""
   * the forth column is the multiple value allowed indicator 0 or 1 of parent field
   * the fifth column is the field name
   * the sixth column is the multiple value allowed indicator of field
   * the seventh column is the type of the field ('primitive', 'controlledVocabulary')
 * Step 2) Convert XSD file, according to the mapping, to JSON
   * No JSON file will be generated on the disk, only json structure on the fly
 * Step 3) Import JSON into Dataverse 
 ```shell
python 02_import_dataset.py 
```
 * Step 4) Publish after checking
```shell
python 03_publish_ds.py
```
###NOTES
* Step 1 and 2 should be run only once, the generated then curated mapping CSV shall be used multiple times.
* Copy/rename dvconfig-sample.py to dvconfig.py, and adjust the parameters accordingly

