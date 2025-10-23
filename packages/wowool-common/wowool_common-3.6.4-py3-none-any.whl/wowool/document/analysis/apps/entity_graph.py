"""Entity graph API classes"""

from dataclasses import dataclass


@dataclass
class Link:
    """Represents a link between two entities in an entity graph.

    A link connects two entities through a specific relationship, forming
    part of a larger entity graph that represents connections and relationships
    within a document.

    Attributes:
        from_ (dict): The source entity of the link, containing entity information
            such as ID, type, and properties.
        to (dict): The target entity of the link, containing entity information
            such as ID, type, and properties.
        relation (dict): The relationship information between the entities,
            including relationship type and properties.
    """

    from_: dict
    to: dict
    relation: dict


def detect_output_format(jo: list):
    if len(jo) > 0 and jo[0].get("from", None) is not None:
        return "graph"
    return "table"


def convert_entity_graph(jo: list):
    if detect_output_format(jo) == "table":
        return jo
    return [Link(from_=link["from"], to=link["to"], relation=link["relation"]) for link in jo]
