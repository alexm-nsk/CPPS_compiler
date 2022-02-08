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

functions = {}

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

    functions[node.function_name] = this_function

    builder = Builder(this_function.get_entry_block())
    scope = CppScope(this_function.get_arguments(), builder)

    for child_node, edge in node.get_result_nodes()[:1]: # do only one for now
        scope.builder.ret( node.nodes[0].emit_cpp(scope) )

    return this_function


def export_literal_to_cpp(node, scope):

    return scope.builder.constant(node.value)


def export_binary_to_cpp(node, scope):

    (left, l_edge), (right, r_edge) = node.get_input_nodes()
    operator = node.operator

    if node.is_node_parent(l_edge.from_):
        lho = scope.vars[l_edge.from_index]
    else:
        lho = left.emit_cpp(scope)

    if node.is_node_parent(r_edge.from_):
        rho = scope.vars[r_edge.from_index]
    else:
        rho = right.emit_cpp(scope)

    return scope.builder.binary(lho, rho, operator)


def export_condition_to_cpp(node, scope):
    (result, edge), = node.get_result_nodes()

    return result.emit_cpp(scope)


def export_branch_to_cpp(node, scope):
    results = node.get_result_nodes()
    if results != []:
        (result, edge), = node.get_result_nodes()

        return result.emit_cpp(scope)
    else:
        edges = node.get_input_edges()

        for edge in edges:
            return scope.vars[edge.from_index]


def export_functioncall_to_cpp(node, scope):
    input_nodes = node.get_input_nodes()
    num_args = len(input_nodes)
    args = [None for a in range(num_args)]

    for (arg_node, edge) in input_nodes:

        index = edge.to_index

        if arg_node.is_node_parent(edge.from_):
            args[index] = scope.vars[edge.from_index]
        else:
            args[index] = arg_node.emit_cpp(scope)

    result = scope.builder.call(functions[node.callee], args)

    return result


def export_if_to_cpp(node, scope):
    cond = node.condition.emit_cpp(scope)

    get_branch = lambda name: list(filter(lambda x: x.name == name, node.branches))[0]

    if_ = scope.builder.if_(cond)
    # TODO get type from outport:
    result = scope.builder.define(IntegerType(32), name = "if_result")

    then = if_.get_then_builder()
    then_scope = CppScope(scope.vars, then)
    then_result = get_branch("Then").emit_cpp(then_scope)
    then_scope.builder.assignment(result, then_result)

    else_ = if_.get_else_builder()
    else_scope = CppScope(scope.vars, else_)
    else_result = get_branch("Else").emit_cpp(else_scope)
    else_scope.builder.assignment(result, else_result)

    return result


def export_precondition_to_cpp(node, scope):
    # the node that puts out the condition value:
    result_node, result_edge = node.get_result_nodes() [0]
    # ~ print( node.params )
    result_node.emit_cpp(scope)


#   int result = 0

#   while (1)
#   {
#       bool cond = i <= N;
#       if (! cond ) break;
#       i = i + 1;
#   }

#   result = i;


def export_oldvalue_to_cpp(node, scope):
    edge = node.get_input_edges()[0]
        
    return scope.vars[edge.from_index]


def export_body_to_cpp(node, scope):
    # calculate values on outports
    # and add assignment to corresponding (to each port) variables
    
    # else_scope.
    for result_node, result_edge in node.get_result_nodes():
        index = result_edge.to_index
        value = result_node.emit_cpp(scope)
        scope.builder.assignment(scope.vars[index], value)


def export_reduction_to_cpp(node, scope):
    pass


def export_returns_to_cpp(node, scope):
    
    pass


def export_loopexpression_to_cpp(node, scope):
    
    # TODO get type from outport:
    result = scope.builder.define(IntegerType(32), name = "while_result")
    # initialize variables from init-node and put them in new scope (at the beginning of the list)
    # the variables we introduce in this loop:
    
    new_vars = []

    # put newly defined variables into new vars (we will add them to scops)
    for index, port in enumerate(node.init.out_ports):
        type_ = port.type.emit_cpp()
        # get variable's name from body's parameters:
        var_name = list(  node.body.params.items()  )[index][0]
        # initialize it:
        new_variable = scope.builder.define(type_, value = 0, name = var_name)
        new_vars.append(new_variable)

    # make a new scope based on the provided one
    for v in reversed(new_vars):
        while_scope_vars = scope.get_vars_copy()
        while_scope_vars.insert(0, v)

    while_ = scope.builder.while_()

    # process pre-condition:
    pre_cond_builder = while_.get_pre_cond_builder()
    pre_cond_scope = CppScope(while_scope_vars, pre_cond_builder)
    node.pre_condition.emit_cpp(pre_cond_scope)

    # process the body:
    body_builder = while_.get_body_builder()
    body_scope = CppScope(while_scope_vars, body_builder)
    node.body.emit_cpp(body_scope)
    
    scope.builder.assignment(result, while_scope_vars[0])
    return result


# ~ //module
# ~ #include <stdio.h>

# ~ int main(int N)
# ~ {
    # ~ // entry:
    # ~ int while_result;
    # ~ int i = 0;
    # ~ while( i <= N )
    # ~ {
        # ~ int i = i + 1;
        # ~         result = i; - if "value" , result += id3; if "sum" initialize result with 0 if summing
    # ~ }
    # ~ while_result = i;
    # ~ return while_result;
# ~ }
