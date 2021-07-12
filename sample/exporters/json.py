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
# TODO write "is_parent(node1, node2)"

#TODO redirect node in to out in "Then" (calculate port index from "parameters")

import ast_.node

import pprint

current_scope = ""
json_nodes = {}


def make_json_edge(from_, to, src_index, dst_index, parent = False):
    #TODO retrieve src and dst type from the nodes here

    dst_type = None

    try:
        src_type = json_nodes[from_]["outPorts"][src_index]["type"]["name"]
    except Exception as e:
        print ("no src ", str(e))


    try:
        if parent:
            dst_type = json_nodes[to]["outPorts"][dst_index]["type"]["name"]
        else:
            dst_type = json_nodes[to]["inPorts"][dst_index]["type"]["name"]

    except Exception as e:
        print ("no dst",str(e), from_, to)


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


def function_gen_out_ports(function, node_id):

    ret_types = function.ret_types
    if not ret_types:
        return []

    ret_val = []

    for n, r in enumerate(ret_types):

        ret_val += [dict(
                        nodeId = node_id,
                        type = dict(location = r["location"],
                                    name = r["type_name"]),
                        index = n
                    )]

    return ret_val


def function_gen_in_ports(function, node_id):

    arg_types = function.params

    if not arg_types:
        return []

    ret_val = []

    for arg_group in arg_types:

        for var in arg_group["vars"]:

            ret_val += [dict(
                            nodeId = node_id,
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

)


def export_function_to_json(node, parent_node):

    global current_scope, json_nodes

    current_scope = node.node_id
    ret_val = {}

    for field, value in node.__dict__.items():
        IR_name          = field_sub_table[field] if field in field_sub_table else field
        ret_val[IR_name] = value

    ret_val["params"]   = function_gen_params( node ) if node.params else None

    ret_val["inPorts"]  = function_gen_in_ports ( node , node.node_id)
    ret_val["outPorts"] = function_gen_out_ports( node , node.node_id)

    ret_val.pop("ret_types")

    # register this node:
    json_nodes[node.node_id] = ret_val

    children = node.nodes[0][0].emit_json( node.node_id )

    ret_val["nodes"] = children["nodes"]
    ret_val["edges"] = children["edges"]

    json_nodes[node.node_id].update ( ret_val )

    # edges that tranfer parameters to child nodes and recieve results from them:

    parameters_edge = make_json_edge(node.node_id, children["nodes"][0]["id"], 0, 0)
    ret_val_edge    = make_json_edge(children["nodes"][0]["id"], node.node_id, 0, 0)

    ret_val["edges"].append(ret_val_edge)
    ret_val["edges"].append(parameters_edge)

    # it's a top node, so no need to return edges upstream
    return ret_val


#---------------------------------------------------------------------------------------------

def export_if_to_json(node, parent_node):

    global current_scope
    scope = current_scope
    ret_val = {}

    # rename fields to name used in JSON IR using a rename dictionary (field_sub_table):
    for field, value in node.__dict__.items():
        IR_name          = field_sub_table[field] if field in field_sub_table else field
        ret_val[IR_name] = value

    ret_val["name"] = field_sub_table[ret_val["name"]]
    ret_val["id"]   = node.node_id

    # make ports for the top node of our 'If'
    ret_val["inPorts"]  = json_nodes[parent_node]["inPorts"]
    ret_val["outPorts"] = json_nodes[parent_node]["outPorts"]
    ret_val["location"] = node.location
    
    # register this node in the global dict:
    json_nodes[ node.node_id ] = ret_val

    # process the branches:____________________________________________________________________________

    json_branches = []

    for br_name, branch in ret_val["branches"].items():
        inPorts = json_nodes[parent_node]["inPorts"]
        outPorts = json_nodes[parent_node]["outPorts"]
        params  = json_nodes[current_scope]["params"]

        inPorts[0]["nodeId"]   = branch[0].node_id
        outPorts[0]["nodeId"]  = branch[0].node_id
        params[0][1]["nodeId"] = branch[0].node_id

        json_branch   =    dict(
                                    name     = field_sub_table[br_name],
                                    id       = branch[0].node_id,
                                    inPorts  = inPorts,
                                    outPorts = outPorts,
                                    params   = params,
                                    location = branch[0].location
                                )

        json_branches.append(json_branch)
        json_nodes[branch[0].node_id] = json_branch

        current_scope = branch[0].node_id

        children = branch[0].emit_json(branch[0].node_id)
        json_branch["nodes"] = children["nodes"]

        if not "edges" in json_branch: json_branch["edges"] = []
        json_branch["edges"].extend(children["edges"])

    ret_val["branches"]  = json_branches

    # process the condition:____________________________________________________________________________

    #                             TODO  ↓          ↓ cond has to be boolean
    inPorts, outPorts = genPorts(["integer"], ["boolean"], node.condition[0].node_id)

    ret_val["condition"] = dict(outPorts = outPorts, inPorts = inPorts )

    json_nodes[node.condition[0].node_id] = ret_val["condition"]

    current_scope = node.condition[0].node_id

    condition_children = node.condition[0].emit_json(node.condition[0].node_id)

    current_scope = scope

    ret_val["condition"].update (condition_children)

    ret_val["condition"].update (dict(
                                        name       = "Condition",
                                        id         = node.condition[0].node_id,
                                        location   = node.condition[0].location,
                                        params     = json_nodes[current_scope]["params"],
                                    ))

    json_nodes[ node.node_id ].update( ret_val )

    #current_scope = scope
    return dict(nodes = [ret_val], edges = [])
                                     #   ret_val["condition"]["edges"]
                                     # + [branch["edges"] for branch in ret_val["branches"]])


#---------------------------------------------------------------------------------------------


def export_call_to_json (node, parent_node):

    ret_val = {}

    for field, value in node.__dict__.items():
        IR_name          = field_sub_table[field] if field in field_sub_table else field
        ret_val[IR_name] = value

    function_name = node.function_name.name

    called_function = ast_.node.Function.functions[function_name]

    ret_val = dict(inPorts  = function_gen_in_ports(called_function, node.node_id),
                   outPorts = function_gen_out_ports(called_function, node.node_id))

    ret_val.update( dict(
                    id       = node.node_id,
                    callee   = function_name,
                    location = node.location,
                    name     = "FunctionCall",
                   ))

    json_nodes[node.node_id] = ret_val

    args_nodes = []
    args_edges = []

    for i, arg in enumerate(node.args):
        children = arg[0].emit_json(node.node_id)
        args_nodes.extend ( children ["nodes"] )
        args_edges.extend ( children ["edges"] )

    json_nodes[node.node_id].update ( ret_val )

    #if not json_nodes[parent_node].edges: json_nodes[parent_node].edges = []
    #json_nodes[parent_node]["edges"].append(make_json_edge(node.node_id, parent_node, 0, 0, True))
    #print (args_edges)
    return dict(nodes = [ret_val] + args_nodes, edges = args_edges)


#---------------------------------------------------------------------------------------------
def genPorts(ins, outs, node_id):

    inPorts  = []
    outPorts = []

    for n, inPort in enumerate(ins):
        inPorts.append (dict (
                                        index = n,
                                        nodeId = node_id,
                                        type = {"location":"not applicable",
                                                "name" : inPort}
                             )
                       )

    for n, outPort in enumerate(outs):
        outPorts.append (dict (
                                        index = n,
                                        nodeId = node_id,
                                        type = {"location":"not applicable",
                                                "name" : outPort}
                             )
                       )



    return (inPorts, outPorts)

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
                # expecting the required value to come from the input
                # TODO: check with multiple arguments (correct indices etc.)
                return current_scope
            else:
                # TODO process edges too
                nodes = operand.emit_json(parent_node)
                return_nodes.extend(nodes["nodes"])
                return_edges.extend(nodes["edges"])
                return operand.node_id

        # if we still have some splitting to do:
        else:

            for n, operator in enumerate(chunk[1::2]):
                # the loop enumerates the list with even values skipped hence the index:
                index = n * 2 + 1

                left  = chunk[ :index]
                right = chunk[index + 1: ]
                # TODO process edges too
                op_json = operator.emit_json(parent_node)["nodes"]
                return_nodes.extend(op_json)

                left_node = get_nodes(left)
                right_node = get_nodes(right)

                return_edges.append(make_json_edge(left_node,  operator.node_id, 0, 0))
                return_edges.append(make_json_edge(right_node, operator.node_id, 0, 1))

                return operator.node_id

    #the node that puts out result of this algebraic expression:
    final_node = get_nodes(exp)

    final_edge = make_json_edge(final_node, parent_node, 0,0)

    if(not "edges" in json_nodes[parent_node]):
        json_nodes[parent_node]["edges"] = []

    #json_nodes[parent_node]["edges"].append(final_edge)
    #print (final_edge, json_nodes[parent_node]["name"])
    return dict(nodes = return_nodes, edges = return_edges + [final_edge])


def export_identifier_to_json (node, parent_node):

    # TODO check the case with loop to self in "then"
    parent = json_nodes[ parent_node ]

    for name, arg in parent["params"]:
        if name == node.name:
            edge = make_json_edge(parent["id"],  parent["id"], 0, 0)

    parent["edges"] = [edge]
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
                                                    ),
                                        )
                                ],
                    value = node.value,
                    name = "Literal"
                )

    json_nodes[node.node_id] = ret_val
    return dict(nodes = [ret_val], edges = [])

operator_out_type_map = {
    "<" : "boolean",
    ">" : "boolean",
    "+" : "integer",
    "-" : "integer",
    "*" : "integer",
}

operator_in_type_map = {
    "<" : "integer",
    ">" : "integer",
    "+" : "integer",
    "-" : "integer",
    "*" : "integer",
}

def export_bin_to_json (node, parent_node):


    ret_val = dict(
                    id = node.node_id,
                    name = "Binary",
                    operator = node.operator,
                    location = node.location,

                    inPorts  = [dict (
                                    index = n,
                                    nodeId = node.node_id,
                                    type = {"location":"not applicable",
                                            "name" : operator_in_type_map[node.operator]}
                                    )
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
