#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
#  llvm.py
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

from llvmlite import ir, binding
from copy import deepcopy
import compiler.nodes


llvm_initialized = False
llvm_functions   = {}
printf           = None
fmt_arg          = None
module           = None


def reset_llvm():
    llvm_initialized = False
    llvm_functions   = {}
    printf           = None
    fmt_arg          = None
    module           = None


class LlvmScope:

    def __init__(self, builder, vars_, expected_type = None, name = ""):
        self.vars          = vars_
        self.builder       = builder
        self.name          = name
        self.expected_type = expected_type

    def get_var_index(self, var_name):
        for i, var in enumerate(self.vars):
            if var_name == var: return i
        return None

    def get_var_by_index(self, index):
        # TODO make sure it's the actual one
        return self.vars[index]


def init_llvm(module_name = "microsisal"):

    global printf, fmt_arg
    reset_llvm()

    binding.initialize()
    binding.initialize_native_target()
    binding.initialize_all_asmprinters()

    module        = ir.Module( name = module_name )
    module.triple = binding.get_default_triple()

    target         = binding.Target.from_default_triple()
    target_machine = target.create_target_machine()
    backing_mod    = binding.parse_assembly("")
    engine         = binding.create_mcjit_compiler(backing_mod, target_machine)

    #initialize printf

    voidptr_ty     = ir.IntType(8).as_pointer()
    printf_ty      = ir.FunctionType(ir.IntType(32), [voidptr_ty], var_arg = True)
    printf         = ir.Function(module, printf_ty, name = "printf")

    llvm_initialized = True
    return module


def add_bitcaster(builder, module):

    voidptr_ty                 = ir.IntType(8).as_pointer()
    fmt = "%i \n\0"

    c_fmt                      = ir.Constant(ir.ArrayType(ir.IntType(8),len(fmt)), bytearray(fmt.encode("utf8")))
    global_fmt                 = ir.GlobalVariable(module, c_fmt.type, name = "fstr")
    global_fmt.linkage         = "internal"
    global_fmt.global_constant = True
    global_fmt.initializer     = c_fmt
    fmt_arg                    = builder.bitcast(global_fmt, voidptr_ty)
    return fmt_arg


def create_module(functions, module_name):
    global module
    module = init_llvm(module_name)

    for function in functions:
        function.emit_llvm()

    return module


def export_function_to_llvm(function_node, scope = None):

    global module, printf, fmt_arg

    arg_types = []
    params    = []

    # get types and names of this function's arguments
    for name, type_ in function_node.params.items():
    #    print (name, type_)
        #for p in type_["vars"]:
        arg_types.append(type_["type"].emit_llvm())
        params.append(name)


    #just one value for now:
    # TODO (make multiresult)
    function_type = ir.FunctionType( function_node.out_ports[0].type.emit_llvm(), (p for p in arg_types), False )

    function = ir.Function(module, function_type, name=function_node.function_name)
    llvm_functions[function_node.function_name]  = function

    # vars_ is a map that connects LLVM identifiers with SISAL names
    vars_ = {}

    # assign names to llvm function parameters (used when we recall those arguments in function's body):
    for n,p in enumerate(params):
        function.args[n].name = p
        vars_[p] = function.args[n]

    block = function.append_basic_block(name = "entry")

    builder = ir.IRBuilder(block)

    scope = LlvmScope(builder, vars_, expected_type = function_node.out_ports[0].type.emit_llvm())

    function_result = function_node.nodes[0].emit_llvm(scope)
    # ~ return
    # needed for printf:
    if function_node.function_name == "main":
        fmt_arg = add_bitcaster(builder, module)
        builder.call(printf, [fmt_arg, function_result])

    scope.builder.ret(function_result)


def is_parent(node1, node2):

        N2 = compiler.nodes.Node.nodes_[node2]
        if not "nodes" in N2.__dict__: return False

        for n in N2.nodes:
            if n.id == node1:
                return True
        return False

def get_edge_between(a, b):
    for e in compiler.nodes.Edge.edges_to[b.id]:
        if e.from_ == a.id:
            return e
    return None

def export_binary_to_llvm(binary_node, scope):

    edges_to = compiler.nodes.Edge.edges_to[binary_node.id]
    print (edges_to)
    # TODO (check if it has exactly two)
    a, b, = binary_node.get_input_nodes()
    print (a)
    print()
    print (b)
    # ~ print
    for i,operand in enumerate([a, b]):
        # find edge that points from this operand to the operation
        index = get_edge_between(operand, binary_node) 
        if is_parent(binary_node.id, operand.id): #parameter
            pass
            # ~ parameter
            print ()
        else:
            pass
            
    return None


def export_branch_to_llvm(branch_node, scope):
        # ~ print (Node)
    #for node, edge in condition_node.get_result_nodes():
     #   print (node)
      #  print (edge)
    return None


def export_condition_to_llvm(condition_node, scope):

    for node, edge in condition_node.get_result_nodes():
        print (compiler.nodes.Node.nodes_[node].emit_llvm(scope))

    pass


def export_if_to_llvm(if_node, scope):

    condition_result = if_node.condition.emit_llvm(scope)
    if_ret_val = scope.builder.alloca(scope.expected_type, name = "if_result_pointer")

    def get_branch(name):
        return next((x for x in if_node.branches if x.name == name), None)

    # ~ with scope.builder.if_else(condition_result) as (then, else_):
        # ~ with then:
            # ~ pass
            # ~ #then_result = get_branch("Then").emit_llvm(scope)
            #print (then_result)
            # ~ scope.builder.store(then_result, if_ret_val)
        # ~ with else_:
            # ~ else_result = get_branch("Else").emit_llvm(scope)
            # ~ scope.builder.store(else_result, if_ret_val)

    return scope.builder.load (if_ret_val, name="if_result")


def export_algebraic_to_llvm(algebraic_node, scope):

    lhs   = algebraic_node.expression[0].emit_llvm(scope)
    rhs   = algebraic_node.expression[2].emit_llvm(scope)
    cmpop = algebraic_node.expression[1].operator

    if cmpop == "<":
        return scope.builder.icmp_signed(cmpop, lhs, rhs, name='cmp_result')
    elif cmpop == "+":
        return scope.builder.add(lhs, rhs, name='sum')
    elif cmpop == "-":
        return scope.builder.sub(lhs, rhs, name='sub')
    else:
        raise Exception ("Unsupported operation:",
                                algebraic_node.expression[1].location,
                                algebraic_node.expression[1].operator)


def export_identifier_to_llvm(identifier_node, scope):
    return scope.vars[identifier_node.name]


def export_literal_to_llvm(literal_node, scope):
    return ir.Constant( literal_node.type.emit_llvm() , int(literal_node.value))


def export_call_to_llvm(function_call_node, scope):

    name = function_call_node.function_name.name
    args = [ arg.emit_llvm(scope) for arg in function_call_node.args ]

    # ~ Call function fn with arguments args, a sequence of values.
    # ~ cconv is the optional calling convention.
    # ~ tail, if True, is a hint for the optimizer to perform tail-call optimization.
    # ~ fastmath is a string or a sequence of strings of names for fast-math flags.

    return scope.builder.call(llvm_functions[name], args, name='call_result', cconv=None, tail=False, fastmath=())


if __name__ == "__main__":
    pass
