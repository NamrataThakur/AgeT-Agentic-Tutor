from fastmcp import FastMCP

import os
import sys
os.pardir

parent_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir))

# 2. Append this parent directory to Python's search paths
if parent_dir not in sys.path:
    sys.path.append(parent_dir)


from knowledge_mcp.tools.create_question_bank import CreateQuestionBankTool
from knowledge_mcp.tools.get_question_bank import GetQuestionBankTool

from api.container.mcp_application_container import MCPApplicationContainer

container = MCPApplicationContainer()

def register_mcp_tools(mcp: FastMCP, container : MCPApplicationContainer):
     
    mcp.add_tool(
        name = "get_question_bank",

        description=("Retrieve the latest question bank for a topic." 
                    "If the question bank is missing, stale, or being regenerated, "
                    "return the current status and job information."),

        fn=container.get_question_bank_tool.get_question_bank,

        tags={"question_bank", "fetch", "regeneration"},
    )
    
    mcp.add_tool(
        name = "create_question_bank",

        description="Create the question bank for a topic.",

        fn=container.create_question_bank_tool.create_question_bank,

        tags={"question_bank", "creation"},
    )


mcp = FastMCP("Knowledge_MCP")
register_mcp_tools(mcp=mcp, container=container)

if __name__ == "__main__":
    mcp.run(transport="stdio")