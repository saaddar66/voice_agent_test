import json
from fastapi import APIRouter, Request, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from typing import Any, Dict, Optional, List

from database import get_db
import crud
import schemas

router = APIRouter(prefix="/vapi", tags=["vapi"])

@router.post("/function-webhook")
async def vapi_function_webhook(
    request: Request, 
    db: AsyncSession = Depends(get_db)
):
    """
    Robust Webhook for Vapi.ai Custom Tools.
    Handles multiple versions of the Vapi tool-call payload.
    """
    try:
        payload_dict = await request.json()
    except Exception:
        return {"status": "ok"}
        
    print("\n========== VAPI REQUEST ==========")
    print(json.dumps(payload_dict, indent=2))
    print("==================================\n")

    message = payload_dict.get("message", {})
    message_type = message.get("type")
    
    tool_calls_to_process = []
    
    # 1. Check for the modern toolWithToolCallList structure
    if message_type == "tool-calls" and "toolWithToolCallList" in message:
        for tool_item in message.get("toolWithToolCallList", []):
            tool_call = tool_item.get("toolCall", {})
            func = tool_call.get("function", {})
            
            tool_name = func.get("name")
            tool_call_id = tool_call.get("id")
            args = func.get("arguments", {})
            
            if isinstance(args, str):
                try:
                    args = json.loads(args)
                except:
                    args = {}
                    
            if tool_name and tool_call_id:
                tool_calls_to_process.append({
                    "id": tool_call_id,
                    "name": tool_name,
                    "arguments": args
                })
                
    # 2. Check for the older structure
    elif "tool" in message and "toolCallId" in message:
        tool = message.get("tool", {})
        tool_name = tool.get("name")
        tool_call_id = message.get("toolCallId")
        args = tool.get("arguments", {})
        
        if tool_name and tool_call_id:
            tool_calls_to_process.append({
                "id": tool_call_id,
                "name": tool_name,
                "arguments": args
            })

    if not tool_calls_to_process:
        print("NO VALID TOOL CALL DETECTED")
        return {"status": "ok"}
        
    results = []
    
    for tool_call in tool_calls_to_process:
        tool_name = tool_call["name"]
        tool_args = tool_call["arguments"]
        tool_call_id = tool_call["id"]
        
        print(f"PROCESSING TOOL: {tool_name}, ID: {tool_call_id}")
        
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
                print(f"=== VAPI TOOL ERROR ===")
                print(f"Exact Exception: {repr(e)}")
                result_data = {
                    "status": "error",
                    "message": f"Failed to register patient: {str(e)}"
                }
        else:
            result_data = {"status": "error", "message": f"Unknown function name: {tool_name}"}
            
        results.append({
            "toolCallId": tool_call_id,
            "result": str(result_data)
        })

    return {"results": results}
