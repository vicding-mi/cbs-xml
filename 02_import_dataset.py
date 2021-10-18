import csv
import os
from os.path import join

import lxml.html
from pyDataverse.exceptions import ApiAuthorizationError
from pyDataverse.api import Api
from requests import post
import json
import dvconfig
import lxml.etree as et
import lxml.objectify as objectify

base_url = dvconfig.base_url
native_api_base_url = f'{base_url}/api'
api_token = dvconfig.api_token
dataverse_id = dvconfig.dataverse_name
input_path = dvconfig.cbs_data_path
cbs_mapping_file = dvconfig.cbs_mapping_file

release = 'no'

ns = {
    'xmlns': 'http://www.cbs.nl/Dsc/4.1'
}
api = Api(base_url, api_token)
print('API status: ' + api.status)


# print(f'curl -u {api_token}: {base_url}/dvn/api/data-deposit/v1.1/swordv2/service-document')


def get_primitive_field(list_elements, typeName, typeClass='primitive', multiple=False):
    result = dict()
    result['typeName'] = typeName
    result['multiple'] = multiple
    result['typeClass'] = typeClass
    print(f'list of elements is {list_elements}')

    if not multiple:
        if isinstance(list_elements[0], str):
            result['value'] = list_elements[0]
        else:
            result['value'] = list_elements[0].text
    else:
        if isinstance(list_elements[0], str):
            result['value'] = [i for i in list_elements]
        else:
            result['value'] = [i.text for i in list_elements]
    if result['value'] is not None:
        return result
    return None


def get_compound_field(pf, subfields, dom, type_class='compound'):
    value_dict = dict()
    static_values = dict()
    result = dict()

    result['typeName'] = pf
    result['multiple'] = get_boolean_value(subfields[0][3])
    result['typeClass'] = type_class
    # get the first xpath from the sub types
    # throws exception when there are multiple fields having xpath
    for row in subfields:
        if row[0].startswith('/'):
            if len(value_dict.keys()) == 0:
                # structure of the value list [value, parent field, pf multiple, this multiple]
                value_dict[row[4]] = [row[0], pf, row[3], row[5]]
            else:
                raise Exception('cannot have more than one subfields which have xpath.')
        else:
            static_values[row[4]] = [row[0], pf, row[3], row[5]]

    if len(value_dict.keys()) == 0:
        # we do not have any xpath, all values are static text
        value_list = list()
        inner_dict = dict()
        for row in subfields:
            inner_dict[row[4]] = get_primitive_field([row[0]], row[4])
        value_list.append(inner_dict)
        if len(value_list) > 0:
            result['value'] = value_list
            return result
    else:
        # we found a xpath, now check if we have multiple xpaths in the string
        value_dict_item = value_dict.popitem()
        k = value_dict_item[0]
        v = value_dict_item[1]
        xpath_lists = v[0].split(';')

        inner_values_list = list()
        for i in xpath_lists:
            # get all the elements from the path
            elements = dom.xpath(i)
            # loop through the elements
            for element in elements:
                # each v should create a compound field
                inner_dict = dict()
                if element is not None and element.text is not None:
                    inner_dict[k] = get_primitive_field([element.text], k, 'primitive', get_boolean_value(v[3]))
                for static_value in static_values.items():
                    k = static_value[0]
                    v = static_value[1]
                    inner_dict[k] = get_primitive_field([v[0]], k, 'primitive', get_boolean_value(v[3]))
                if len(inner_dict.items()) > 0:
                    inner_values_list.append(inner_dict)

        if len(inner_values_list) > 0:
            # TODO
            if result['multiple']:
                result['value'] = inner_values_list
            else:
                result['value'] = inner_values_list[0]
            # if k == 'socialScienceNotesSubject' and len(inner_values_list) > 0:
            #     print(result)
            #     exit()
            return result
    return None


def get_boolean_value(text_value):
    positive_boolean_values = ['yes', 'true', '1', 1]
    return True if text_value.lower() in positive_boolean_values else False


def get_all_rows_for_current_type(current_type, mapping_csv, key=2):
    return [r for r in mapping_csv if r[key] == current_type]


