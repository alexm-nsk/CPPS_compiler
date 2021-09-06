#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
#  parse_file.py
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

# TODO: Expresssion groups (e.g. return values)

import re
import pprint

pp = pprint.PrettyPrinter(indent = 4, depth = 6)

from parsimonious.grammar    import Grammar
from parsimonious.nodes      import NodeVisitor
from parsimonious.exceptions import ParseError

# "ast_" is used instead of "ast" to avoid conflicts
from ast_.node import *
from ast_.edge import *

from sisal_type.sisal_type import *

from parser.arithmetic_helpers import set_priorities

# connect recursive objects like
#       args_groups_list = arg_def_group (_ ";" _ arg_def_group)*
# into one array-list


def unpack_rec_list(node):
    return [node[0]] + [r[-1] for r in node[1]]


#----------------------------------------------------
#
# TreeVisitor class that allows us to go through
# everything the parser has found
#
# We go through separate strings containing each function
#
#----------------------------------------------------


class TreeVisitor(NodeVisitor):


    def get_location(self, node):
        text = node.full_text

        start_row    = text[:node.start].count("\n") + 1 # line numbers have to start from "1"
        start_column = len (  (text[:node.start].split("\n"))[-1]  )

        if start_row == 1: start_column += self.column_offset

        end_row      = text[:node.end].count("\n") + 1
        end_column   = len (  (text[:node.end].split("\n"))[-1]  )

        if end_row == 1: end_row += self.column_offset

        return "{}:{}-{}:{}".format(start_row + self.line_offset,
                                    start_column,
                                    end_row + self.line_offset,
                                    end_column)

    # rule: type          = ("array" _ "of" _ type ) / std_type
    def visit_type(self, node, visited_children):

        return visited_children[0]

    # rule: std_type      = "integer" / "real"
    def visit_std_type(self, node, visited_children):
        type_name = node.text
        location = self.get_location(node)

        if type_name == "integer":
            return IntegerType(location)
        elif type_name == "real":
            return RealType(location)


        #return dict(type_name = node.text, location = self.get_location(node))

    def visit_array(self, node, visited_children):
        element_type = visited_children[4]
        return ArrayType(element_type,  self.get_location(node))

    def visit__(self, node, visited_children):
        return None


    def visit_empty(self, node, visited_children):
        return None

    #----------------------------------------------------
    # these methods address parsing of function arguments:
    #----------------------------------------------------

    # rule: function_arguments = args_groups_list / _
    def visit_function_arguments(self, node, visited_children):
        return visited_children[0]

    # rule: arg_def_list  = identifier (_ "," _ identifier)*
    def visit_arg_def_list(self, node, visited_children):
        return unpack_rec_list(visited_children)

    # rule: arg_def_group = arg_def_list _ ":" _ type
    def visit_arg_def_group(self, node, visited_children):
        type_ = visited_children[4]
        var_names = visited_children[0]

        return dict(type = type_, vars = var_names)

    # rule: args_groups_list = (arg_def_group (_ ";" _ arg_def_group)*) / _
    def visit_args_groups_list(self, node, visited_children):

        args_groups = unpack_rec_list(visited_children)
        return args_groups

    # rule: function_retvals   = ("returns" _ type_list) / _
    def visit_function_retvals(self, node, visited_children):
        if (visited_children != [None]):
            ret_types = unpack_rec_list(visited_children[0][2])
            return ret_types
        else:
            return None

    # just return the operation's string
    def visit_bin_op(self, node, visited_children):
        return Bin(location  = self.get_location(node),
                    operator = node.text)

    # rule: algebraic          = (operand) (_ bin_op _ operand)*
    def visit_algebraic(self, node, visited_children):

        expression = [visited_children[0]]
        if len(visited_children):
            for n,v in enumerate(visited_children[1]):
                expression += [v[1]] + [v[3]]

        return Algebraic(expression = expression, location = self.get_location(node))

    # exp (_ "," _ exp)*
    def visit_args_list(self, node, visited_children):
        return unpack_rec_list(visited_children)

    # !("function" _) identifier _ lpar _ args_list _ rpar
    def visit_call(self, node, visited_children):

        args = visited_children[5]
        function_name = visited_children[1]
        ret_val = Call(function_name = function_name,
                              args = args,
                              location = self.get_location(node)
                          )
        return ret_val

    # rule: number_literal_int             = ~"[0-9]+"
    def visit_number_literal_int(self, node, visited_children):
        return Literal(value = node.text, location = self.get_location(node), type = IntegerType())

    def visit_identifier(self, node, visited_children):
        return Identifier(name = node.text, location = self.get_location(node))

    #----------------------------------------------------
    #
    #----------------------------------------------------

    # rule: function     = _ "function" _ identifier _
    #                            lpar _
    #                            function_arguments _
    #                            function_retvals _
    #                            rpar
    #                            _ exp _
    #                         "end function" _

    def visit_function(self, node, visited_children):

        #if the function has parameters, generate corresponding IR-piece
        name          = visited_children[ 3 ].name #this is an identifier,  so we get it's name
        ret_types     = visited_children[ 9 ],
        if ret_types:
           ret_types = ret_types[0] # TODO this is a crutch (although a fully functional one), fix this

        function_body = visited_children[ 13 ]

        params = dict(
                        name          = "Lambda",
                        function_name = name,
                        nodes         = function_body,
                        location      = self.get_location(node),
                        params        = visited_children[7] if visited_children[7] else [],
                        ret_types     = ret_types if ret_types else [VoidType()]
                      )

        function = Function(**params)

        return function


    #----------------------------------------------------
    #
    #----------------------------------------------------
    # rule: if = "if" _ exp _ "then" _ exp _ ("elseif" _ exp _ "then" _ exp _)*  (_ "else" _ exp )? _ "end if"

    def visit_if(self, node, visited_children):

        condition_nodes = visited_children[2]
        then_node       = visited_children[6]
        else_nodes      = visited_children[9][0][3]
        elseifs = []

        for n,e in enumerate(visited_children[8]):
            condition_nodes.append(e[2][0])
            elseifs.append(e[6][0])

        retval = dict(conditions   = condition_nodes,
                        then         = then_node,
                        elseif_nodes = elseifs,
                        else_nodes   = else_nodes,
                        location     = self.get_location(node))

        # ~ for k, v in retval.items():
            # ~ print(k, ":\n   ", v)
            # ~ print ()


        return If(
                        conditions   = condition_nodes,
                        then         = then_node,
                        elseif_nodes = elseifs,
                        else_nodes   = else_nodes,
                        location     = self.get_location(node),
                    )


    #----------------------------------------------------
    #
    #----------------------------------------------------
    # rule: array_access       = identifier  (_ "[" _ array_index  _"]")+
    def visit_array_access(self, node, visited_children):
        array_name  = visited_children[0].name

        indices = [index_group[3] for index_group in visited_children[1]]
        #indices.reverse()

        # creates a "nested doll" of Array objects
        # it facilitates the numeration of nodes
        def make_array(index = 0, array_index = 0):
            if index < len(indices):
                return ArrayAccess(
                                name     = array_name,
                                location = self.get_location(node),
                                index    = indices[index],
                                subarray = make_array(index + 1, array_index + 1),
                                array_index = array_index
                            )

        array = make_array()
        array.inline_indices = indices #save it for LLVM
        return array

    #----------------------------------------------------
    #
    #----------------------------------------------------

    def visit_brackets_algebraic(self, node, visited_children):
        return visited_children[2]

    def visit_exp(self, node, visited_children):
        all_exps = unpack_rec_list(visited_children)
        return all_exps

    def visit_exp_singular(self, node, visited_children):
        return visited_children[0]

    def visit_operand(self, node, visited_children):
        return visited_children[0]

    def visit_alg_start(self, node, visited_children):
        return visited_children[0]

    def visit_number_literal(self, node, visited_children):
        return visited_children[0]

    def visit_array_index(self, node, visited_children):
        return visited_children[0]

    # this passes through any nodes for which we don't have a visit_smth(...) method defined
    def generic_visit(self, node, visited_children):

        return visited_children or node

    def parse(self, parsed_data, line_offset, column_offset):
        self.line_offset   = line_offset
        self.column_offset = column_offset
        IR = super().visit(parsed_data)

        return IR

