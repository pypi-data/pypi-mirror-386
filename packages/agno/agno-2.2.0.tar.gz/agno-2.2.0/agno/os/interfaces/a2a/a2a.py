"""Main class for the A2A app, used to expose an Agno Agent, Team, or Workflow in an A2A compatible format."""

from typing import Optional

from fastapi.routing import APIRouter
from typing_extensions import List

from agno.agent import Agent
from agno.os.interfaces.a2a.router import attach_routes
from agno.os.interfaces.base import BaseInterface
from agno.team import Team
from agno.workflow import Workflow


class A2A(BaseInterface):
    type = "a2a"

    router: APIRouter

    def __init__(
        self,
        agents: Optional[List[Agent]] = None,
        teams: Optional[List[Team]] = None,
        workflows: Optional[List[Workflow]] = None,
        prefix: str = "/a2a",
        tags: Optional[List[str]] = None,
    ):
        self.agents = agents
        self.teams = teams
        self.workflows = workflows
        self.prefix = prefix
        self.tags = tags or ["A2A"]

        if not (self.agents or self.teams or self.workflows):
            raise ValueError("Agents, Teams, or Workflows are required to setup the A2A interface.")

    def get_router(self, **kwargs) -> APIRouter:
        self.router = APIRouter(prefix=self.prefix, tags=self.tags)  # type: ignore

        self.router = attach_routes(router=self.router, agents=self.agents, teams=self.teams, workflows=self.workflows)

        return self.router
