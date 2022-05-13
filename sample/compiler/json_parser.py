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
# ~ from compiler.llvm import *
# ~ from compiler.cpp import *

# ~ def compile_to_llvm(json_data):
    # ~ init_llvm()
    # ~ functions = [parse_node (function) for function in json_data["functions"]]
    # ~ print ( create_llvm_module(functions, "module") )


def compile_to_cpp(json_data, name = "module"):
    Node.nodes = {}
    Edge.edges = []
    Edge.edges_from = {}
    Edge.edges_to   = {}
    module = Module(name)

    functions = [parse_node (function) for function in json_data["functions"]]

    for f in functions:
        # cpp_function is a function object from C++ code generator
        # it can be converted to a string C++ src. code using the standardized "str" method
        # f.emit_cpp() returns a list because one function can translate to several functions in C++
        # like main produces "main" and "sisal_main"
        cpp_data = f.emit_cpp()

        for cpp_function in cpp_data["functions"]:
            module.add_function (cpp_function)

        for import_ in cpp_data["imports"]:
            module.add_header(import_)

    # ~ module = create_cpp_module(functions, name)

    return module


def main(args):
    pass


if __name__ == '__main__':

    import sys
    sys.exit(main(sys.argv))
