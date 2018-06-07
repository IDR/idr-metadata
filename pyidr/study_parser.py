#! /usr/bin/env python

from argparse import ArgumentParser
import glob
import json
import logging
import os
import re
import sys
import traceback

logging.basicConfig(level=int(os.environ.get("DEBUG", logging.INFO)))
log = logging.getLogger("pyidr.study_parser")

TYPES = ["Experiment", "Screen"]
MANDATORY_KEYS = {}
OPTIONAL_KEYS = {}
MANDATORY_KEYS["Study"] = [
    'Comment\[IDR Study Accession\]',
    'Study Title',
    'Study Description',
    'Study Type',
    'Study Publication Title',
    'Study Author List',
    'Study Organism',
]
OPTIONAL_KEYS["Study"] = [
    'Study Publication Preprint',
    'Study PubMed ID',
    'Study PMC ID',
    'Study DOI',
    'Study Copyright',
    'Study License',
    'Study License URL',
    'Study Data Publisher',
    'Study Data DOI',
    'Study Experiments Number',
    'Study Screens Number',
]
MANDATORY_KEYS["Experiment"] = [
    'Comment\[IDR Experiment Name\]',
    'Experiment Description',
    'Experiment Imaging Method',
    'Experiment Number'
]
OPTIONAL_KEYS["Experiment"] = [
    'Experiment Data DOI',
    "Experiment Data Publisher",
]

MANDATORY_KEYS["Screen"] = [
    'Comment\[IDR Screen Name\]',
    'Screen Description',
    'Screen Imaging Method',
    'Screen Number',
    'Screen Type',
]
OPTIONAL_KEYS["Screen"] = [
    'Screen Data DOI',
    "Screen Data Publisher",
    'Screen Technology Type',
]

DOI_PATTERN = re.compile("https?://(dx.)?doi.org/(?P<id>.*)")


