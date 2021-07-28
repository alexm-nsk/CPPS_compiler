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

import ast_.node
import itertools
import pprint
import copy

from sisal_type.sisal_type import *

current_scope = ""
json_nodes = {}


#---------------------------------------------------------------------------------------------


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


#---------------------------------------------------------------------------------------------


def function_gen_params(function):

    params = function.params
    nodeId = function.node_id

    ret_val = []
    #print (params)
    for group in params:
        for n, var in enumerate(group["vars"]):
            ret_val += [
                [ var.name, emit_type_object(nodeId, group["type"], n, location = var.location) ]
            ]

    return ret_val


#---------------------------------------------------------------------------------------------


def function_gen_out_ports(function, node_id):

    ret_types = function.ret_types
    if not ret_types:
        return []

    ret_val = []

    for n, r in enumerate(ret_types):
        ret_val += [emit_type_object(node_id, r, n)]

    return ret_val


#---------------------------------------------------------------------------------------------


def function_gen_in_ports(function, node_id):

    arg_types = function.params

    if not arg_types:
        return []

    ret_val = []

    for arg_group in arg_types:
        for var in arg_group["vars"]:
            ret_val += [emit_type_object(node_id, arg_group["type"], len(ret_val), var.location)]

    return ret_val


#---------------------------------------------------------------------------------------------


field_sub_table = dict(

    function_name = "functionName",
    node_id       = "id",
    if_           = "If",
    then          = "Then",
    else_         = "Else",

)


#---------------------------------------------------------------------------------------------


def export_function_to_json(node, parent_node, slot = 0):

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

    ret_val["nodes"] = []
    ret_val["edges"] = []

    for n, child in enumerate(node.nodes):
        json_child = child.emit_json( node.node_id , n)

        ret_val["nodes"].extend(json_child["nodes"])
        ret_val["edges"].extend(json_child["edges"] + json_child["final_edges"])

        #TODO make emit_json return the mediator node

    json_nodes[node.node_id].update ( ret_val )

    # it's a top node, so no need to return edges upstream
    return ret_val


#---------------------------------------------------------------------------------------------


def export_if_to_json(node, parent_node, slot):

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

    # process the branches:___________________________________________________________________

    json_branches = []

    for br_name, branch in ret_val["branches"].items():

        inPorts  = copy.deepcopy(json_nodes[parent_node]["inPorts"])
        outPorts = copy.deepcopy(json_nodes[parent_node]["outPorts"])
        params   = copy.deepcopy(json_nodes[current_scope]["params"])

        #TODO check that outports number matches subnodes outputs
        # copy ports from parent node and change node_id in our copies to current node:
        for iP in inPorts: iP["nodeId"]         = branch["node_id"]
        for oP in outPorts: oP["nodeId"]        = branch["node_id"]
        for param in params: param[1]["nodeId"] = branch["node_id"]

        json_branch   =    dict(
                                    name     = field_sub_table[br_name],
                                    id       = branch["node_id"],
                                    inPorts  = inPorts,
                                    outPorts = outPorts,
                                    params   = params,
                                    # TODO make location here:
                                    #location = branch["nodes"].location,
                                    nodes    = [],
                                    edges    = []
                                )
        json_branches.append(json_branch)
        json_nodes[branch["node_id"]] = json_branch

        if len(branch["nodes"]) != len(outPorts):
            # connect all node locations (in src. code) into one string:
            locations = ", ".join(  list(map(lambda x: x.location, branch["nodes"]))  )


            raise Exception("Output port number doesn't match the number of return values! (nodes at "
                                            + locations + ")")

        for n, child_node in enumerate(branch["nodes"]):

            current_scope = branch["node_id"]
            children = child_node.emit_json(current_scope, n)
            current_scope = scope

            json_branch["edges"].extend(children["edges"] + children["final_edges"])
            json_branch["nodes"].extend(children["nodes"])


    ret_val["branches"]  = json_branches

    # process the condition:__________________________________________________________________

    #                             TODO  ↓          ↓ cond has to be boolean
    inPorts, outPorts = gen_ports(["integer"], ["boolean"], node.condition[0].node_id)

    ret_val["condition"] = dict(outPorts = outPorts,
                                inPorts  = inPorts ,
                                params   = json_nodes[current_scope]["params"])

    json_nodes[node.condition[0].node_id] = ret_val["condition"]

    current_scope = node.condition[0].node_id
    condition_children = node.condition[0].emit_json(node.condition[0].node_id)
    ret_val["condition"]["edges"] += condition_children["edges"] + condition_children["final_edges"]
    ret_val["condition"]["nodes"] =  condition_children["nodes"]
    current_scope = scope

    ret_val["condition"].update (dict(
                                        name       = "Condition",
                                        id         = node.condition[0].node_id,
                                        location   = node.condition[0].location,
                                    ))

    json_nodes[ node.node_id ].update( ret_val )

    # the edge that connects this (If) node with parent node:

    final_edge = make_json_edge(node.node_id, parent_node, 0, slot)

    return dict(nodes = [ret_val], edges = [], final_edges = [final_edge])


