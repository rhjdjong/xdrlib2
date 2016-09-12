'''
Created on 12 sep. 2016

@author: Ruud
'''

from xdrlib2.xdr_base import config_file, config
import grako
from fs.opener import fsopendir

grammar = config['files']['grammar']
parser = config['files']['parser']
    
grammar_path = '/grammar/' + grammar
parser_path = '/parser/' + parser

fs = fsopendir('mount://' + config_file)

def main():
    if ( not fs.exists(parser_path) or
         fs.getinfo(parser_path)['modified_time'] < fs.getinfo(grammar_path)['modified_time']):
        
        print("Generating parser for grammar '{}'".format(grammar))
        with fs.open(grammar_path) as g_f:
            with fs.open(parser_path, 'w') as p_f:
                p_f.write(grako.gencode(grammar=g_f.read()))
        print("Parser generation completed succesfully")
    else:
        print("Parser is up to date")

if __name__ == '__main__':
    main()