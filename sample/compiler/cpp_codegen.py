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

# C++ code generation module, inspired by llvmlite

# TODO make default values for types
# TODO make sure builders are always initialized once
# TODO separate scope result variable?
# TODO move get_idntifier name to scope

CPP_INDENT         = " " * 4
REDUCTION_FIRST    = True
OPTIMIZE_CPP       = False
MAIN_FUNCTION_NAME = "sisal_main"

from compiler.cpp_opt import *

from copy import copy

class CppScope:

    def __init__(self, vars_, builder = None):
        self.builder = builder
        self.vars = copy(vars_)

    def add_var_to_front(self, var):
        self.vars.insert(0, var)

    def add_var_to_back(self, var):
        self.vars.append(var)

    def get_vars_copy(self):
        return copy(self.vars)


class Type:

    def __init__(self):
        pass

    def print_code(self):
        return "this is a base class for type"


class ArrayType(Type):

    def __init__(self, element_type):
        self.element_type = element_type

    def __str__(self):
        return f"vector<{self.element_type}>"

    # indices is ArrayType.indices with some items removed (so we don't have name collisions)
    def print_code(self, name):

        return f"result[\"{name}\"] = iterable_to_json({name});"

        # ~ return f"for(unsigned int {index} = 0; {index} < {name}.size(); ++{index})\n" + \
               # ~ "{\n" + CPP_INDENT + \
                   # ~ self.element_type.print_code(str(name) + f"[{index}]") + \
               # ~ "\n}"


class IntegerType(Type):

    def __init__(self, bit_depth = 64):
        self.bit_depth = bit_depth

    def default(self):
        return 0

    def __str__(self):
        if self.bit_depth == 32:
            return "int"
        if self.bit_depth == 64:
            return "long long int"

    def print_code(self, name = ""):
        return f"result[\"{name}\"] = {name};"
        # ~ return f"printf(\"%d\", {name});"


class RealType(Type):

    def __init__(self, bit_depth = 64):
        self.bit_depth = bit_depth

    def default(self):
        return 0

    def __str__(self):
        if self.bit_depth == 32:
            return "float"
        if self.bit_depth == 64:
            return "double"

    def print_code(self, name = "", new_indices = None):
        return f"result[\"{name}\"] = {name};"
        # ~ return f'printf("%f", {name});'


class BooleanType(Type):

    def __init__(self):
        pass

    def default(self):
        return 0

    def __str__(self):
        return "bool"


class StringType(Type):

    def __init__(self, value):
        self.value = value

    def __str__(self):
        return self.value


class VoidType(Type):

    def __str__(self):
        return "void"


class Statement:

    def __init__(self):
        self.no_semicolon = False
        return 0

    def __str__(self):
        return 0


class Assignment(Statement):

    def __init__(self, var, value):
        super().__init__()
        self.var = var
        self.value = value

    def __str__(self):
        return str(self.var) + " = " + str(self.value)


class Return(Statement):

    def __init__(self, object_):
        super().__init__()
        self.object = object_

    def __str__(self):
        return "return " + str(self.object)


class Expression():

    # for id1, id2, id3... identifiers
    num_identifiers = 0

    # for repated named identifiers like if_result, if_result1... (we store number for each name),
    # see __init__ for details
    names = {}

    def get_new_name(self):
        if (type(self)==Constant):
            return "const"
        Expression.num_identifiers += 1
        return "id" + str(Expression.num_identifiers)

    def __init__(self, name):

        self.no_semicolon = False

        if not name:
            self.name = self.get_new_name()
        else:
            # ~ if name in Expression.names:
                # ~ Expression.names[name] += 1
                # ~ self.name = name + str(Expression.names[name])
            # ~ else:
                # ~ Expression.names[name] = 1
                # ~ self.name = name
            self.name = name

    def __str__(self):
        return self.name