#---------------------------------------------------------------------------------------------


def export_call_to_json (node, parent_node, slot = 0):

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
                    params   = function_gen_params(called_function),
                   ))

    json_nodes[node.node_id] = ret_val

    args_nodes = []
    args_edges = []

    for i, arg in enumerate(node.args):
        children = arg[0].emit_json(node.node_id)
        args_nodes.extend ( children ["nodes"] )
        args_edges.extend ( children ["edges"] + children ["final_edges"])

    json_nodes[node.node_id].update ( ret_val )

    final_edge = make_json_edge(node.node_id, parent_node, 0, slot)
    return dict(nodes = [ret_val] + args_nodes, edges = args_edges , final_edges = [final_edge])


#---------------------------------------------------------------------------------------------


def gen_ports(ins, outs, node_id):

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


#---------------------------------------------------------------------------------------------


def return_type(left, right):
    if left == "real" or right == "real":
        return "real"
    else:
        return "integer"


#---------------------------------------------------------------------------------------------


def export_algebraic_to_json (node, parent_node, slot = 0):

    return_nodes = []
    return_edges = []
    exp = node.expression

    # recursively splits the algebraic expression until we have a few nodes connected with edges

    def get_nodes(chunk):

        # if only an operand left:
        if len(chunk) == 1:
            operand = chunk[0]

            # return parent node's (?) node_id
            if type(operand) == ast_.node.Identifier:
                # expecting the required value to come from the input

                name = operand.name

                # find the argument with identifier's name in scope's paramaeters:
                identifier_slot = -1
                for n, p in enumerate(json_nodes[current_scope]["params"]):
                    if(p[0] == name):
                        identifier_slot = n
                        type_ = p[1]["type"]["name"]
                        break
                # if we haven't found it, raise an exception:
                if identifier_slot == -1:
                    raise Exception("value {} ({}) not found in current scope".format (name, operand.location))

                return dict(id = current_scope, slot = identifier_slot, type = type_)
            else:

                nodes = operand.emit_json(current_scope)
                return_nodes.extend(nodes["nodes"])
                return_edges.extend(nodes["edges"])
                type_ = nodes["nodes"][0]["outPorts"][0]["type"]["name"]
                return dict(id = operand.node_id, slot = 0, type = type_)

        # if we still have some splitting to do:
        else:

            for n, operator in enumerate(chunk[1::2]):
                # the loop enumerates the list with even values skipped hence the index:
                index = n * 2 + 1

                left  = chunk[         : index ]
                right = chunk[index + 1:       ]

                op_json = operator.emit_json(parent_node)["nodes"]
                return_nodes.extend(op_json)

                left_node = get_nodes(left)
                right_node = get_nodes(right)

                return_edges.append(make_json_edge(left_node["id"],  operator.node_id, left_node["slot"], 0))
                return_edges.append(make_json_edge(right_node["id"], operator.node_id, right_node["slot"], 1))

                type_ = return_type(left_node["type"], right_node["type"])

                op_json[0]["outPorts"][0]["type"]["name"] = type_

                return dict(id = operator.node_id, slot = 0, type = type_)

    # the node that puts out result of this algebraic expression:
    final_node = get_nodes(exp)["id"]

    final_edge = make_json_edge(final_node, parent_node, 0, slot)

    # TODO is this necessary?
    if(not "edges" in json_nodes[parent_node]):
        json_nodes[parent_node]["edges"] = []

    return dict(nodes = return_nodes, edges = return_edges, final_edges = [final_edge])


#---------------------------------------------------------------------------------------------


