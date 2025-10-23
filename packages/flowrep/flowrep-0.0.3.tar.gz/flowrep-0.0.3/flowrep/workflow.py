import ast
import builtins
import copy
import hashlib
import inspect
import json
import textwrap
from collections import deque
from collections.abc import Callable, Iterable
from functools import cached_property, update_wrapper
from typing import Any, Generic, TypeVar, cast

import networkx as nx
from networkx.algorithms.dag import topological_sort

from flowrep import tools

F = TypeVar("F", bound=Callable[..., object])


class FunctionWithWorkflow(Generic[F]):
    def __init__(self, func: F, workflow: dict[str, object], run) -> None:
        self.func = func
        self._semantikon_workflow: dict[str, object] = workflow
        self.run = run
        update_wrapper(self, func)  # Copies __name__, __doc__, etc.

    def __call__(self, *args, **kwargs):
        return self.func(*args, **kwargs)

    def __getattr__(self, item):
        return getattr(self.func, item)


def serialize_functions(data: dict[str, Any]) -> dict[str, Any]:
    """
    Separate functions from the data dictionary and store them in a function
    dictionary. The functions inside the data dictionary will be replaced by
    their name (which would for example make it easier to hash it)

    Args:
        data (dict[str, Any]): The data dictionary containing nodes and
            functions.

    Returns:
        tuple: A tuple containing the modified data dictionary and the
            function dictionary.
    """
    data = copy.deepcopy(data)
    if "nodes" in data:
        for key, node in data["nodes"].items():
            data["nodes"][key] = serialize_functions(node)
    elif "function" in data and not isinstance(data["function"], str):
        data["function"] = _get_function_metadata(data["function"])
    if "test" in data and not isinstance(data["test"]["function"], str):
        data["test"]["function"] = _get_function_metadata(data["test"]["function"])
    return data


