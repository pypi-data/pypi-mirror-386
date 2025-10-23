
from typing import Any, Callable, Optional
from langchain_core.prompts import ChatPromptTemplate
from langchain_openai.chat_models.base import BaseChatOpenAI
from langchain_community.callbacks.openai_info import OpenAICallbackHandler
from langchain_core.messages import SystemMessage, HumanMessage
from pydantic import BaseModel, Field
from tenacity import retry, stop_after_attempt, wait_incrementing
import logging

from bioguider.utils.utils import escape_braces, increase_token_usage

logger = logging.getLogger(__name__)

class RetryException(Exception):
    """Exception need to retry"""

    pass

class CommonAgentResult(BaseModel):
    reasoning_process: str = Field(
        description="A detailed explanation of the thought process or reasoning steps taken to reach a conclusion."
    )

class CommonAgent:
    def __init__(self, llm: BaseChatOpenAI):
        self.llm = llm
        self.exception: RetryException | None = None
        self.token_usage: dict | None = None

    def go(
        self,
        system_prompt: str,
        instruction_prompt: str,
        schema: any,
        pre_process: Optional[Callable] = None,
        post_process: Optional[Callable] = None,
        **kwargs: Optional[Any],
    ):
        """
        execute agent

        Args:
        system_prompt str: system prompt
        instruction_prompt str: user prompt to guide how llm execute agent
        schema pydantic.BaseModel or json schema: llm output result schema
        pre_process Callable or None: pre-processor that would be executed before llm.invoke
        post_process Callable or None: post-processor that would be executed after llm.invoke
        kwargs None or dict: args for pre_proces and post_process

        Return:
        (output that comply with input args `schema`)
        """
        self._initialize()
        if pre_process is not None:
            is_OK = pre_process(**kwargs)
            if not is_OK:  # skip
                return
        
        return self._invoke_agent(
            system_prompt,
            instruction_prompt,
            schema,
            post_process,
            **kwargs,
        )

    def _initialize(self):
        self.exception = None
        self.token_usage = None

    def _process_retryexception_message(
        self, prompt: ChatPromptTemplate
    ) -> ChatPromptTemplate:
        if self.exception is None:
            return prompt

        existing_messages = prompt.messages
        updated_messages = existing_messages + [("human", str(self.exception))]
        self.exception = None
        updated_prompt = ChatPromptTemplate.from_messages(updated_messages)
        return updated_prompt

    def _incre_token_usage(self, token_usage):
        incremental_token_usage = token_usage
        if not isinstance(token_usage, dict):
            incremental_token_usage = vars(incremental_token_usage)
        self.token_usage = increase_token_usage(
            self.token_usage, incremental_token_usage
        )

    @retry(
        stop=stop_after_attempt(5),
        wait=wait_incrementing(start=1.0, increment=3, max=10),
    )
    def _invoke_agent(
        self,
        system_prompt: str,
        instruction_prompt: str,
        schema: any,
        post_process: Optional[Callable] = None,
        **kwargs: Optional[Any],
    ) -> tuple[Any, Any, dict | None, Any | None]:
        system_prompt = escape_braces(system_prompt)
        prompt = ChatPromptTemplate.from_messages([
            ("system", system_prompt),
            ("human", instruction_prompt),
        ])
        # Initialize the callback handler
        callback_handler = OpenAICallbackHandler()

        updated_prompt = self._process_retryexception_message(prompt)
        agent = updated_prompt | self.llm.with_structured_output(schema)
        try:
            res = agent.invoke(
                input={},
                config={
                    "callbacks": [callback_handler],
                },
            )
            self._incre_token_usage(callback_handler)
        except Exception as e:
            logger.error(str(e))
            raise e
        processed_res = res
        if post_process is not None:
            try:
                processed_res = post_process(res, **kwargs)
            except RetryException as e:
                logger.error(str(e))
                self.exception = e
                raise e
            except Exception as e:
                logger.error(str(e))
                raise e
        return res, processed_res, self.token_usage, None
    