def export_identifier_to_json (node, parent_node, slot = 0):

    # TODO check the case with loop to self in "then"

    parent = json_nodes[ parent_node ]
    final_edge = {}
    for n, (name, arg) in enumerate(parent["params"]):
        if name == node.name:
            edge = make_json_edge(current_scope,  parent["id"], n, 0)

    return dict(nodes = [], edges = [], final_edges = [edge])


#---------------------------------------------------------------------------------------------


def export_literal_to_json (node, parent_node, slot = 0):

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
    final_edge = make_json_edge(node.node_id, parent_node, 0, slot)
    return dict(nodes = [ret_val], edges = [], final_edges = [final_edge])

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


#---------------------------------------------------------------------------------------------


def export_bin_to_json (node, parent_node, slot = 0):

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
                                                        #TODO put the type here
                                                        name = operator_out_type_map[node.operator]
                                                    )
                                        )
                                ],
                )
    json_nodes[node.node_id] = ret_val


    return dict(nodes = [ret_val], edges = [])


#---------------------------------------------------------------------------------------------

# 1-dimentional ArrayAccess IR example:

  # ~ {
          # ~ "name": "ArrayAccess",
          # ~ "location": "2:4-2:7",
          # ~ "outPorts": [
            # ~ {
              # ~ "nodeId": "node2",
              # ~ "type": {
                # ~ "location": "1:26-1:30",
                # ~ "name": "real"
              # ~ },
              # ~ "index": 0
            # ~ }
          # ~ ],
          # ~ "inPorts": [
            # ~ {
              # ~ "nodeId": "node2",
              # ~ "type": {
                # ~ "location": "1:17-1:31",
                # ~ "element": {
                  # ~ "location": "1:26-1:30",
                  # ~ "name": "real"
                # ~ }
              # ~ },
              # ~ "index": 0
            # ~ },
            # ~ {
              # ~ "nodeId": "node2",
              # ~ "type": {
                # ~ "location": "not applicable",
                # ~ "name": "integer"
              # ~ },
              # ~ "index": 1
            # ~ }
          # ~ ],
          # ~ "id": "node2"
        # ~ }




# 2-dimentional ArrayAccess IR example:
 # ~ {
          # ~ "name": "ArrayAccess",
          # ~ "location": "2:4-2:7",
          # ~ "outPorts": [
            # ~ {
              # ~ "nodeId": "node2",
              # ~ "type": {
                # ~ "location": "1:26-1:40",
                # ~ "element": {
                  # ~ "location": "1:35-1:39",
                  # ~ "name": "real"
                # ~ }
              # ~ },
              # ~ "index": 0
            # ~ }
          # ~ ],
          # ~ "inPorts": [
            # ~ {
              # ~ "nodeId": "node2",
              # ~ "type": {
                # ~ "location": "1:17-1:40",
                # ~ "element": {
                  # ~ "location": "1:26-1:40",
                  # ~ "element": {
                    # ~ "location": "1:35-1:39",
                    # ~ "name": "real"
                  # ~ }
                # ~ }
              # ~ },
              # ~ "index": 0
            # ~ },
            # ~ {
              # ~ "nodeId": "node2",
              # ~ "type": {
                # ~ "location": "not applicable",
                # ~ "name": "integer"
              # ~ },
              # ~ "index": 1
            # ~ }
          # ~ ],
          # ~ "id": "node2"
        # ~ },
        
        # ~ {
          # ~ "name": "ArrayAccess",
          # ~ "location": "2:7-2:10",
          # ~ "outPorts": [
            # ~ {
              # ~ "nodeId": "node4",
              # ~ "type": {
                # ~ "location": "1:35-1:39",
                # ~ "name": "real"
              # ~ },
              # ~ "index": 0
            # ~ }
          # ~ ],
          # ~ "inPorts": [
            # ~ {
              # ~ "nodeId": "node4",
              # ~ "type": {
                # ~ "location": "1:26-1:40",
                # ~ "element": {
                  # ~ "location": "1:35-1:39",
                  # ~ "name": "real"
                # ~ }
              # ~ },
              # ~ "index": 0
            # ~ },
            # ~ {
              # ~ "nodeId": "node4",
              # ~ "type": {
                # ~ "location": "not applicable",
                # ~ "name": "integer"
              # ~ },
              # ~ "index": 1
            # ~ }
          # ~ ],
          # ~ "id": "node4"
        # ~ }



def export_array_access_to_json (node, parent_node, slot = 0):
    # TODO check with array's definition if types and dimensions match
    return dict(nodes = [], edges = [], final_edges = [])
