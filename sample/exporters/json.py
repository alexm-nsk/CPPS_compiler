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

#TODO make fictitious brackets for <=, < , > , >=

#---------------------------------------------------------------------------------------------

import ast_.node
import copy

import sys, os

from ast_.port import *
from sisal_type.sisal_type import *
from ast_.node import *

json_nodes = {}


#---------------------------------------------------------------------------------------------


def make_port(index, node_id, type_):
    return dict(
                index = 0,
                nodeId = node_id,
                type = type_.emit_json() if not type(type_) == dict else type_
            )


#---------------------------------------------------------------------------------------------

def check_type_matching(c_src_type, c_dst_type, from_, to):

    if c_src_type != c_dst_type:
        src_node = ast_.node.Node.nodes[from_]
        dst_node = ast_.node.Node.nodes[to]

        summary = ""
        if current_scope == to:
            summary = "function or scope return type doesn't match the returned value (%s vs. %s)" \
                            % (c_src_type["name"], c_dst_type["name"])

        raise(Exception("Type mismatch between %s and %s (%s)" %
                    (src_node.location, dst_node.location, summary)))


#---------------------------------------------------------------------------------------------

# "parent" means destination node contains the source node so we connect source node's output
# with destination (parent) node's output instead of it's input

def make_json_edge(from_, to, src_index, dst_index, parent = False, parameter = False):
    dst_type = None

    try:
        port_type = "inPorts" if parameter else "outPorts"
        src_port = json_nodes[from_][port_type][src_index]
        src_type = src_port["type"]

    except Exception as e:
        print ("no src ", str(e))

    try:
        port_type = "outPorts" if parent else "inPorts"
        dst_port = json_nodes[to][port_type][dst_index]
        dst_type = dst_port["type"]

    except Exception as e:
        print (json_nodes[to][port_type],dst_index)
        print ("no dst",str(e),"\n\n", json_nodes[from_],"\n\n", json_nodes[to])
        exc_type, exc_obj, exc_tb = sys.exc_info()
        fname = os.path.split(exc_tb.tb_frame.f_code.co_filename)[1]
        print(exc_type, fname, exc_tb.tb_lineno)

    #check if parameters match:
    #make copies for comparison (we are going to remove locations)
    def remove_locations(dict_):
        for k,v in dict_.items():
            if k=="location": dict_[k]=""
            if type(v)==dict:
                dict_[k] = remove_locations(v)
        return (dict_)

    c_src_type = remove_locations(copy.deepcopy(src_type))
    c_dst_type = remove_locations(copy.deepcopy(dst_type))

    #check_type_matching(c_src_type, c_dst_type, from_, to)

    return [
                {
                    "index"  : src_index,
                    "nodeId" : from_,
                    "type"   : {"location" : "TODO", **src_type}
                },

                {
                    "index"  : dst_index,
                    "nodeId" : to,
                    "type"   : {"location" : "TODO", **dst_type}
                }
            ]


#---------------------------------------------------------------------------------------------