class FunctionDictFlowAnalyzer:
    def __init__(self, ast_dict, scope):
        self.graph = nx.DiGraph()
        self.scope = scope  # mapping from function names to objects
        self.function_defs = {}
        self.ast_dict = ast_dict
        self._call_counter = {}
        self._control_flow_list = []
        self._parallel_var = {}

    @staticmethod
    def get_inputs_with_default(inp):
        if len(inp["defaults"]) == 0:
            return {}
        args = [tag["arg"] for tag in inp["args"]]
        defaults = []
        for d in inp["defaults"]:
            assert d["_type"] == "Constant"
            defaults.append(d["value"])
        return dict(zip(args[-len(defaults) :], defaults, strict=True))

    def analyze(self) -> tuple[nx.DiGraph, dict[str, Any]]:
        for arg in self.ast_dict.get("args", {}).get("args", []):
            if arg["_type"] == "arg":
                self._add_output_edge("input", arg["arg"])
        inputs = self.get_inputs_with_default(self.ast_dict.get("args", {}))
        return_was_called = False
        for node in self.ast_dict.get("body", []):
            assert not return_was_called
            self._visit_node(node)
            if node["_type"] == "Return":
                return_was_called = True
        return self.graph, self.function_defs, inputs

    def _visit_node(self, node, control_flow: str | None = None):
        if node["_type"] == "Assign":
            self._handle_assign(node, control_flow=control_flow)
        elif node["_type"] == "Expr":
            self._handle_expr(node, control_flow=control_flow)
        elif node["_type"] == "While":
            self._handle_while(node, control_flow=control_flow)
        elif node["_type"] == "For":
            self._handle_for(node, control_flow=control_flow)
        elif node["_type"] == "If":
            self._handle_if(node, control_flow=control_flow)
        elif node["_type"] == "Return":
            self._handle_return(node, control_flow=control_flow)
        else:
            raise NotImplementedError(f"Node type {node['_type']} not implemented")

    def _handle_return(self, node, control_flow: str | None = None):
        if not node["value"]:
            return
        if node["value"]["_type"] == "Tuple":
            for idx, elt in enumerate(node["value"]["elts"]):
                if elt["_type"] != "Name":
                    raise NotImplementedError("Only variable returns supported")
                self._add_input_edge(elt, "output", input_index=idx)
        elif node["value"]["_type"] == "Name":
            self._add_input_edge(node["value"], "output")

    def _handle_if(self, node, control_flow: str | None = None):
        assert node["test"]["_type"] == "Call"
        control_flow = self._convert_control_flow(control_flow, tag="If")
        self._parse_function_call(node["test"], control_flow=f"{control_flow}-test")
        for n in node["body"]:
            self._visit_node(n, control_flow=f"{control_flow}-body")
        for n in node.get("orelse", []):
            cf_else = "/".join(
                control_flow.split("/")[:-1]
                + [control_flow.split("/")[-1].replace("If", "Else") + "-body"]
            )
            self._visit_node(n, control_flow=cf_else)
            self._reconnect_parallel(cf_else, f"{control_flow}-body")
            self._register_parallel_variables(cf_else, f"{control_flow}-body")

    def _reconnect_parallel(self, control_flow: str, ref_control_flow: str):
        all_edges = list(self.graph.edges.data())
        for edge in all_edges:
            if (
                "control_flow" not in edge[2]
                or edge[2]["control_flow"] != control_flow
                or edge[2]["type"] == "output"
            ):
                continue
            var, ind = "_".join(edge[0].split("_")[:-1]), int(edge[0].split("_")[-1])
            while True:
                if any(
                    [
                        e[2].get("control_flow") == ref_control_flow
                        for e in self.graph.in_edges(f"{var}_{ind}", data=True)
                    ]
                ):
                    ind -= 1
                break
            if f"{var}_{ind}" != edge[0]:
                self.graph.add_edge(f"{var}_{ind}", edge[1], **edge[2])
                self.graph.remove_edge(edge[0], edge[1])

    def _register_parallel_variables(self, control_flow: str, ref_control_flow: str):
        data: dict[str, dict] = {control_flow: {}, ref_control_flow: {}}
        for edge in self.graph.edges.data():
            if (
                edge[2].get("control_flow", "") in [control_flow, ref_control_flow]
                and edge[2]["type"] == "output"
            ):
                data[edge[2]["control_flow"]][edge[1].rsplit("_", 1)[0]] = edge[1]
        for key in set(data[control_flow].keys()).intersection(
            data[ref_control_flow].keys()
        ):
            values = sorted([data[control_flow][key], data[ref_control_flow][key]])
            self._parallel_var[values[-1]] = [values[0]]
            if values[0] in self._parallel_var:
                self._parallel_var[values[-1]].extend(self._parallel_var.pop(values[0]))

    def _handle_while(self, node, control_flow: str | None = None):
        assert node["test"]["_type"] == "Call"
        control_flow = self._convert_control_flow(control_flow, tag="While")
        self._parse_function_call(node["test"], control_flow=f"{control_flow}-test")
        for n in node["body"]:
            self._visit_node(n, control_flow=f"{control_flow}-body")

    def _handle_for(self, node, control_flow: str | None = None):
        assert node["iter"]["_type"] == "Call"
        control_flow = self._convert_control_flow(control_flow, tag="For")

        unique_func_name = self._parse_function_call(
            node["iter"], control_flow=f"{control_flow}-iter"
        )
        self._parse_outputs(
            [node["target"]], unique_func_name, control_flow=control_flow
        )
        for n in node["body"]:
            self._visit_node(n, control_flow=f"{control_flow}-body")

    def _handle_expr(self, node, control_flow: str | None = None) -> str:
        value = node["value"]
        return self._parse_function_call(value, control_flow=control_flow)

    def _parse_function_call(self, value, control_flow: str | None = None) -> str:
        if value["_type"] != "Call":
            raise NotImplementedError(
                f"Only function calls allowed on RHS: {value['_type']}"
            )

        func_node = value["func"]
        if func_node["_type"] != "Name":
            raise NotImplementedError("Only simple functions allowed")

        func_name = func_node["id"]
        unique_func_name = self._get_unique_func_name(func_name)

        if func_name not in self.scope:
            raise ValueError(f"Function {func_name} not found in scope")

        self.function_defs[unique_func_name] = {"function": self.scope[func_name]}
        if control_flow is not None:
            self.function_defs[unique_func_name]["control_flow"] = control_flow

        arg_list = _get_function_keywords(self.scope[func_name])

        # Parse inputs (positional + keyword)
        for i, arg in enumerate(value.get("args", [])):
            self._add_input_edge(
                arg, unique_func_name, input_name=arg_list[i], control_flow=control_flow
            )
        for kw in value.get("keywords", []):
            self._add_input_edge(
                kw["value"],
                unique_func_name,
                input_name=kw["arg"],
                control_flow=control_flow,
            )
        return unique_func_name

    def _handle_assign(self, node, control_flow: str | None = None):
        unique_func_name = self._handle_expr(node, control_flow=control_flow)
        self._parse_outputs(
            node["targets"], unique_func_name, control_flow=control_flow
        )

    def _parse_outputs(
        self, targets, unique_func_name, control_flow: str | None = None
    ):
        if len(targets) == 1 and targets[0]["_type"] == "Tuple":
            for idx, elt in enumerate(targets[0]["elts"]):
                self._add_output_edge(
                    unique_func_name,
                    elt["id"],
                    output_index=idx,
                    control_flow=control_flow,
                )
        else:
            for target in targets:
                self._add_output_edge(
                    unique_func_name, target["id"], control_flow=control_flow
                )

    def _get_max_index(self, variable: str) -> int:
        index = 0
        while True:
            if len(self.graph.in_edges(f"{variable}_{index}")) > 0:
                index += 1
                continue
            break
        return index

    def _get_var_index(self, variable: str, output: bool = False) -> int:
        index = self._get_max_index(variable)
        if index == 0 and not output:
            raise KeyError(
                f"Variable {variable} not found in graph. "
                "This usually means that the variable was never defined."
            )
        if output:
            return index
        else:
            return index - 1

    def _add_output_edge(
        self, source: str, target: str, control_flow: str | None = None, **kwargs
    ):
        """
        Add an output edge from the source to the target variable.

        Args:
            source (str): The source node (function name).
            target (str): The target variable name.
            control_flow (str | None): The control flow tag, if any.
            **kwargs: Additional keyword arguments to pass to the edge.

        In the case of the following line:

        >>> y = f(x)

        This function will add an edge from the function `f` to the variable `y`.
        """
        versioned = f"{target}_{self._get_var_index(target, output=True)}"
        if control_flow is not None:
            kwargs["control_flow"] = control_flow
        self.graph.add_edge(source, versioned, type="output", **kwargs)

    def _add_input_edge(
        self, source: dict, target: str, control_flow: str | None = None, **kwargs
    ):
        """
        Add an input edge from the source variable to the target node.

        Args:
            source (dict): The source variable node.
            target (str): The target node (function name).
            control_flow (str | None): The control flow tag, if any.
            **kwargs: Additional keyword arguments to pass to the edge.

        In the case of the following line:

        >>> y = f(x)

        This function will add an edge from the variable `x` to the function `f`.
        """
        if source["_type"] != "Name":
            raise NotImplementedError(f"Only variable inputs supported, got: {source}")
        var_name = source["id"]
        if control_flow is not None:
            kwargs["control_flow"] = control_flow
        versioned = f"{var_name}_{self._get_var_index(var_name)}"
        self.graph.add_edge(versioned, target, type="input", **kwargs)
        if versioned in self._parallel_var:
            for key in self._parallel_var.pop(versioned):
                self.graph.add_edge(key, target, type="input", **kwargs)

    def _get_unique_func_name(self, base_name):
        i = self._call_counter.get(base_name, 0)
        self._call_counter[base_name] = i + 1
        return f"{base_name}_{i}"

    def _convert_control_flow(self, control_flow: str | None, tag: str) -> str:
        control_flow = "" if control_flow is None else f"{control_flow.split('-')[0]}/"
        counter = 0
        while True:
            if f"{control_flow}{tag}_{counter}" not in self._control_flow_list:
                self._control_flow_list.append(f"{control_flow}{tag}_{counter}")
                break
            counter += 1
        return f"{control_flow}{tag}_{counter}"


