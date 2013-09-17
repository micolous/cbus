#!/usr/bin/env python2
# fetch_protocol_docs.py - Downloads official Clipsal Protocol documentation
# Copyright 2013 Michael Farrell <micolous+git@gmail.com>
# 
# This library is free software: you can redistribute it and/or modify
# it under the terms of the GNU Lesser General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
# 
# This library is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU Lesser General Public License for more details.
# 
# You should have received a copy of the GNU Lesser General Public License
# along with this library.  If not, see <http://www.gnu.org/licenses/>.

import requests, argparse
from HTMLParser import HTMLParser
from urlparse import urlparse, urljoin, urlunparse
from urllib import unquote
from os.path import join


DOCUMENTATION_INDEX = 'http://training.clipsal.com/downloads/OpenCBus/OpenCBusProtocolDownloads.html'
DOCUMENTATION_INDEX_U = urlparse(DOCUMENTATION_INDEX)


class DocumentationParser(HTMLParser):
	links = []

	def handle_starttag(self, tag, attrs):
		if tag.lower() == 'a':
			# is a link, handle attributes.
			href = None
			for k, v in attrs:
				if k.lower() == 'href':
					href = urlparse(urljoin(DOCUMENTATION_INDEX, v))
					break

			# sanity check
			if href != None and \
				href.scheme in ('http', 'https') and \
				href.netloc == DOCUMENTATION_INDEX_U.netloc and \
				href.path.endswith('.pdf'):
				# This has a link to a document on this server, queue it.
				self.links.append(href)


def download_docs(destination):
	print ("Fetching documentation index from clipsal.com...")
	r = requests.get(DOCUMENTATION_INDEX)

	# now parse out the links to documentation
	parser = DocumentationParser()
	parser.feed(r.text)
	parser.close()

	# and read back the links
	total_links = len(parser.links)
	for i, link in enumerate(parser.links):
		uri = urlunparse(link)
		fname = join(destination, unquote(link.path.split('/')[-1]))

		print ("[%02d/%02d]: Downloading %r to %r..." % (
			i + 1,
			total_links,
			uri,
			fname
		))

		document = requests.get(uri).content
		fh = open(fname, 'wb')
		fh.write(document)
		fh.close()

	print ("Downloaded documentation!")


def main():
	parser = argparse.ArgumentParser()

	parser.add_argument(
		'destination',
		help='Controls the output directory for the documentation'
	)

	options = parser.parse_args()

	download_docs(options.destination)


if __name__ == '__main__':
	main()


