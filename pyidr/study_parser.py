#! /usr/bin/env python

import logging
import os
import re
import sys

logging.basicConfig(level=int(os.environ.get("DEBUG", logging.INFO)))

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


class StudyParser():

    def __init__(self, study_file):
        self._study_file = study_file
        self._dir = os.path.dirname(self._study_file)
        with open(self._study_file, 'r') as f:
            logging.info("Parsing %s" % sys.argv[1])
            self._study_lines = f.readlines()
            self.study = self.parse(
                MANDATORY_KEYS["Study"], OPTIONAL_KEYS["Study"])

        self.components = []
        for t in TYPES:
            n = int(self.study.get('Study %ss Number' % t, 0))
            for i in range(n):
                logging.debug("Parsing %s %g" % (t, i + 1))

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
                logging.debug("Cannot find %s" % annotation_path)
                continue

            # Generate GitHub annotation URL
            base_url = "https://github.com/IDR/%s/blob/master/%s/%s"
            if os.path.exists(os.path.join(self._dir, ".git")):
                annotation_url = base_url % (
                    m.group(1), m.group(2), annotation_filename)
            else:
                annotation_url = base_url % (
                    "idr-metadata", name, annotation_filename)
            component["Annotation File"] = annotation_url
            return
        return


class Object():

    def __init__(self, component):
        self.name = self.NAME % component
        self.description = self.generate_description(component)
        self.map = self.generate_annotation(component)

    def generate_description(self, component):
        return self.DESCRIPTION % component

    def generate_annotation(self, component):

        s = []
        for key, formatter in self.MAP_PAIRS:
            try:
                s.append(('%s' % key, formatter % component))
            except KeyError, e:
                logging.debug("Missing %s" % e.message)
        return s


class Screen(Object):

    NAME = "%(Comment\[IDR Screen Name\])s"
    DESCRIPTION = (
        "Publication Title\n%(Study Publication Title)s\n\n"
        "Screen Description\n%(Screen Description)s")
    MAP_PAIRS = [
        ('Study Type', "%(Study Type)s"),
        ('Organism', "%(Study Organism)s"),
        ('Screen Type', "%(Screen Type)s"),
        ('Screen Technology Type', "%(Screen Technology Type)s"),
        ('Imaging Method', "%(Screen Imaging Method)s"),
        ('Publication Title', "%(Study Publication Title)s"),
        ('Publication Authors', "%(Study Author List)s"),
        ('Pubmed ID', "%(Study PubMed ID)s "
         "https://www.ncbi.nlm.nih.gov/pubmed/%(Study PubMed ID)s"),
        ('PMC ID', "%(Study PMC ID)s"),
        ('Publication DOI', "%(Study DOI)s https://dx.doi.org/%(Study DOI)s"),
        ('License', "%(Study License)s %(Study License URL)s"),
        ('Copyright', "%(Study Copyright)s"),
        ('Data Publisher', "%(Study Data Publisher)s"),
        ('Data DOI', "%(Study Data DOI)s "
         "https://dx.doi.org/%(Study Data DOI)s"),
        ('Annotation File', "%(Annotation File)s"),
        ]


class Project(Object):

    NAME = "%(Comment\[IDR Experiment Name\])s"
    DESCRIPTION = (
        "Publication Title\n%(Study Publication Title)s\n\n"
        "Experiment Description\n%(Experiment Description)s")
    MAP_PAIRS = [
        ('Study Type', "%(Study Type)s"),
        ('Organism', "%(Study Organism)s"),
        ('Imaging Method', "%(Experiment Imaging Method)s"),
        ('Publication Title', "%(Study Publication Title)s"),
        ('Publication Authors', "%(Study Author List)s"),
        ('Pubmed ID', "%(Study PubMed ID)s "
         "https://www.ncbi.nlm.nih.gov/pubmed/%(Study PubMed ID)s"),
        ('PMC ID', "%(Study PMC ID)s"),
        ('Publication DOI', "%(Study DOI)s https://dx.doi.org/%(Study DOI)s"),
        ('License', "%(Study License)s %(Study License URL)s"),
        ('Copyright', "%(Study Copyright)s"),
        ('Data Publisher', "%(Study Data Publisher)s"),
        ('Data DOI', "%(Study Data DOI)s "
         "https://dx.doi.org/%(Study Data DOI)s"),
        ('Annotation File', "%(Annotation File)s"),
        ]


if __name__ == "__main__":
    if len(sys.argv) == 0:
        raise Exception("Requires one study file as an input")
    p = StudyParser(sys.argv[1])
    if len(sys.argv) == 3 and sys.argv[2] == '--report':
        experiments = [c for c in p.components if c['Type'] == "Experiment"]
        for e in experiments:
            logging.info("Generating %s" % sys.argv[1])
            obj = Project(e)
            print "name:\n%s\n" % obj.name
            print "description:\n%s\n" % obj.description
            print "map:\n%s\n" % obj.map
        screens = [c for c in p.components if c['Type'] == "Screen"]
        for s in screens:
            obj = Screen(s)
            print "name:\n%s\n" % obj.name
            print "description:\n%s\n" % obj.description
            print "map:\n%s\n" % obj.map
