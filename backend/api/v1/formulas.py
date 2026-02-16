"""
Formulas API v1 endpoint

Full implementation for formula management and execution.
"""

from datetime import datetime
from typing import List, Optional, Dict, Any
from pydantic import BaseModel
from sqlalchemy.orm import Session
from fastapi import APIRouter, Depends, HTTPException, status, Query

from backend.db import get_db
from backend.models.auth import User
from backend.core.security import get_current_user

router = APIRouter(prefix="/formulas", tags=["formulas-v1"])


# Schemas
class FormulaCreate(BaseModel):
    name: str
    expression: str
    description: Optional[str] = None
    variables: Optional[List[str]] = None
    project_id: Optional[int] = None


class FormulaUpdate(BaseModel):
    name: Optional[str] = None
    expression: Optional[str] = None
    description: Optional[str] = None
    variables: Optional[List[str]] = None


class FormulaResponse(BaseModel):
    id: int
    name: str
    expression: str
    description: Optional[str] = None
    variables: List[str]
    created_at: datetime
    updated_at: datetime
    project_id: Optional[int] = None
    created_by: int
    
    class Config:
        from_attributes = True


class FormulaExecuteRequest(BaseModel):
    variables: Dict[str, Any]


class FormulaExecuteResponse(BaseModel):
    formula_id: int
    result: Any
    execution_time_ms: float
    variables_used: Dict[str, Any]
    error: Optional[str] = None


class FormulaValidateRequest(BaseModel):
    expression: str


class FormulaValidateResponse(BaseModel):
    valid: bool
    message: str
    detected_variables: List[str]
    error: Optional[str] = None


# In-memory storage (replace with database in production)
_formulas = {}
_formula_id = 0


def _get_next_formula_id() -> int:
    global _formula_id
    _formula_id += 1
    return _formula_id


def _extract_variables(expression: str) -> List[str]:
    """Extract variable names from expression."""
    import re
    # Match variable names (letters, numbers, underscores, not starting with number)
    pattern = r'\b[a-zA-Z_][a-zA-Z0-9_]*\b'
    matches = re.findall(pattern, expression)
    # Filter out Python keywords and math functions
    keywords = {'if', 'else', 'for', 'while', 'def', 'class', 'import', 'from', 'return',
                'abs', 'round', 'max', 'min', 'sum', 'pow', 'len', 'int', 'float', 'str'}
    return sorted(list(set(m for m in matches if m not in keywords)))


def _validate_expression(expression: str) -> tuple[bool, str, List[str]]:
    """Validate formula expression for safety."""
    # Check for dangerous patterns
    dangerous = ['import', 'exec', 'eval', 'compile', '__', 'open', 'file', 'subprocess',
                 'os.', 'sys.', 'importlib', 'exec(', 'eval(']
    for pattern in dangerous:
        if pattern in expression.lower():
            return False, f"Expression contains forbidden pattern: {pattern}", []
    
    # Extract variables
    variables = _extract_variables(expression)
    
    # Try to compile
    try:
        compile(expression, '<string>', 'eval')
        return True, "Expression is valid", variables
    except SyntaxError as e:
        return False, f"Syntax error: {e}", variables
    except Exception as e:
        return False, f"Validation error: {e}", variables


def _execute_formula(expression: str, variables: Dict[str, Any]) -> tuple[Any, Optional[str]]:
    """Execute formula with given variables."""
    import time
    import math
    
    start = time.time()
    
    try:
        # Create safe namespace with only math operations
        safe_namespace = {
            'abs': abs, 'round': round, 'max': max, 'min': min, 'sum': sum,
            'pow': pow, 'len': len, 'int': int, 'float': float,
            'math': math,
        }
        safe_namespace.update(variables)
        
        # Compile and execute
        code = compile(expression, '<string>', 'eval')
        result = eval(code, {"__builtins__": {}}, safe_namespace)
        
        elapsed = (time.time() - start) * 1000
        return result, None
    except Exception as e:
        elapsed = (time.time() - start) * 1000
        return None, str(e)


