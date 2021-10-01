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
from compiler.llvm import *


def parse_json(json_data):
    init_llvm()
    functions = [parse_node (function) for function in json_data["functions"]]
    #print (Edge.edges_to["node3"])
    #print (Node.is_parent("node2", "node1"))
    print ( create_module(functions, "module") )
    #print (functions[0].emit_llvm())
    #print (get_result_nodes("node1"))
    return []


def main(args):
    pass


if __name__ == '__main__':

    import sys
    sys.exit(main(sys.argv))
