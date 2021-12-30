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


# TODO get it from the system and put it into a settings module
SYSTEM_BIT_DEPTH = 64


# TODO check if it's necessary to create it.IntType(32) every time
type_map = {
    "integer" : ir.IntType(SYSTEM_BIT_DEPTH)
}


class LlvmScope:

    def __init__(self, builder, expected_type = None, name = "", function = None):

        self.builder       = builder
        self.name          = name
        self.expected_type = expected_type
        self.location      = "" # TODO assign this
        self.vars          = {}
        self.var_index     = {} # stores varname to index pairs
        self.function      = function

    def add_var(self, name,  var_):
        self.vars[name] = var_
        self.var_index[name] = len(self.var_index)

    # accepts descriptions in form of:
    # {'type': {'location': 'not applicable', 'descr': 'integer'}, 'index': 0

    def add_vars(self, var_): #add a dict {"name" : internals}
        for name, value in var_.items():
            self.vars[name] = value
            self.var_index[name] = len(self.var_index)

    def prepend_vars(self, var_):

        for name in self.var_index:
            self.var_index[name] += len(var_)

        for n , (name, value) in enumerate(var_.items()):
            self.vars[name] = value
            self.var_index[name] = n

    def get_var_index(self, var_name):
        for i, var in enumerate(self.vars):
            if var_name == var: return i
        return None

    def get_var_by_index(self, var_index):
        # TODO make sure it's the actual one
        for name, index in self.var_index.items():
            if index == var_index:
                return self.vars[name]

        raise Exception (f"Variable with index {index} not found, location: {self.location}")


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
    printf_ty      = ir.FunctionType(ir.IntType(SYSTEM_BIT_DEPTH), [voidptr_ty], var_arg = True)
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
    return_llvm_type = function_node.out_ports[0].type.emit_llvm()
    function_type = ir.FunctionType( return_llvm_type, (p for p in arg_types), False )

    function = ir.Function(module, function_type, name=function_node.function_name)
    llvm_functions[function_node.function_name]  = function

    # vars_ is a map that connects LLVM identifiers with SISAL names
    vars_ = {}

    # assign names to llvm function parameters (used when we recall those arguments in function's body):

    block = function.append_basic_block(name = "entry")
    builder = ir.IRBuilder(block)

    scope = LlvmScope(builder, expected_type = return_llvm_type, function = function)

    for n,p in enumerate(params):
        function.args[n].name = p
        scope.add_vars({p : function.args[n]})

    result_node, edge = function_node.get_input_nodes()[0]

    # TODO use scope.expected_type for further nodes
    function_result = result_node.emit_llvm(scope)


    exit_block = scope.builder.append_basic_block(name = "exit")
    scope.builder.position_after(function_result)
    scope.builder.branch(exit_block)
    # needed for printf:

    with scope.builder.goto_block(exit_block):
        if function_node.function_name == "main":
            fmt_arg = add_bitcaster(builder, module)
            builder.call(printf, [fmt_arg, function_result])
        scope.builder.ret(function_result)

    return function_result


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


def get_edges_between(a, b):

    return [
                e
                for e in compiler.nodes.Edge.edges_to[b.id]
                if e.from_ == a.id
            ]


'''
    • IRBuilder.icmp_signed(cmpop, lhs, rhs, name='')
    Signed integer compare lhs with rhs. The string cmpop can be one of <, <=, ==, !=, >= or >.

    • IRBuilder.icmp_unsigned(cmpop, lhs, rhs, name='')
    Unsigned integer compare lhs with rhs. The string cmpop can be one of <, <=, ==, !=, >= or >.

    • IRBuilder.fcmp_ordered(cmpop, lhs, rhs, name='', flags=[])
    Floating-point ordered compare lhs with rhs.
    – The string cmpop can be one of <, <=, ==, !=, >=, >, ord or uno.
    – The flags list can include any of nnan, ninf, nsz, arcp and fast, which implies all previous flags.

    • IRBuilder.fcmp_unordered(cmpop, lhs, rhs, name='', flags=[])
    Floating-point unordered compare lhs with rhs.
    – The string cmpop, can be one of <, <=, ==, !=, >=, >, ord or uno.
    – The flags list can include any of nnan, ninf, nsz, arcp and fast, which implies all previous flags
'''


