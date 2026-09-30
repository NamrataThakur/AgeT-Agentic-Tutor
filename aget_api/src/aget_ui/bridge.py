#This file is the bridge between UI and Chainlit. 
# When the background job is completed, SSE send a message to UI. 
# UI forwards that message to the Chainlit through window.postMessage that triggers 
# the Chainlit's @cl.on_window_message. 
# This handles the message and displays the Continue Interview / Restart Interview button. 
# This button re-starts the graph.

import json
import chainlit as cl


@cl.on_window_message
async def handle_message(payload: str):
    print("Payload received from UI..!")

    try:
        if isinstance(payload, str):
            payload = json.loads(payload)

    except Exception as e:
        print(f"Invalid Message Received. Error: {str(e)}")
        return
    
    message = payload.get("type")
    data = payload.get("data")

    if message == "aget-job-completed" or message == "aget-job-failed":
        interview_id = data.get("interview_id", "")
        job_id = data.get("job_id", "")
        user_id = data.get("user_id", "")
        message = data["message"]

        if not interview_id:
            raise ValueError(f"Interview Id cannot be empty..!")

        if not job_id:
            raise ValueError(f"Job Id cannot be empty ..!")

        if not user_id:
            raise ValueError(f"User Id cannot be empty ..!")

        await show_continue(interview_id=interview_id,
                            user_id=user_id, 
                            job_id=job_id,
                            message=message)

    else:
        raise ValueError(f"Invalid Message Received: {message}")


async def show_continue(interview_id: str, 
                        user_id: str,
                        job_id: str, 
                        message: str):

    if message == "Question Bank Generation Failed.":
        label = "Restart Interview"
    else:
        label = "Continue Interview"

    actions = [
        cl.Action(
            name="continue_interview",
            label=label,
            payload={
                "interview_id" : interview_id,
                "user_id" : user_id,
                "job_id" : job_id
            }
        )
    ]

    await cl.Message(content=(f"Background Job is Completed. "
                              f"You can {label.lower()}."), 
                     actions=actions).send()
    

    

