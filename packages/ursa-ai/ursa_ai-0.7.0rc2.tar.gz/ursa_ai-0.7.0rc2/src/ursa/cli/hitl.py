import os
import platform
import sqlite3
from cmd import Cmd
from dataclasses import dataclass
from functools import cached_property
from pathlib import Path
from typing import Callable, Optional

import httpx
from langchain_core.messages import HumanMessage
from langchain_openai import ChatOpenAI, OpenAIEmbeddings
from langgraph.checkpoint.sqlite import SqliteSaver
from pydantic import SecretStr
from rich.console import Console
from rich.markdown import Markdown
from rich.theme import Theme
from typer import Typer

from ursa.agents import (
    ArxivAgent,
    ExecutionAgent,
    PlanningAgent,
    RecallAgent,
    WebSearchAgent,
)
from ursa.util.memory_logger import AgentMemory

app = Typer()

ursa_banner = r"""
  __  ________________ _
 / / / / ___/ ___/ __ `/
/ /_/ / /  (__  ) /_/ / 
\__,_/_/  /____/\__,_/  
"""


def make_console():
    return Console(
        theme=Theme({
            "success": "green",
            "error": "bold red",
            "dim": "grey50",
            "warn": "yellow",
            "emph": "bold cyan",
        })
    )


def wrap_api_key(api_key: Optional[str]) -> Optional[SecretStr]:
    return None if api_key is None else SecretStr(api_key)


