#!/usr/bin/env python

"""An adpater class to support the htmllib interface with lxml.

The htmllib module was deprecated in Python 2.6 and will be removed in 3.0, but
it provides a convenient and useful visitor interface.  Therefore, rather than
rewriting our code, we've created this adapter.

The SAX-like interface that htmllib provides is lower-level than the ElementTree
or DOM interfaces that lxml provides, but it's also more efficient.
"""

htmllib = None
etree = None
try:
    from lxml import etree
except ImportError:
    try:
        # If the user doesn't have lxml installed, fall back to htmllib if it's
        # available, even though it's deprecated.
        import htmllib
    except ImportError:
        raise ImportError("Install lxml.  Neither lxml or htmllib are present.")


if etree:

    class HTMLParser(object):

        def __init__(self):
            self.parser = etree.HTMLParser(target=self, recover=True)

        def feed(self, fragment):
            """Delegates feeding the document to the parser."""
            self.parser.feed(fragment)

        def close(self):
            """Subclasses should override to reset their state."""
            pass

        def start(self, tag, attrs):
            method = getattr(self, 'start_' + tag, None)
            if not method:
                method = getattr(self, 'do_' + tag, None)
            if method:
                # htmllib passes a list of tuples while lxml uses a dictionary, so
                # we translate by calling items().
                method(attrs.items())

        def end(self, tag):
            method = getattr(self, 'end_' + tag, None)
            if method:
                method()

        def data(self, data):
            pass

        def comment(self, text):
            pass

else:

    HTMLParser = htmllib.HTMLParser
