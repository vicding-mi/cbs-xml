import os
import re
from typing import Optional, List

import dvconfig

input_path = dvconfig.cbs_data_path


def all_files(input_path: str = input_path, extension:str = 'dsc') -> Optional[List[str]]:
    """
    Generator for all files with specific extension in given directory

    :param input_path:
    :param extension:
    :return:
    """
    for root, dirs, files in os.walk(input_path):
        for name in files:
            full_input_file = os.path.join(root, name)
            if full_input_file.endswith(extension):
                yield full_input_file


def pattern_exists(file: str, pattern: re.Pattern) -> Optional[List[str]]:
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


def main():
    counter = 0
    # checking for emails
    email_pattern = re.compile(r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}')
    for file in all_files():
        email_results = pattern_exists(file, email_pattern)
        if email_results:
            counter += 1
            print(f'{counter} {email_results} in {file}')


if __name__ == '__main__':
    print('starting...')
    main()
    print('...done')
