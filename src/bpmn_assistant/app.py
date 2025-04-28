from fastapi import FastAPI
from fastapi.responses import JSONResponse, StreamingResponse
from starlette.middleware.cors import CORSMiddleware

import os
import sys

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))


from bpmn_assistant.api.requests import (
    BpmnToJsonRequest,
    ConversationalRequest,
    DetermineIntentRequest,
    ModifyBpmnRequest,
)
from bpmn_assistant.core import handle_exceptions
from bpmn_assistant.core.enums import OutputMode
from bpmn_assistant.services import (
    BpmnJsonGenerator,
    BpmnModelingService,
    BpmnXmlGenerator,
    ConversationalService,
    determine_intent,
)
from bpmn_assistant.utils import (
    replace_reasoning_model,
    get_available_providers,
    get_llm_facade,
)

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

bpmn_modeling_service = BpmnModelingService()
bpmn_xml_generator = BpmnXmlGenerator()


@app.post("/bpmn_to_json")
@handle_exceptions
async def _bpmn_to_json(request: BpmnToJsonRequest) -> JSONResponse:
    """
    Convert the BPMN XML to its JSON representation
    """
    bpmn_json_generator = BpmnJsonGenerator()
    result = bpmn_json_generator.create_bpmn_json(request.bpmn_xml)
    return JSONResponse(content=result)


@app.get("/available_providers")
@handle_exceptions
async def _available_providers() -> JSONResponse:
    """
    Get the available LLM providers
    """
    providers = get_available_providers()
    return JSONResponse(content=providers)


@app.post("/determine_intent")
@handle_exceptions
async def _determine_intent(request: DetermineIntentRequest) -> JSONResponse:
    """
    Determine the intent of the user query
    """
    model = replace_reasoning_model(request.model)
    llm_facade = get_llm_facade(model)
    intent = determine_intent(llm_facade, request.message_history)
    return JSONResponse(content=intent)


@app.post("/modify")
@handle_exceptions
async def _modify(request: ModifyBpmnRequest) -> JSONResponse:
    """
    Modify the BPMN process based on the user query. If the request does not contain a BPMN JSON,
    then create a new BPMN process. Otherwise, edit the existing BPMN process.
    """
    llm_facade = get_llm_facade(request.model)
    text_llm_facade = get_llm_facade(request.model, OutputMode.TEXT)

    if request.process:
        process = bpmn_modeling_service.edit_bpmn(
            llm_facade, text_llm_facade, request.process, request.message_history
        )
    else:
        process = bpmn_modeling_service.create_bpmn(
            llm_facade,
            request.message_history,
        )

    bpmn_xml_string = bpmn_xml_generator.create_bpmn_xml(process)
    return JSONResponse(content={"bpmn_xml": bpmn_xml_string, "bpmn_json": process})


@app.post("/talk")
async def _talk(request: ConversationalRequest) -> StreamingResponse:
    model = replace_reasoning_model(request.model)
    conversational_service = ConversationalService(model)

    if request.needs_to_be_final_comment:
        response_generator = conversational_service.make_final_comment(
            request.message_history, request.process
        )
    else:
        response_generator = conversational_service.respond_to_query(
            request.message_history, request.process
        )

    return StreamingResponse(response_generator)