@dataclass
class HITL:
    workspace: Path
    llm_model_name: str
    llm_base_url: str
    llm_api_key: Optional[str]
    max_completion_tokens: int
    emb_model_name: str
    emb_base_url: str
    emb_api_key: Optional[str]
    share_key: bool
    arxiv_summarize: bool
    arxiv_process_images: bool
    arxiv_max_results: int
    arxiv_database_path: Optional[Path]
    arxiv_summaries_path: Optional[Path]
    arxiv_vectorstore_path: Optional[Path]
    arxiv_download_papers: bool
    ssl_verify: bool

    def get_path(self, path: Optional[Path], default_subdir: str) -> str:
        if path is None:
            return str(self.workspace / default_subdir)
        return str(path)

    def __post_init__(self):
        self.workspace.mkdir(parents=True, exist_ok=True)

        # Specify API key only once and share for llm and embedder.
        if self.share_key:
            match self.llm_api_key, self.emb_api_key:
                case None, None:
                    raise ValueError(
                        "When sharing API keys, both llm_api_key and emb_api_key "
                        "cannot be empty!"
                    )
                case str(), str():
                    raise ValueError(
                        "When sharing API keys, do not supply both llm_api_key and "
                        "emb_api_key."
                    )
                case None, str():
                    self.llm_api_key = self.emb_api_key
                case str(), None:
                    self.emb_api_key = self.llm_api_key

        llm_api_secret = wrap_api_key(self.llm_api_key)
        emb_api_secret = wrap_api_key(self.emb_api_key)

        self.model = ChatOpenAI(
            model=self.llm_model_name,
            max_completion_tokens=self.max_completion_tokens,
            base_url=self.llm_base_url,
            api_key=llm_api_secret,
            http_client=None if self.ssl_verify else httpx.Client(verify=False),
        )

        self.embedding = OpenAIEmbeddings(
            model=self.emb_model_name,
            base_url=self.emb_base_url,
            api_key=emb_api_secret,
            http_client=None if self.ssl_verify else httpx.Client(verify=False),
        )

        self.memory = AgentMemory(
            embedding_model=self.embedding, path=str(self.workspace / "memory")
        )

        self.last_agent_result = ""
        self.arxiv_state = []
        self.executor_state = {}
        self.planner_state = {}
        self.websearcher_state = {}

    def update_last_agent_result(self, result: str):
        self.last_agent_result = result

    @cached_property
    def arxiv_agent(self) -> ArxivAgent:
        return ArxivAgent(
            llm=self.model,
            summarize=self.arxiv_summarize,
            process_images=self.arxiv_process_images,
            max_results=self.arxiv_max_results,
            # rag_embedding=self.embedding,
            database_path=self.get_path(
                self.arxiv_database_path, "arxiv_downloaded_papers"
            ),
            summaries_path=self.get_path(
                self.arxiv_summaries_path, "arxiv_generated_summaries"
            ),
            vectorstore_path=self.get_path(
                self.arxiv_vectorstore_path, "arxiv_vectorstores"
            ),
            download_papers=self.arxiv_download_papers,
        )

    @cached_property
    def executor(self) -> ExecutionAgent:
        edb_path = self.workspace / "executor_checkpoint.db"
        edb_path.parent.mkdir(parents=True, exist_ok=True)
        econn = sqlite3.connect(str(edb_path), check_same_thread=False)
        self.executor_checkpointer = SqliteSaver(econn)
        return ExecutionAgent(
            llm=self.model,
            checkpointer=self.executor_checkpointer,
            agent_memory=self.memory,
        )

    @cached_property
    def planner(self) -> PlanningAgent:
        pdb_path = Path(self.workspace) / "planner_checkpoint.db"
        pdb_path.parent.mkdir(parents=True, exist_ok=True)
        pconn = sqlite3.connect(str(pdb_path), check_same_thread=False)
        self.planner_checkpointer = SqliteSaver(pconn)
        return PlanningAgent(
            llm=self.model,
            checkpointer=self.planner_checkpointer,
        )

    @cached_property
    def websearcher(self) -> WebSearchAgent:
        rdb_path = Path(self.workspace) / "websearcher_checkpoint.db"
        rdb_path.parent.mkdir(parents=True, exist_ok=True)
        rconn = sqlite3.connect(str(rdb_path), check_same_thread=False)
        self.websearcher_checkpointer = SqliteSaver(rconn)

        return WebSearchAgent(
            llm=self.model,
            checkpointer=self.websearcher_checkpointer,
        )

    @cached_property
    def rememberer(self) -> RecallAgent:
        return RecallAgent(llm=self.model, memory=self.memory)

    def run_arvix(self, prompt: str) -> str:
        llm_search_query = self.model.invoke(
            f"The user stated {prompt}. Generate between 1 and 8 words for a search query to address the users need. Return only the words to search."
        ).content
        print("Searching ArXiv for ", llm_search_query)

        if isinstance(llm_search_query, str):
            arxiv_result = self.arxiv_agent.invoke(
                arxiv_search_query=llm_search_query,
                context=prompt,
            )
            self.arxiv_state.append(arxiv_result)
            self.update_last_agent_result(arxiv_result)
            return f"[ArXiv Agent Output]:\n {self.last_agent_result}"
        else:
            raise RuntimeError("Unexpected error while running ArxivAgent!")

    def run_executor(self, prompt: str) -> str:
        if "messages" in self.executor_state and isinstance(
            self.executor_state["messages"], list
        ):
            self.executor_state["messages"].append(
                HumanMessage(
                    f"The last agent output was: {self.last_agent_result}\n"
                    f"The user stated: {prompt}"
                )
            )
            executor_state = self.executor.invoke(
                self.executor_state,
            )

            if isinstance(
                content := executor_state["messages"][-1].content, str
            ):
                self.update_last_agent_result(content)
            else:
                raise TypeError(
                    f"content is supposed to have type str! Instead, it is {content}"
                )
        else:
            self.executor_state = dict(
                workspace=self.workspace,
                messages=[
                    HumanMessage(
                        f"The last agent output was: {self.last_agent_result}\n The user stated: {prompt}"
                    )
                ],
            )
            self.executor_state = self.executor.invoke(
                self.executor_state,
            )
            self.update_last_agent_result(
                self.executor_state["messages"][-1].content
            )
        return f"[Executor Agent Output]:\n {self.last_agent_result}"

    def run_rememberer(self, prompt: str) -> str:
        memory_output = self.rememberer.remember(prompt)
        return f"[Rememberer Output]:\n {memory_output}"

    def run_chatter(self, prompt: str) -> str:
        chat_output = self.model.invoke(
            f"The last agent output was: {self.last_agent_result}\n The user stated: {prompt}"
        )

        if not isinstance(chat_output.content, str):
            raise TypeError(
                f"chat_output is not a str! Instead, it is: {chat_output}."
            )

        self.update_last_agent_result(chat_output.content)
        # return f"[{self.model.model_name}]: {self.last_agent_result}"
        return f"{self.last_agent_result}"

    def run_planner(self, prompt: str) -> str:
        self.planner_state.setdefault("messages", [])
        self.planner_state["messages"].append(
            HumanMessage(
                f"The last agent output was: {self.last_agent_result}\n"
                f"The user stated: {prompt}"
            )
        )
        self.planner_state = self.planner.invoke(
            self.planner_state,
        )

        plan = "\n\n\n".join(
            f"## {step['id']} -- {step['name']}\n\n"
            + "\n\n".join(
                f"* {key}\n    * {value}" for key, value in step.items()
            )
            for step in self.planner_state["plan_steps"]
        )
        self.update_last_agent_result(plan)
        return f"[Planner Agent Output]:\n {self.last_agent_result}"

    def run_websearcher(self, prompt: str) -> str:
        if self.websearcher_state:
            self.websearcher_state["messages"].append(
                HumanMessage(
                    f"The last agent output was: {self.last_agent_result}\n"
                    f"The user stated: {prompt}"
                )
            )
            self.websearcher_state = self.websearcher.invoke(
                self.websearcher_state,
            )
            self.update_last_agent_result(
                self.websearcher_state["messages"][-1].content
            )
        else:
            self.websearcher_state = {
                "messages": [
                    HumanMessage(
                        f"The last agent output was: {self.last_agent_result}\n"
                        f"The user stated: {prompt}"
                    )
                ]
            }
            self.websearcher_state = self.websearcher.invoke(
                self.websearcher_state,
            )
            self.update_last_agent_result(
                self.websearcher_state["messages"][-1].content
            )
        return f"[Planner Agent Output]:\n {self.last_agent_result}"


