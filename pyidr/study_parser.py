#! /usr/bin/env python

from argparse import ArgumentParser
import glob
import json
import logging
import os
import re
import sys

logging.basicConfig(level=int(os.environ.get("DEBUG", logging.INFO)))
log = logging.getLogger("pyidr.study_parser")

TYPES = ["Experiment", "Screen"]


class Key(object):

    def __init__(self, pattern, scope, optional=False):
        self.pattern = pattern
        self.scope = scope
        self.optional = optional


KEYS = (
    # OPTIONAL_KEYS["Study"]
    Key('Comment\[IDR Study Accession\]', 'Study'),
    Key('Study Title', 'Study'),
    Key('Study Description', 'Study'),
    Key('Study Type', 'Study'),
    Key('Study Type Term Source REF', 'Study', optional=True),
    Key('Study Type Term Accession', 'Study', optional=True),
    Key('Study Publication Title', 'Study'),
    Key('Study Author List', 'Study'),
    Key('Study Organism', 'Study'),
    Key('Study Organism Term Source REF', 'Study', optional=True),
    Key('Study Organism Term Accession', 'Study', optional=True),
    # OPTIONAL_KEYS["Study"]
    Key('Study BioStudies Accession', 'Study', optional=True),
    Key('Study Publication Preprint', 'Study', optional=True),
    Key('Study PubMed ID', 'Study', optional=True),
    Key('Study PMC ID', 'Study', optional=True),
    Key('Study DOI', 'Study', optional=True),
    Key('Study Copyright', 'Study', optional=True),
    Key('Study License', 'Study', optional=True),
    Key('Study License URL', 'Study', optional=True),
    Key('Study Data Publisher', 'Study', optional=True),
    Key('Study Data DOI', 'Study', optional=True),
    Key('Study Experiments Number', 'Study', optional=True),
    Key('Study Screens Number', 'Study', optional=True),
    Key('Study External URL', 'Study', optional=True),
    Key('Study Public Release Date', 'Study', optional=True),
    Key('Study Person Last Name', 'Study', optional=True),
    Key('Study Person First Name', 'Study', optional=True),
    Key('Study Person Email', 'Study', optional=True),
    Key('Study Person Address', 'Study', optional=True),
    Key('Study Person Roles', 'Study', optional=True),
    Key('Study Person ORCID', 'Study', optional=True),
    Key('Term Source Name', 'Study', optional=True),
    Key('Term Source URI', 'Study', optional=True),
    # MANDATORY_KEYS["Experiment"]
    Key('Comment\[IDR Experiment Name\]', 'Experiment'),
    Key('Experiment Description', 'Experiment'),
    Key('Experiment Imaging Method', 'Experiment'),
    Key('Experiment Number', 'Experiment'),
    # OPTIONAL_KEYS["Experiment"]
    Key('Experiment Data DOI', 'Experiment', optional=True),
    Key("Experiment Data Publisher", 'Experiment', optional=True),
    # MANDATORY_KEYS["Screen"]
    Key('Comment\[IDR Screen Name\]', 'Screen'),
    Key('Screen Description', 'Screen'),
    Key('Screen Imaging Method', 'Screen'),
    Key('Screen Number', 'Screen'),
    Key('Screen Type', 'Screen'),
    # OPTIONAL_KEYS["Screen"]
    Key('Screen Data DOI', 'Screen', optional=True),
    Key('Screen Data Publisher', 'Screen', optional=True),
    Key('Screen Technology Type', 'Screen', optional=True),
)

DOI_PATTERN = re.compile("https?://(dx.)?doi.org/(?P<id>.*)")


