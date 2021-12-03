[1mdiff --git a/sample/exporters/graphml.py b/sample/exporters/graphml.py[m
[1mindex 728acb7..d07d107 100644[m
[1m--- a/sample/exporters/graphml.py[m
[1m+++ b/sample/exporters/graphml.py[m
[36m@@ -130,7 +130,7 @@[m [mdef make_node(node):[m
     elif node["name"] == "LoopExpression":[m
 [m
         contents  = "".join([m
[31m-                            [make_node(node[field]) for field in ["init", "body", "preCondition"]][m
[32m+[m[32m                            [make_node(node[field]) for field in ["init", "body", "preCondition", "reduction"]][m
                             )[m
 [m
         contents += make_edges()[m
[1mdiff --git a/sample/exporters/json.py b/sample/exporters/json.py[m
[1mindex 1e52c26..e0ed33c 100644[m
[1m--- a/sample/exporters/json.py[m
[1m+++ b/sample/exporters/json.py[m
[36m@@ -911,7 +911,7 @@[m [mdef create_body_for_loop(node, retval, parent_node, slot, current_scope):[m
     json_nodes[ node.body_id ] = body[m
     copy_ports_and_params(body, retval["preCondition"])[m
     body["outPorts"] = [][m
[31m-    body["results"]  = [] [m
[32m+[m[32m    body["results"]  = [][m
 [m
     for i, param in enumerate(retval["init"]["results"]):[m
         body["outPorts"].append(make_port(i, node.body_id, param[1]["type"]))[m
[36m@@ -922,7 +922,6 @@[m [mdef create_body_for_loop(node, retval, parent_node, slot, current_scope):[m
         body["nodes"].extend(ast["nodes"])[m
         body["edges"].extend(ast["edges"] + ast["final_edges"])[m
 [m
[31m-    [m
     retval["body"] = body[m
 [m
 [m
[36m@@ -1013,7 +1012,7 @@[m [mdef export_loop_to_json (node, parent_node, slot, current_scope):[m
     create_test_for_loop(node, retval, parent_node, slot, current_scope)[m
     create_body_for_loop(node, retval, parent_node, slot, current_scope)[m
     create_ret_for_loop (node, retval, parent_node, slot, current_scope)[m
[31m-    [m
[32m+[m
     in_edges = [][m
     # make edges that connect the scope to whis node[m
     for n, param in enumerate(json_nodes[parent_node]["params"]):[m
[36m@@ -1021,16 +1020,16 @@[m [mdef export_loop_to_json (node, parent_node, slot, current_scope):[m
                         make_json_edge(parent_node, node.node_id,[m
                                        n,           n, parameter = True)[m
                        )[m
[31m-        [m
[32m+[m
     out_edges = [][m
[31m-    [m
[32m+[m
     for n, output in enumerate(json_nodes[parent_node]["outPorts"]):[m
          out_edges.append([m
                         make_json_edge(node.node_id, parent_node,[m
                                        n,            n,[m
                                        parent = True)[m
                        )[m
[31m-    [m
[32m+[m
     return dict([m
                 nodes       = [retval],[m
                 edges       = in_edges + out_edges,[m
