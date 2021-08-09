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

llvm_initialized = False
llvm_functions   = {}
printf = None
fmt_arg = None
module = None

class LlvmScope:

    def __init__(self, builder, vars_, name = ""):
        self.vars    = vars_
        self.builder = builder
        self.name    = name

def init_llvm(module_name = "microsisal"):

    global printf, fmt_arg

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
        function.emit_llvm(module)

    return module


def export_function_to_llvm(function_node, scope = None):

    global module, printf, fmt_arg

    arg_types = []
    params    = []

    # get types and names of this function's arguments
    for type_ in function_node.params:
        for p in type_["vars"]:
            arg_types.append(type_["type"].emit_llvm())
            params.append(p.name)


    #just one value for now:
    # TODO (make multiresult)
    function_type = ir.FunctionType(function_node.ret_types[0].emit_llvm(), (p for p in arg_types), False)

    function = ir.Function(module, function_type, name=function_node.function_name)
    llvm_functions[function_node.function_name]  = function

    # vars_ is a map that connects LLVM identifiers with SISAL names
    vars_ = {}
    # assign names to llvm function parameters (not necessary, but makes llvm code easier to read):
    for n,p in enumerate(params):
        function.args[n].name = p
        vars_[p] = function.args[n]

    block = function.append_basic_block(name = "entry")

    builder = ir.IRBuilder(block)

    scope = LlvmScope(builder, vars_)

    function_result = function_node.nodes[0].emit_llvm(scope)
    # needed for printf:
    if function_node.function_name == "main":
        fmt_arg = add_bitcaster(builder, module)
        builder.call(printf, [fmt_arg, function_result])

    scope.builder.ret(function_result)


def export_if_to_llvm(if_node, scope):

    condition_result = if_node.condition[0].emit_llvm(scope)

    # TODO put actual type here

    if_ret_val = scope.builder.alloca(ir.IntType(32), name = "if_result_pointer")

    with scope.builder.if_else(condition_result) as (then, else_):
        with then:
            then_result = if_node.branches["then"]["nodes"][0].emit_llvm(scope)
            scope.builder.store(then_result, if_ret_val)
        with else_:
            else_result = if_node.branches["else_"]["nodes"][0].emit_llvm(scope)
            scope.builder.store(else_result, if_ret_val)

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
    args = [ arg[0].emit_llvm(scope) for arg in function_call_node.args ]

    # ~ Call function fn with arguments args, a sequence of values.
    # ~ cconv is the optional calling convention.
    # ~ tail, if True, is a hint for the optimizer to perform tail-call optimization.
    # ~ fastmath is a string or a sequence of strings of names for fast-math flags.

    return scope.builder.call(llvm_functions[name], args, name='call_result', cconv=None, tail=False, fastmath=())


if __name__ == "__main__":
    pass
