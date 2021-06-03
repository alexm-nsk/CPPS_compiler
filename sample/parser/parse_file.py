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
from ast_.node import Node
from ast_.edge import Edge

from sisal_type.sisal_type import *

import parser.arithmetic_helpers

# a quick debugging thing to stop the program on the spot
def exit():
    import sys
    sys.exit(0)

# connect recursive objects like
#       args_groups_list = arg_def_group (_ ";" _ arg_def_group)*
# into one array-list

def unpack_rec_list(node):
    return [node[0]]    +    [r[-1] for r in node[1]]

#--------------------------------------------------------------------------------
# get to the contents of [[[...[ ... ]]
# ~ def unwrap_list(list_):

    # ~ #while type(list_) == list and type(list_[0]) == list:
     # ~ #   list_ = list_[0]

    # ~ while type(list_) == list and len(list_) <=1 :
        # ~ list_ = list_[0]

    # ~ return list_

#----------------------------------------------------
#
# TreeVisitor class that allows us to go through
# everything the parser has found
#
# We go through separate strings containing each function
#
#----------------------------------------------------

class TreeVisitor(NodeVisitor):

    # rule: type_list     = type (_ "," _ type)*
    # rule: type          = ("array" _ "[" _ type  _"]") / std_type
    def visit_type(self, node, visited_children):

        child_type = type(visited_children[0])

        if child_type == str:
            return node.text
        elif child_type == list:
            item_type = visited_children[0][4]
            return SisalArray(item_type)

    # rule: std_type      = "integer" / "real"
    def visit_std_type(self, node, visited_children):
        return node.text

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
        type_name = visited_children[4]
        var_names = visited_children[0]

        return {"type_name" :type_name, "var_names" : var_names}

    # rule: args_groups_list = (arg_def_group (_ ";" _ arg_def_group)*) / _
    def visit_args_groups_list(self, node, visited_children):

        if len(visited_children)>1:
            return unpack_rec_list(visited_children)
        else:

            return visited_children[0]

    # rule: function_retvals   = ("returns" _ type_list) / _
    def visit_function_retvals(self, node, visited_children):

        if (visited_children != [None]):
            return unpack_rec_list(visited_children[0][2])
        else:
            return None

    # just return the operation's string
    def visit_bin_op(self, node, visited_children):
        return node.text
        
    # rule: bin = operand _ bin_op _ operand
    def visit_algebraic(self, node, visited_children):
        if len(visited_children) == 1:
            return visited_children[0][0]
        else:

            retval = visited_children[0]
            
            for r in visited_children[1]:
                retval.append(r[-3])
                retval.extend(r[-1])
            print (retval)
            return retval

    # rule: call               = !("function" _) identifier _ lpar _ args_list _ rpar
    def visit_call(self, node, visited_children):
        args = unpack_rec_list(visited_children[5])
                
        function_name = visited_children[1]#["identifier"]

        print ("args:", args)
        return {"functionName" : function_name, "args" : args}

    # rule: number             = ~"[0-9]+"
    def visit_number(self, node, visited_children):
        # all we need
        return node.text

    def visit_identifier(self, node, visited_children):
        return node.text

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

        function_name = visited_children[3]
        args          = visited_children[7]
        ret_type      = visited_children[9]
        body          = visited_children[13]

        #print ("body:",body)
        #print (f"name: {function_name}\nargs: {args}\nret_type: {ret_type}\n")

        return [function_name, args, ret_type, body]

    #----------------------------------------------------
    #
    #----------------------------------------------------
    # rule: if_else       = "if" _ exp _ "then" _ exp _ "else" _ exp _ "end if"

    def visit_if_else(self, node, visited_children):
        condition_node =  visited_children[2]  
        then_node      =  visited_children[6]  
        else_node      =  visited_children[10] 
        print({"cond " : condition_node, "then" : then_node, "else": else_node})
        return {"cond " : condition_node, "then" : then_node, "else": else_node}

    #----------------------------------------------------
    #
    #----------------------------------------------------
    def visit_brackets_algebraic(self, node, visited_children):
        return visited_children[2]
        return "brackets %s" % str(visited_children[2]) 

    def visit_exp(self, node, visited_children):
        return visited_children[0]
        
    # this passes through any nodes for which we don't have a visit_smth(...) method defined
    def generic_visit(self, node, visited_children):
        return visited_children or node

    def translate(self, parsed_data):
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

        try:
            parsed_functions.append ( grammar.parse(text) )
        except Exception as e:

            if type(e) == ParseError:
                # since we separated the source code into function texts, we need to
                # calculate the offset number of lines where errors occured:

                line_offset   = text[:start].count("\n")
                #   we get the length of text between closest newline preceding
                #   the current function block:
                column_offset = len( (text[:start].split("\n"))[-1] )

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
        IRs.append( function_tree_visitor.translate(  parsed_function  ) )

    #return IRs


def main(args):
    return 0


if __name__ == '__main__':
    import sys
    sys.exit(main(sys.argv))