class ArrayAccess(Expression):

    def __init__(self, array_object, index_object, name = None):
        super().__init__(name)
        self.array_object = array_object
        self.index_object = index_object
        # must be an array:
        self.type = array_object.type.element_type
        self.init_code = f"{self.array_object}[{self.index_object}]"

    # ~ def __str__(self):
        # ~ return f"{self.array_object}[{self.index_object}]"


class Variable(Expression):

    def __init__(self, type_, value = None, name = None):
        super().__init__(name)
        self.type = type_
        self.value = value
        self.init_code = str(value) if value not in [None, ""] else ""


class Constant(Expression):

    def __init__(self, value, type_, name = None):
        super().__init__(name)
        self.value = value
        # ~ if value==3:
        if type(type_) == IntegerType:
            self.type = IntegerType(32)
        else:
            self.type = RealType(32)

    def __str__(self):
        return str(self.value)


class Call(Expression):

    def __init__(self, function, args : "a list of c++ identifiers", name = None):
        super().__init__(name)
        self.function = function

        self.type = function.return_type

        # TODO probably not the best way to do this:
        if function.name == MAIN_FUNCTION_NAME:
            args = [v.name for v in function.arguments]
            self.init_code = self.function.name + "(" + ",".join((str(s) for s in args)) + ")"
        else:
            self.args = args
            self.init_code = self.function.name + "(" + ",".join((str(s) for s in self.args)) + ")"


class If(Expression):

    def __init__(self, cond, indent_level, name = None):
        super().__init__(name)
        self.no_semicolon = True
        self.cond  = cond
        self.then  = Block(indent_level + 1)
        self.else_ = Block(indent_level + 1)
        self.indent_level = indent_level

    def get_then(self):
        return self.then

    def get_else(self):
        return self.else_

    def get_then_builder(self):
        return Builder(self.then)

    def get_else_builder(self):
        return Builder(self.else_)

    def __str__(self):
        ind = self.indent_level * CPP_INDENT
        # "" used to contain \n:
        return f"if({self.cond})\n" + ind +  "{\n" + str(self.then) +\
                "" + ind +"}\n"+ ind +"else\n" + ind + "{\n" +\
                str(self.else_) +""+ ind + "}"


class WhileLoop(Expression):

    def __init__(self, indent_level = 0, name = None):
        super().__init__(name)
        self.no_semicolon = True
        self.indent_level = indent_level
        self.pre_cond = Block(indent_level + 1, name = "precondition")
        self.body = Block(indent_level + 1, name = "body")
        self.reduction = Block(indent_level + 1, name = "reduction")

    def get_pre_cond_builder(self):
        return Builder(self.pre_cond)

    def get_body_builder(self):
        return Builder(self.body)

    def get_reduction_builder(self):
        return Builder(self.reduction)

    def __str__(self):
        ind = self.indent_level * CPP_INDENT
        cond_code = self.pre_cond.inits[0].init_code
        if REDUCTION_FIRST:
            return "while( " + cond_code + " )\n" + ind + "{\n" + \
                    str(self.reduction) + \
                    str(self.body) + ind + \
                    "}"
        else:
            return "while( " + cond_code + " )\n" + ind + "{\n" + \
                    str(self.body) + \
                    str(self.reduction) + ind + \
                    "}"


class CppCode(Expression):

    def __init__(self, code, name = None):
        super().__init__(name)
        self.no_semicolon = True
        self.code = code

    def __str__(self):
        return self.code


class Binary(Expression):

    def __init__(self, left, right, operator, name = None):
        super().__init__(name)
        self.left     = left
        self.right    = right
        self.operator = operator
        if self.operator in ["<=", "<", ">", "==", ">="]:
            self.type = BooleanType()
        else:
            # ~ print (self.right.type, self.right)
            # TODO write proper type
            if type(self.left.type) == RealType or type(self.right.type) == RealType:
                self.type = RealType(32)
            elif type(self.left.type) == ArrayType or type(self.right.type) == ArrayType:
                self.type = self.left.type
            else:
                self.type = IntegerType(32)

        self.init_code = f"{str(self.left)} {self.operator} {str(self.right)}"