def _get_variables_from_subgraph(graph: nx.DiGraph, io_: str) -> set[str]:
    """
    Get variables from a subgraph based on the type of I/O and control flow.

    Args:
        graph (nx.DiGraph): The directed graph representing the function.
        io_ (str): The type of I/O to filter by ("input" or "output").
        control_flow (list, str): A list of control flow types to filter by.

    Returns:
        set[str]: A set of variable names that match the specified I/O type and
            control flow.
    """
    assert io_ in ["input", "output"], "io_ must be 'input' or 'output'"
    if io_ == "input":
        edge_ind = 0
    elif io_ == "output":
        edge_ind = 1
    return set(
        [edge[edge_ind] for edge in graph.edges.data() if edge[2]["type"] == io_]
    )


def _get_parent_graph(graph: nx.DiGraph, control_flow: str) -> nx.DiGraph:
    """
    Get parent body of the indented body

    Args:
        graph (nx.DiGraph): Full graph to look for the parent graph from
        control_flow (str): Control flow whose parent graph is to look for

    Returns:
        (nx.DiGraph): Parent graph
    """
    return nx.DiGraph(
        [
            edge
            for edge in graph.edges.data()
            if not _get_control_flow(edge[2]).startswith(control_flow)
        ]
    )


def _detect_io_variables_from_control_flow(
    graph: nx.DiGraph, subgraph: nx.DiGraph
) -> dict[str, list[str]]:
    """
    Detect input and output variables from a graph based on control flow.

    Args:
        graph (nx.DiGraph): The directed graph representing the function.

    Returns:
        dict[str, set]: A dictionary with keys "input" and "output", each
            containing a set

    Take a look at the unit tests for examples of how to use this function.
    """
    sg_body = nx.DiGraph(
        [
            edge
            for edge in subgraph.edges.data()
            if edge[0] != "input" and edge[1] != "output"
        ]
    )
    cf = sorted(
        [
            _get_control_flow(edge[2])
            for edge in sg_body.edges.data()
            if "control_flow" in edge[2]
        ]
    )
    if len(cf) == 0:
        return {"inputs": [], "outputs": []}
    assert all([cf[ii + 1].startswith(cf[ii]) for ii in range(len(cf) - 1)])
    parent_graph = _get_parent_graph(graph, cf[0])
    var_inp_1 = _get_variables_from_subgraph(graph=sg_body, io_="input")
    var_inp_2 = _get_variables_from_subgraph(graph=parent_graph, io_="output")
    var_out_1 = _get_variables_from_subgraph(graph=parent_graph, io_="input")
    var_out_2 = _get_variables_from_subgraph(graph=sg_body, io_="output")
    inputs = var_inp_1.intersection(var_inp_2)
    input_stem = [inp.rsplit("_", 1)[0] for inp in inputs]
    outputs = var_out_1.intersection(var_out_2)
    # Lines below are needed in order to add those outputs which are updated
    # during the control flow to the outputs. For example, the variable x in the
    # following workflow has to be in the outputs because it is updated in the
    # while loop, even though it is not used subsequently.
    # def f(x):
    #     while h(x):
    #         x, y = k(y)
    #     return y
    output_candidate = {}
    for edges in subgraph.edges:
        if edges[0] == "input" or edges[1] == "output":
            continue
        if edges[1].rsplit("_", 1)[0] in input_stem:
            output_candidate[edges[1].rsplit("_", 1)[0]] = edges[1]
    outputs.update(set(output_candidate.values()))
    return {
        "inputs": list(inputs),
        "outputs": list(outputs),
    }


