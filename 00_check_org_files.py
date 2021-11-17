import os
import re
from typing import Optional, List

import dvconfig

input_path = dvconfig.cbs_data_path


def all_files(input_path: str = input_path, extension:str = 'dsc') -> Optional[List[str]]:
    """
    Generator for all files with specific extension in given directory

    :param input_path: The folder contains the files as str
    :param extension: Default to 'dsc', could be any extension str
    :return: list of filenames
    """
    for root, dirs, files in os.walk(input_path):
        for name in files:
            full_input_file = os.path.join(root, name)
            if full_input_file.endswith(extension):
                yield full_input_file


def pattern_exists_in_file(file: str, pattern: re.Pattern) -> Optional[List[str]]:
    """
    Matches pattern in a given file, return file list if pattern found, otherwise return None

    :param file:
    :param pattern:
    :return:
    """
    with open(file, 'r', encoding='utf-8') as f:
        file_content = f.read()
        result = pattern.findall(file_content)
        if len(result) > 0:
            return result


def pattern_in_all_files(pattern: re.Pattern) -> List[List[str]]:
    """
    Look for mails in the files
    :return:
    """
    results = []
    for file in all_files():
        pattern_results = pattern_exists_in_file(file, pattern)
        if pattern_results:
            pattern_results.append(file)
            results.append(pattern_results)
    return results


def main():
    # checking for emails
    email_pattern = re.compile(r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}')
    results = pattern_in_all_files(email_pattern)
    for r in results:
        print(r)
    print(f'There are {len(results)} files having emails')

    # checking for links
    links_pattern = re.compile(r'(http|ftp|https):\/\/([\w\-_]+(?:(?:\.[\w\-_]+)+))([\w\-\.,@?^=%&:/~\+#]*[\w\-\@?^=%&/~\+#])?')
    results = pattern_in_all_files(links_pattern)
    counter = 0
    for r in results:
        if len(r) > 4:
            counter += 1
            print(r[3:])
    print(f'There are {counter} files having links')

    # checking for phone numbers
    phone_pattern = re.compile(r'(\d{3})\D*(\d{3})\D*(\d{4})\D*(\d*)$')
    results = pattern_in_all_files(phone_pattern)
    for r in results:
        print(r)
    print(f'There are {len(results)} files having phone numbers')


if __name__ == '__main__':
    print('starting...')
    main()
    print('...done')
