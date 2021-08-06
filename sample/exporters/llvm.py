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

int32 = ir.IntType(32)

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
    
    # ~ print (function.function_name)
    #print (function_node.params)
    if (function_node.params):
        for type_ in function_node.params:
            for p in type_["vars"]:
                print (p.name, type_["type"])
    
    #if( num_return_vals > 1):
     #   function_type         = ir.FunctionType(ir.PointerType(ir.IntType(32)),args, False)
    #else:
    args                      = (int32 for p in range(1))
    
    function_type         = ir.FunctionType(ir.IntType(32), args, False)

    function = ir.Function(module, function_type, name=function_node.function_name)
    
    llvm_functions[function_node.function_name] = function
    
    block = function.append_basic_block(name = "entry")

    # vars_ is a map that connects LLVM identifiers with SISAL names
    vars_ = []

    # ~ #put names for each parameter into our function definition in our module
    # ~ for n,p in enumerate(self.params):
        # ~ self.function.args[n].name = p["name"]
        # ~ # vars_ is a map that connects LLVM identifiers with SISAL names
        # ~ vars_.append({"name": p["name"], "llvm_identifier" : self.function.args[n]})
        # ~ # set values to the node's output so that it can be read anytime by it's child nodes
        # ~ self.output.append( self.function.args[n] )

    builder = ir.IRBuilder(block)

    # needed for printf:
    if function_node.function_name == "main":
        fmt_arg = add_bitcaster(builder, module)

    
    #llvm_functions[function_name]  = self.function
    return None


if __name__ == "__main__":
    pass
