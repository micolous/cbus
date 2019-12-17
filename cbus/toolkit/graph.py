#!/usr/bin/env python3
"""
cbus/toolkit/graph.py
Generate graphs of a CBus network.

Copyright 2012-2019 Michael Farrell <micolous+git@gmail.com>

This library is free software: you can redistribute it and/or modify
it under the terms of the GNU Lesser General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

This library is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU Lesser General Public License for more details.

You should have received a copy of the GNU Lesser General Public License
along with this library.  If not, see <http://www.gnu.org/licenses/>.
"""

from argparse import ArgumentParser, FileType
import json
import pydot
from typing import BinaryIO, Text


def generate_graph(in_f: BinaryIO, out_f: Text) -> None:
    """
    Generates a Graphviz DOT graph for the given network.

    :param in_f: Input file-like object to read the network data from, in JSON
                  format from the dump_labels tool.

    :param out_f: Output file name to write the graph to.
    """
    networks = json.load(in_f)

    # warning: pydot has a bad case of the stupid and doesn't sanitise
    # inputs correctly.
    graph = pydot.Dot(out_f.replace('.', '_').replace('-', '_'),
                      graph_type='digraph')

    # create groups for networks
    for network_id, network in networks.items():
        loads = set()

        subgraph = pydot.Subgraph(f'Network_{network_id}')
        # cluster = pydot.Cluster('Network %s' % network_id)

        for unit_id, unit in network['units'].items():
            node = pydot.Node(unit['name'])
            subgraph.add_node(node)
            node.groups = unit['groups']
            [loads.add(x) for x in node.groups]
            for x in unit['groups']:
                if x == 255:
                    continue
                subgraph.add_edge(pydot.Edge(unit['name'], f'GA {x}'))

        for group in loads:
            node = pydot.Node(f'GA {group}')

            subgraph.add_node(node)

        # cluster.add_subgraph(subgraph)
        graph.add_subgraph(subgraph)

    # Dot.write must be a file name to write to -- not a file-like
    # object.
    graph.write(out_f)


def main():
    parser = ArgumentParser(
        description='Creates a Graphviz dot-file describing a CBus network.',
        epilog="""\
        Render the output of this tool to an image with a command like:

        python -m cbus.toolkit.dump_labels mynetwork.cbz -o mynetwork.json;
        python -m cbus.toolkit.graph mynetwork.json -o mynetwork.dot;
        fdp mynetwork.dot -Tpng -o mynetwork.png;""")
    parser.add_argument(
        '-o', '--output', metavar='FILE', required=True,
        help='write dot output to FILE')
    parser.add_argument(
        'input', nargs=1, metavar='FILE', type=FileType('rb'),
        help='read JSON dump from FILE')
    options = parser.parse_args()

    generate_graph(options.input[0], options.output)


if __name__ == "__main__":
    main()