def dereference_value(value, scope):

    if isinstance(value, ir.AllocaInstr):
        return scope.builder.load(value, name = "deref__" + value.name)
    elif isinstance(value, ir.PointerType):
        return scope.builder.load(value.pointee, name = "deref__" + value.name)
    return value


def export_binary_to_llvm(binary_node, scope):

    edges_to = compiler.nodes.Edge.edges_to[binary_node.id]

    input_nodes = binary_node.get_input_nodes()

    if len(input_nodes) != 2:
        raise Exception("Binary node has wrong number of nodes pointing at it (must be 2), location: " + binary_node.location)

    ops = []

    def dereference_and_add(value):
        # dereference the value if we have a pointer operand (Llvm can't compare pointer with non-pointer):
        # TODO no need to dereference if both are pointers
        if isinstance(value, ir.AllocaInstr):
            value = scope.builder.load(value, name = "deref__" + value.name)
        elif isinstance(value, ir.PointerType):
            value = scope.builder.load(value.pointee, name = "deref__" + value.name)
        ops.append(value)

    for n, (operand, edge) in enumerate(input_nodes[:2]):
        # find edge that points from this operand to the operation
        if is_parent(binary_node.id, operand.id):
            index = get_edges_between(operand, binary_node)[n].from_index
            dereference_and_add(scope.get_var_by_index(index))
        else:
            dereference_and_add(operand.emit_llvm(scope))

    lhs, rhs = ops

    op = binary_node.operator

    # get operand types:
    type_a, type_b = [port.type.descr for port in binary_node.in_ports]

    if op in ["<", "<=", "==", "!=", ">=", ">."]:
        if type_a == "integer" and type_b == "integer":
            return scope.builder.icmp_signed(op, lhs, rhs)
        else:
            print(f'Warning: comparing different types: {type_a, type_b} at {binary_node.location}')
            return scope.builder.fcmp_ordered(op, lhs, rhs)
    elif op == "+":
        return scope.builder.add(lhs, rhs)
    elif op == "-":
        return scope.builder.sub(lhs, rhs)
    elif op == "*":
        return scope.builder.mul(lhs, rhs)
    elif op == "/":
        return scope.builder.sdiv(lhs, rhs)


def export_literal_to_llvm(literal_node, scope):
    llvm_type = literal_node.out_ports[0].type.emit_llvm()
    return ir.Constant( llvm_type, int(literal_node.value))


def export_branch_to_llvm(branch_node, scope):

    result_nodes = branch_node.get_result_nodes()
    if result_nodes != []:
        for node, edge in result_nodes:
            # return first and only port value for now
            # TODO implement multiple outputs
            return node.emit_llvm(scope)
    else:
        input_edges = branch_node.get_input_edges()
        for edge in input_edges:
            return scope.get_var_by_index(edge.from_index)


def export_condition_to_llvm(condition_node, scope):

    for node, edge in condition_node.get_result_nodes():
        # return first and only port value for now
        return node.emit_llvm(scope)


def export_if_to_llvm(if_node, scope):

    condition_result = if_node.condition.emit_llvm(scope)
    if_ret_val = scope.builder.alloca(scope.expected_type, name = "if_result_pointer")

    # TODO there could be multiple else_if branches

    def get_branch(name):
        return next((x for x in if_node.branches if x.name == name), None)

    with scope.builder.if_else(condition_result) as (then, else_):
        with then:
            then_result = get_branch("Then").emit_llvm(scope)
            scope.builder.store(then_result, if_ret_val)
        with else_:
            else_result = get_branch("Else").emit_llvm(scope)
            scope.builder.store(else_result, if_ret_val)

    return scope.builder.load (if_ret_val, name="if_result")