json_pipe_loader = '''\
// this code loads JSON input data from file
// or pipe (depending on code generator configuration)
Json::Value root;
std::cin >> root;'''

json_result_printer = '''\
std::cout << result << "\\n";
std::cout << std::endl;'''

def unpack_variable(a):

    if type(a.type) == ArrayType:
        init_code =  f"{a.type} {a};\n"
        init_code += f"for ( unsigned int index = 0; index < root[\"{a}\"].size(); ++index )\n"
        # TODO it's asInt now, make it an arbitrary type!
        init_code += CPP_INDENT + f"{a}.push_back(root[\"{a}\"][index].asInt());\n"
        return init_code

    elif type(a.type) == IntegerType:
        return f"{a.type} {a} = root[\"{a}\"].asInt();\n"


def init_arg_loader(args):

    arg_init_code = ""
    for a in args:
        arg_init_code += unpack_variable(a)

    final = json_pipe_loader + "\n" + arg_init_code
    return final


def init_result_printer():
    result_printer_code = "Json::Value result;"
    return result_printer_code


def indent_cpp(code, steps = 1):

    code = code.strip()
    return CPP_INDENT * steps + code.replace('\n', '\n' + CPP_INDENT * steps)


class Function:

    functions = {}

    def __init__(self, name, return_type, arguments: "list of (name, type) - tuples", main = False):
        self.name        = name
        self.return_type = return_type
        self.arguments   = []
        self.statements  = []
        self.entry_block = Block(name = "entry")
        self.is_main     = main
        Function.functions[name] = self

        if not main:
            for index, (name, type_) in enumerate(arguments):
                argument = Variable (name = name,type_ =  type_)
                self.arguments.append(argument)
        else:
            self.return_type = IntegerType(32)
            self.arguments = []

    def get_entry_block(self):
        return self.entry_block

    def get_argument_by_name(self, name):
        return list(filter(lambda x: x.name == name, self.arguments))[0]

    def get_argument_by_index(self, index):
        return self.arguments[index]

    def get_arguments(self):
        return self.arguments

    def __str__(self):
        text = ""
        footer = ""

        if self.is_main:
            arg_text = "int argc, char **argv"
            footer = CPP_INDENT + "return 0;\n"
        else:
            arg_text = ", ".join([str (a.type) +" "+ str(a) for a in self.arguments])

        text += f"{self.return_type} {self.name}({arg_text})\n"

        text += "{\n"

        # TODO move the whole thing out to cpp.py and do it using explicit C++ inserts
        # this should make name collision prevention code also work
        if self.is_main:
            # add a simple try-catch
            text += CPP_INDENT + "try\n" + CPP_INDENT +"{\n"

            #add code that loads arguments
            args =  Function.functions[MAIN_FUNCTION_NAME].arguments
            text += indent_cpp(init_arg_loader(args), 2) + "\n"
            text += indent_cpp(init_result_printer(), 2) + "\n"

            entry_block = str(self.entry_block)
            text += f"{CPP_INDENT + indent_cpp(entry_block)}\n"
            text += indent_cpp(json_result_printer, 2) + "\n"
            text += CPP_INDENT + "}\n" +\
                    CPP_INDENT + "catch(int)\n" + CPP_INDENT +\
                    "{\n" + CPP_INDENT*2 +\
                        "return 1;\n" + CPP_INDENT +\
                    "}\n"
        else:
            text += f"{self.entry_block}"

        text += footer + "}"
        if OPTIMIZE_CPP:
            return post_opt(text)
        return text