def _extract_control_flows(graph: nx.DiGraph) -> list[str]:
    return list(set([_get_control_flow(edge[2]) for edge in graph.edges.data()]))


def _split_graphs_into_subgraphs(graph: nx.DiGraph) -> dict[str, nx.DiGraph]:
    return {
        control_flow: nx.DiGraph(
            [
                edge
                for edge in graph.edges.data()
                if _get_control_flow(edge[2]) == control_flow
            ]
        )
        for control_flow in _extract_control_flows(graph)
    }


def _get_subgraphs(graph: nx.DiGraph, cf_graph: nx.DiGraph) -> dict[str, nx.DiGraph]:
    """
    Separate a flat graph into subgraphs nested by control flows

    Args:
        graph (nx.DiGraph): Flat workflow graph
        cf_graph (nx.DiGraph): Control flow graph (cf. _get_control_flow_graph)

    Returns:
        dict[str, nx.DiGraph]: Subgraphs
    """
    subgraphs = _split_graphs_into_subgraphs(graph)
    for key in list(topological_sort(cf_graph))[::-1]:
        subgraph = subgraphs[key]
        node_name = "injected_" + key.replace("/", "_")
        io_ = _detect_io_variables_from_control_flow(graph, subgraph)
        for parent_graph_name in cf_graph.predecessors(key):
            parent_graph = subgraphs[parent_graph_name]
            for inp in io_["inputs"]:
                parent_graph.add_edge(
                    inp, node_name, type="input", input_name=_remove_index(inp)
                )
            for out in io_["outputs"]:
                parent_graph.add_edge(
                    node_name, out, type="output", output_name=_remove_index(out)
                )
        for inp in io_["inputs"]:
            subgraph.add_edge("input", inp, type="output")
        for out in io_["outputs"]:
            subgraph.add_edge(out, "output", type="input")
    return subgraphs


def _extract_functions_from_graph(graph: nx.DiGraph) -> set:
    function_names = []
    for edge in graph.edges.data():
        if edge[2]["type"] == "output" and edge[0] != "input":
            function_names.append(edge[0])
        elif edge[2]["type"] == "input" and edge[1] != "output":
            function_names.append(edge[1])
    return set(function_names)


def _get_control_flow_graph(control_flows: list[str]) -> nx.DiGraph:
    """
    Create a graph based on the control flows. The indentation level
    corresponds to the graph level. The higher level body is the parent node
    of the lower body.


    Args:
        control_flows (list[str]): All control flows present in a workflow

    Returns:
        nx.DiGraph: Control flow graph
    """
    cf_list = []
    for cf in control_flows:
        if cf == "":
            continue
        if "/" in cf:
            cf_list.append(["/".join(cf.split("/")[:-1]), cf])
        else:
            cf_list.append(["", cf])
    graph = nx.DiGraph(cf_list)
    if len(graph) == 0:
        graph.add_node("")
    return graph


def _function_to_ast_dict(node):
    if isinstance(node, ast.AST):
        result = {"_type": type(node).__name__}
        for field, value in ast.iter_fields(node):
            result[field] = _function_to_ast_dict(value)
        return result
    elif isinstance(node, list):
        return [_function_to_ast_dict(item) for item in node]
    else:
        return node


def get_ast_dict(func: Callable) -> dict:
    """Get the AST dictionary representation of a function."""
    source_code = textwrap.dedent(inspect.getsource(func))
    tree = ast.parse(source_code)
    return _function_to_ast_dict(tree)


def analyze_function(func: Callable) -> tuple[nx.DiGraph, dict[str, Any]]:
    """Extracts the variable flow graph from a function"""
    ast_dict = get_ast_dict(func)
    scope = inspect.getmodule(func).__dict__ | vars(builtins)
    analyzer = FunctionDictFlowAnalyzer(ast_dict["body"][0], scope)
    return analyzer.analyze()