class UrsaRepl(Cmd):
    console = make_console()
    exit_message: str = "[dim]Exiting ursa..."
    _help_message: str = "[dim]For help, type: ? or help. Exit with Ctrl+d."
    prompt: str = "ursa> "

    def get_input(self, msg: str, end: str = "", **kwargs):
        # NOTE: Printing in rich with Prompt somehow gets removed when
        # backspacing. This is a workaround that captures the print output and
        # converts it to the proper string format for your terminal.
        with self.console.capture() as capture:
            self.console.print(msg, end=end, **kwargs)
        return input(capture.get())

    def __init__(self, hitl: HITL, **kwargs):
        self.hitl = hitl
        super().__init__(**kwargs)

    def show(self, msg: str, markdown: bool = True, **kwargs):
        self.console.print(Markdown(msg) if markdown else msg, **kwargs)

    def default(self, prompt: str):
        with self.console.status("Generating response"):
            response = self.hitl.run_chatter(prompt)
            self.show(response)

    def postcmd(self, stop: bool, line: str):
        print()
        return stop

    def do_exit(self, _: str):
        """Exit shell."""
        self.show(self.exit_message, markdown=False)
        return True

    def do_EOF(self, _: str):
        """Exit on Ctrl+D."""
        self.show(self.exit_message, markdown=False)
        return True

    def do_clear(self, _: str):
        """Clear the screen. Same as pressing Ctrl+L."""
        os.system("cls" if platform.system() == "Windows" else "clear")

    def emptyline(self):
        """Do nothing when an empty line is entered"""
        pass

    def run_agent(self, agent: str, run: Callable[[str], str]):
        # prompt = self.get_input(f"Enter your prompt for [emph]{agent}[/]: ")
        prompt = input(f"Enter your prompt for {agent}: ")
        with self.console.status("Generating response"):
            return run(prompt)

    def do_arxiv(self, _: str):
        """Run ArxivAgent"""
        self.show(self.run_agent("Arxiv Agent", self.hitl.run_arvix))

    def do_plan(self, _: str):
        """Run PlanningAgent"""
        self.show(self.run_agent("Planning Agent", self.hitl.run_planner))

    def do_execute(self, _: str):
        """Run ExecutionAgent"""
        self.show(self.run_agent("Execution Agent", self.hitl.run_executor))

    def do_web(self, _: str):
        """Run WebSearchAgent"""
        self.show(self.run_agent("Websearch Agent", self.hitl.run_websearcher))

    def do_recall(self, _: str):
        """Run RecallAgent"""
        self.show(self.run_agent("Recall Agent", self.hitl.run_rememberer))

    def run(self):
        """Handle Ctrl+C to avoid quitting the program"""
        # Print intro only once.
        self.show(f"[magenta]{ursa_banner}", markdown=False)
        self.show(self._help_message, markdown=False)

        while True:
            try:
                self.cmdloop()
                break  # Allows breaking out of loop if EOF is triggered.
            except KeyboardInterrupt:
                print(
                    "\n(Interrupted) Press Ctrl+D to exit or continue typing."
                )

    def do_models(self, _: str):
        """List models and base urls"""
        self.show(
            f"[dim]*[/] LLM: [emph]{self.hitl.model.model_name} "
            f"[dim]{self.hitl.llm_base_url}",
            markdown=False,
        )
        self.show(
            f"[dim]*[/] Embedding Model: [emph]{self.hitl.embedding.model} "
            f"[dim]{self.hitl.emb_base_url}",
            markdown=False,
        )


# TODO:
# * Add option to swap models in REPL
# * Add option for seed setting via flags
# * Name change: --llm-model-name -> llm
# * Name change: --emb-model-name -> emb
