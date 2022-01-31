#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
#  cpp.py
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

from compiler.cpp_codegen import *


type_map = {
    "integer" : IntegerType(32)
}


def sisal_to_cpp_type(type_):
    return type_map[str(type_)]


def create_cpp_module(functions, name):
    module = Module(name)

    for f in functions:
        module.add_function (f.emit_cpp())

    return module


def export_function_to_cpp(node, scope):

    # turn function input arguments into c++ arguments
    args = []
    for n, a in enumerate(node.params):
        arg = (a, sisal_to_cpp_type(node.in_ports[n].type))
        args.append(arg)

    ret_type = sisal_to_cpp_type(node.out_ports[0].type)

    this_function = Function(node.function_name, ret_type, args, node.name == "main")

    builder = Builder(this_function.get_entry_block())
    scope = CppScope(this_function.get_arguments(), builder)

    for child_node, edge in node.get_result_nodes()[:1]: # do only one for now
        node.nodes[0].emit_cpp(scope)

    return this_function


def export_literal_to_cpp(node, scope):

    return scope.builder.constant(node.value)


def get_var_from_scope(edge, scope):
    index = edge.from_index
    return scope.vars[index]


def export_binary_to_cpp(node, scope):

    (left, l_edge), (right, r_edge) = node.get_input_nodes()
    operator = node.operator

    if node.is_node_parent(l_edge.from_):
        lho = get_var_from_scope(l_edge, scope)
    else:
        lho = left.emit_cpp(scope)

    if node.is_node_parent(r_edge.from_):
        rho = get_var_from_scope(r_edge, scope)
    else:
        rho = right.emit_cpp(scope)

    return scope.builder.binary(lho, rho, operator)


def export_condition_to_cpp(node, scope):
    (result, edge), = node.get_result_nodes()

    return result.emit_cpp(scope)


def export_if_to_cpp(node, scope):
    cond = node.condition.emit_cpp(scope)
    scope.builder.if_(cond)
    pass
