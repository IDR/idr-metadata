#! /usr/bin/env python

from argparse import ArgumentParser
import glob
import json
import logging
import os
import re
import sys


TYPES = ["Experiment", "Screen"]


class Key(object):

    def __init__(self, pattern, scope, optional=False):
        self.pattern = pattern
        self.scope = scope
        self.optional = optional


KEYS = (
    # OPTIONAL_KEYS["Study"]
    Key(r'Comment\[IDR Study Accession\]', 'Study'),
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
    Key('Study Version History', 'Study', optional=True),
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
    Key(r'Comment\[IDR Experiment Name\]', 'Experiment'),
    Key('Experiment Description', 'Experiment'),
    Key('Experiment Imaging Method', 'Experiment'),
    Key('Experiment Number', 'Experiment'),
    # OPTIONAL_KEYS["Experiment"]
    Key('Experiment Data DOI', 'Experiment', optional=True),
    Key("Experiment Data Publisher", 'Experiment', optional=True),
    # MANDATORY_KEYS["Screen"]
    Key(r'Comment\[IDR Screen Name\]', 'Screen'),
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


class StudyError(Exception):
    pass


class StudyParser():

    def __init__(self, study_file):
        self._study_file = study_file
        self._dir = os.path.dirname(self._study_file)
        self.log = logging.getLogger("pyidr.study_parser.StudyParser")
        with open(self._study_file, 'r') as f:
            self.log.info("Parsing %s" % self._study_file)
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
                self.log.debug("Parsing %s %g" % (t, i + 1))

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
        PATTERN = re.compile(r"^%s Number\t(\d+)" % component_type)
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
        import glob

        accession_number = component[r"Comment\[IDR Study Accession\]"]
        pattern = re.compile(r"(%s-\w+(-\w+)?)/(\w+)$" % accession_number)
        name = component[r"Comment\[IDR %s Name\]" % component["Type"]]
        m = pattern.match(name)
        if not m:
            raise Exception("Unmatched name %s" % name)

        # Check for annotation.csv file
        component_path = os.path.join(self._dir, m.group(3))
        basename = "%s-%s-annotation" % (accession_number, m.group(3))

        # Generate GitHub annotation URL
        if os.path.exists(os.path.join(self._dir, ".git")):
            base_gh_url = "https://github.com/IDR/%s/blob/master/%s" % (
                m.group(1), m.group(3))
        else:
            base_gh_url = (
                "https://github.com/IDR/idr-metadata/blob/master/%s" % name)

        # Try to find single annotation file in root directory
        for extension in ['.csv', '.csv.gz']:
            annotation_filename = "%s%s" % (basename, extension)
            annotation_path = os.path.join(component_path, annotation_filename)
            if os.path.exists(annotation_path):
                component["Annotations"] = [{
                    "Annotation File": "%s %s" % (
                        annotation_filename, base_gh_url + "/%s" %
                        annotation_filename)}]
                return

        component["Annotations"] = []
        annotation_filenames = sorted(glob.glob(os.path.join(
            component_path, "**", "%s.csv.gz" % basename)))
        for annotation_filename in annotation_filenames:
            component["Annotations"].append({
                "Annotation File": "%s %s" % (
                    os.path.basename(annotation_filename),
                    base_gh_url + "%s" %
                    annotation_filename[len(component_path):])
            })
        return

    def parse_publications(self):

        titles = self.study['Study Publication Title'].split('\t')
        authors = self.study['Study Author List'].split('\t')
        assert len(titles) == len(authors), (
            "Mismatching publication titles and authors")
        if titles == [''] and authors == ['']:
            return

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

        parse_ids("Study PubMed ID", re.compile(r"(?P<id>\d+)"))
        parse_ids("Study PMC ID", re.compile(r"(?P<id>PMC\d+)"))
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
        ('BioStudies Accession', "%(Study BioStudies Accession)s"
         " https://www.ebi.ac.uk/biostudies/studies/"
         "%(Study BioStudies Accession)s"),
    ]
    ANNOTATION_PAIRS = [('Annotation File', "%(Annotation File)s")]

    def __init__(self, parser, inspect=False):
        self.log = logging.getLogger("pyidr.study_parser.Formatter")
        self.parser = parser
        self.basedir = os.path.dirname(parser._study_file)
        self.inspect = inspect
        self.m = {
          "name": os.path.basename(self.basedir),
          "source": self.parser._study_file,
          "experiments": [],
          "screens": [],
        }

        # Serialize experiments/screens
        for component in self.parser.components:
            name = component[r"Comment\[IDR %s Name\]" % component["Type"]]
            d = {
              "name": name,
              "description": self.generate_description(component),
              "map": self.generate_annotation(component),
            }
            if self.inspect:
                self.log.info("Inspect the internals of %s" % self.basedir)
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
        publication_title = ""
        if component["Study Publication Title"]:
            # Only display the first publication
            publication_title = (
                "Publication Title\n%(Study Publication Title)s" %
                component).split('\t')[0] + "\n\n"
        if "Type" in component:
            key = "%s Description" % component["Type"]
        else:
            key = "Study Description"
        component_title = (
            "%s\n%s" % (key, component[key])).decode('string_escape')
        if "Study Version History" in component:
            history = ("\n\nVersion History\n%s" %
                       component["Study Version History"])
        else:
            history = ""

        return publication_title + component_title + history

    def generate_annotation(self, component):
        """Generate the map annotation of the study/experiment/screen"""

        def add_key_values(d, pairs):
            for key, formatter in pairs:
                try:
                    value = formatter % d
                    for v in value.split('\t'):
                        s.append({'%s' % key: v})
                except KeyError, e:
                    self.log.debug("Missing %s" % e.message)

        s = []
        add_key_values(component, self.TOP_PAIRS)
        if component.get("Type", None) == "Experiment":
            add_key_values(component, self.EXPERIMENT_PAIRS)
        elif component.get("Type", None) == "Screen":
            add_key_values(component, self.SCREEN_PAIRS)
        for publication in component.get("Publications", []):
            add_key_values(publication, self.PUBLICATION_PAIRS)
        add_key_values(component, self.BOTTOM_PAIRS)
        for annotation in component.get("Annotations", []):
            add_key_values(annotation, self.ANNOTATION_PAIRS)
        return s

    def check_object(self, gateway, o, obj_type):
        """Check description and map of individual object on OMERO server"""

        STUDY_NS = "openmicroscopy.org/omero/client/mapAnnotation"

        log.info("Checking %s %s" % (obj_type, o["name"]))
        obj = gateway.getObject(obj_type, attributes={"name": o["name"]})

        if obj.description != o["description"]:
            log.error("Mismatching description: current:%s\nexpected:%s" %
                      (obj.description, o["description"]))
            raise StudyError

        anns = list(obj.listAnnotations(ns=STUDY_NS))
        if len(anns) > 1:
            log.error("Found multiple annotations with the same namespace")
            raise StudyError

        expected_pairs = [(k, v) for i in o["map"] for k, v in i.iteritems()]
        if len(anns) == 0:
            log.error("Missing map annotation")
            raise StudyError

        if anns[0].getValue() != expected_pairs:
            log.error("Mismatching map annotation: current:%s\nexpected:%s" %
                      (anns[0].getValue(), expected_pairs))
            raise StudyError

    def check(self):

        from omero.cli import CLI
        from omero.gateway import BlitzGateway

        cli = CLI()
        cli.loadplugins()
        cli.onecmd('login -q')

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
    parser.add_argument(
        '--verbose', '-v', action='count', default=0,
        help='Increase the command verbosity')
    args = parser.parse_args(argv)

    logging.basicConfig(level=logging.WARN - 10 * args.verbose)
    log = logging.getLogger("pyidr.study_parser")

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
