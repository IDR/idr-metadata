"""\
Get all URLs for image zip archives from the dataset's web page.
"""

import urllib2
import re
from urlparse import urlparse, urljoin
from HTMLParser import HTMLParser


URL = "https://data.broadinstitute.org/bbbc/BBBC021/"
PATTERN = re.compile(r"^BBBC.+_images_.+\.zip$")


class BBBCParser(HTMLParser):

    def __init__(self):
        HTMLParser.__init__(self)
        self.img_links = []

    def handle_starttag(self, tag, attrs):
        if tag != "a":
            return
        attrs = dict(attrs)
        try:
            link = attrs["href"]
        except KeyError:
            return
        if PATTERN.match(link.strip()):
            self.img_links.append(link)


def main():
    content = urllib2.urlopen(URL).read()
    parser = BBBCParser()
    parser.feed(content)
    for link in parser.img_links:
        if not urlparse(link).netloc:
            link = urljoin(URL, link)
        print(link)


if __name__ == "__main__":
    main()