class StudyParser():

    def __init__(self, study_file):
        self._study_file = study_file
        self._dir = os.path.dirname(self._study_file)
        with open(self._study_file, 'r') as f:
            log.info("Parsing %s" % self._study_file)
            self._study_lines = f.readlines()
            self._study_lines_used = [
                [] for x in range(len(self._study_lines))]

        self.study = self.parse("Study")
        self.has_children_doi = False

        self.parse_publications()
        self.study.update(self.parse_data_doi(self.study, "Study Data DOI"))

        self.components = []
        for t in TYPES:
            n = int(self.study.get('Study %ss Number' % t, 0))
            for i in range(n):
                log.debug("Parsing %s %g" % (t, i + 1))

                d = self.parse(t, lines=self.get_lines(i + 1, t))
                d.update({'Type': t})
                d.update(self.study)
                doi = self.parse_data_doi(d, "%s Data DOI" % t)
                if doi:
                    d.update(doi)
                    self.has_children_doi = True
                self.parse_annotation_file(d)
                self.components.append(d)

        if not self.components:
            raise Exception("Need to define at least one screen or experiment")

    def get_value(self, key, expr=".*", fail_on_missing=True, lines=None):
        pattern = re.compile("^%s\t(%s)" % (key, expr))
        if lines:
            # Fake space since we don't know what the caller is passing
            used = [[] for x in range(len(lines))]
        else:
            lines = self._study_lines
            used = self._study_lines_used
        for idx, line in enumerate(lines):
            m = pattern.match(line)
            if m:
                used[idx].append(("get_value", key, expr))
                return m.group(1).rstrip()
        if fail_on_missing:
            raise Exception("Could not find value for key %s " % key)

    def parse(self, scope, lines=None):
        d = {}
        mandatory_keys = [x.pattern for x in KEYS
                          if x.scope == scope and not x.optional]
        optional_keys = [x.pattern for x in KEYS
                         if x.scope == scope and x.optional]
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
        for idx, line in enumerate(self._study_lines):
            m = PATTERN.match(line)
            if m:
                if int(m.group(1)) == index:
                    found = True
                elif int(m.group(1)) != index and found:
                    return lines
            if found:
                self._study_lines_used[idx].append(("get_lines", index))
                lines.append(line)
        if not lines:
            raise Exception("Could not find %s %g" % (component_type, index))
        return lines

    def parse_annotation_file(self, component):
        accession_number = component["Comment\[IDR Study Accession\]"]
        pattern = re.compile("(%s-\w+(-\w+)?)/(\w+)$" % accession_number)
        name = component["Comment\[IDR %s Name\]" % component["Type"]]
        m = pattern.match(name)
        if not m:
            raise Exception("Unmatched name %s" % name)

        # Check for annotation.csv file
        component_path = os.path.join(self._dir, m.group(3))
        basename = "%s-%s-annotation" % (accession_number, m.group(3))
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
                    m.group(1), m.group(3), annotation_filename)
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

    def parse_data_doi(self, d, key):
        if key not in d:
            return {}
        m = DOI_PATTERN.match(d[key])
        if not m:
            raise Exception(
                "Invalid Data DOI: %s" % d[key])
        return {"Data DOI": m.group("id")}