@router.post("", response_model=FormulaResponse, status_code=201)
async def create_formula(
    payload: FormulaCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Create a new formula."""
    # Validate expression
    valid, message, detected_vars = _validate_expression(payload.expression)
    if not valid:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=message
        )
    
    formula_id = _get_next_formula_id()
    now = datetime.utcnow()
    
    formula = {
        "id": formula_id,
        "name": payload.name,
        "expression": payload.expression,
        "description": payload.description,
        "variables": payload.variables or detected_vars,
        "created_at": now,
        "updated_at": now,
        "project_id": payload.project_id,
        "created_by": current_user.id,
    }
    _formulas[formula_id] = formula
    
    return FormulaResponse(**formula)


@router.get("", response_model=List[FormulaResponse])
async def list_formulas(
    project_id: Optional[int] = None,
    search: Optional[str] = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """List all formulas with optional filtering."""
    formulas = list(_formulas.values())
    
    # Filter by project
    if project_id is not None:
        formulas = [f for f in formulas if f.get("project_id") == project_id]
    
    # Filter by search term
    if search:
        search_lower = search.lower()
        formulas = [
            f for f in formulas 
            if search_lower in f.get("name", "").lower() 
            or search_lower in f.get("description", "").lower()
        ]
    
    return [FormulaResponse(**f) for f in formulas]


@router.get("/{formula_id}", response_model=FormulaResponse)
async def get_formula(
    formula_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get a specific formula by ID."""
    formula = _formulas.get(formula_id)
    if not formula:
        raise HTTPException(status_code=404, detail="Formula not found")
    return FormulaResponse(**formula)


@router.put("/{formula_id}", response_model=FormulaResponse)
async def update_formula(
    formula_id: int,
    payload: FormulaUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Update an existing formula."""
    formula = _formulas.get(formula_id)
    if not formula:
        raise HTTPException(status_code=404, detail="Formula not found")
    
    # Check ownership (optional - can be removed for shared formulas)
    if formula.get("created_by") != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized to edit this formula")
    
    # Validate new expression if provided
    if payload.expression:
        valid, message, detected_vars = _validate_expression(payload.expression)
        if not valid:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=message
            )
        formula["expression"] = payload.expression
        formula["variables"] = payload.variables or detected_vars
    
    if payload.name:
        formula["name"] = payload.name
    if payload.description is not None:
        formula["description"] = payload.description
    if payload.variables and not payload.expression:
        formula["variables"] = payload.variables
    
    formula["updated_at"] = datetime.utcnow()
    
    return FormulaResponse(**formula)


@router.delete("/{formula_id}")
async def delete_formula(
    formula_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Delete a formula."""
    formula = _formulas.get(formula_id)
    if not formula:
        raise HTTPException(status_code=404, detail="Formula not found")
    
    if formula.get("created_by") != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized to delete this formula")
    
    del _formulas[formula_id]
    return {"message": "Formula deleted successfully"}


@router.post("/{formula_id}/execute", response_model=FormulaExecuteResponse)
async def execute_formula(
    formula_id: int,
    payload: FormulaExecuteRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Execute a formula with provided variable values."""
    formula = _formulas.get(formula_id)
    if not formula:
        raise HTTPException(status_code=404, detail="Formula not found")
    
    import time
    start = time.time()
    
    result, error = _execute_formula(formula["expression"], payload.variables)
    
    elapsed = (time.time() - start) * 1000
    
    return FormulaExecuteResponse(
        formula_id=formula_id,
        result=result,
        execution_time_ms=elapsed,
        variables_used=payload.variables,
        error=error,
    )


@router.post("/validate", response_model=FormulaValidateResponse)
async def validate_formula(payload: FormulaValidateRequest):
    """Validate a formula expression without saving it."""
    valid, message, variables = _validate_expression(payload.expression)
    
    return FormulaValidateResponse(
        valid=valid,
        message=message,
        detected_variables=variables,
        error=message if not valid else None,
    )


# =============================================================================
# Formula Library Endpoints
# =============================================================================

from backend.services.formula_library import (
    get_formula as get_lib_formula,
    list_formulas as list_lib_formulas,
    get_categories,
    execute_formula as execute_lib_formula,
)


class LibraryExecuteRequest(BaseModel):
    formula_id: str
    variables: Dict[str, Any]


class LibraryExecuteResponse(BaseModel):
    formula_id: str
    name: str
    result: Any
    unit: Optional[str]
    variables_used: Dict[str, Any]


@router.get("/library/list")
async def list_library_formulas(category: Optional[str] = None):
    """List formulas from the construction formula library."""
    return {
        "formulas": list_lib_formulas(category),
        "categories": get_categories(),
    }


@router.get("/library/{formula_id}")
async def get_library_formula(formula_id: str):
    """Get a specific formula from the library."""
    formula = get_lib_formula(formula_id)
    if not formula:
        raise HTTPException(status_code=404, detail="Formula not found in library")
    return formula


@router.post("/library/eval", response_model=LibraryExecuteResponse)
async def execute_library_formula(payload: LibraryExecuteRequest):
    """Execute a formula from the library with given variables."""
    try:
        result = execute_lib_formula(payload.formula_id, payload.variables)
        return LibraryExecuteResponse(**result)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Execution error: {str(e)}")


@router.get("/library/categories")
async def list_categories():
    """List all formula categories."""
    return get_categories()