def _get_output_counts(graph: nx.DiGraph) -> dict[str, int]:
    """
    Get the number of outputs for each node in the graph.

    Args:
        graph (nx.DiGraph): The directed graph representing the function.

    Returns:
        dict: A dictionary mapping node names to the number of outputs.
    """
    f_dict: dict[str, int] = {}
    for edge in graph.edges.data():
        if edge[2]["type"] != "output":
            continue
        f_dict[edge[0]] = f_dict.get(edge[0], 0) + 1
    if "input" in f_dict:
        del f_dict["input"]
    return f_dict


def _get_nodes(
    data: dict[str, dict],
    output_counts: dict[str, int],
    control_flow: None | str = None,
) -> dict[str, dict]:
    result = {}
    for label, function in data.items():
        func = function["function"]
        if hasattr(func, "_semantikon_workflow"):
            data_dict = func._semantikon_workflow.copy()
            result[label] = data_dict
            result[label]["label"] = label
        else:
            result[label] = get_node_dict(function=func)
    return result


def _remove_index(s: str) -> str:
    return "_".join(s.split("_")[:-1])


def _get_control_flow(data: dict[str, Any]) -> str:
    """
    Get the control flow name

    Args:
        data (dict[str, Any]): metadata of the edge (which is stored in the
            third element of each edge of nx.Digraph)

    Returns:
        (str): Control flow name (e.g. While_0, For_3 etc.)
    """
    return data.get("control_flow", "").split("-")[0]


def _get_sorted_edges(graph: nx.DiGraph) -> list:
    """
    Sort the edges of the graph based on the topological order of the nodes.

    Args:
        graph (nx.DiGraph): The directed graph representing the function.

    Returns:
        list: A sorted list of edges in the graph.

    Example:

    >>> graph.add_edges_from([('A', 'B'), ('B', 'D'), ('A', 'C'), ('C', 'D')])
    >>> sorted_edges = _get_sorted_edges(graph)
    >>> print(sorted_edges)

    Output:

    >>> [('A', 'B', {}), ('A', 'C', {}), ('B', 'D', {}), ('C', 'D', {})]
    """
    topo_order = list(topological_sort(graph))
    node_order = {node: i for i, node in enumerate(topo_order)}
    return sorted(graph.edges.data(), key=lambda edge: node_order[edge[0]])


def _remove_and_reconnect_nodes(
    G: nx.DiGraph, nodes_to_remove: list[str]
) -> nx.DiGraph:
    for node in set(nodes_to_remove):
        preds = list(G.predecessors(node))
        succs = list(G.successors(node))
        for u in preds:
            for v in succs:
                G.add_edge(u, v)
        G.remove_node(node)
    return G


def _get_edges(graph: nx.DiGraph) -> list[tuple[str, str]]:
    edges = []
    nodes_to_remove = []
    for edge in graph.edges.data():
        if edge[0] == "input":
            edges.append([edge[0] + "s." + _remove_index(edge[1]), edge[1]])
            nodes_to_remove.append(edge[1])
        elif edge[1] == "output":
            edges.append([edge[0], edge[1] + "s." + _remove_index(edge[0])])
            nodes_to_remove.append(edge[0])
        elif edge[2]["type"] == "input":
            tag = edge[2].get("input_name", edge[2].get("input_index"))
            if tag is None:
                raise ValueError(f"Edge {edge} has no input_name or input_index")
            edges.append([edge[0], f"{edge[1]}.inputs.{tag}"])
            nodes_to_remove.append(edge[0])
        elif edge[2]["type"] == "output":
            tag = edge[2].get("output_name", edge[2].get("output_index", "output"))
            edges.append([f"{edge[0]}.outputs.{tag}", edge[1]])
            nodes_to_remove.append(edge[1])
    new_graph = _remove_and_reconnect_nodes(nx.DiGraph(edges), nodes_to_remove)
    return list(new_graph.edges)


def get_node_dict(
    function: Callable,
) -> dict:
    """
    Get a dictionary representation of the function node.

    Args:
        func (Callable): The function to be analyzed.
        data_format (str): The format of the output. Options are "semantikon" and
            "ape".

    Returns:
        (dict) A dictionary representation of the function node.
    """
    data = {
        "function": function,
        "type": "Function",
    }
    return data


def _to_workflow_dict_entry(
    inputs: dict[str, dict],
    nodes: dict[str, dict],
    edges: list[tuple[str, str]],
    label: str,
    **kwargs,
) -> dict[str, object]:
    assert all(
        "function" in v or ("nodes" in v and "edges" in v) for v in nodes.values()
    )
    return {
        "inputs": inputs,
        "nodes": nodes,
        "edges": edges,
        "label": label,
        "type": "Workflow",
    } | kwargs


def _get_test_dict(f_dict: dict[str, dict]) -> dict[str, str]:
    """
    dict to translate test and iter nodes into "test" and "iter"

    Args:
        f_dict (dict[str, dict]): Function dictionary

    Returns:
        dict[str, str]: Translation of node name to "test" or "iter"
    """
    return {
        key: tag
        for key, value in f_dict.items()
        for tag in ["test", "iter"]
        if value.get("control_flow", "").endswith(tag)
    }