#-----------------------------------------------------------------------
#
#-----------------------------------------------------------------------


def parse_file(input_text):

    # get the absolute path of the main program script
    # (so we can get correct path of files we need to load)
    import os
    path = os.path.dirname(os.path.realpath(__file__))

    grammar = Grammar(open(path+ "/function_grammar.ini", "r").read())
    function_tree_visitor = TreeVisitor()

    function_matches = re.finditer("function.*?end function", input_text, re.DOTALL)

    # parse functions separately:

    parsed_functions = []

    for function_text in function_matches:

        text  = function_text.group(0)
        start = function_text.start()
        end   = function_text.end()

        function_line_offset = input_text[:start].count("\n")
        function_column_offset = len (  (input_text[:start].split("\n"))[-1]  )

        try:
            parsed_functions.append ( {"text" : grammar.parse(text) , "line_offset" : function_line_offset, "column_offset" : function_column_offset} )
        except Exception as e:

            if type(e) == ParseError:
                # since we separated the source code into function texts, we need to
                # calculate the offset number of lines where errors occured:

                line_offset   = input_text[:start].count("\n")
                #   we get the length of text between current symbol and
                #   the closest newline ("\n") preceding the current function block:
                column_offset = 0

                # get the hopefully informative piece of text near the problematic place:
                piece = e.text[e.pos : min (len (e.text), e.pos + 10)]

                # put out our error message
                print ("Syntax error, unexpected symbol at line: "\
                                "%s, column: %s, \n %s" % (
                                                               line_offset + e.line(),
                                                               e.column() + column_offset,
                                                               piece))

                break

            else:
                raise e

    # translate functions separately:

    IRs = []

    for parsed_function in parsed_functions:
        parsed = function_tree_visitor.parse(
                                            parsed_function["text"] ,
                                            parsed_function["line_offset"],
                                            parsed_function["column_offset"]
                                            )
        # ~ IRs.append( parsed.emit_json(None) )
        IRs.append( parsed )

    # ~ return {"functions":IRs}
    return IRs


def main(args):
    return 0


if __name__ == '__main__':
    import sys
    sys.exit(main(sys.argv))
