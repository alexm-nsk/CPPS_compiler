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

import re

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

        start_row    = text[:node.start].count("\n") + 1 # lines have to start from "1"
        start_column = len (  (text[:node.start].split("\n"))[-1]  )

        if start_row == 1: start_column += self.column_offset

        end_row      = text[:node.end].count("\n") + 1  # lines have to start from "1"
        end_column   = len (  (text[:node.end].split("\n"))[-1]  )

        if end_row == 1: end_row += self.column_offset

        return "{}:{}-{}:{}".format(start_row + self.line_offset,
                                    start_column,
                                    end_row + self.line_offset,
                                    end_column)


    # rule: type_list     = type (_ "," _ type)*
    # rule: type          = ("array" _ "[" _ type  _"]") / std_type
    def visit_type(self, node, visited_children):

        child_type = type(visited_children[0])

        if child_type == dict:
            return visited_children[0]

        elif child_type == list:
            item_type = visited_children[0][4]
            #return str()
            return dict(type_name = f"Array[{item_type}]", location = self.get_location(node))

    # rule: std_type      = "integer" / "real"
    def visit_std_type(self, node, visited_children):

        return dict(type_name = node.text, location = self.get_location(node))

    def visit__(self, node, visited_children):
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
        #print ("Binary: ",node.text ,self.get_location(node))
        return dict(location  = self.get_location(node),
                    operation = node.text)

    # rule: algebraic          = (operand) (_ bin_op _ algebraic)*
    def visit_algebraic(self, node, visited_children):

        if issubclass(type(visited_children[0][0]), Node):

            return visited_children[0][0]
        else:
            retval = visited_children[0]
            for r in visited_children[1]:
                retval.append(r[-3])
                retval.extend(r[-1])

        return dict (name = "algebraic",
                     expression = retval
                    )

    # rule: call               = !("function" _) identifier _ lpar _ args_list _ rpar
    def visit_call(self, node, visited_children):

        args = unpack_rec_list(visited_children[5])

        function_name = visited_children[1]

        ret_val = Call(**dict(function_name = function_name,
                              args = args,
                              location = self.get_location(node))
                          )

        return ret_val

    # rule: number             = ~"[0-9]+"
    def visit_number(self, node, visited_children):
        # all we need
        return node.text

    def visit_identifier(self, node, visited_children):
        return dict(name = node.text, location = self.get_location(node))

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
        name          = visited_children[ 3 ]["name"] #this is an identifier,  so we get it's name
        ret_types     = visited_children[ 9  ],
        if ret_types:
           ret_types = ret_types[0] # TODO this is a crutch, fix this

        function_body = visited_children[ 13 ]

        params = dict(
                        name          = "Lambda",
                        function_name = name,
                        nodes         = [ function_body ],
                        location      = self.get_location(node),
                        params        = visited_children[7],
                        ret_types     = ret_types
                      )

        function = Function(**params)

        return function


    #----------------------------------------------------
    #
    #----------------------------------------------------
    # rule: if       = "if" _ exp _ "then" _ exp _ "else" _ exp _ "end if"

    def visit_if(self, node, visited_children):

        condition_node = visited_children[2]
        then_node      = visited_children[6]
        else_node      = visited_children[10]

        branches = dict(then = then_node, else_ = else_node)

        return If(**dict(
                        branches  = branches,
                        condition =  condition_node,
                    ))

    #----------------------------------------------------
    #
    #----------------------------------------------------
    def visit_brackets_algebraic(self, node, visited_children):
        return visited_children[2]

    def visit_exp(self, node, visited_children):
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
                #   we get the length of text between closest newline preceding
                #   the current function block:
                column_offset = 0#len( (text[:start].split("\n"))[-1] )

                # get ther hopefully informative piece of text near the problematic place:
                piece = e.text[e.pos : min (len (e.text), e.pos + 10)]

                # put out our error message
                print ("Syntax error, unexpected symbol at line: "\
                                "%s, column: %s, \n %s" % (
                                                               line_offset + e.line(),
                                                               e.column() + column_offset,
                                                               piece))

                break

            else:
                print (str(e))

    # translate functions separately:

    IRs = []

    for parsed_function in parsed_functions:
        parsed = function_tree_visitor.parse(  parsed_function["text"] , parsed_function["line_offset"], parsed_function["column_offset"] )
        IRs.append( parsed.emit_json() )

    return {"functions":IRs}


def main(args):
    return 0


if __name__ == '__main__':
    import sys
    sys.exit(main(sys.argv))
