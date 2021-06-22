#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
#  node.py
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

# props to cover
# ~ self.props.location
# ~ self.props.nodes
# ~ self.props.edges
# ~ self.props.name
# ~ self.props.out_ports
# ~ self.props.in_ports
# ~ self.props.id
# ~ self.props.params
# ~ self.props.function_name

from exporters.json    import *

class Node:

    node_counter = 0

    def get_node_id():

        Node.node_counter += 1
        return "node" + str(Node.node_counter)

    def __init__(self, *args, **kwargs):

        self.node_id = Node.get_node_id()
        # TODO consider list of allowed props (https://stackoverflow.com/questions/8187082/how-can-you-set-class-attributes-from-variable-arguments-kwargs-in-python)
        self.__dict__.update(kwargs)

    def emit_obj(self):
        pass

    def emit_json(self):
        pass

    def emit_cpp(self):
        pass

    def emit_llvm(self):
        pass

    def __repr__(self):
        return (str(self.__dict__))

    def __str__(self):
        return (str(self.__dict__))


class Function(Node):
    
    #static field storing name - function node pairs
    functions = {}
    
    def __init__(self, *args, **kwargs):
        super().__init__(**kwargs)
        Function.functions[self.function_name] = self

    def emit_json(self):
            return export_function_to_json(self)
        # ~ try:
        # ~ except:
            # ~ return "Error converting to JSON"


class Bin(Node):

    def __init__(self, *args, **kwargs):
        super().__init__(**kwargs)

class Call(Node):

    def __init__(self, *args, **kwargs):
        super().__init__(**kwargs)        

    def emit_json(self):        
        return export_call_to_json(self)

class If(Node):

    def __init__(self, *args, **kwargs):
        super().__init__(**kwargs)
        self.name = "if_"

    def emit_json(self):
        return (export_if_to_json(self))

class Algebraic(Node):

    def __init__(self, *args, **kwargs):
        super().__init__(**kwargs)
        self.name = "algebraic"

    def emit_json(self):
        return (export_algebraic_to_json(self))

class Identifier(Node):
    
    def __init__(self, *args, **kwargs):
        super().__init__(**kwargs)
        self.name = "identifier"

    def emit_json(self):
        return (export_identifier_to_json(self))
