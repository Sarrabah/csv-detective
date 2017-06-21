"""
Ce script analyse les premières lignes d'un CSV pour essayer de déterminer le
contenu possible des champs
"""

import sys

import pandas as pd
import os
import itertools
from pkg_resources import resource_string


from csv_detective import detect_fields

from .detection import (detect_ints_as_floats,
                       detect_separator,
                       detect_encoding,
                       detect_headers,
                       detect_heading_columns,
                       detect_trailing_columns,
                       )

#############################################################################
############### ROUTINE DE TEST CI DESSOUS ##################################


def test_col(serie, test_func, proportion = 0.9, skipna = True, num_rows = 50):
    ''' Tests values of the serie using test_func.
         - skipna : if True indicates that NaNs are not counted as False
         - proportion :  indicates the proportion of values that have to pass the test
    for the serie to be detected as a certain type
    '''
    serie = serie[serie.notnull()]
    ser_len = len(serie)
    if ser_len == 0:
        return False
    if proportion == 1: # Then try first 1 value, then 5, then all
        for _range in [range(0,min(1, ser_len)), range(min(1, ser_len),min(5, ser_len)), range(min(5, ser_len),min(num_rows, ser_len))]: # Pour ne pas faire d'opérations inutiles, on commence par 1, puis 5 puis num_rows valeurs
            if all(serie.iloc[_range].apply(test_func)):
                pass
            else:
                return False
        return True
    else:
        return serie.apply(test_func).sum() > proportion * len(serie)


# def all_tests_recursive(path):
#     '''Returns all the tests that are in path as paths'''
#     in_path = os.listdir(path)
#     if len(in_path) == 0:
#         raise('Path must point to folder')
#     elif all([os.path.isfile(os.path.join(path, x)) for x in in_path]):
#         return [path]
#     else:
#         all_folders = [x for x in in_path if os.path.isdir(os.path.join(path, x))]
#         all_folder_paths = [os.path.join(path, folder) for folder in all_folders]
#         return [os.path.join(x) for x in itertools.chain.from_iterable([all_tests_recursive(path) for path in all_folder_paths])]

# def return_all_tests(user_input_tests):
#     '''Returns a list of python functions that are the tests to be passed
#     user_input_tests can be:
#         - None : All tests available will be conducted
#         - string ('FR.geo') : Will get all tests inside FR.geo directory
#         - list of strings (['FR.geo', 'temp', '-FR.geo.code_departement']) : the minus sign will cut off a branch
#     '''
#     from setuptools import find_packages
#     base_path = 'detect_fields'#os.path.join(os.path.dirname(os.path.realpath(__file__)), 'detect_fields')

#     if isinstance(user_input_tests, str):
#         assert user_input_tests[0] != '-'
#         if user_input_tests == 'ALL':
#             paths_to_do = ['detect_fields']
#         else:
#             paths_to_do = [os.path.join(base_path, *user_input_tests.split('.'))]
#         paths_to_not_do = []
#     elif isinstance(user_input_tests, list):
#         tests_to_do = [x for x in user_input_tests if x[0] != '-']
#         tests_to_not_do = [x for x in user_input_tests if x[0] == '-']
#         if 'ALL' in tests_to_do:
#             paths_to_do = [base_path] + [os.path.join(base_path, *x.split('.')) \
#                                                 for x in tests_to_do if x != 'ALL']
#         else:
#             paths_to_do = [os.path.join(base_path, *x.split('.')) for x in tests_to_do]
#         paths_to_not_do = [os.path.join(base_path, *x[1:].split('.')) for x in tests_to_not_do]

#     all_fields_to_do = ['.'.join(y.split(os.sep)) for y in itertools.chain.from_iterable([all_tests_recursive(x) for x in paths_to_do])]
#     all_fields_to_not_do = ['.'.join(y.split(os.sep)) for y in itertools.chain.from_iterable([all_tests_recursive(x) for x in paths_to_not_do])]
#     all_fields = [x for x in all_fields_to_do if x not in all_fields_to_not_do]

#     print all_fields

#     # NB on `eval` : I don't see a real risk here since field is generated by os.path.join. Am I wrong ?
#     all_tests = [eval(field) for field in all_fields]
#     return all_tests

