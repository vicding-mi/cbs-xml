# encoding: utf-8
import lxml.objectify as objectify
import lxml.etree
import lxml.etree as et
import os
import csv
import xmltodict
import logging

logging.basicConfig(level=logging.INFO)

default_namespaces = {'xs': 'http://www.w3.org/2001/XMLSchema'}
xml_file = '/Users/vic/Documents/DANS/projects/ODISSEI/cbs-data/DSC.4.0_short.xsd'
csv_file = '/Users/vic/Documents/DANS/projects/ODISSEI/cbs-data/cbs_mapping.csv'
all_types = None
simple_types = None
complex_types = None
debug = True


def get_all_tree_root_elements(tree, namespaces=default_namespaces):
    root = tree.getroot()
    elements = list()

    for i in root.xpath("./xs:element", namespaces=namespaces):
        if i.get('name', None):
            logging.debug(i.get('name'))
            elements.append(i)
    return elements


def get_branch_elements_from_complex_type(current_element, namespaces=default_namespaces):
    current_type_name = current_element.get('type', None)
    elements = list()
    if current_type_name:
        current_type = get_type_by_name(current_type_name)
        logging.debug(f'current type is {current_type.get("name")}')
        for i in current_type.xpath(f'./xs:sequence/xs:element', namespaces=namespaces):
            if i.get('name', None):
                elements.append(i)
        logging.debug(f'found {len(elements)} elements under current type')
        return elements
    else:
        for i in current_element.xpath(f'./xs:complexType/xs:sequence/xs:element', namespaces=namespaces):
            if i.get('name', None):
                elements.append(i)
        logging.debug(f'found {len(elements)} elements under current element')
        return elements


def get_tree_root_types(tree, namespaces=default_namespaces, node_type='all'):
    root = tree.getroot()
    types_dict = dict()

    if node_type == 'all':
        simple_types = root.xpath('./xs:simpleType', namespaces=namespaces)
        complex_types = root.xpath('./xs:complexType', namespaces=namespaces)
        both_types = simple_types + complex_types if simple_types or complex_types else None
        if not both_types:
            return dict()

        for i in both_types:
            if i.get('name', None):
                types_dict[i.get('name')] = i
    elif node_type == 'simpleType':
        for i in root.xpath('./xs:simpleType', namespaces=namespaces):
            if i.get('name', None):
                types_dict[i.get('name')] = i
    elif node_type == 'complexType':
        for i in root.xpath('./xs:complexType', namespaces=namespaces):
            if i.get('name', None):
                types_dict[i.get('name')] = i
    else:
        logging.info(f'node_type {node_type} not supported')
        raise TypeError

    return types_dict


def get_type_by_name(name=None):
    global all_types
    if name and name in all_types.keys():
        logging.debug(f'{name} is in the keys')
        return all_types[name]
    return None


def is_simple_type(current_type):
    global simple_types, all_types
    if not current_type:
        # no type, regarded as complex type
        return False
    if current_type not in all_types:
        # external type, regarded as simple type
        return True
    return True if current_type in simple_types else False


def get_structured_element(current_element):
    global all_types, simple_types, complex_types
    result = list()
    # current_type = get_type_by_name(name=current_element.get('name', None))
    current_type = current_element.get('type', None)
    if is_simple_type(current_type):
        result.append({current_element.get('name', None): []})
        return result
    else:
        logging.debug(f'current element {current_element.get("name")} is of complex type')
        next_elements = get_branch_elements_from_complex_type(current_element)
        # logging.debug(next_elements)
        if next_elements:
            for i in next_elements:
                # when in the complex type definition, its sub element uses its own type as the sub element type
                # This creates a loop
                # IS THIS ALLOWED IN XSD?
                # TODO: check this (see TreeListItemType) with CBS, for now, treat it as simple type
                counter = 0
                if i.get('type', None) == current_type:
                    counter += 1
                    logging.debug(counter)
                    result.append({current_element.get('name', None): []})
                    return result
                result.append({current_element.get('name', None): get_structured_element(i)})
        else:
            result.append({current_element.get('name', None): []})
            return result
    logging.debug(f'current type is: {current_type}')
    return result

flat_paths_list = list()
flat_path = list()
def get_flat_element(structured_elements):
    global aa, flat_paths_list
    if type(structured_elements) is list:
        logging.debug(f'type is {type(structured_elements)}')
        if len(structured_elements) > 0:
            for next_item in structured_elements:
                get_flat_element(next_item)
        else:
            flat_paths_list.append(flat_path.copy())
            flat_path.pop()
    else:
        logging.debug(f'type is {type(structured_elements)}')
        for next_item in structured_elements.items():
            k, v = next_item
            flat_path.append(k)
            get_flat_element(v)
            if len(v) > 0:
                flat_path.pop()


def __main__():
    global all_types, simple_types, complex_types, aa
    with open(xml_file, 'rb') as f:
        if os.path.join(f.name).endswith('xsd'):
            tree = et.parse(f)
            all_types = get_tree_root_types(tree, node_type='all')
            simple_types = get_tree_root_types(tree, node_type='simpleType')
            complex_types = get_tree_root_types(tree, node_type='complexType')

            all_root_elements = get_all_tree_root_elements(tree)

            # get elements into structure
            structured_elements = list()
            for current_element in all_root_elements:
                logging.debug(f'current element is: {current_element.get("name")}')
                structured_element = get_structured_element(current_element)
                structured_elements.append(structured_element)

            # get elements in flat lines
            '''
            NOTE: It seems that the actual data file is using only 1 root element out of 17
            We are only storing those particular paths to reduce the mapping work and make the file more redable
            '''
            logging.debug(f'original structured elements \n {structured_elements[1]}')
            get_flat_element(structured_elements[1])
            logging.debug('flat_paths_list is')

            # writing paths to CSV
            with open(csv_file, 'w') as csvf:
                csv_writer = csv.writer(csvf)
                for i in flat_paths_list:
                    row = '/'.join(i)
                    csvf.writelines(f'"{row}", \n')
                    # csv_writer.writerow(row)


if __name__ == '__main__':
    __main__()
