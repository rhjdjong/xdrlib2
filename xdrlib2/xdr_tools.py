'''
Created on 8 sep. 2016

@author: Ruud
'''

import os
import logging
import configparser

import grako
from fs.opener import fsopendir

__all__ = [ 'use',

           ]

ini_file = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'etc', 'xdr.ini'))

cp = configparser.ConfigParser()
with open(ini_file) as f:
    cp.read_file(f)
    
grammar = cp['files']['grammar']
parser = cp['files']['parser']
    
grammar_path = '/grammar/' + grammar
parser_path = '/parser/' + parser

fs = fsopendir('mount://' + ini_file)

def use(name, fs=fs):
    # Regenerate parser if it does not exist, or if the grammar is newer
    if ( not fs.exists(parser_path) or
         fs.getinfo(parser_path)['modified_time'] < fs.getinfo(grammar_path)['modified_time']):
        
        logging.info("Generating parser for grammar '{}'".format(grammar))
        try:
            with fs.open(grammar_path) as g_f:
                with fs.open(parser_path, 'w') as p_f:
                    p_f.write(grako.gencode(grammar=g_f.read()))
        except grako.exceptions.GrakoException as e:
            logging.error(e)
            logging.error("Cannot generate parser for grammar '{}'".format(grammar))
            raise
        else:
            logging.info("Parser generation completed succesfully")
         
