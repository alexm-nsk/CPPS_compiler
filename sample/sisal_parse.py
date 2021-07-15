#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
#  parse.py
#`
#  Copyright 2021 alexm
#
#  This program is free software; you can redistribute it and/or modify
#  it under the terms of the GNU General Public License as published by
#  the Free Software Foundation; either version 2 of the License, or
#  (at your option) any later version.
#
#  This program is distributed in the hope that it will be useful,
#  but WITHOUT ANY WARRANTY; without even the implied warranty of
#  MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#  GNU General Public License for more details.
#
#  You should have received a copy of the GNU General Public License
#  along with this program; if not, write to the Free Software
#  Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston,
#  MA 02110-1301, USA.
#
#

from parser.parse_file import parse_file

import re
import os, json
from ast_.node import *

def parse(input_text):
    return parse_file(input_text)


def main(args):

#    print ("_"*50, "\n")

    if ( len( args ) < 2 ):
        print ( "usage: python sisal_parse.py source_code.sis" )
    else:

        input_file_name = args[1]
        try:
            file_contents = open(input_file_name, "r").read()
        except:
            # TODO make sure to isolate I/O error from malformed commandline parameters
            print ("error reading %s" % input_file_name)
            return 1

        try:
            output = parse(file_contents)

            #print (output)
            if "--graph" in args:
                from exporters.graphml import make_document
                os.system ("echo '%s'| pygmentize -l xml" % make_document(output[0].emit_graphml(None)))
            else:
                
                formatted = json.dumps(dict(function = [o.emit_json(None) for o in output]))
                #print (formatted)
                os.system ("echo '%s' | jq" % formatted)


        except Exception as e:
            # ~ print (str(e))
            raise e

    return 0


if __name__ == '__main__':

    import sys
    sys.exit(main(sys.argv))
