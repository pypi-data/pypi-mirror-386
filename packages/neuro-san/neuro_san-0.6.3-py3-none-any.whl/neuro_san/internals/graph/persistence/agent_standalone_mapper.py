
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
from pathlib import Path, PurePosixPath

from neuro_san.internals.interfaces.agent_name_mapper import AgentNameMapper


class AgentStandaloneMapper(AgentNameMapper):
    """
    A simple policy implementation defining conversion
    between agent name and agent standalone definition file
    (not specified relative to registry manifest root)
    """
    def __init__(self, path_method=Path):
        """
        Constructor

        :param path_method: Optional Path method to use for path manipulations.
            Default is pathlib.Path, but can be overridden for testing purposes.
        """
        self.path_method = path_method

    def agent_name_to_filepath(self, agent_name: str) -> str:
        """
        Agent name is its filepath.
        """
        return str(self.path_method(PurePosixPath(agent_name)))

    def filepath_to_agent_network_name(self, filepath: str) -> str:
        """
        Converts a file path to agent standalone definition file
        to agent network name identifying it to the service.
        """
        # Take the file name only - with no file path, and no file name extension:
        # /root/file_path/my_agent.hocon => my_agent
        return str(self.path_method(filepath).stem)