def _nest_nodes(
    graph: nx.DiGraph, nodes: dict[str, dict], f_dict: dict[str, dict]
) -> tuple[dict[str, dict], list[tuple[str, str]]]:
    """
    Nest workflow nodes

    Args:
        graph (nx.DiGraph): The directed graph representing the function.
        nodes (dict[str, dict]): The dictionary of nodes.
        f_dict (dict[str, dict]): The dictionary of functions.

    Returns:
        dict: A dictionary containing the nested nodes, edges, and label.
    """
    test_dict = _get_test_dict(f_dict=f_dict)
    cf_graph = _get_control_flow_graph(_extract_control_flows(graph))
    subgraphs = _get_subgraphs(graph, cf_graph)
    injected_nodes: dict[str, Any] = {}
    for cf_key in list(topological_sort(cf_graph))[::-1]:
        subgraph = nx.relabel_nodes(subgraphs[cf_key], test_dict)
        new_key = "injected_" + cf_key.replace("/", "_") if len(cf_key) > 0 else cf_key
        current_nodes = {}
        for key in _extract_functions_from_graph(subgraphs[cf_key]):
            if key in test_dict:
                current_nodes[test_dict[key]] = nodes[key]
            elif key in nodes:
                current_nodes[key] = nodes[key]
            else:
                current_nodes[key] = injected_nodes.pop(key)
        injected_nodes[new_key] = {
            "nodes": current_nodes,
            "edges": _get_edges(subgraph),
            "label": new_key,
        }
        for tag in ["test", "iter"]:
            if tag in injected_nodes[new_key]["nodes"]:
                injected_nodes[new_key][tag] = injected_nodes[new_key]["nodes"].pop(tag)
    return injected_nodes[""]["nodes"], injected_nodes[""]["edges"]


def get_workflow_dict(func: Callable) -> dict[str, object]:
    """
    Get a dictionary representation of the workflow for a given function.

    Args:
        func (Callable): The function to be analyzed.

    Returns:
        dict: A dictionary representation of the workflow, including inputs,
            outputs, nodes, edges, and label.
    """
    graph, f_dict, inputs = analyze_function(func)
    nodes = _get_nodes(f_dict, _get_output_counts(graph))
    nested_nodes, edges = _nest_nodes(graph, nodes, f_dict)
    return _to_workflow_dict_entry(
        inputs=inputs,
        nodes=nested_nodes,
        edges=edges,
        label=func.__name__,
    )


def _get_missing_edges(edge_list: list[tuple[str, str]]) -> list[tuple[str, str]]:
    """
    Insert processes into the data edges. Take the following workflow:

    >>> y = f(x=x)
    >>> z = g(y=y)

    The data flow is

    - f.inputs.x -> f.outputs.y
    - f.outputs.y -> g.inputs.y
    - g.inputs.y -> g.outputs.z

    `_get_missing_edges` adds the processes:

    - f.inputs.x -> f
    - f -> f.outputs.y
    - f.outputs.y -> g.inputs.y
    - g.inputs.y -> g
    - g -> g.outputs.z
    """
    extra_edges = []
    for edge in edge_list:
        for tag in edge:
            if len(tag.split(".")) < 3:
                continue
            if tag.split(".")[1] == "inputs":
                new_edge = (tag, tag.split(".")[0])
            elif tag.split(".")[1] == "outputs":
                new_edge = (tag.split(".")[0], tag)
            if new_edge not in extra_edges:
                extra_edges.append(new_edge)
    return extra_edges


