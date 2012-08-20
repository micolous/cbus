#!/usr/bin/env python
"""
cbus/toolkit/graph.py
Generate graphs of a CBus network

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

from optparse import OptionParser
import json
import pydot

def generate_graph(input, output):
	with open(input, 'rb') as i:
		networks = json.load(i)
	graph = pydot.Dot(input.replace('.', '_'), graph_type='digraph')

	# create groups for networks
	for network_id, network in networks.iteritems():
		loads = set()

		subgraph = pydot.Subgraph('Network %s' % network_id)
		cluster = pydot.Cluster('Network %s' % network_id)

		for unit_id, unit in network['units'].iteritems():
			node = pydot.Node(unit['name'])
			subgraph.add_node(node)
			node.groups = unit['groups']
			[loads.add(x) for x in node.groups]
			for x in unit['groups']:
				if x == 255: continue
				subgraph.add_edge(pydot.Edge(unit['name'], 'GA %s' % x))

		for group in loads:
			node = pydot.Node('GA %s' % group)

			subgraph.add_node(node)


		cluster.add_subgraph(subgraph)
		graph.add_subgraph(cluster)





	graph.write(output)



def main():
	parser = OptionParser(usage='%prog -i input.json -o output.dot', version='%prog 1.0')
	parser.add_option('-o', '--output', dest='output', metavar='FILE', help='write dot output to FILE')
	parser.add_option('-i', '--input', dest='input', metavar='FILE', help='read JSON dump from FILE')
	options, args = parser.parse_args()

	if options.input == None:
		parser.error('Input filename not given.')

	if options.output == None:
		parser.error('Output filename not given.')

	generate_graph(options.input, options.output)

if __name__ == "__main__":
	main()