def return_all_tests(user_input_tests):
    all_packages = resource_string(__name__, 'all_packages.txt')
    all_packages = all_packages.decode().split('\n')
    all_packages.remove('')
    all_packages.remove('csv_detective')
    all_packages = [x.replace('csv_detective.', '') for x in all_packages]

    if isinstance(user_input_tests, str):
        assert user_input_tests[0] != '-'
        if user_input_tests == 'ALL':
            tests_to_do = ['detect_fields']
        else:
            tests_to_do = ['detect_fields' + '.' + user_input_tests]
        tests_to_not_do = []
    elif isinstance(user_input_tests, list):
        if 'ALL' in user_input_tests:
            tests_to_do = ['detect_fields']
        else:
            tests_to_do = ['detect_fields' + '.' + x for x in user_input_tests if x[0] != '-']
        tests_to_not_do = ['detect_fields' + '.' + x[1:] for x in user_input_tests if x[0] == '-']

    all_fields = [x for x in all_packages if any([y == x[:len(y)] for y in tests_to_do]) and all([y != x[:len(y)] for y in tests_to_not_do])]
    all_tests = [eval(field) for field in all_fields]
    all_tests = [test for test in all_tests if '_is' in dir(test)] # TODO : Fix this shit
    return all_tests


def routine(file_path, num_rows=50, user_input_tests='ALL'):
    '''Returns a dict with information about the csv table and possible
    column contents
    '''
    print('This is tests_to_do', user_input_tests)

    l1_file = open(file_path, 'r', encoding='latin-1')
    b_file = open(file_path, 'rb')

    sep = detect_separator(l1_file)
    header_row_idx, header = detect_headers(l1_file, sep)
    if header is None:
        return_dict = {'error': True}
        return return_dict
    elif isinstance(header, list):
        if any([x is None for x in header]):
            return_dict = {'error': True}
            return return_dict
    heading_columns = detect_heading_columns(l1_file, sep)
    trailing_columns = detect_trailing_columns(l1_file, sep, heading_columns)
    # print headers_row, heading_columns, trailing_columns
    chardet_res, table = detect_encoding(b_file, sep, header_row_idx, num_rows)
    if chardet_res['encoding'] is None:
        return_dict = {'error': True}
        return return_dict

    # Detects columns that are ints but written as floats
    res_ints_as_floats = list(detect_ints_as_floats(table))

    # Creating return dictionnary
    return_dict = dict()
    return_dict['encoding'] = chardet_res
    return_dict['separator'] = sep
    return_dict['header_row_idx'] = header_row_idx
    return_dict['header'] = header

    return_dict['heading_columns'] = heading_columns
    return_dict['trailing_columns'] = trailing_columns
    return_dict['ints_as_floats'] = res_ints_as_floats

    all_tests = return_all_tests(user_input_tests)


    # Initialising dict for tests
    test_funcs = dict()
    for test in all_tests:
        name = test.__name__.split('.')[-1]

        test_funcs[name] = {'func' : test._is,
                            'prop' : test.PROPORTION
                            }

    return_table = pd.DataFrame(columns = table.columns)
    for key, value in test_funcs.items():
        return_table.loc[key] = table.apply(lambda serie: test_col(serie, value['func'], value['prop']))

    # Filling the columns attributes of return dictionnary
    return_dict_cols = dict()
    for col in return_table.columns:
        possible_values = list(return_table[return_table[col]].index)
        if possible_values != []:
            print( '  >>  La colonne', col, 'est peut-être :',)
            print(possible_values)
            return_dict_cols[col] = possible_values
    return_dict['columns'] = return_dict_cols

    return return_dict



if __name__ == '__main__':

    import os
    import json

    file_path = os.path.join('..', 'tests', 'code_postaux_v201410.csv')

    list_tests = ['FR.geo', '-FR.geo.code_departement']

    # Open your file and run csv_detective
    with open(file_path, 'r') as file:
        inspection_results = routine(file, user_input_tests = list_tests)

    # Write your file as json
    with open(file_path.replace('.csv', '.json'), 'wb') as fp:
        json.dump(inspection_results, fp, indent=4, separators=(',', ': '), encoding="utf-8")