def export_functioncall_to_llvm(function_call_node, scope):

    name = function_call_node.callee

    arg_nodes = function_call_node.get_input_nodes()
    num_in_ports = len(function_call_node.in_ports)

    # put argument values into appropriate argument slots:
    args = [None for i in range(num_in_ports)]
    for (node, edge) in arg_nodes:
        args[edge.to_index] = node.emit_llvm(scope)

    # ~ Call function fn with arguments args, a sequence of values.
    # ~ cconv is the optional calling convention.
    # ~ tail, if True, is a hint for the optimizer to perform tail-call optimization.
    # ~ fastmath is a string or a sequence of strings of names for fast-math flags.

    return scope.builder.call(llvm_functions[name], args, name='call_result', cconv=None, tail=False, fastmath=())


def export_init_to_llvm(init_node, scope):
    ret_val = None
    results = init_node.get_result_nodes()
    for n , (name, descr) in enumerate(init_node.results.items()):
        new_var = scope.builder.alloca(descr['type'].emit_llvm(), name = name)

        if n == 0:
            ret_val = new_var
            # we return the first initialization instruction for proper structuring later

        scope.prepend_vars({name: new_var})
        node, edge = results[n]
        if (node == init_node):
            #scope.builder.store(node.emit_llvm(scope), scope.vars[var])
            #TODO store scope's var in this var
            pass
        else:
            scope.builder.store(node.emit_llvm(scope), scope.vars[name])
    return ret_val
    # doesn't need to return anything, only to initialize the loop


def export_precondition_to_llvm (pre_cond_node, scope):

    result_nodes = pre_cond_node.get_result_nodes()

    if (len (result_nodes) > 1):
        raise Exception("only one loop condition is supported at the moment, location: " + pre_cond_node.location)

    node, edge = result_nodes[0]
    return node.emit_llvm(scope)


def export_reduction_to_llvm (reduction_node, scope):

    # TODO alternatively, get the nodes that targets the second port (index #1)
    node, edge = reduction_node.get_parameter_nodes()[0]

    if (reduction_node.operator == "value"):
        index = edge.from_index
        return scope.get_var_by_index(index)


def export_returns_to_llvm (returns_node, scope):

    # must influence the body:
    # if it's "value" we return the value
    # if it's sum we must accumulate it each time after body is executed
    node, edge = returns_node.get_result_nodes()[0]
    return node.emit_llvm(scope)

def export_oldvalue_to_llvm (oldvalue_node, scope):

    edge = oldvalue_node.get_input_edges()[0]
    index = edge.from_index
    return scope.get_var_by_index(index)


def export_body_to_llvm(body_node, scope):

    result_node, edge = body_node.get_result_nodes()[0]
    index = edge.to_index
    final_value = result_node.emit_llvm(scope)
    scope.builder.store(final_value, scope.get_var_by_index(index))


def export_loopexpression_to_llvm(loopexpression_node, scope):

    init     = loopexpression_node.init.emit_llvm(scope)

    loop_check  = scope.function.append_basic_block(name = "loop_check")
    loop_result = scope.builder.alloca(scope.expected_type, name = "loop_result")
    scope.builder.branch(loop_check)

    with scope.builder.goto_block(loop_check):

        pre_cond = loopexpression_node.pre_condition.emit_llvm(scope)

        with scope.builder.if_else(pre_cond) as (then, else_):
            with then: # condition satisfied - keep looping
                loopexpression_node.body.emit_llvm(scope)
                scope.builder.branch(loop_check)
            with else_: # exit
                scope.builder.store( 
                                    dereference_value( loopexpression_node.reduction.emit_llvm(scope), scope ), 
                                    loop_result
                                    )

        result = scope.builder.load(loop_result, name = "loop_result_deref")

    return result


if __name__ == "__main__":
    pass
