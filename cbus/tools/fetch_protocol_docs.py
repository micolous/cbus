#!/usr/bin/env python
# fetch_protocol_docs.py - Downloads official Clipsal Protocol documentation
# Copyright 2013-2019 Michael Farrell <micolous+git@gmail.com>
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

from __future__ import absolute_import
from __future__ import print_function

import argparse
import requests
import os

from six.moves.html_parser import HTMLParser
from six.moves.urllib.parse import urlparse, urljoin, urlunparse, unquote

DOCUMENTATION_INDEX = ('https://updates.clipsal.com/ClipsalSoftwareDownload'
                       '/DL/downloads/OpenCBus/OpenCBusProtocolDownloads.html')
DOCUMENTATION_INDEX_U = urlparse(DOCUMENTATION_INDEX)
TERMS_URL = ('https://updates.clipsal.com/ClipsalSoftwareDownload/DL/downloads'
             '/OpenCBus/Open%20C-Bus%20Serial%20Protocol%20Agreement.pdf')


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
            if (href is not None and href.scheme in ('http', 'https') and
                href.netloc == DOCUMENTATION_INDEX_U.netloc and
                    href.path.endswith('.pdf')):
                # This has a link to a document on this server, queue it.
                self.links.append(href)


def download_file(link, destination, i=0, total_links=0):
    """
    Downloads a file from a remote webserver.

    :param link: A urlparsed link to fetch
    :type link: urllib.parse.ParseResult
    :param destination: Destination directory for the file
    :type destination: str
    :param i: Current file number, when showing progress. 0-indexed.
    :param total_links: Total number of links to download, when showing
                        progress. When set to 0, total progress is not
                        displayed.
    :return: None
    """
    uri = urlunparse(link)
    short_fname = unquote(link.path.split('/')[-1])
    fname = os.path.join(destination, short_fname)
    if os.path.exists(fname):
        print('Skipping `{}`, file already exists!'.format(short_fname))
        return

    if total_links:
        print('[{:02d}/{:02d}]: Downloading `{}` <{}>...'.format(
            i + 1, total_links, short_fname, uri))
    else:
        print('Downloading `{}` <{}>...'.format(short_fname, uri))

    document = requests.get(uri).content
    fh = open(fname, 'wb')
    fh.write(document)
    fh.close()


def download_docs(destination):
    if not os.path.exists(destination):
        os.makedirs(destination)
    elif not os.path.isdir(destination):
        raise IOError('Destination {} exists, but is not a directory!'.format(
            destination))

    # Download the terms and conditions
    download_file(urlparse(TERMS_URL), destination)

    print('Fetching documentation index from updates.clipsal.com...')
    r = requests.get(DOCUMENTATION_INDEX)

    # now parse out the links to documentation
    parser = DocumentationParser()
    parser.feed(r.text)
    parser.close()

    # and read back the links
    total_links = len(parser.links)
    for i, link in enumerate(parser.links):
        download_file(link, destination, i, total_links)

    print('Downloaded documentation to: {}'.format(destination))


def main():
    parser = argparse.ArgumentParser(description="""\
    Downloads C-Bus serial protocol documentation from the Clipsal website.
    """)

    parser.add_argument(
        'destination',
        help='Directory to save documentation to')

    options = parser.parse_args()

    download_docs(options.destination)


if __name__ == '__main__':
    main()