def convert_xml_to_dv_json(dom, mapping_csv):
    processed_fields = list()
    result = {
        'datasetVersion': {
            "termsOfUse": "N/A",
            'license': 'NONE',
            'metadataBlocks': {
                # 'citation': {
                #     # 'displayName': 'Citation Metadata',
                #     'fields': [
                #
                #     ]
                # },
                # 'socialscience': {
                #     # 'displayName': 'Social Sciences',
                #     'fields': [
                #
                #     ]
                # }
            }
        }
    }
    # get metadata blocks from mapping
    blocks = get_column_names(mapping_csv, 1)
    for b in blocks:
        print(f'running block: {b}')
        fields = list()
        result['datasetVersion']['metadataBlocks'][b] = {'fields': []}
        current_simple_fields = get_simple_fields_per_block(b, mapping_csv)
        current_complex_fields = get_complex_fields_per_block(b, mapping_csv)
        print(f'all the simple fields of {b}: {current_simple_fields}')
        print(f'all the complex fields of {b}: {current_complex_fields}')

        # preparing all the complex fields for the current block
        # get all parent fields of current block
        unique_parent_fields_per_block = get_column_names(current_complex_fields, 2)
        print(f'all the unique parent fields {unique_parent_fields_per_block}')
        for pf in unique_parent_fields_per_block:
            subfields = get_all_rows_for_current_type(pf, current_complex_fields)
            print(f'adding complex value {pf}')
            current_complex_field_value = get_compound_field(pf, subfields, dom)
            if current_complex_field_value is not None:
                fields.append(current_complex_field_value)

        # preparing all the simple fields for the current block
        for current_field in current_simple_fields:
            value = current_field[0] if not current_field[0].startswith('/') else dom.xpath(current_field[0])
            # got xml elements using xpath as list
            if type(value) == list:
                # field allows multiple instances,
                # reading all the Element and set multiple to True
                if value is not None and len(value) > 0:
                    print(f'adding simple value: {value} to {current_field[4]}')
                    current_simple_field_value = get_primitive_field(value, current_field[4], current_field[6], get_boolean_value(current_field[5]))
                    if current_simple_field_value is not None:
                        fields.append(current_simple_field_value)
            else:
                # got static string as value
                fields.append(get_primitive_field([value], current_field[4], current_field[6], get_boolean_value(current_field[5])))

        # adding all the fields to dict and ready to be dumped to json
        result['datasetVersion']['metadataBlocks'][b]['fields'] = fields
    return json.dumps(result)


def load_mapping_file(mapping_file):
    with open(mapping_file, 'r') as csvfile:
        mapping_csv = csv.reader(csvfile)
        return [r for r in mapping_csv]


def remove_ns_from_xml(dom):
    # Iterate through all XML elements
    for elem in dom.getiterator():
        # Skip comments and processing instructions,
        # because they do not have names
        if not (isinstance(elem, et._Comment) or isinstance(elem, et._ProcessingInstruction)):
            # Remove a namespace URI in the element's name
            elem.tag = et.QName(elem).localname
    # Remove unused namespace declarations
    et.cleanup_namespaces(dom)
    return dom


def get_column_names(mapping_list, index):
    results = [r[index] for r in mapping_list]
    return set(results)


def get_fields_per_block(fname, mapping_list):
    return [r for r in mapping_list if r[1] == fname]


def get_complex_fields_per_block(fname, mapping_list):
    return [r for r in mapping_list if r[1] == fname and r[2] != '']


def get_simple_fields_per_block(fname, mapping_list):
    return [r for r in mapping_list if r[1] == fname and r[2] == '']


def __main__():
    # testing with single json file
    # full_input_file = '/Users/vic/Library/Application Support/JetBrains/PyCharm2021.2/scratches/scratch_5.json'
    # with open(full_input_file, 'r') as jsonfile:
    #     jsonfile = json.load(jsonfile)
    #     resp = api.create_dataset(dataverse_id, json.dumps(jsonfile))
    #     print(resp.status_code)
    #     print(resp.text)
    #     print('okokok')
    # exit()

    counter = 1
    mapping_list = load_mapping_file(cbs_mapping_file)
    print('mapping file loaded')
    for root, dirs, files in os.walk(input_path):
        for name in files:
            full_input_file = join(root, name)
            if full_input_file.endswith('dsc'):
                print(f'{counter} working on {full_input_file}')
                counter += 1
                dom = et.parse(full_input_file)
                # remove namespaces and use etree in order to use absolute path
                dom = remove_ns_from_xml(dom)
                # convert xml file to DV json file
                cbs_json = convert_xml_to_dv_json(dom, mapping_list)
                # print(cbs_json)
                # exit()
                resp = api.create_dataset(dataverse_id, cbs_json)
                print(resp.status_code)
                if not 300 > resp.status_code > 199:
                    print(resp.text)
                    print(cbs_json)
                    raise Exception('error occurred')


if __name__ == '__main__':
    print('starting...')
    __main__()
