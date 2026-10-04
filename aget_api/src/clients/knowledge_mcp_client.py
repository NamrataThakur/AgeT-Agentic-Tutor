from contextlib import AsyncExitStack
from typing import Any, List
import asyncio
from mcp import ClientSession
from mcp.client.stdio import stdio_client, StdioServerParameters

import os
import sys
os.pardir

parent_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir))

# 2. Append this parent directory to Python's search paths
if parent_dir not in sys.path:
    sys.path.append(parent_dir)

from knowledge_mcp.schema import GetQSBankRequest,GetQSBankResponse, CreateQSBankResponse, CreateQSBankRequest



class KnowledgeMCPClient:
    def __init__(self, server_command : str, server_args : List[str]):
        self.server_command = server_command
        self.server_args = server_args

        self._exit_stack : AsyncExitStack | None = None
        self.client_session : ClientSession | None = None

    #---Connecting to the Knowledge MCP Server ---
    #Knowledge Service does the connection and close of the client session:
    async def connect(self) -> None:

        #Step 1: First check if a session is already exisiting, if yes then raise a RuntimeError:
        if self.client_session is not None:
            raise RuntimeError("Knowledge MCP Client is already connected..!")

        #Step 2: No session exisiting, let's start creating a session:
        #Step 2a: Initialise the async context manager to handle all the session contexts:
        exit_stack = AsyncExitStack()

        try:
            #Step 2b: Construct the server parameters required to connect to the MCP Server:
            server_params = StdioServerParameters(command=self.server_command,
                                                  args=self.server_args)

            #Step 2c: Get the read and write streams and enter these streams to the async context manager:
            read_stream, write_stream = await exit_stack.enter_async_context(cm=
                                                                             stdio_client(
                                                                                 server=server_params
                                                                                )
                                                                            )

            #Step 2d: Get the client session and enter the session to the async context manager:
            session = await exit_stack.enter_async_context(cm=
                                                           ClientSession(
                                                               read_stream=read_stream,
                                                               write_stream=write_stream
                                                            )
                                                        )
            #Step 3: Start the session:
            await session.initialize()

            self._exit_stack = exit_stack
            self.client_session = session
            print("Connection to Knowledge MCP Server is Successfull..!")

        except Exception as e:
            await exit_stack.aclose()
            self._exit_stack = None
            self.client_session = None
            raise Exception(f"Exception raised while connecting to MCP : {str(e)}")


    async def close(self) -> None:

        exit_stack = self._exit_stack

        #Close the Async Context Manager:
        if exit_stack is not None:
            exit_stack.aclose()

        self._exit_stack = None

        #Close the session:
        self.client_session = None


    async def ensure_connected(self) -> ClientSession:

        #Step 1: First check if a session is already exisiting, if yes then raise a RuntimeError:
        if self.client_session is None:
            raise RuntimeError("Knowledge MCP Client is not connected..!")

        return self.client_session


    async def list_tools(self) -> List[Any]:

        session = self.ensure_connected()
        result = await session.list_tools()
        return result.tools


    async def call_tool(self, tool_name: str, args: dict) -> Any:

        session = self.ensure_connected()
        return await session.call_tool(name=tool_name, arguments=args)


    #---Knowledge MCP Capabilities---
    async def get_question_bank(self, topic_name: str, user_input: str, user_id : str, interview_id : str) -> GetQSBankResponse:

        if not topic_name:
            raise ValueError("topic_name must not be empty")

        if not user_input:
            raise ValueError("user_input must not be empty")

        #Client-side timeout of 10 secs
        async with asyncio.timeout(10):
            
            return await self.call_tool(tool_name="get_question_bank", 
                                    args={
                                            "topic_id" : topic_name,
                                            "user_input" : user_input,
                                            "user_id" : user_id,
                                            "interview_id" : interview_id

                                        }
                                )

    async def create_question_bank(self, topic_name: str, user_input: str) -> CreateQSBankResponse:

        if not topic_name:
            raise ValueError("topic_name must not be empty")

        if not user_input:
            raise ValueError("user_input must not be empty")


        #Client-side timeout of 10 secs
        async with asyncio.timeout(10):

            return await self.call_tool(tool_name="create_question_bank",
                                    args={
                                        "topic_id" : topic_name,
                                        "user_input" : user_input
                                    }
                                )

    



