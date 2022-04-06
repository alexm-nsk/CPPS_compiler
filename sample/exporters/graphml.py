#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
#  graphml.py
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
from exporters.json    import *

nodemap = []

#indent text within another block for propper nesting
def indent(string):
    indentation = "  "
    return (indentation + string.replace("\n", "\n" + indentation))#.strip()

def make_document(content):
    document = '<?xml version="1.0" encoding="UTF-8"?>\n'\
           '<graphml xmlns="http://graphml.graphdrawing.org/xmlns"\n\n'\
           '  xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"\n'\
           '  xsi:schemaLocation="http://graphml.graphdrawing.org/xmlns\n'\
           '    http://graphml.graphdrawing.org/xmlns/1.0/graphml.xsd">\n\n'\
           '    <key id="type" for="node" attr.name="nodetype" attr.type="string"/>\n'\
           '    <key id="location" for="node" attr.name="location" attr.type="string" />\n\n\n'\
           '  %s\n'\
           '\n\n</graphml>' % indent(content)
    document = re.sub("\n\s*\n", "\n", document)
    return document

def get_type(type_):
    if "name" in type_:
        return type_["name"]
    else:
        return "array of " + get_type(type_["element"])

def make_edge(from_ , to, src_port, dst_port, type):
    return f'<edge source="{from_}" target="{to}" sourceport="{src_port}" targetport="{dst_port}">\n'\
         f'  <data key="type">{get_type(type)}</data>\n'\
         f'</edge>'\

props_to_save = { #name in graphml: #name in IR node:
                  #   ↓                     ↓
                    "type":         "name",
                    "functionName": "functionName",
                    "value":        "value",
                    "operator":     "operator",
                    "location":     "location",
                    "callee":       "callee",
                }

def make_graph(id, contents):
    return f'<graph id="{id}" edgedefault="directed">\n{ indent(contents) }\n</graph>'


def make_node(node):

    def is_parent(n1, n2):
        global nodemap
        if not "nodes" in nodemap[n1]:
            return False
        if any([n for n in nodemap[n1]["nodes"] if n["id"]==n2]):
            return True
        return False

    def make_edges():
        edges_string = ""
        if "edges" in node:
            for e in node["edges"]:
                source_port_type = "in"  if is_parent(e[0]["nodeId"], e[1]["nodeId"]) else "out"
                target_port_type = "out" if is_parent(e[1]["nodeId"], e[0]["nodeId"]) else "in"

                if e[0]["nodeId"] == e[1]["nodeId"]:
                        source_port_type = "in"
                        target_port_type = "out"

                edges_string += "\n" + make_edge(
                e[0]["nodeId"],e[1]["nodeId"],
                source_port_type + str(e[0]["index"])
                , target_port_type + str(e[1]["index"]),
                e[1]["type"])

        return edges_string

    props_str =  "\n".join(
                    [f'<data key=\"{key}\">{str(node[ir_name]).replace("<", "&lt;").replace(">", "&gt;")}</data>'
                    for key, ir_name in props_to_save.items()
                    if ir_name in node])

    ports_str = ""
    if "inPorts" in node:
        ports_str =  "".join(
                    [f'<port name=\"in{n}\" type=\"{ get_type (port["type"]) }\"/>\n'
                        for n, port in enumerate(node["inPorts"])]
                   )

    if "outPorts" in node:
        ports_str +=  "\n".join(
                    [f'<port name=\"out{n}\" type=\"{ get_type (port["type"]) }\"/>'
                        for n, port in enumerate(node["outPorts"])]
                   )

    if "nodes" in node and node["nodes"]:
        contents = "\n".join([make_node(node) for node in node["nodes"]])
        contents += make_edges()
        # ~ print (contents)
        contents = make_graph(node["id"]+"_graph", contents)
    #TODO make test for "If" here: (and add join below)
    elif "branches" in node:
        contents  = make_node(node["condition"])
        contents += make_node(node["branches"][0]) + make_node(node["branches"][1])
        contents += make_edges()
        contents  = make_graph(node["id"]+"_graph", contents)
    elif node["name"] == "LoopExpression":

        contents  = "".join(
                            [make_node(node[field]) for field in ["init", "body", "preCondition", "reduction"]]
                            )

        contents += make_edges()
        contents  = make_graph(node["id"]+"_graph", contents)
    elif node["name"] == "Let":

        contents  = "".join(
                            [make_node(node[field]) for field in ["init", "body"]]
                            )

        contents += make_edges()
        contents  = make_graph(node["id"]+"_graph", contents)
    else:
        contents = make_edges()
        if contents:
            contents = make_graph(node["id"]+"_graph", contents)
# ~ init
# ~ preCondition
# ~ body
# ~ reduction

    return f'<node id=\"{node["id"]}\">\n'\
           f'{indent(props_str)}\n'\
           f'{indent(ports_str)}\n'\
           f'{indent(contents)}\n'\
           f'</node>\n'


def emit(IR, nodes):
    global nodemap, json_nodes
    nodemap = json_nodes

    graph = ""
    for ir in IR:
        graph    += make_graph("id", make_node(ir.emit_json(None))) + "\n"

    document = make_document(graph)

    return document

def main(args):
    return 0

if __name__ == '__main__':
    import sys
    sys.exit(main(sys.argv))

def export_function_to_graphml(node, parent_node):

    global nodemap, json_nodes
    nodemap = json_nodes

    graph = make_graph("id", make_node(node.emit_json(None)))

    return graph
