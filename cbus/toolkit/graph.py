#!/usr/bin/env python
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

from __future__ import absolute_import
from argparse import ArgumentParser, FileType
import json
import pydot
import six


def generate_graph(input, output):
    """
    Generates a Graphviz DOT graph for the given network.

    :param input: Input file-like object to read the network data from, in JSON
                  format from the dump_labels tool.
    :type input: file

    :param output: Output file name to write the graph to.
    :type output: str
    """
    networks = json.load(input)

    # warning: pydot has a bad case of the stupid and doesn't sanitise
    # inputs correctly.
    graph = pydot.Dot(output.replace('.', '_').replace('-', '_'),
                      graph_type='digraph')

    # create groups for networks
    for network_id, network in six.iteritems(networks):
        loads = set()

        subgraph = pydot.Subgraph('Network_%s' % network_id)
        # cluster = pydot.Cluster('Network %s' % network_id)

        for unit_id, unit in six.iteritems(network['units']):
            node = pydot.Node(unit['name'])
            subgraph.add_node(node)
            node.groups = unit['groups']
            [loads.add(x) for x in node.groups]
            for x in unit['groups']:
                if x == 255:
                    continue
                subgraph.add_edge(pydot.Edge(unit['name'], 'GA %s' % x))

        for group in loads:
            node = pydot.Node('GA %s' % group)

            subgraph.add_node(node)

        # cluster.add_subgraph(subgraph)
        graph.add_subgraph(subgraph)

    # Dot.write must be a file name to write to -- not a file-like
    # object.
    graph.write(output)


def main():
    parser = ArgumentParser(
        usage='%(prog)s -i input.json -o output.dot',
        version='1.0',
        description='Creates a Graphviz dot-file describing a CBus network.',
        epilog="""\
        Render the output of this tool to an image with a command like:

        python -m cbus.toolkit.dump_labels -i mynetwork.cbz -o mynetwork.json;
        python -m cbus.toolkit.graph -i mynetwork.json -o mynetwork.dot;
        fdp mynetwork.dot -Tpng -o mynetwork.png;""")
    parser.add_argument(
        '-o', '--output',
        dest='output', metavar='FILE',
        help='write dot output to FILE')
    parser.add_argument(
        '-i', '--input',
        dest='input', metavar='FILE', type=FileType('rb'),
        help='read JSON dump from FILE')
    options = parser.parse_args()

    if options.input is None:
        parser.error('Input filename not given.')

    if options.output is None:
        parser.error('Output filename not given.')

    generate_graph(options.input, options.output)


if __name__ == "__main__":
    main()
