#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
#  json_parser.py
#
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

from compiler.nodes import *

def parse_json(json_data):

    for function in json_data["functions"]:
        parse_node (function)
        # ~ print (function["functionName"])
        # ~ for edge in function["edges"]:
            # ~ print (f"{edge[0]['nodeId']} to {edge[1]['nodeId']}" )
            # ~ Edge.edges.append(f"{edge[0]['nodeId']} to {edge[1]['nodeId']}")
            
    for k, n in Node.nodes.items():
        print (n.name, n, "\n")
        
    return []


def main(args):
    pass


if __name__ == '__main__':

    import sys
    sys.exit(main(sys.argv))