class StudyParser():

    def __init__(self, study_file):
        self._study_file = study_file
        self._dir = os.path.dirname(self._study_file)
        with open(self._study_file, 'r') as f:
            log.info("Parsing %s" % self._study_file)
            self._study_lines = f.readlines()
        self.study = self.parse(
            MANDATORY_KEYS["Study"], OPTIONAL_KEYS["Study"])
        self.parse_publications()
        self.parse_data_doi()

        self.components = []
        for t in TYPES:
            n = int(self.study.get('Study %ss Number' % t, 0))
            for i in range(n):
                log.debug("Parsing %s %g" % (t, i + 1))

                d = self.parse(MANDATORY_KEYS[t], OPTIONAL_KEYS[t],
                               lines=self.get_lines(i + 1, t))
                d.update({'Type': t})
                d.update(self.study)
                self.parse_annotation_file(d)
                self.components.append(d)

        if not self.components:
            raise Exception("Need to define at least one screen or experiment")

    def get_value(self, key, expr=".*", fail_on_missing=True, lines=None):
        pattern = re.compile("^%s\t(%s)" % (key, expr))
        if not lines:
            lines = self._study_lines
        for line in lines:
            m = pattern.match(line)
            if m:
                return m.group(1).rstrip()
        if fail_on_missing:
            raise Exception("Could not find value for key %s " % key)

    def parse(self, mandatory_keys, optional_keys, lines=None):
        d = {}
        for key in mandatory_keys:
            d[key] = self.get_value(key, lines=lines)
        for key in optional_keys:
            value = self.get_value(key, fail_on_missing=False, lines=lines)
            if value:
                d[key] = value
        return d

    def get_lines(self, index, component_type):
        PATTERN = re.compile("^%s Number\t(\d+)" % component_type)
        found = False
        lines = []
        for line in self._study_lines:
            m = PATTERN.match(line)
            if m:
                if int(m.group(1)) == index:
                    found = True
                elif int(m.group(1)) != index and found:
                    return lines
            if found:
                lines.append(line)
        if not lines:
            raise Exception("Could not find %s %g" % (component_type, index))
        return lines

    def parse_annotation_file(self, component):
        accession_number = component["Comment\[IDR Study Accession\]"]
        pattern = re.compile("(%s-\w+-\w+)/(\w+)$" % accession_number)
        name = component["Comment\[IDR %s Name\]" % component["Type"]]
        m = pattern.match(name)
        if not m:
            raise Exception("Unmatched name %s" % name)

        # Check for annotation.csv file
        component_path = os.path.join(self._dir, m.group(2))
        basename = "%s-%s-annotation" % (accession_number, m.group(2))
        for extension in ['.csv', '.csv.gz']:
            annotation_filename = "%s%s" % (basename, extension)
            annotation_path = os.path.join(component_path, annotation_filename)
            if not os.path.exists(annotation_path):
                log.debug("Cannot find %s" % annotation_path)
                continue

            # Generate GitHub annotation URL
            base_url = "https://github.com/IDR/%s/blob/master/%s/%s"
            if os.path.exists(os.path.join(self._dir, ".git")):
                annotation_url = base_url % (
                    m.group(1), m.group(2), annotation_filename)
            else:
                annotation_url = base_url % (
                    "idr-metadata", name, annotation_filename)
            component["Annotation File"] = "%s %s" % (
                annotation_filename, annotation_url)
            return
        return

    def parse_publications(self):

        titles = self.study['Study Publication Title'].split('\t')
        authors = self.study['Study Author List'].split('\t')
        assert len(titles) == len(authors), (
            "Mismatching publication titles and authors")
        publications = [{"Title": title, "Author List": author}
                        for title, author in zip(titles, authors)]

        def parse_ids(key, pattern):
            if key not in self.study:
                return
            split_ids = self.study[key].split('\t')
            key2 = key.strip("Study ")
            for i in range(len(split_ids)):
                if not split_ids[i]:
                    continue
                m = pattern.match(split_ids[i])
                if not m:
                    raise Exception("Invalid %s: %s" % (key2, split_ids[i]))
                publications[i][key2] = m.group("id")

        parse_ids("Study PubMed ID", re.compile("(?P<id>\d+)"))
        parse_ids("Study PMC ID", re.compile("(?P<id>PMC\d+)"))
        parse_ids("Study DOI", DOI_PATTERN)

        self.study["Publications"] = publications

    def parse_data_doi(self):
        if 'Study Data DOI' not in self.study:
            return
        m = DOI_PATTERN.match(self.study['Study Data DOI'])
        if not m:
            raise Exception(
                "Invalid Data DOI: %s" % self.study['Study Data DOI'])
        self.study["Data DOI"] = m.group("id")


class Object():

    PUBLICATION_PAIRS = [
        ('Publication Title', "%(Title)s"),
        ('Publication Authors', "%(Author List)s"),
        ('PubMed ID', "%(PubMed ID)s "
         "https://www.ncbi.nlm.nih.gov/pubmed/%(PubMed ID)s"),
        ('PMC ID',
         "%(PMC ID)s https://www.ncbi.nlm.nih.gov/pmc/articles/%(PMC ID)s"),
        ('Publication DOI', "%(DOI)s https://doi.org/%(DOI)s"),
    ]
    BOTTOM_PAIRS = [
        ('License', "%(Study License)s %(Study License URL)s"),
        ('Copyright', "%(Study Copyright)s"),
        ('Data Publisher', "%(Study Data Publisher)s"),
        ('Data DOI', "%(Data DOI)s "
         "https://doi.org/%(Data DOI)s"),
        ('Annotation File', "%(Annotation File)s"),
    ]

    def __init__(self, component):
        self.component = component
        if component['Type'] == "Experiment":
            self.type = "Project"
            self.NAME = "%(Comment\[IDR Experiment Name\])s"
            self.DESCRIPTION = (
                "Experiment Description\n%(Experiment Description)s")
            self.TOP_PAIRS = [
                ('Study Type', "%(Study Type)s"),
                ('Organism', "%(Study Organism)s"),
                ('Imaging Method', "%(Experiment Imaging Method)s"),
                ]
        else:
            self.type = "Screen"
            self.NAME = "%(Comment\[IDR Screen Name\])s"
            self.DESCRIPTION = (
                "Screen Description\n%(Screen Description)s")
            self.TOP_PAIRS = [
                ('Study Type', "%(Study Type)s"),
                ('Organism', "%(Study Organism)s"),
                ('Screen Type', "%(Screen Type)s"),
                ('Screen Technology Type', "%(Screen Technology Type)s"),
                ('Imaging Method', "%(Screen Imaging Method)s"),
            ]
        self.name = self.NAME % component
        self.description = self.generate_description(component)
        self.map = self.generate_annotation(component)

    def generate_description(self, component):
        # Only display the first publication
        publication_title = (
            "Publication Title\n%(Study Publication Title)s" %
            component).split('\t')[0]
        return publication_title + "\n\n" + self.DESCRIPTION % component

    def generate_annotation(self, component):

        def add_key_values(d, pairs):
            for key, formatter in pairs:
                try:
                    value = formatter % d
                    for v in value.split('\t'):
                        s.append(('%s' % key, v))
                except KeyError, e:
                    log.debug("Missing %s" % e.message)

        s = []
        add_key_values(component, self.TOP_PAIRS)
        for publication in component["Publications"]:
            add_key_values(publication, self.PUBLICATION_PAIRS)
        add_key_values(component, self.BOTTOM_PAIRS)
        return s


