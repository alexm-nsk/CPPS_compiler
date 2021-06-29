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
# TODO everywhere "emit_json" is called check if it generated any edges and if so, add them
# TODO suggestion to put "linearization" of subtrees in there also (node decides whether it should break up the node list), make function that calls emit_json (node) and returns what's needed

import ast_.node

import pprint

current_scope = ""
json_nodes = {}


def make_json_edge(from_, to, src_index, dst_index, src_type = None, dst_type = None):
    #TODO retrieve src and dst type from the nodes here

    if src_type == None:
        try:
            src_type = json_nodes[from_]["outPorts"][src_index]["type"]["name"]
  #          print ("src:", src_type)
        except Exception as e:
            pass
            print ("no src ", str(e))

    if dst_type == None:
        try:
            dst_type = json_nodes[to]["inPorts"][dst_index]["type"]["name"]
 #           print ("dst:", dst_type)

        except Exception as e:
            pass
            print ("no dst",str(e))


    return [

            {
                "index"  : src_index,
                "nodeId" : from_,
                "type"   : {"location" : "TODO", "name" : src_type}
            },

            {
                "index"  : dst_index,
                "nodeId" : to,
                "type"   : {"location" : "TODO", "name" : dst_type}
            }

            ]

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
    #condition     = "Condition",

)


def export_function_to_json(function, parent_node):

    global current_scope, json_nodes

    current_scope = function.node_id
    ret_val = {}

    for field, value in function.__dict__.items():
        IR_name          = field_sub_table[field] if field in field_sub_table else field
        ret_val[IR_name] = value

    ret_val["params"]   = function_gen_params( function ) if function.params else None
    ret_val["outPorts"] = function_gen_out_ports(function)
    ret_val["inPorts"]  = function_gen_in_ports (function)

    ret_val.pop("ret_types")

    json_nodes[function.node_id] = ret_val
    #print (json_nodes[function.node_id]["params"])
    children = function.nodes[0].emit_json(function.node_id)

    ret_val["nodes"] = children["nodes"]
    ret_val["edges"] = children["edges"]


    json_nodes[function.node_id].update ( ret_val )

    # it's a top node, so no need, to return edges upstream
    return ret_val


#---------------------------------------------------------------------------------------------

def export_if_to_json(node, parent_node):

    ret_val = {}

    for field, value in node.__dict__.items():
        IR_name          = field_sub_table[field] if field in field_sub_table else field
        ret_val[IR_name] = value

    ret_val["name"] = field_sub_table[ret_val["name"]]

    json_branches = []

    for br_name, branch in ret_val["branches"].items():
        json_branch   =    dict(
                                    name  = field_sub_table[br_name],
                                    id    = branch.node_id,
                                    
                                    #TODO
                                    inPorts = json_nodes[parent_node]["inPorts"],
                                    outPorts = json_nodes[parent_node]["outPorts"]
                                )

        json_branches.append(json_branch)
        json_nodes[branch.node_id] = json_branch
        children = branch.emit_json(branch.node_id)
        json_branch["nodes"] = children["nodes"]

        if not "edges" in json_branch: json_branch["edges"] = []
        json_branch["edges"].extend(children["edges"])

    ret_val["branches"]  = json_branches

    condition_children = node.condition.emit_json(node.node_id)
    ret_val["condition"] = condition_children
    ret_val["condition"].update(dict(
                                        name       = "Condition",
                                        id         = node.condition.node_id,
                                        location   = node.condition.location,
                                        # TODO copy it from the scope, or derive from used identifiers
                                        parameters = json_nodes[current_scope]["params"],
                                    ))

    ret_val["id"] = node.node_id

    json_nodes[ node.node_id ] = ret_val

    return dict(nodes = [ret_val], edges = [])


#---------------------------------------------------------------------------------------------


def export_call_to_json (node, parent_node):

    ret_val = {}

    for field, value in node.__dict__.items():
        IR_name          = field_sub_table[field] if field in field_sub_table else field
        ret_val[IR_name] = value

    function_name = node.function_name.name

    called_function = ast_.node.Function.functions[function_name]

    json_nodes[node.node_id] = dict(inPorts = function_gen_in_ports(called_function),
                                    outPorts= function_gen_out_ports(called_function))

    ret_val = dict( id       = node.node_id,
                    callee   = function_name,
                    location = node.location,
                    name     = "FunctionCall",
                   )
    # TODO add edges (from arguments)
    json_nodes[node.node_id].update ( ret_val )
    return dict(nodes = [ret_val], edges = [])

#---------------------------------------------------------------------------------------------

def export_algebraic_to_json (node, parent_node):

    return_nodes = []
    return_edges = []
    exp = node.expression

    # recursively splits the algebraic expression until we have a few nodes connected with edges

    def get_nodes(chunk):

        # if only an operand left:
        if len(chunk) == 1:
            operand = chunk[0]
            #return parent node's (?) node_id
            if type(operand) == ast_.node.Identifier:
                return current_scope
            else:
                # TODO process edges too
                return_nodes.append(operand.emit_json(node.node_id)["nodes"])
                return operand.node_id

        # if we still have some splitting to do:
        else:

            for n, operator in enumerate(chunk[1::2]):
                # the loop enumerates the list with even values skipped hence the index:
                index = n * 2 + 1

                left  = exp[ :index]
                right = exp[index + 1: ]
                # TODO process edges too
                op_json = operator.emit_json(node.node_id)["nodes"]
                return_nodes.append(op_json)

                left_node = get_nodes(left)
                right_node = get_nodes(right)

                return_edges.append(make_json_edge(left_node,  operator.node_id, 0, 0))
                return_edges.append(make_json_edge(right_node, operator.node_id, 0, 1))

                return operator.node_id

    get_nodes(exp)
    #print (return_edges)
    #print (dict(nodes = return_nodes, edges = return_edges))
    return dict(nodes = return_nodes, edges = return_edges)


def export_identifier_to_json (node, parent_node):
    # TODO check the case with loop to self in "then"
    parent = json_nodes[ parent_node ]
    parent["edges"] = [make_json_edge(current_scope,  parent["id"], 0, 0)]
    return dict(nodes = [], edges = [])


def export_literal_to_json (node, parent_node):

    ret_val = dict(
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
    json_nodes[node.node_id] = ret_val
    return dict(nodes = [ret_val], edges = [])

operator_out_type_map = {
    "<" : "boolean",
    ">" : "boolean",
    "+" : "integer",
    "-" : "integer",
}

operator_in_type_map = {
    "<" : "integer",
    ">" : "integer",
    "+" : "integer",
    "-" : "integer",
}

def export_bin_to_json (node, parent_node):
    ret_val = dict(
                    id = node.node_id,
                    name = "Binary",
                    operator = node.operator,
                    location = node.location,

                    inPorts  = [dict (index = n, nodeId = node.node_id, type = {"location":"not applicable", "name" : operator_in_type_map[node.operator]})
                                for n in range(2)],

                    outPorts = [
                                    dict(
                                            index = 0,
                                            nodeId = node.node_id,
                                            type = dict(
                                                        location = "not applicable",
                                                        name = operator_out_type_map[node.operator] #TODO put the type here
                                                    )
                                        )
                                ],
                )
    json_nodes[node.node_id] = ret_val
    return dict(nodes = [ret_val], edges = [])