def function_gen_params(function):

    params = function.params
    node_id = function.node_id

    ret_val = []

    for group in params:
        for n, var in enumerate(group["vars"]):
            ret_val += [
                [ var.name, emit_type_object(node_id, group["type"], n, location = var.location) ]
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


def export_function_to_json(node, parent_node, slot = 0, current_scope = None):

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
        json_child = child.emit_json( node.node_id, n, current_scope)

        ret_val["nodes"].extend(json_child["nodes"])
        ret_val["edges"] += json_child["edges"] + json_child["final_edges"]

    json_nodes[node.node_id].update ( ret_val )

    # it's a top node, so no need to return edges upstream
    return ret_val


#---------------------------------------------------------------------------------------------

# duplicates ports and parameters from src_node and changes "nodeId" to target's id
def copy_ports_and_params(target, src_node):

    if "inPorts" in src_node:
        target["inPorts"]  = copy.deepcopy(src_node["inPorts"])
        for i in target["inPorts"]:
            i["nodeId"] = target["id"]

    if "outPorts" in src_node:
        target["outPorts"] = copy.deepcopy(src_node["outPorts"])
        for i in target["outPorts"]:
            i["nodeId"] = target["id"]

    if "params" in src_node:
        target["params"]   = copy.deepcopy(src_node["params"])
        for i in target["params"]:
            i[1]["nodeId"] = target["id"]

    return target

# adds ports and parameters from src_node and changes "nodeId" to target's id
def add_ports_and_params(target, src_node, inPorts = True, outPorts = True, params = True):

    def process_block(name, param = False):

        if name in src_node:
            if not name in target: target [name] = []
            new_items = copy.deepcopy(src_node[name])
            for n in new_items:
                if param:
                    n[1]["index"] += len(target[name])
                else:
                    n["index"] += len(target[name])
            target[name]  += new_items
            for i in target[name]:
                if param:
                    i[1]["nodeId"] = target["id"]
                else:
                    i["nodeId"] = target["id"]

    if inPorts:  process_block("inPorts")
    if outPorts: process_block("outPorts")
    if params:   process_block("params", True)

    return target


#---------------------------------------------------------------------------------------------


def create_out_ports_for_condition_node(number, node_id):
    return [ make_port(n , node_id, BooleanType()) for n in range(number) ]


#---------------------------------------------------------------------------------------------


def generate_conditions(ret_val, node, parent_node, slot, current_scope):

    ret_val["condition"]          = {}
    condition                     = ret_val["condition"]
    condition["id"]               = node.conditions["id"]
    json_nodes[ condition["id"] ] = condition

    condition["location"] = "not applicable"
    condition["name"]     = "Condition"

    copy_ports_and_params(condition, json_nodes[current_scope])
    condition["outPorts"] = create_out_ports_for_condition_node( len(node.conditions["nodes"]), condition["id"] )

    condition["edges"]    = []
    condition["nodes"]    = []


    for port, cond in enumerate(node.conditions["nodes"]):
        subnodes    = cond.emit_json( condition["id"], port, condition["id"] )
        nodes       = subnodes["nodes"]
        edges       = subnodes["edges"] + subnodes["final_edges"]
        condition ["nodes"].extend(nodes)
        condition ["edges"].extend(edges)


#---------------------------------------------------------------------------------------------


def generate_branches(ret_val, node, parent_node, slot, current_scope):

    ret_val["branches"] = []
    branches_list = []

    branches_list.append(dict(name = "Then", nodes = node.then_nodes["nodes"], id = node.then_nodes["id"]))

    for n, elseif in enumerate(node.elseif_nodes):
        branches_list.append(dict(name = "ElseIf", nodes = elseif["nodes"], id = elseif["id"]))

    branches_list.append(dict(name = "Else", nodes = node.else_nodes["nodes"], id = node.else_nodes["id"]))

    for branch in branches_list:

        id_   = branch["id"]

        new_branch = dict(
                            name     = branch["name"],
                            location = "",
                            outPorts = [],
                            inPorts  = [],
                            id       = id_,
                            params   = [],
                            edges    = [],
                            nodes    = []
                         )

        copy_ports_and_params(new_branch, json_nodes[parent_node])

        # get the start location of first node and the end location of last node and construct a
        # "location" for this branch

        location = ("|".join([br.location for br in branch["nodes"]])).split("-")
        new_branch["location"] = location[0] +"-"+ location[-1]

        json_nodes[id_] = new_branch

        for port, child_node in enumerate(branch["nodes"]):
            nodes_and_edges = child_node.emit_json(id_, port, id_)
            nodes = nodes_and_edges["nodes"]
            edges = nodes_and_edges["edges"] + nodes_and_edges["final_edges"]
            json_nodes[id_]["nodes"].extend(nodes)
            json_nodes[id_]["edges"].extend(edges)

        ret_val["branches"].append(new_branch)


#---------------------------------------------------------------------------------------------


def export_if_to_json(node, parent_node, slot, current_scope):

    ret_val = {}

    ret_val["name"]     = "If"
    ret_val["location"] = node.location
    ret_val["id"]       = node.node_id
    ret_val["edges"]    = []
    ret_val["nodes"]    = []

    copy_ports_and_params(ret_val, json_nodes[current_scope])

    # ~ # register this node in the global dict:
    json_nodes[ node.node_id ] = ret_val

    json_branches = []

    generate_conditions (ret_val, node, node.node_id, slot, current_scope)
    generate_branches   (ret_val, node, node.node_id, slot, current_scope)

    final_edge = make_json_edge(node.node_id, parent_node, 0, slot)

    return dict(nodes = [ret_val], edges = [], final_edges = [final_edge])


#---------------------------------------------------------------------------------------------


def export_call_to_json (node, parent_node, slot, current_scope):

    function_name = node.function_name.name

    if not function_name in ast_.node.Function.functions:
        raise Exception ("Function '%s' referenced to at %s not found" % (function_name, node.location))

    ret_val = {}

    for field, value in node.__dict__.items():
        IR_name          = field_sub_table[field] if field in field_sub_table else field
        ret_val[IR_name] = value


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
        children = arg.emit_json(node.node_id, 0, current_scope)
        args_nodes.extend ( children ["nodes"] )
        args_edges.extend ( children ["edges"] + children ["final_edges"] )

    json_nodes[node.node_id].update ( ret_val )

    final_edge = make_json_edge(node.node_id, parent_node, 0, slot, parent = (parent_node == current_scope))
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

#TODO make it return used variables (put them into the scope?)
def export_algebraic_to_json (node, parent_node, slot, current_scope):

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
                    var_name, var_type = p
                    if(var_name == name):
                        identifier_slot = n
                        type_ = var_type["type"]["name"]
                        break
                # if we haven't found it, raise an exception:
                if identifier_slot == -1:
                    raise Exception("value {} ({}) not found in current scope".format (name, operand.location))

                return dict(id = current_scope, slot = identifier_slot, type = type_, parameter = True)
            else:

                nodes = operand.emit_json(current_scope, 0, current_scope)
                return_nodes.extend(nodes["nodes"])
                return_edges.extend(nodes["edges"])
                type_ = nodes["nodes"][0]["outPorts"][0]["type"]["name"]
                return dict(id = operand.node_id, slot = 0, type = type_, parameter = False)

        # if we still have some splitting to do:
        else:
            operator = chunk[1]

            left  = chunk[  : 1]
            right = chunk[2 :  ]

            op_json = operator.emit_json(parent_node, 0, current_scope)["nodes"]
            return_nodes.extend(op_json)

            left_node = get_nodes(left)
            right_node = get_nodes(right)

            return_edges.append(
                    make_json_edge(left_node["id"],  operator.node_id,
                                   left_node["slot"],  0,
                                   parameter = left_node["parameter"]))

            return_edges.append(
                    make_json_edge(right_node["id"], operator.node_id,
                    right_node["slot"], 1,
                    parameter = right_node["parameter"]))

            type_ = return_type(left_node["type"], right_node["type"])

            op_json[0]["outPorts"][0]["type"]["name"] = type_

            return dict(id = operator.node_id, slot = 0, type = type_, parameter = False)

    # the node that puts out result of this algebraic expression:
    final_node = get_nodes(exp)["id"]
    #     Here we check if target node is the scope, this determines wether we target our output edge at "in" or "out" port
    final_edge = make_json_edge(final_node, parent_node, 0, slot, parent = (parent_node == current_scope))

    # TODO is this necessary?
    if(not "edges" in json_nodes[parent_node]):
        json_nodes[parent_node]["edges"] = []

    return dict(nodes = return_nodes, edges = return_edges, final_edges = [final_edge])


#---------------------------------------------------------------------------------------------


def export_identifier_to_json (node, parent_node, slot, current_scope):

    parent     = json_nodes[ parent_node ]
    scope      = json_nodes[ current_scope ]
    final_edge = {}
    #print (scope["params"])
    for n, (name, arg) in enumerate(scope["params"]):
        if name == node.name:
            edge = make_json_edge(current_scope,  parent["id"], n, slot,
                                  parameter = True,
                                  parent = (current_scope == parent_node))

    return dict(nodes = [], edges = [], final_edges = [edge])


#---------------------------------------------------------------------------------------------


def export_literal_to_json (node, parent_node, slot, current_scope):

    ret_val = dict(
                    id       = node.node_id,
                    location = node.location,
                    inPorts  = [],
                    outPorts = [ make_port(0, node.node_id, IntegerType() ) ],
                    value    = node.value,
                    name     = "Literal"
                  )

    json_nodes[node.node_id] = ret_val
    final_edge = make_json_edge(node.node_id, parent_node, 0, slot, parent = (parent_node == current_scope))
    return dict(nodes = [ret_val], edges = [], final_edges = [final_edge])


#---------------------------------------------------------------------------------------------


operator_out_type_map = {
    "<" : "boolean",
    ">" : "boolean",
    "+" : "integer",
    "-" : "integer",
    "*" : "integer",
    "<=" : "integer",
    ">=" : "integer",
}

operator_in_type_map = {
    "<" : "integer",
    ">" : "integer",
    "+" : "integer",
    "-" : "integer",
    "*" : "integer",
    "<=" : "integer",
    ">=" : "integer",
}


#---------------------------------------------------------------------------------------------


def export_bin_to_json (node, parent_node, slot, current_scope):

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


def export_arrayaccess_to_json (node, parent_node, slot, current_scope):
    # TODO check with array's definition if types and dimensions match

    # need to get array's type:
    params     = json_nodes[current_scope]["params"]
    scope_node = json_nodes[current_scope]

    if not params:
        raise Exception ("Error accessing the array: current scope doesn't have any variables", node.location)

    # find this array in scope's parameters:
    for array_index_in_params, p in enumerate(params):
        var_name, var_desc = p
        # params go in pairs["name", {description}], so p[0] is the name
        # and we compare it with name of arrray requested:
        if var_name == node.name:

            # need to lower dimensions of the array in "type" according to node's index:
            # i.e. array of array of integer -> array of integer
            # array_index is a number (beginning from zero) of a "[ index ]" block in "A[][index][]...[]"

            #check if array's measurements correspond to what we request in here:
            if "inline_indices" in node.__dict__: #means it's the first ArrayAccess node
                #number of [...] in the expression:
                access_length = len (node.inline_indices)
                defined_type = var_desc["type"]
                # check if there is enough dimensions in array's definition for the ammount of definitions we use
                # in our ArrayAccess:
                try:
                    for i in range(access_length):
                        defined_type = defined_type["element"] if "element" in defined_type else defined_type["type"]
                except:
                    raise Exception ("Array's (%s, %s) defined dimensions are smaller than ArrayAccess' dimensions (%s)." % (var_name,scope_node["location"], node.location))

            # strip "array of"s according to current dimension:
            type_ = var_desc["type"]
            for i in range (node.array_index):
                type_ = type_["element"]

            # form our dict that we will turn into json
            json_node = dict(
                                name = "ArrayAccess",
                                location = node.location,

                                inPorts = [dict(node_Id = node.node_id, type = type_, index = 0),
                                           dict(node_Id = node.node_id, type =
                                                    dict(location = "not applicable", name = "integer"),
                                           index = 1)],

                                outPorts = [dict(node_Id = node.node_id, type = type_["element"], index = 0)],

                                id = node.node_id
                            )

            json_nodes[node.node_id] = json_node

            index_nodes = node.index.emit_json( node.node_id, 1, current_scope)

            # we create final edge aimed at scope node only when it's a terminal (the final dimension's) ArrayAccess-node
            # i.e A[][][][*this one*]
            if not node.subarray:
                final_edges = [make_json_edge(node.node_id, current_scope, 0, slot, True)]
                array_input_edge = make_json_edge(parent_node, node.node_id, array_index_in_params, 0, False, parameter = False)
            else:
                final_edges = []
                array_input_edge = make_json_edge(parent_node, node.node_id, array_index_in_params, 0, False, parameter = True)

            # generate the rest of ArrayAccess's and connect them with edges:
            sub_nodes = []
            sub_edges = []

            if node.subarray:
                subarray = node.subarray.emit_json(node.node_id, slot, current_scope)
                sub_nodes = subarray["nodes"]
                sub_edges = subarray["edges"] + subarray["final_edges"]

            return dict(nodes       = [json_node] + index_nodes["nodes"] + sub_nodes,
                        edges       = index_nodes["edges"] + [array_input_edge] + index_nodes["final_edges"] + sub_edges,
                        final_edges = final_edges)

    # if we didn't find it, raise an exception:
    raise Exception ("Array %s not found in this scope!(%s)" % (node.name, node.location))


def pull_value_from_scope(name, current_scope, location):
    params = json_nodes[current_scope]["params"]
    for array_index_in_params, p in enumerate(params):
        var_name, var_desc = p
        if var_name == name.name:
            return var_desc["type"]

    raise Exception ("Identifier %s not found in this scope!(%s)" % (name, location))


def export_oldvalue_to_json (node, parent_node, slot, current_scope):

    type_ = pull_value_from_scope(node.name, current_scope, node.location)

    retval = dict (
                    outPorts = [make_port(0, node.node_id, type_)],
                    inPorts  = [make_port(0, node.node_id, type_)],
                    id       = node.node_id,
                    name     = "OldValue",
                    location = node.location
                )

    json_nodes[node.node_id] = retval
            
    return dict(nodes = [ retval ],
         edges = [ make_json_edge(current_scope, node.node_id, 0, 0, parameter = True) ],
         final_edges = [])
    


def export_sum_to_json(node, parent_node, slot, current_scope):

    return dict(
                 nodes = [],
                 edges = [],
                 final_edges = []
                )


def export_value_to_json(node, parent_node, slot, current_scope):

    retval = dict(
                    name     = "Returns",
                    location = "not applicable",
                    # TODO make appropriate type (get it from type of the variable we
                    # get the value of
                    outPorts = [make_port(0,node.node_id, IntegerType())],
                    inPorts  = [],
                    id       = node.node_id,
                    params   = []
                 )

    return dict(
                 nodes       = [retval],
                 edges       = [],
                 final_edges = []
                )

#TODO register new variables in the scope
def export_assignment_to_json(node, parent_node, slot, current_scope):

    value_ast = node.value.emit_json (parent_node, slot, current_scope)

    #TODO get type from what you get in value:
    # ~ create_parameter_definition(node.identifier.name, IntegerType(), current_scope)

    return value_ast
            # ~ dict(
                # ~ nodes       = [],
                # ~ edges       = [],
                # ~ final_edges = []
               # ~ )


#---------------------------------------------------------------------------------------------
# used only for loops
def create_parameter_definition(name, type_, node_id):
    node  = json_nodes[node_id]
    index = 0
    for p in node["params"]:
        p[1]["index"] += 1
    node["params"].insert(0, [ name, emit_type_object(node_id, type_, index, "not applicable") ] )


#---------------------------------------------------------------------------------------------
# used to create loop's initiaization
# init doesn't contain variables defined in it as parameters
# instead, they are placed in preCondition, body and reduction BEFORE function's arguments


def create_init_for_loop(node, retval, parent_node, slot, current_scope):

    nodes = []
    edges = []
    results = []
    out_ports = []
    in_ports = []
    node_id       = node.init_id
    json_nodes[node_id] = {"results" : [], "outPorts" : [], "inPorts" : [], "id" : node_id}

    add_ports_and_params(json_nodes[node_id], json_nodes[current_scope], outPorts = False, params = True)

    for n, i in enumerate(node.init):
        json_nodes[node_id]["outPorts"].append(make_port(n, node_id , IntegerType()))
        json_nodes[node_id]["results"].append(
                                    [
                                        i.identifier.name,
                                        dict(
                                               nodeId = node_id,
                                               type   = IntegerType().emit_json(),
                                               index = n
                                            )
                                    ] )

    # ~ for n, i in enumerate(node.init):
        init_ast = i.emit_json(node_id, n, node_id)
        nodes.append(init_ast["nodes"])
        edges.append(init_ast["edges"] + init_ast["final_edges"])

    json_nodes[node_id].update( dict(
                    name     = "Init",
                    location = "not applicable",
                    edges    = edges,
                    nodes    = nodes,
                ))


    retval["init"] = json_nodes[node_id]


#used to create loop's test
def create_test_for_loop(node, retval, parent_node, slot, current_scope):
    # retval is what is returned in export_loop_to_json that calls this function
    # to create the subnode for the loop test (see below)
    nodes = []
    edges = []

    #copy ports from the scope and put parameters' ports in front of them:
    in_ports = []
    for index, port in enumerate(json_nodes[node.init_id]["outPorts"] + json_nodes[current_scope]["inPorts"]):
        new_port = port;
        new_port["nodeId"] = node.test_id
        new_port["index"] = index
        in_ports.append(new_port)

    # add parameters the same way: first - init's variables, then - all scope's parameters
    params = []
    for index, param in enumerate(json_nodes[node.init_id]["results"] + json_nodes[current_scope]["params"]):
        new_param = param
        new_param[1]["nodeId"] = node.test_id
        new_param[1]["index"] = index
        params.append(new_param)

    test = dict(
                    name     = "PreCondition",
                    location = "not applicable",
                    outPorts = [make_port(0,node.test_id, BooleanType())],
                    inPorts  = in_ports,
                    id       = node.test_id,
                    params   = params,
                )

    # if nodes request parameters, they will get it from this (test) node as a scope
    json_nodes[node.test_id] = test
    sub_ir = node.loop_test[0].emit_json(node.test_id, 0, node.test_id)
    json_nodes[node.test_id]["nodes"] = sub_ir["nodes"]
    json_nodes[node.test_id]["edges"] = sub_ir["edges"] + sub_ir["final_edges"]

    retval["preCondition"] = test


#used to create loop's test
def create_body_for_loop(node, retval, parent_node, slot, current_scope):
    body = {"name" : "Body", "location": "not applicable", "id" : node.body_id}
    json_nodes[node.body_id] = body
    copy_ports_and_params(body, retval["preCondition"])
    # ~ print (body)
    print (node.loop_body[0].emit_json(node.body_id, 0, node.body_id))
    retval["body"] = body


def export_loop_to_json (node, parent_node, slot, current_scope):
    # ~ init
    # ~ loop_test
    # ~ loop_body
    # ~ ret

    retval = dict(
                    name      = "LoopExpression",
                    id        = node.node_id,
                    nodes     = [],#\
                    edges     = [],#/ both empty
                    location  = node.location
                 )

    copy_ports_and_params(retval, json_nodes[current_scope])
    json_nodes[node.node_id] = retval

    create_init_for_loop(node, retval, parent_node, slot, current_scope)
    create_test_for_loop(node, retval, parent_node, slot, current_scope)
    create_body_for_loop(node, retval, parent_node, slot, current_scope)

    #reduction_json = node.ret.emit_json(node.node_id, 0, current_scope)
    #retval["reduction"] = reduction_json["nodes"]

    return dict(
                nodes       = [retval],
                edges       = [],
                final_edges = [])