def check(obj):

    from omero.cli import CLI
    from omero.gateway import BlitzGateway

    cli = CLI()
    cli.loadplugins()
    cli.onecmd('login')

    try:
        gateway = BlitzGateway(client_obj=cli.get_client())
        remote_obj = gateway.getObject(
                obj.type, attributes={"name": obj.name})
        errors = []
        if remote_obj.description != obj.description:
            errors.append("current:%s\nexpected:%s" % (
                remote_obj.description, obj.description))
        for al in remote_obj._getAnnotationLinks(
                ns="openmicroscopy.org/omero/client/mapAnnotation"):
            mapValue = al.child.mapValue
            kv_pairs = [(m.name, m.value) for m in mapValue]
            for i in range(len(kv_pairs)):
                if kv_pairs[i] != obj.map[i]:
                    errors.append(
                        "current:%s\nexpected:%s" % (kv_pairs[i], obj.map[i]))
        if not errors:
            log.info("No annotations mismatch detected")
        else:
            for e in errors:
                log.info("Found some annotations mismatch")
                print e
    finally:
        if cli:
            cli.close()
        gateway.close()


class JsonPrinter(object):

    def __init__(self):
        self.objects = []

    def consume(self, obj):
        m = {
            "description": obj.description,
            "map": dict((v[0], v[1]) for v in obj.map),
        }
        if hasattr(obj, "files"):
            m["files"] = obj.files
        self.objects.append(m)

    def finish(self):
        print json.dumps(self.objects, indent=4, sort_keys=True)


class TextPrinter(object):

    def consume(self, obj):
        print "description:\n%s\n" % obj.description
        print "map:"
        print "\n".join(["%s\t%s" % (v[0], v[1]) for v in obj.map])
        if hasattr(obj, "files"):
            print "files:"
            for f in obj.files:
                print "\t", f

    def finish(self):
        pass


def main(argv):

    parser = ArgumentParser()
    parser.add_argument("studyfile", help="Study file to parse", nargs='+')
    parser.add_argument("--inspect", action="store_true",
                        help="Inspect the internals of the study directory")
    parser.add_argument("--report", action="store_true",
                        help="Create a report of the generated objects")
    parser.add_argument("--check", action="store_true",
                        help="Check against IDR")
    parser.add_argument("--format", default="text", choices=("text", "json"),
                        help="Format for the report")
    args = parser.parse_args(argv)

    if args.format == "json":
        Printer = JsonPrinter
    else:
        Printer = TextPrinter

    try:
        for s in args.studyfile:
            p = StudyParser(s)
            printer = Printer()
            objects = [Object(x) for x in p.components]
            if args.inspect:
                basedir = os.path.dirname(s)
                log.info("Inspect the internals of %s" % basedir)
                for o in objects:
                    path = "%s/%s/*" % (basedir, o.name.split("/")[-1])
                    o.files = glob.glob(path)

            if args.report:
                for o in objects:
                    log.info("Generating annotations for %s" % o.name)
                    printer.consume(o)

            if args.check:
                for o in objects:
                    log.info("Check annotations for %s" % o.name)
                    check(o)
            printer.finish()
            return p
    except Exception:
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    parser = main(sys.argv[1:])
