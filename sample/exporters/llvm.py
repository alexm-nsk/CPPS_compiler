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

llvm_initialized = False
llvm_functions   = {}

def init_llvm(module_name = "microsisal"):


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

    module = init_llvm(module_name)

    for function in functions:
        function.emit_llvm(module)

    return module


def export_function_to_llvm(function_node, module):

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

    # vars_ is a map that connects LLVM identifiers with SISAL names
    vars_ = []
    # assign names to llvm function parameters (not necessary, but makes llvm code easier to read):
    for n,p in enumerate(params):
        function.args[n].name = p
        vars_.append({"name": p, "llvm_identifier" : function.args[n]})
    
    block = function.append_basic_block(name = "entry")

    builder = ir.IRBuilder(block)

    #print(function_node.nodes)
    print (function_node.function_name)
    function_node.nodes[0].emit_llvm(module)

    # needed for printf:
    if function_node.function_name == "main":
        fmt_arg = add_bitcaster(builder, module)


    llvm_functions[function_node.function_name]  = function


def export_if_to_llvm(function_node, module):
    pass
    
def export_call_to_llvm(function_node, module):
    pass

if __name__ == "__main__":
    pass
