
# Copyright (C) 2023-2025 Cognizant Digital Business, Evolutionary AI.
# All Rights Reserved.
# Issued under the Academic Public License.
#
# You can be released from the terms, and requirements of the Academic Public
# License by purchasing a commercial license.
# Purchase of a commercial license is mandatory for any use of the
# neuro-san SDK Software in commercial settings.
#
# END COPYRIGHT

from neuro_san.internals.parsers.structure.json_structure_parser import JsonStructureParser
from neuro_san.internals.parsers.structure.structure_parser import StructureParser


class StructureParserFactory:
    """
    Factory for creating StructureParser instances based on a string type
    """

    def create_structure_parser(self, parser_type: str) -> StructureParser:
        """
        Creates a structure parser given the string type

        :param parser_type: A string describing the format of the structure parser.
        """

        structure_parser: StructureParser = None

        if parser_type is None or not isinstance(parser_type, str):
            structure_parser = None
        elif parser_type.lower() == "json":
            structure_parser = JsonStructureParser()

        return structure_parser
