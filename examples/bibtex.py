#-*- coding: utf-8 -*-
#######################################################################
# Name: bibtex.py
# Purpose: Parser for bibtex files
# Author: Igor R. Dejanovic <igor DOT dejanovic AT gmail DOT com>
# Copyright: (c) 2013 Igor R. Dejanovic <igor DOT dejanovic AT gmail DOT com>
# License: MIT License
#
# This example demonstrates grammar and parser for bibtex files.
#######################################################################
import pprint

import sys
from arpeggio import *
from arpeggio.export import PMDOTExporter, PTDOTExporter
from arpeggio import RegExMatch as _


# Grammar
def bibfile():                  return ZeroOrMore([comment_entry, bibentry, comment]), EndOfFile
def comment_entry():            return "@comment", "{", _(r'[^}]*'), "}"
def bibentry():                 return bibtype, "{", bibkey, ",", field, ZeroOrMore(",", field), "}"
def field():                    return fieldname, "=", fieldvalue
def fieldvalue():               return [fieldvalue_braces, fieldvalue_quotes]
def fieldvalue_braces():        return "{", fieldvalue_braced_content, "}"
def fieldvalue_quotes():        return '"', fieldvalue_quoted_content, '"'

# Lexical rules
def fieldname():                return _(r'[-\w]+')
def comment():                  return _(r'[^@]+')
def bibtype():                  return _(r'@\w+')
def bibkey():                   return _(r'[^\s,]+')
def fieldvalue_quoted_content():    return _(r'((\\")|[^"])*')
def fieldvalue_braced_content():    return Combine(ZeroOrMore(Optional(And("{"), fieldvalue_inner),\
                                                    fieldvalue_part))

def fieldvalue_part():          return _(r'((\\")|[^{}])+')
def fieldvalue_inner():         return "{", fieldvalue_braced_content, "}"

# Semantic actions
class BibFileSem(SemanticAction):
    """
    Just returns list of child nodes (bibentries).
    """
    def first_pass(self, parser, node, nodes):
        if parser.debug:
            print "Processing Bibfile"

        # Return only dict nodes
        return [x for x in nodes if type(x) is dict]


class BibEntrySem(SemanticAction):
    """
    Constructs a map where key is bibentry field name.
    Key is returned under 'bibkey' key. Type is returned under 'bibtype'.
    """
    def first_pass(self, parser, node, nodes):
        if parser.debug:
            print "  Processing bibentry %s" % nodes[2]
        bib_entry_map = {
            'bibtype': nodes[0].value,
            'bibkey': nodes[2].value
        }
        for field in nodes[3:]:
            if isinstance(field, tuple):
                bib_entry_map[field[0]] = field[1]
        return bib_entry_map


class FieldSem(SemanticAction):
    """
    Constructs a tuple (fieldname, fieldvalue).
    """
    def first_pass(self, parser, node, nodes):
        if parser.debug:
            print "    Processing field %s" % nodes[0]
        field = (nodes[0].value, nodes[2])
        return field


class FieldValueSem(SemanticAction):
    """
    Serbian Serbian letters form latex encoding to Unicode.
    Remove braces. Remove newlines.
    """
    def first_pass(self, parser, node, nodes):
        value = nodes[1].value
        value = value.replace(r"\'{c}", u"ć")\
                    .replace(r"\'{C}", u"Ć")\
                    .replace(r"\v{c}", u"č")\
                    .replace(r"\v{C}", u"Č")\
                    .replace(r"\v{z}", u"ž")\
                    .replace(r"\v{Z}", u"Ž")\
                    .replace(r"\v{s}", u"š")\
                    .replace(r"\v{S}", u"Š")
        value = re.sub("[\n{}]", '', value)
        return value

# Connecting rules with semantic actions
bibfile.sem = BibFileSem()
bibentry.sem = BibEntrySem()
field.sem = FieldSem()
fieldvalue_braces.sem = FieldValueSem()
fieldvalue_quotes.sem = FieldValueSem()

if __name__ == "__main__":
    # First we will make a parser - an instance of the bib parser model.
    # Parser model is given in the form of python constructs therefore we
    # are using ParserPython class.
    parser = ParserPython(bibfile, reduce_tree=True)

    # Then we export it to a dot file in order to visualise it. This is
    # particulary handy for debugging purposes.
    # We can make a jpg out of it using dot (part of graphviz) like this
    # dot -O -Tjpg calc_parse_tree_model.dot
    PMDOTExporter().exportFile(parser.parser_model,
                    "bib_parse_tree_model.dot")

    # First parameter is bibtex file
    if len(sys.argv) > 1:
        with open(sys.argv[1], "r") as bibtexfile:
            bibtexfile_content = bibtexfile.read()


            # We create a parse tree or abstract syntax tree out of textual input
            parse_tree = parser.parse(bibtexfile_content)

            # Then we export it to a dot file in order to visualise it.
            PTDOTExporter().exportFile(parse_tree,
                            "bib_parse_tree.dot")

            # getASG will start semantic analysis.
            # In this case semantic analysis will list of bibentry maps.
            ast = parser.getASG()

            pp = pprint.PrettyPrinter(indent=4)
            pp.pprint(ast)

    else:
        print "Usage: python bibtex.py file_to_parse"