class Block:

    def __init__(self, indent_offset = 1, name = None):
        self.inits = []
        self.statements = []
        self.indent_level = indent_offset
        self.name = name

    def add_expression(self, exp, name = None):
        self.statements.append(exp)
        if type (exp) == Variable:
            inits.append(exp)

    def add_init(self, identifier):
        self.inits.append(identifier)

    def __str__(self):

        label = "" if self.name == None else CPP_INDENT * self.indent_level + f"// {self.name}:"  + "\n"

        inits = "".join(  CPP_INDENT * self.indent_level +
                            str(s.type) + " "  +
                            str(s.name) +
                            ((" = " + str(s.init_code)) if s.init_code not in ["", None] else "") +
                            ("" if s.no_semicolon else ";") + "\n"
                            for s in self.inits)

        # ~ body = "\n".join( CPP_INDENT * self.indent_level +
                            # ~ str(s) + (";" if type(s) not in [If, WhileLoop] else "") for s in self.statements)

        body = "\n".join( CPP_INDENT * self.indent_level +
                            str(s) + ("" if s.no_semicolon else ";") for s in self.statements)

        return label + inits + body + "\n"

    def add_ret(self, object_):
        self.statements.append(Return(object_))

    def add_if(self, if_):
        self.statements.append(if_)

    def add_bin(self, bin_):
        self.statements.append(bin_)

    def add_assignment(self, assignment):
        self.statements.append(assignment)

    def add_while_loop(self, wl):
        self.statements.append(wl)

    def add_array_access(self, aa):
        self.statements.append(aa)


class Builder:

    def __init__(self, block):
        self.block = block

    def call(self, function, args, name = None):
        call = Call(function, args, name)
        self.block.add_init(call)
        return call

    def define(self, type_, value = None, name = None):
        identifier = Variable(type_, value, name)
        self.block.add_init(identifier)
        return identifier

    def ret(self, object_):
        self.block.add_ret(object_)

    def printf(self, object_):
        code = f'printf("%d", {object_})'
        self.block.add_expression(CppCode(code))

    def if_(self, cond):
        if_ = If(cond, self.block.indent_level)
        self.block.add_if(if_)
        return if_

    def binary(self, left, right, op):
        bin_ = Binary(left, right, op)
        self.block.add_init(bin_)
        return bin_

    def constant(self, value, type_):
        c = Constant(value, type_)
        return c

    def while_(self):
        while_loop = WhileLoop(indent_level = self.block.indent_level)
        self.block.add_while_loop(while_loop)
        return while_loop

    def assignment(self, var, value):
        assignment = Assignment(var, value)
        self.block.add_assignment(assignment)
        return assignment

    def array_access(self, array_object, index_index):
        aa = ArrayAccess(array_object, index_index)
        self.block.add_init(aa)
        return aa

    def cpp_code(self, code):
        for c in code.split("\n"):
            self.block.add_expression(CppCode(c))

header = '''\
#include <stdio.h>
#include <vector>
#include <iostream>
#include <fstream>
#include <json/json.h>// uses jsoncpp library

using namespace std;

template <typename Iterable>

Json::Value iterable_to_json(Iterable const& cont) {
    Json::Value v;
    for (auto&& element: cont) {
        v.append(element);
     }
    return v;
}

template <typename I>
vector<I> operator | (const vector<I>& lhs, const vector<I>& rhs){
    vector<I> result = lhs;
    result.insert(result.end(), rhs.begin(), rhs.end());
    return result;	// returning the vector "result"
}
'''

class Module:

    def __init__(self, name):
        self.name = name
        self.functions = {}
        self.headers = []
        Module.printf = Function("printf", IntegerType(32), [("number", IntegerType(32))])

    def add_function(self, function):
        # ~ function.module = self
        self.functions[function.name] = function
        function.containing_module = self

    def add_header(self, header_name):
        # ~ self.headers.append(f"#include <{header_name}>")
        if not header_name in self.headers:
            self.headers.append(header_name)

    def __str__(self):
        text = "//" +  self.name + "\n"
        text += header
        text += "\n\n".join([f"#include <{str(h)}>" for h in self.headers]) + "\n\n"
        text += "\n\n".join([str(f) for name, f in self.functions.items()])
        return text.strip()
