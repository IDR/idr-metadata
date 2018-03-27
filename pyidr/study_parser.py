#! /usr/bin/env python

import logging
import os
import re
import sys

logging.basicConfig(level=int(os.environ.get("DEBUG", logging.INFO)))


class StudyParser():

    TYPES = ["Experiment", "Screen"]
    MANDATORY_STUDY_KEYS = {
        'Title': 'Study Title',
        'Description': 'Study Description',
        'Study Type': 'Study Type',
        'Publication Title': 'Study Publication Title',
        'Publication Authors': 'Study Author List',
        'License': 'Study License',
        'License URL': 'Study License URL'
    }
    OPTIONAL_STUDY_KEYS = {
        'Publication Preprint': 'Study Publication Preprint',
        'PubMed ID': 'Study PMC ID',
        'Publication DOI': 'Study DOI',
    }
    MANDATORY_COMPONENT_KEYS = {
        'Name': 'Comment\[IDR %s Name\]',
        'Description': '%s Description',
        'Imaging Method': '%s Imaging Method'
    }
    OPTIONAL_COMPONENT_KEYS = {
        'Data DOI': '%s Data DOI',
        'Data Publisher': "%s Data Publisher",
    }

    def __init__(self, s):
        self._study_file = s
        self.parse_study()
        self.parse_components()

    def get_value(self, key, expr=".*", fail_on_missing=True, lines=None):
        pattern = re.compile("^%s\t(%s)" % (key, expr))
        if not lines:
            lines = self._study_file
        for line in lines:
            m = pattern.match(line)
            if m:
                return m.group(1).rstrip()
        if fail_on_missing:
            raise Exception("Could not find value for key %s " % key)

    def parse_study(self):
        self.study = {}
        for key1, key2 in self.MANDATORY_STUDY_KEYS.iteritems():
            self.study[key1] = self.get_value(key2)
        for key1, key2 in self.OPTIONAL_STUDY_KEYS.iteritems():
            self.study[key1] = self.get_value(key2, fail_on_missing=False)

    def parse_components(self):
        self.components = []
        for t in self.TYPES:
            key = "Study %ss Number" % t
            n = self.get_value(key, expr="\d+", fail_on_missing=False)
            if not n:
                continue
            self.type = t
            self.components = [{} for x in range(int(n))]
            break

        if not self.components:
            raise Exception("Could not find valid study type")

        for i in range(len(self.components)):
            logging.debug("Parsing %s %g" % (self.type, i + 1))
            self.parse_component(i)

    def parse_component(self, index):
        lines = self.get_component_lines(index + 1)
        for key1, key2 in self.MANDATORY_COMPONENT_KEYS.iteritems():
            self.components[index][key1] = self.get_value(
                key2 % self.type, lines=lines)

    def get_component_lines(self, index):
        EXPERIMENT_NUMBER_PATTERN = re.compile("^%s Number\t(\d+)" % self.type)
        found = False
        lines = []
        for line in self._study_file:
            m = EXPERIMENT_NUMBER_PATTERN.match(line)
            if m:
                if int(m.group(1)) == index:
                    found = True
                elif int(m.group(1)) != index and found:
                    return lines
            if found:
                lines.append(line)
        return lines


if __name__ == "__main__":
    if len(sys.argv) == 0:
        raise Exception("Requires one study file as an input")
    logging.info("Reading %s" % sys.argv[1])
    with open(sys.argv[1], 'r') as f:
        parser = StudyParser(f.readlines())