class _Workflow:
    def __init__(self, workflow_dict: dict[str, Any]):
        self._workflow = tools.dict_to_recursive_dd(workflow_dict)

    @cached_property
    def _all_edges(self) -> list[tuple[str, str]]:
        edges = cast(dict[str, list], self._workflow)["edges"]
        return edges + _get_missing_edges(edges)

    @cached_property
    def _graph(self) -> nx.DiGraph:
        return nx.DiGraph(self._all_edges)

    @cached_property
    def _execution_list(self) -> list[list[str]]:
        return find_parallel_execution_levels(self._graph)

    def _sanitize_input(self, *args, **kwargs) -> dict[str, Any]:
        keys = list(self._workflow["inputs"].keys())
        for ii, arg in enumerate(args):
            if keys[ii] in kwargs:
                raise TypeError(
                    f"{self._workflow['label']}() got multiple values for"
                    " argument '{keys[ii]}'"
                )
            kwargs[keys[ii]] = arg
        return kwargs

    def _set_inputs(self, *args, **kwargs):
        kwargs = self._sanitize_input(*args, **kwargs)
        for key, value in kwargs.items():
            self._workflow["inputs"][key] = value

    def _get_value_from_global(self, path: str) -> Any:
        io, var = path.split(".")
        assert io in self._workflow, f"{io} not in workflow"
        assert var in self._workflow[io], f"{var} not in workflow {io}"
        return self._workflow[io][var]

    def _get_value_from_node(self, path: str) -> Any:
        node, io, var = path.split(".")
        return self._workflow["nodes"][node][io][var]

    def _set_value_from_global(self, path, value):
        io, var = path.split(".")
        self._workflow[io][var] = value

    def _set_value_from_node(self, path, value):
        node, io, var = path.split(".")
        self._workflow["nodes"][node][io][var] = value

    def _execute_node(self, function: str) -> Any:
        node = self._workflow["nodes"][function]
        input_kwargs = {}
        input_args = []
        try:
            for key, content in node.get("inputs", {}).items():
                try:
                    input_args.append(int(content))
                except ValueError:
                    input_kwargs[key] = content
        except KeyError:
            raise KeyError(f"value not defined for {function}") from None
        if "function" not in node:
            workflow = _Workflow(node)
            outputs = list(
                workflow.run(*input_args, **input_kwargs)["outputs"].values()
            )
            if len(outputs) == 1:
                outputs = outputs[0]
        else:
            outputs = node["function"](*input_args, **input_kwargs)
        return outputs

    def _set_value(self, tag, value):
        if len(tag.split(".")) == 2 and tag.split(".")[0] in ("inputs", "outputs"):
            self._set_value_from_global(tag, value)
        elif len(tag.split(".")) == 3 and tag.split(".")[1] in ("inputs", "outputs"):
            self._set_value_from_node(tag, value)
        elif "." in tag:
            raise ValueError(f"{tag} not recognized")

    def _get_value(self, tag: str):
        if len(tag.split(".")) == 2 and tag.split(".")[0] in ("inputs", "outputs"):
            return self._get_value_from_global(tag)
        elif len(tag.split(".")) == 3 and tag.split(".")[1] in ("inputs", "outputs"):
            return self._get_value_from_node(tag)
        elif "." not in tag:
            return self._execute_node(tag)
        else:
            raise ValueError(f"{tag} not recognized")

    def run(self, *args, **kwargs) -> dict[str, Any]:
        self._set_inputs(*args, **kwargs)
        for current_list in self._execution_list:
            for item in current_list:
                values = self._get_value(item)
                nodes = self._graph.edges(item)
                if "." not in item and len(nodes) > 1:
                    for value, node in zip(values, nodes, strict=False):
                        self._set_value(node[1], value)
                else:
                    for node in nodes:
                        self._set_value(node[1], values)
        return tools.recursive_dd_to_dict(self._workflow)


def find_parallel_execution_levels(G: nx.DiGraph) -> list[list[str]]:
    """
    Find levels of parallel execution in a directed acyclic graph (DAG).

    Args:
        G (nx.DiGraph): The directed graph representing the function.

    Returns:
        list[list[str]]: A list of lists, where each inner list contains nodes
            that can be executed in parallel.

    Comment:
        This function only gives you a list of nodes that can be executed in
        parallel, but does not tell you which processes can be executed in
        case there is a process that takes longer at a higher level.
    """
    in_degree = dict(cast(Iterable[tuple[Any, int]], G.in_degree()))
    queue = deque([node for node in G.nodes if in_degree[node] == 0])
    levels = []

    while queue:
        current_level = list(queue)
        if "input" not in current_level and "output" not in current_level:
            levels.append(current_level)

        next_queue: deque = deque()
        for node in current_level:
            for neighbor in G.successors(node):
                in_degree[neighbor] -= 1
                if in_degree[neighbor] == 0:
                    next_queue.append(neighbor)

        queue = next_queue

    return levels


def workflow(func: Callable) -> FunctionWithWorkflow:
    """
    Decorator to convert a function into a workflow with metadata.

    Args:
        func (Callable): The function to be converted into a workflow.

    Returns:
        FunctionWithWorkflow: A callable object that includes the original function

    Example:

    >>> def operation(x: float, y: float) -> tuple[float, float]:
    >>>     return x + y, x - y
    >>>
    >>>
    >>> def add(x: float = 2.0, y: float = 1) -> float:
    >>>     return x + y
    >>>
    >>>
    >>> def multiply(x: float, y: float = 5) -> float:
    >>>     return x * y
    >>>
    >>>
    >>> @workflow
    >>> def example_macro(a=10, b=20):
    >>>     c, d = operation(a, b)
    >>>     e = add(c, y=d)
    >>>     f = multiply(e)
    >>>     return f
    >>>
    >>>
    >>> @workflow
    >>> def example_workflow(a=10, b=20):
    >>>     y = example_macro(a, b)
    >>>     z = add(y, b)
    >>>     return z

    This example defines a workflow `example_macro`, that includes `operation`,
    `add`, and `multiply`, which is nested inside another workflow
    `example_workflow`. Both workflows can be executed using their `run` method,
    which returns the dictionary representation of the workflow with all the
    intermediate steps and outputs.
    """
    workflow_dict = get_workflow_dict(func)
    w = _Workflow(workflow_dict)
    func_with_metadata = FunctionWithWorkflow(func, workflow_dict, w.run)
    return func_with_metadata