class Formatter(object):

    TOP_PAIRS = [('Study Type', "%(Study Type)s")]
    EXPERIMENT_PAIRS = [
        ('Organism', "%(Study Organism)s"),
        ('Imaging Method', "%(Experiment Imaging Method)s"),
    ]
    SCREEN_PAIRS = [
        ('Organism', "%(Study Organism)s"),
        ('Screen Type', "%(Screen Type)s"),
        ('Screen Technology Type', "%(Screen Technology Type)s"),
        ('Imaging Method', "%(Screen Imaging Method)s"),
    ]
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
        ('BioStudies ID', "%(Study BioStudies Accession)s"
         " https://www.ebi.ac.uk/biostudies/studies/"
         "%(Study BioStudies Accession)s"),
        ('Annotation File', "%(Annotation File)s"),
    ]

    def __init__(self, parser, inspect=False):
        self.parser = parser
        self.basedir = os.path.dirname(parser._study_file)
        self.inspect = inspect
        self.m = {
          "name": self.basedir,
          "source": self.parser._study_file,
          "experiments": [],
          "screens": [],
        }

        # Serialize experiments/screens
        for component in self.parser.components:
            name = component["Comment\[IDR %s Name\]" % component["Type"]]
            d = {
              "name": name,
              "description": self.generate_description(component),
              "map": self.generate_annotation(component),
            }
            if self.inspect:
                log.info("Inspect the internals of %s" % self.basedir)
                path = "%s/%s/*" % (self.basedir, name.split("/")[-1])
                d["files"] = glob.glob(path)
            self.m["%ss" % component['Type'].lower()].append(d)

        # Add top-level study
        if self.parser.has_children_doi:
            d = {
                "description": self.generate_description(self.parser.study),
                "map": self.generate_annotation(self.parser.study),
            }
            self.m.update(d)

    def __str__(self):
        return json.dumps(self.m, indent=4, sort_keys=True)

    def generate_description(self, component):
        """Generate the description of the study/experiment/screen"""
        # Only display the first publication
        publication_title = (
            "Publication Title\n%(Study Publication Title)s" %
            component).split('\t')[0]
        if "Type" in component:
            key = "%s Description" % component["Type"]
        else:
            key = "Study Description"
        component_title = (
            "%s\n%s" % (key, component[key])).decode('string_escape')
        return publication_title + "\n\n" + component_title

    def generate_annotation(self, component):
        """Generate the map annotation of the study/experiment/screen"""

        def add_key_values(d, pairs):
            for key, formatter in pairs:
                try:
                    value = formatter % d
                    for v in value.split('\t'):
                        s.append({'%s' % key: v})
                except KeyError, e:
                    log.debug("Missing %s" % e.message)

        s = []
        add_key_values(component, self.TOP_PAIRS)
        if component.get("Type", None) == "Experiment":
            add_key_values(component, self.EXPERIMENT_PAIRS)
        elif component.get("Type", None) == "Screen":
            add_key_values(component, self.SCREEN_PAIRS)
        for publication in component["Publications"]:
            add_key_values(publication, self.PUBLICATION_PAIRS)
        add_key_values(component, self.BOTTOM_PAIRS)
        return s

    def check_object(self, gateway, o, obj_type):
        """Check description and map of individual object on OMERO server"""

        log.info("Checking %s %s" % (obj_type, o["name"]))
        remote_obj = gateway.getObject(
            obj_type, attributes={"name": o["name"]})
        errors = []
        if remote_obj.description != o["description"]:
            errors.append("current:%s\nexpected:%s" % (
                remote_obj.description, o["description"]))
        for al in remote_obj._getAnnotationLinks(
                ns="openmicroscopy.org/omero/client/mapAnnotation"):
            kv_pairs = [{m.name: m.value} for m in al.child.mapValue
                        if m.name != "Study"]
            if kv_pairs != o["map"]:
                for i in range(min(len(kv_pairs), len(o["map"]))):
                    if kv_pairs[i] != o["map"][i]:
                        errors.append("current:%s\nexpected:%s" % (
                            kv_pairs[i], o["map"][i]))
        if not errors:
            log.info("No annotations mismatch detected")
        else:
            log.error("Found some annotations mismatch")
            for e in errors:
                print e

    def check(self):

        from omero.cli import CLI
        from omero.gateway import BlitzGateway

        cli = CLI()
        cli.loadplugins()
        cli.onecmd('login')

        try:
            gateway = BlitzGateway(client_obj=cli.get_client())
            for experiment in self.m["experiments"]:
                self.check_object(gateway, experiment, "Project")
            for experiment in self.m["screens"]:
                self.check_object(gateway, experiment, "Screen")
            if "map" in self.m:
                if self.m["experiments"]:
                    study_type = "Project"
                else:
                    study_type = "Screen"
                self.check_object(gateway, self.m, study_type)
        finally:
            if cli:
                cli.close()
            gateway.close()


def main(argv):

    parser = ArgumentParser()
    parser.add_argument("studyfile", help="Study file to parse", nargs='+')
    parser.add_argument("--strict", action="store_true",
                        help="Fail if unknown keys are detected")
    parser.add_argument("--inspect", action="store_true",
                        help="Inspect the internals of the study directory")
    parser.add_argument("--report", action="store_true",
                        help="Create a report of the generated objects")
    parser.add_argument("--check", action="store_true",
                        help="Check against IDR")
    args = parser.parse_args(argv)

    for s in args.studyfile:
        p = StudyParser(s)
        unknown = []
        for idx, line in enumerate(p._study_lines_used):
            if not line:
                line = p._study_lines[idx].strip()
                if line and \
                        not line.startswith('#') and \
                        not line.startswith('"'):
                    key = line.split("\t")[0]
                    if args.strict:
                        unknown.append(key)
                    else:
                        log.warn("Unknown key: %s", key)
        if unknown:
            print "Found %s unknown keys:" % len(unknown)
            raise Exception("\n".join(unknown))
        d = Formatter(p, inspect=args.inspect)

        if args.report:
            print str(d)

        if args.check:
            d.check()
    return p


if __name__ == "__main__":
    parser = main(sys.argv[1:])
