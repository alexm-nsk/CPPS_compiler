#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
#  json.py
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

# Implements exporting Node and it's descendants into JSON IR

#---------------------------------------------------------------------------------------------
# TODO use decorators for field name substitusions
import ast_.node


def function_gen_params(function):

    params = function.params
    nodeId = function.node_id

    ret_val = []

    for group in params:
        ret_val.extend([
            [var.name,
                dict(
                    nodeId = nodeId,
                    type = dict(location = var.location,
                                name = group["type"]["type_name"])
                )
            ]
            for var in group["vars"]
        ])
    return ret_val


def function_gen_out_ports(function):

    ret_types = function.ret_types
    if not ret_types:
        return []

    ret_val = []

    for n, r in enumerate(ret_types):

        ret_val += [dict(
                        nodeId = function.node_id,
                        type = dict(location = r["location"],
                                    name = r["type_name"]),
                        index = n
                    )]

    return ret_val


def function_gen_in_ports(function):

    arg_types = function.params

    if not arg_types:
        return []

    ret_val = []

    for arg_group in arg_types:

        for var in arg_group["vars"]:

            ret_val += [dict(
                            nodeId = function.node_id,
                            type = dict(location = var.location,
                                        name     = arg_group["type"]["type_name"]),
                            index = len(ret_val)
                        )]

    return ret_val


field_sub_table = dict(

    function_name = "functionName",
    node_id       = "id",
    if_           = "If",
    then          = "Then",
    else_         = "Else",
    condition     = "condition",

)


def export_function_to_json(function):

    ret_val = {}

    for field, value in function.__dict__.items():
        IR_name          = field_sub_table[field] if field in field_sub_table else field
        ret_val[IR_name] = value

    ret_val["nodes"] = function.nodes[0].emit_json()
    try:
        pass
    except:
        print ("JSON not implemented for %s yet! Node contents: %s"
                                % (type(function.nodes[0]), function.nodes[0]), "\n")

    ret_val["params"]   = function_gen_params( function ) if function.params else None

    ret_val["outPorts"] = function_gen_out_ports(function)
    ret_val["inPorts"]  = function_gen_in_ports (function)

    return ret_val


#---------------------------------------------------------------------------------------------
  # ~ {
          # ~ "id": "node11",
          # ~ "inPorts": [
            # ~ {
              # ~ "index": 0,
              # ~ "nodeId": "node14",
              # ~ "type": {
                # ~ "location": "1:14-1:15",
                # ~ "name": "integer"
              # ~ }
            # ~ }
          # ~ ],
          # ~ "location": "not applicable",
          # ~ "name": "Then",
          # ~ "nodes": [],
          # ~ "outPorts": [
            # ~ {
              # ~ "index": 0,
              # ~ "nodeId": "node14",
              # ~ "type": {
                # ~ "location": "not applicable",
                # ~ "name": "integer"
              # ~ }
            # ~ }
          # ~ ],
          # ~ "params": [
            # ~ [
              # ~ "M",
              # ~ {
                # ~ "index": 0,
                # ~ "nodeId": "node14",
                # ~ "type": {
                  # ~ "location": "1:14-1:15",
                  # ~ "name": "integer"
                # ~ }
              # ~ }
            # ~ ]
          # ~ ]
        # ~ },

def export_if_to_json(node):

    ret_val = {}

    for field, value in node.__dict__.items():
        IR_name          = field_sub_table[field] if field in field_sub_table else field
        ret_val[IR_name] = value

    ret_val["name"] = field_sub_table[ret_val["name"]]

    json_branches = []

    for br_name, branch in ret_val["branches"].items():
        json_branches.append(dict(
                                    name  = field_sub_table[br_name],
                                    nodes = [branch.emit_json()],

                                    #TODO
                                ))

    ret_val["branches"]  = json_branches
    ret_val["condition"] = node.condition.emit_json()

    return ret_val


