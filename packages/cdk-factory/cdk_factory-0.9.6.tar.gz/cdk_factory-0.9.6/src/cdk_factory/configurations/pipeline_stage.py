"""
Geek Cafe, LLC
Maintainers: Eric Wilson
MIT License.  See Project Root for the license information.
"""

# import os
# from typing import List, Optional
from typing import List, Dict, Any

from cdk_factory.configurations.stack import StackConfig


class PipelineStageConfig:
    """A Representation of a pipeline stage"""

    def __init__(self, stage: dict, workload: dict) -> None:
        self.__dictionary: dict = stage
        self.__workload: dict = workload
        self.__stacks: List[StackConfig] = []

        self.__load_stacks()

    @property
    def workload(self) -> dict:
        """
        Returns the workload name
        """
        return self.__workload

    @property
    def workload_name(self) -> str:
        """
        Returns the workload name
        """

        value = self.workload.get("name")
        if not value:
            raise ValueError("Workload name is not defined in the configuration")

        return value

    @property
    def dictionary(self) -> dict:
        """
        Returns the dictionary of the stage
        """
        return self.__dictionary

    @property
    def name(self) -> str:
        """
        Returns the stage name
        """
        value = self.dictionary.get("name")
        if not value:
            raise ValueError("Stage name is not defined in the configuration")

        return value

    @property
    def enabled(self) -> bool:
        """
        Returns the stage enabled status
        """
        return str(self.dictionary.get("enabled", True)).lower() == "true"

    @property
    def description(self) -> str | None:
        """
        Returns the stage description
        """
        return self.dictionary.get("description")

    @property
    def wave_name(self) -> str | None:
        """
        Returns the wave name if found
        """
        return self.dictionary.get("wave") or self.dictionary.get("wave_name")

    @property
    def module(self) -> str | None:
        """
        Returns the module name
        """
        return self.dictionary.get("module")

    @property
    def stacks(self) -> List[StackConfig]:
        """Deployment Stacks"""
        return self.__stacks

    def __load_stacks(self):
        """
        Loads the stacks for the deployment
        """
        stacks = self.__dictionary.get("stacks", [])
        self.__stacks = []
        for stack in stacks:
            if isinstance(stack, dict):
                self.__stacks.append(StackConfig(stack, self.__workload))
            if isinstance(stack, str):
                # if the stack is a string, it's the stack name
                # and we need to load the stack configuration
                # from the workload
                stack_list: List[dict] = self.__workload.get("stacks", [])
                stack_dict: dict | None = None
                for stack_item in stack_list:
                    if stack_item.get("name") == stack:
                        stack_dict = stack_item
                        break
                if stack_dict is None:
                    raise ValueError(f"Stack {stack} not found in workload")
                self.__stacks.append(StackConfig(stack_dict, self.__workload))

    @property
    def builds(self) -> List[Dict[str, Any]]:
        """
        Returns the stages for this pipeline
        """
        builds = self.workload.get("builds", [])

        return builds
