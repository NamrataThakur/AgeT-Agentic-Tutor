from pathlib import Path
import os
import sys
os.pardir

parent_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir))

# 2. Append this parent directory to Python's search paths
if parent_dir not in sys.path:
    sys.path.append(parent_dir)

from graph.workflow import create_workflow_graph

class InterviewService:
    def __init__(self, compiled_graph):
        self.graph = compiled_graph #create_workflow_graph().compile()


    @staticmethod
    def extract_response(output):
        context = output.get("response", None)

        if context is None:
            return "No response"

        return context

    
    async def process_text(self, user_id : str, interview_id: str, message : str):

        state = {
                    "source": "local",
                    "user_id" : user_id,
                    "interview_id" : interview_id,
                    "raw_input": {
                        "modality": "text",
                        "data": message,
                        "mime_type": "text/plain",
                    },
                }
        result = await self.graph.ainvoke(input=state)

        response = self.extract_response(output=result)

        return response

    async def process_audio(self, user_id : str, interview_id: str, audio_path : str):

        state = {
                    "source": "local",
                    "user_id" : user_id,
                    "interview_id" : interview_id,
                    "raw_input": {
                        "modality": "audio",
                        "data": str(audio_path),
                        "mime_type": "audio/wav",
                    },
                }

        result = await self.graph.ainvoke(input=state)
        
        response = self.extract_response(output=result)

        return response


    async def resume_interview(self, user_id : str, interview_id: str, message : str):
        state = {
                    "source": "local",
                    "user_id" : user_id,
                    "interview_id" : interview_id,
                    "raw_input": {
                        "modality": "text",
                        "data": message,
                        "mime_type": "text/plain",
                    },
                }
        result = await self.graph.ainvoke(input=state)

        response = self.extract_response(output=result)

        return response