#---------------------------------------------------------------------------------------------
# ~ {
  # ~ "name": "FunctionCall",
  # ~ "location": "5:8-5:15",
  # ~ "outPorts": [
    # ~ {
      # ~ "nodeId": "node9",
      # ~ "type": {
        # ~ "location": "1:35-1:42",
        # ~ "name": "integer"
      # ~ },
      # ~ "index": 0
    # ~ }
  # ~ ],
  # ~ "inPorts": [
    # ~ {
      # ~ "nodeId": "node9",
      # ~ "type": {
        # ~ "location": "1:19-1:26",
        # ~ "name": "integer"
      # ~ },
      # ~ "index": 0
    # ~ }
  # ~ ],
  # ~ "id": "node9",
  # ~ "callee": "Fib"
# ~ },


def export_call_to_json (node):

    ret_val = {}

    for field, value in node.__dict__.items():
        IR_name          = field_sub_table[field] if field in field_sub_table else field
        ret_val[IR_name] = value

    function_name = node.function_name.name

    called_function = ast_.node.Function.functions[function_name]

    ret_val = dict( id       = node.node_id,
                    callee   = function_name,
                    location = node.location,
                    name     = "FunctionCall",
                    # these have to be generated again,
                    # since we dont store them currently:
                    in_Ports = function_gen_in_ports(called_function),
                    out_Ports= function_gen_out_ports(called_function),
                   )
    return ret_val


def export_algebraic_to_json (node):
    #print (node)
    for operand in node.expression:
        print (operand.emit_json())
    print ("\n\n")
        # ~ try:
        # ~ except Exception as e:
            # ~ print ("\n\n\n", operand, str(e) ,"\n\n\n")
    return "Algebraic"


def export_identifier_to_json (node):
    return node.name

# ~ {
  # ~ "id": "node6",
  # ~ "location": "5:26-5:27",
  # ~ "name": "Literal",
  # ~ "outPorts": [
    # ~ {
      # ~ "index": 0,
      # ~ "nodeId": "node6",
      # ~ "type": {
        # ~ "location": "not applicable",
        # ~ "name": "integer"
      # ~ }
    # ~ }
  # ~ ],
  # ~ "value": 2
# ~ }

def export_literal_to_json (node):
    
    return dict(
                    id = node.node_id,
                    location = node.location,
                    outPorts = [
                                    dict(
                                            index = 0,
                                            nodeId = node.node_id,
                                            type = dict(
                                                        location = "not applicable",
                                                        name     = "integer" #TODO put the type here
                                                    )
                                        )
                                ],
                    value = node.value,                    
                )
                
# ~ {
# ~ "id": "node2",
# ~ "inPorts": [
  # ~ {
    # ~ "index": 0,
    # ~ "nodeId": "node2",
    # ~ "type": {
      # ~ "location": "not applicable",
      # ~ "name": "integer"
    # ~ }
  # ~ },
  # ~ {
    # ~ "index": 1,
    # ~ "nodeId": "node2",
    # ~ "type": {
      # ~ "location": "not applicable",
      # ~ "name": "integer"
    # ~ }
  # ~ }
# ~ ],
# ~ "location": "2:5-2:10",
# ~ "name": "Binary",
# ~ "operator": "<",
# ~ "outPorts": [
  # ~ {
    # ~ "index": 0,
    # ~ "nodeId": "node2",
    # ~ "type": {
      # ~ "location": "not applicable",
      # ~ "name": "boolean"
    # ~ }
  # ~ }
# ~ ]
# ~ },

operator_type_map = {
    "<" : "boolean",
    ">" : "boolean",
    "+" : "integer",
    "-" : "integer",    
}

def export_bin_to_json (node):
     return dict(
                    id = node.node_id,
                    name = "Binary",
                    operator = node.operator,
                    location = node.location,
                    
                    inPorts  = [dict (index = n, nodeId = node.node_id, type = {"location":"not applicable", "name" : operator_type_map[node.operator]})
                                for n in range(2)],
                                
                    outPorts = [
                                    dict(
                                            index = 0,
                                            nodeId = node.node_id,
                                            type = dict(
                                                        location = "not applicable",
                                                        name     = "integer" #TODO put the type here
                                                    )
                                        )
                                ],
                )
