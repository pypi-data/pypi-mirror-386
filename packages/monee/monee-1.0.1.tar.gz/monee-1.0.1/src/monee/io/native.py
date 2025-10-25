import inspect
import json

from monee.model import Network
from monee.model.core import Var, component_list


class PersistenceException(Exception):
    """
    No docstring provided.
    """


def init_model(model_type, preprocessed_dict):
    """
    No docstring provided.
    """
    model = None
    model_type_dict = {
        component_cls.__name__: component_cls for component_cls in component_list
    }
    if model_type in model_type_dict:
        model_cls = model_type_dict[model_type]
        model = model_cls(
            **dict.fromkeys(
                [
                    argname
                    for argname, _ in list(
                        inspect.signature(model_cls.__init__).parameters.items()
                    )[1:]
                ],
                0,
            )
        )
        for key, value in preprocessed_dict.items():
            setattr(model, key, value)
    else:
        raise PersistenceException(
            f"The type {model_type} is not known! Maybe you forgot to decorate your model class with @model?"
        )
    return model


def preprocess_dict(model_dict):
    """
    No docstring provided.
    """
    result = {}
    for k, v in model_dict.items():
        if type(v) is dict:
            if "max" in v and "min" in v and ("value" in v):
                result[k] = Var(v["value"], v["max"], v["min"])
        else:
            result[k] = v
    return result


def native_dict_to_network(dict_struct) -> Network:
    """
    No docstring provided.
    """
    network = Network(None)
    grid_by_name = dict_struct["grids"]
    for k, v in grid_by_name.items():
        values_grid_dict = v["values"]
        model = init_model(v["model_type"], values_grid_dict)
        grid_by_name[k] = model
    childs = dict_struct["childs"]
    nodes = dict_struct["nodes"]
    branches = dict_struct["branches"]
    for child_dict in childs:
        values_child_dict = child_dict["values"]
        preprocessed_dict = preprocess_dict(values_child_dict)
        model = init_model(child_dict["model_type"], preprocessed_dict)
        network.child(model, overwrite_id=child_dict["id"])
    for node_dict in nodes:
        values_node_dict = node_dict["values"]
        preprocessed_dict = preprocess_dict(values_node_dict)
        model = init_model(node_dict["model_type"], preprocessed_dict)
        network.node(
            model,
            child_ids=node_dict["child_ids"],
            grid=grid_by_name[node_dict["grid_id"]],
            overwrite_id=node_dict["id"],
        )
    if "compounds" in dict_struct:
        compounds = dict_struct["compounds"]
        for compound_dict in compounds:
            values_compound_dict = compound_dict["values"]
            preprocessed_dict = preprocess_dict(values_compound_dict)
            model = init_model(compound_dict["model_type"], preprocessed_dict)
            network.compound(model, **compound_dict["connected_to"])
    for branch_dict in branches:
        values_branch_dict = branch_dict["values"]
        preprocessed_dict = preprocess_dict(values_branch_dict)
        model = init_model(branch_dict["model_type"], preprocessed_dict)
        network.branch(
            model,
            from_node_id=branch_dict["from_node"],
            to_node_id=branch_dict["to_node"],
            grid=grid_by_name[branch_dict["grid_id"]],
        )
    return network


def load_to_network(file) -> Network:
    """
    No docstring provided.
    """
    dict_struct = None
    with open(file) as read_fp:
        dict_struct = json.load(read_fp)
    return native_dict_to_network(dict_struct)


def write_omef_network(file, network: Network):
    """
    No docstring provided.
    """
    grids = {}
    nodes = network.nodes
    branches = network.branches
    childs = network.childs
    compounds = network.compounds
    node_dict_list = []
    branch_dict_list = []
    child_dict_list = []
    compound_dict_list = []
    for node in nodes:
        if not network.is_blacklisted(node):
            node_dict_list.append(node_to_dict(node, grids))
    for branch in branches:
        if not network.is_blacklisted(branch):
            branch_dict_list.append(branch_to_dict(branch, grids))
    for child in childs:
        if not network.is_blacklisted(child):
            child_dict_list.append(child_to_dict(child))
    for compound in compounds:
        compound_dict_list.append(compound_to_dict(compound))
    to_serialize = dict(
        grids={
            k: {"values": v.__dict__, "model_type": type(v).__name__}
            for k, v in grids.items()
        },
        nodes=node_dict_list,
        childs=child_dict_list,
        branches=branch_dict_list,
        compounds=compound_dict_list,
    )
    with open(file, "w") as write_fp:
        json.dump(to_serialize, write_fp, indent=3, default=vars)


def child_to_dict(child):
    """
    No docstring provided.
    """
    return dict(
        id=child.id,
        values=model_to_dict(child.model),
        model_type=type(child.model).__name__,
    )


def compound_to_dict(compound):
    """
    No docstring provided.
    """
    return dict(
        id=compound.id,
        values=model_to_dict(compound.model),
        model_type=type(compound.model).__name__,
        connected_to=compound.connected_to,
    )


def fetch_grid_to_dict(grid_dict, grid_from_model):
    """
    No docstring provided.
    """
    if grid_from_model.name not in grid_dict:
        grid_dict[grid_from_model.name] = grid_from_model
    elif grid_dict[grid_from_model.name] is not grid_from_model:
        raise PersistenceException(
            f"You must not define multiple grids with the same name: {grid_from_model.name}"
        )


def branch_to_dict(branch, grids):
    """
    No docstring provided.
    """
    fetch_grid_to_dict(grids, branch.grid)
    return dict(
        id=branch.id,
        from_node=branch.id[0],
        to_node=branch.id[1],
        grid_id=branch.grid.name,
        values=model_to_dict(branch.model),
        model_type=type(branch.model).__name__,
    )


def node_to_dict(node, grids):
    """
    No docstring provided.
    """
    fetch_grid_to_dict(grids, node.grid)
    return dict(
        id=node.id,
        grid_id=node.grid.name,
        child_ids=node.child_ids,
        values=model_to_dict(node.model),
        model_type=type(node.model).__name__,
    )


def model_to_dict(model):
    """
    No docstring provided.
    """
    base_dict = model.vars
    result = dict(base_dict)
    return result
