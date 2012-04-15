# toolkit #

Scripts relating to interacting with CBus Toolkit and files.

## CBZ File Format ##

CBus Toolkit makes project backup files with the extension `cbz`.  These are ZIP-compressed XML files, and contain all the metadata about the network, and unit descriptions.

As `libcbus` does not presently offer a way to lookup this information from the network and some information like Group Address labels is not available on the network except under certain limited circumstances, we must parse these to dump information for other programs in an easy way.

`lxml` gives an object-oriented view of the XML in the `CBZ.root` attribute.

## dump_labels.py ##

Dumps metadata from CBus units on the network.