def get_workflow_graph(workflow_dict: dict[str, Any]) -> nx.DiGraph:
    edges = cast(list[tuple[str, str]], workflow_dict["edges"])
    missing_edges = [edge for edge in _get_missing_edges(edges)]
    all_edges = sorted(edges + missing_edges)
    return _replace_input_ports(nx.DiGraph(all_edges), workflow_dict)


def _replace_input_ports(
    graph: nx.DiGraph, workflow_dict: dict[str, Any]
) -> nx.DiGraph:
    G = graph.copy()
    for n in list(G.nodes):
        if G.in_degree(n) == 0:
            assert n.startswith("inputs.")
            data = _get_entry(workflow_dict, n)
            nx.relabel_nodes(G, {n: data}, copy=False)
    return G


def get_hashed_node_dict(
    node: str, graph: nx.DiGraph, nodes_dict: dict[str, dict]
) -> dict[str, Any]:
    """
    Get a dictionary representation of a node for hashing purposes and database
    entries. This function extracts the metadata of the node, its inputs, and
    outputs, and returns a dictionary that can be hashed.

    Args:
        node (str): The name of the node to be hashed.
        graph (nx.DiGraph): The directed graph representing the function.
        nodes_dict (dict[str, dict]): A dictionary containing metadata for all nodes.

    Returns:
        dict[str, Any]: A dictionary representation of the node for hashing.

    Raises:
        ValueError: If the node does not have a function or if the data is not flat.
    """
    if "function" not in nodes_dict[node]:
        raise ValueError("Hashing works only on flat data")
    data_dict = {
        "node": _get_function_metadata(nodes_dict[node]["function"]),
        "inputs": {},
        "outputs": [tag.split(".")[-1] for tag in graph.successors(node)],
    }
    connected_inputs = []
    for tag in graph.predecessors(node):
        assert "inputs" in tag
        key = tag.split(".")[-1]
        predecessor = list(graph.predecessors(tag))
        assert len(predecessor) == 1
        predecessor = predecessor[0]
        pre_predecessor = list(graph.predecessors(predecessor))
        if len(pre_predecessor) > 0:
            assert len(pre_predecessor) == 1
            value = (
                get_node_hash(pre_predecessor[0], graph, nodes_dict)
                + "@"
                + predecessor.split(".")[-1]
            )
            connected_inputs.append(key)
        else:
            value = predecessor
        data_dict["inputs"][key] = value
    data_dict["node"]["connected_inputs"] = connected_inputs
    return data_dict


def get_node_hash(node: str, graph: nx.DiGraph, nodes_dict: dict[str, dict]) -> str:
    """
    Get a hash of the node's metadata, inputs, and outputs.

    Args:
        node (str): The name of the node to be hashed.
        graph (nx.DiGraph): The directed graph representing the function.
        nodes_dict (dict[str, dict]): A dictionary containing metadata for all nodes.

    Returns:
        str: A SHA-256 hash of the node's metadata, inputs, and outputs.
    """
    data_dict = get_hashed_node_dict(node=node, graph=graph, nodes_dict=nodes_dict)
    return hashlib.sha256(
        json.dumps(data_dict, sort_keys=True).encode("utf-8")
    ).hexdigest()


def _get_entry(data: dict[str, Any], key: str) -> Any:
    """
    Get a value from a nested dictionary at the specified key path.

    Args:
        data (dict[str, Any]): The dictionary to search.
        key (str): The key path to retrieve the value from, separated by dots.

    Returns:
        Any: The value at the specified key path.

    Raises:
        KeyError: If the key path does not exist in the dictionary.
    """
    for item in key.split("."):
        data = data[item]
    return data


def _set_entry(
    data: dict[str, Any], key: str, value: Any, create_missing: bool = False
) -> None:
    """
    Set a value in a nested dictionary at the specified key path.

    Args:
        data (dict[str, Any]): The dictionary to modify.
        key (str): The key path to set the value at, separated by dots.
        value (Any): The value to set.
        create_missing (bool): Whether to create missing keys in the path.
    """
    keys = key.split(".")
    for k in keys[:-1]:
        if k not in data:
            if create_missing:
                data[k] = {}
            else:
                raise KeyError(f"Key '{k}' not found in data.")
        data = data[k]
    data[keys[-1]] = value


def _get_function_metadata(cls: Callable | dict[str, str]) -> dict[str, str]:
    if isinstance(cls, dict) and "module" in cls and "qualname" in cls:
        return cls
    module = cls.__module__
    qualname = cls.__qualname__
    from importlib import import_module

    base_module = import_module(module.split(".")[0])
    version = (
        base_module.__version__
        if hasattr(base_module, "__version__")
        else "not_defined"
    )
    return {
        "module": module,
        "qualname": qualname,
        "version": version,
    }


def _get_function_keywords(function: Callable) -> list[str | int]:
    signature = inspect.signature(function)
    items = []
    for ii, (name, param) in enumerate(signature.parameters.items()):
        if param.kind == inspect.Parameter.POSITIONAL_ONLY:
            items.append(ii)
        else:
            items.append(name)
    return items
