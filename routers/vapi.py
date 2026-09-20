from fastapi import APIRouter, Request, Depends
from pydantic import BaseModel, ConfigDict
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Any, Dict, Optional, List

from database import get_db
import crud
import schemas

router = APIRouter(prefix="/vapi", tags=["vapi"])

class VapiTool(BaseModel):
    name: str
    arguments: Dict[str, Any]

class VapiMessage(BaseModel):
    type: str
    toolCallId: Optional[str] = None
    tool: Optional[VapiTool] = None
    call: Optional[Dict[str, Any]] = None
    
    model_config = ConfigDict(extra="allow")

class VapiPayload(BaseModel):
    message: VapiMessage
    
    model_config = ConfigDict(extra="allow")

@router.post("/function-webhook")
async def vapi_function_webhook(
    payload: VapiPayload, 
    db: AsyncSession = Depends(get_db)
):
    """
    Webhook for Vapi.ai Custom Tools.
    """
    print("\n========== VAPI REQUEST ==========")
    print(payload.model_dump())
    print("==================================\n")

    message = payload.message
    
    # If it's a test ping or something else without a tool call, return 200
    if not message.tool or not message.toolCallId:
        print("NO TOOL CALL DETECTED")
        return {"status": "ok"}
        
    tool_name = message.tool.name
    tool_args = message.tool.arguments
    tool_call_id = message.toolCallId

    print(f"TOOL NAME: {tool_name}")
    print(f"TOOL ARGS: {tool_args}")
    print(f"TOOL CALL ID: {tool_call_id}")
    
    result_data = {}
    
    if tool_name == "create_patient":
        try:
            patient_create_data = schemas.PatientCreate(**tool_args)
            new_patient = await crud.create_patient(db, patient_create_data)
            
            result_data = {
                "status": "success",
                "message": f"Patient {new_patient.first_name} {new_patient.last_name} registered successfully.",
                "patient_id": str(new_patient.patient_id)
            }
        except Exception as e:
            print(f"\n=== VAPI TOOL ERROR ===")
            print(f"Raw tool_args payload: {tool_args}")
            print(f"Exact Exception: {repr(e)}")
            print(f"=======================\n")
            
            result_data = {
                "status": "error",
                "message": f"Failed to register patient: {str(e)}"
            }
            
    else:
        result_data = {"status": "error", "message": f"Unknown function name: {tool_name}"}

    # Vapi strictly requires this response format
    return {
        "results": [
            {
                "toolCallId": tool_call_id,
                "result": str(result_data)
            }
        ]
    }
