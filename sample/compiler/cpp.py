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


def resolve(edge, scope):
    from_node = edge.get_from_node()
    to_node   = edge.get_to_node()

    if to_node.is_node_parent(edge.from_) or from_node == to_node:
        return scope.vars[edge.from_index]
    else:
        return from_node.emit_cpp(scope)


def sisal_to_cpp_type(type_):
    return type_map[str(type_)]


def create_cpp_module(functions, name):
    module = Module(name)

    for f in functions:
        # cpp_function is a function object from C++ code generator
        # it can be converted to a string C++ src. code using the standardized "str" method
        for cpp_function in f.emit_cpp():
            module.add_function (cpp_function)

    return module


def make_cpp_main_function():
    pass


def export_function_to_cpp(node, scope):

    # turn function input arguments into c++ arguments
    args = []
    for n, a in enumerate(node.params):
        arg = (a, node.in_ports[n].type.emit_cpp())
        args.append(arg)

    ret_type = node.out_ports[0].type.emit_cpp()

    is_main = (node.function_name == "main")

    # rename "main"-function to "sisal_main" and create a C++ - main:
    if is_main:
        node.function_name = "sisal_main"

    this_function = Function(node.function_name, ret_type, args)#, main = is_main)
    functions[node.function_name] = this_function

    # define code builder object for C++-main here so we can use it in the return value
    # whether or not this is main (see return in this function)
    cpp_main = None

    if is_main:
        # args is like [('N', type), ('M', other_type)...]
        # TODO put json loader here
        cpp_main = Function("main", None, [], main = True)
        main_builder = Builder(cpp_main.get_entry_block())
                                                    # why does this work?..
        sisal_main_result = main_builder.call(this_function, [], name = "sisal_main_results")
        code = sisal_main_result.type.print_code(sisal_main_result)
        main_builder.cpp_code( code )
        functions["main"] = cpp_main

    builder = Builder(this_function.get_entry_block())
    scope = CppScope(this_function.get_arguments(), builder)

    for edge in node.get_input_edges()[:1]: # do only one for now
        scope.builder.ret( resolve(edge, scope) )

    return dict ( functions = [this_function] + ([cpp_main] if cpp_main else []),
                  imports = [])


names_to_header = {
    "cos": "math.h",
    "sin": "math.h"
}


def export_functionimport_to_cpp(node, scope):

    # turn function input arguments into c++ arguments
    args = []
    for n, a in enumerate(node.params):
        arg = (a, node.in_ports[n].type.emit_cpp())
        args.append(arg)

    ret_type = node.out_ports[0].type.emit_cpp()

    is_main = (node.function_name == "main")

    # rename "main"-function to "sisal_main" and create a C++ - main:
    if is_main:
        node.function_name = "sisal_main"

    this_function = Function(node.function_name, ret_type, args)#, main = is_main)
    functions[node.function_name] = this_function

    # define code builder object for C++-main here so we can use it in the return value
    # whether or not this is main (see return in this function)
    cpp_main = None

    if is_main:
        # args is like [('N', type), ('M', other_type)...]
        # TODO put json loader here
        cpp_main = Function("main", None, [], main = is_main)
        main_builder = Builder(cpp_main.get_entry_block())
        sisal_main_result = main_builder.call(this_function, [main_builder.constant(10)], name = "sisal_main_results")
        code = sisal_main_result.type.print_code(sisal_main_result)
        main_builder.cpp_code( code )
        functions["main"] = cpp_main

    builder = Builder(this_function.get_entry_block())
    scope = CppScope(this_function.get_arguments(), builder)

    return dict( functions = [], imports = [names_to_header[node.function_name]] )


def export_literal_to_cpp(node, scope):
    # ~ print (node.out_ports[0].type)
    # ~ print (type(node.out_ports[0].type))
    # ~ if (type(node.out_ports[0].type) == IntegerType):
        # ~ print("got integer")
    literal_type = node.out_ports[0].type.emit_cpp()
    return scope.builder.constant(node.value, literal_type)


def export_binary_to_cpp(node, scope):

    (left, l_edge), (right, r_edge) = node.get_input_nodes()
    operator = node.operator

    lho = resolve(l_edge, scope)
    rho = resolve(r_edge, scope)

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
        args[index] = resolve(edge, scope)

    # Here we replace callee with sisal main if we call main (because main is now a C++ "int main(etc...")

    result = scope.builder.call(functions["sisal_main" if node.callee == "main" else node.callee], args)
    return result


def export_if_to_cpp(node, scope):
    cond = node.condition.emit_cpp(scope)

    get_branch = lambda name: list(filter(lambda x: x.name == name, node.branches))[0]

    if_ = scope.builder.if_(cond)

    type_ = node.out_ports[0].type.emit_cpp()

    result = scope.builder.define(type_, name = "if_result")

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
    result_node.emit_cpp(scope)


def export_oldvalue_to_cpp(node, scope):
    edge = node.get_input_edges()[0]
    return scope.vars[edge.from_index]


def export_body_to_cpp(node, scope):
    # calculate values on outports
    # and add assignment to corresponding (to each port) variables

    for result_node, result_edge in node.get_result_nodes():
        index = result_edge.to_index
        value = result_node.emit_cpp(scope)
        scope.builder.assignment(scope.vars[index], value)


def export_reduction_to_cpp(node, scope):

    index = node.get_input_edges()[0].from_index

    value = resolve(node.get_input_edges()[1],scope)

    if node.operator == "value":
        return scope.builder.assignment(scope.vars[-1], value)

    elif node.operator == "sum":
        return scope.builder.assignment(scope.vars[-1],
                scope.builder.binary(  scope.vars[-1] , value , "+")
            )


def export_returns_to_cpp(node, scope):

    for result_node, result_edge in node.get_result_nodes():
        return result_node.emit_cpp(scope)


def export_loopexpression_to_cpp(node, scope):
    # TODO make use of "results" in the nodes
    result = scope.builder.define(node.out_ports[0].type.emit_cpp(), name = "while_result",  value = 0)
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

    new_vars = new_vars + scope.vars

    # make a new scope based on the provided one
    while_scope_vars = new_vars + scope.get_vars_copy() + [result]
    while_ = scope.builder.while_()

    # process pre-condition:
    pre_cond_builder = while_.get_pre_cond_builder()
    pre_cond_scope = CppScope(while_scope_vars, pre_cond_builder)
    node.pre_condition.emit_cpp(pre_cond_scope)

    # process the body:
    body_builder = while_.get_body_builder()
    body_scope = CppScope(while_scope_vars, body_builder)
    node.body.emit_cpp(body_scope)

    # process the reduction:
    reduction_builder = while_.get_reduction_builder()
    # TODO double the variables here
    reduction_scope_vars = []
    for v in new_vars:
        for a in range(2):
            reduction_scope_vars.append(v)

    reduction_scope = CppScope(reduction_scope_vars + scope.vars + [result], reduction_builder)
    node.reduction.emit_cpp(reduction_scope)

    return result


def export_arrayaccess_to_cpp(node, scope):
    (array_src, array_edge), (index_src, index_edge) = node.get_input_nodes()
    return scope.builder.array_access(resolve(array_edge, scope), resolve(index_edge, scope))
