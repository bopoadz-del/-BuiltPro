"""
Construction Formula Library

Standard construction and engineering formulas.
"""

FORMULA_LIBRARY = {
    "name": "Construction Formula Library",
    "version": "1.0.0",
    "description": "Standard construction and engineering formulas",
    "formulas": {
        "concrete_volume": {
            "name": "Concrete Volume",
            "description": "Calculate volume of concrete for rectangular shapes",
            "expression": "length * width * height",
            "variables": ["length", "width", "height"],
            "units": {
                "length": "m",
                "width": "m",
                "height": "m",
                "result": "m³"
            },
            "category": "concrete"
        },
        "rebar_weight": {
            "name": "Rebar Weight",
            "description": "Calculate weight of reinforcing steel bars",
            "expression": "(diameter ** 2) / 162 * length * quantity",
            "variables": ["diameter", "length", "quantity"],
            "units": {
                "diameter": "mm",
                "length": "m",
                "quantity": "pcs",
                "result": "kg"
            },
            "category": "steel"
        },
        "slab_concrete": {
            "name": "Slab Concrete",
            "description": "Calculate concrete needed for a slab",
            "expression": "length * width * thickness",
            "variables": ["length", "width", "thickness"],
            "units": {
                "length": "m",
                "width": "m",
                "thickness": "m",
                "result": "m³"
            },
            "category": "concrete"
        },
        "column_concrete": {
            "name": "Column Concrete",
            "description": "Calculate concrete needed for columns",
            "expression": "3.14159 * (diameter / 2) ** 2 * height * quantity",
            "variables": ["diameter", "height", "quantity"],
            "units": {
                "diameter": "m",
                "height": "m",
                "quantity": "pcs",
                "result": "m³"
            },
            "category": "concrete"
        },
        "beam_concrete": {
            "name": "Beam Concrete",
            "description": "Calculate concrete needed for beams",
            "expression": "width * height * length * quantity",
            "variables": ["width", "height", "length", "quantity"],
            "units": {
                "width": "m",
                "height": "m",
                "length": "m",
                "quantity": "pcs",
                "result": "m³"
            },
            "category": "concrete"
        },
        "wall_bricks": {
            "name": "Wall Bricks",
            "description": "Calculate number of bricks needed for a wall",
            "expression": "(length * height * 10000) / (brick_length * brick_height) * (1 + wastage / 100)",
            "variables": ["length", "height", "brick_length", "brick_height", "wastage"],
            "units": {
                "length": "m",
                "height": "m",
                "brick_length": "cm",
                "brick_height": "cm",
                "wastage": "%",
                "result": "pcs"
            },
            "category": "masonry"
        },
        "paint_area": {
            "name": "Paint Area",
            "description": "Calculate paintable surface area",
            "expression": "2 * (length + width) * height - openings",
            "variables": ["length", "width", "height", "openings"],
            "units": {
                "length": "m",
                "width": "m",
                "height": "m",
                "openings": "m²",
                "result": "m²"
            },
            "category": "finishing"
        },
        "roof_tiles": {
            "name": "Roof Tiles",
            "description": "Calculate number of roof tiles needed",
            "expression": "(length * width) / (tile_length * tile_width) * (1 + overlap / 100)",
            "variables": ["length", "width", "tile_length", "tile_width", "overlap"],
            "units": {
                "length": "m",
                "width": "m",
                "tile_length": "m",
                "tile_width": "m",
                "overlap": "%",
                "result": "pcs"
            },
            "category": "roofing"
        },
        "excavation_volume": {
            "name": "Excavation Volume",
            "description": "Calculate excavation volume with slopes",
            "expression": "((top_length + bottom_length) / 2) * ((top_width + bottom_width) / 2) * depth",
            "variables": ["top_length", "top_width", "bottom_length", "bottom_width", "depth"],
            "units": {
                "top_length": "m",
                "top_width": "m",
                "bottom_length": "m",
                "bottom_width": "m",
                "depth": "m",
                "result": "m³"
            },
            "category": "earthwork"
        },
        "steel_plate_weight": {
            "name": "Steel Plate Weight",
            "description": "Calculate weight of steel plates",
            "expression": "length * width * thickness * 7850",
            "variables": ["length", "width", "thickness"],
            "units": {
                "length": "m",
                "width": "m",
                "thickness": "m",
                "result": "kg"
            },
            "category": "steel"
        }
    },
    "categories": {
        "concrete": "Concrete and cement works",
        "steel": "Steel reinforcement and structures",
        "masonry": "Brick and block works",
        "finishing": "Paint and finishing works",
        "roofing": "Roof covering materials",
        "earthwork": "Excavation and earth moving"
    }
}


def get_formula(formula_id: str) -> dict:
    """Get a formula by ID."""
    return FORMULA_LIBRARY["formulas"].get(formula_id)


def list_formulas(category: str = None) -> dict:
    """List all formulas, optionally filtered by category."""
    formulas = FORMULA_LIBRARY["formulas"]
    if category:
        return {k: v for k, v in formulas.items() if v.get("category") == category}
    return formulas


def get_categories() -> dict:
    """Get all formula categories."""
    return FORMULA_LIBRARY["categories"]


def execute_formula(formula_id: str, variables: dict) -> dict:
    """Execute a formula with given variables."""
    formula = get_formula(formula_id)
    if not formula:
        raise ValueError(f"Formula not found: {formula_id}")
    
    import math
    
    # Create safe namespace with only math operations
    safe_namespace = {
        'abs': abs, 'round': round, 'max': max, 'min': min, 'sum': sum,
        'pow': pow, 'len': len, 'int': int, 'float': float,
        'math': math,
    }
    safe_namespace.update(variables)
    
    # Compile and execute
    code = compile(formula["expression"], '<string>', 'eval')
    result = eval(code, {"__builtins__": {}}, safe_namespace)
    
    return {
        "formula_id": formula_id,
        "name": formula["name"],
        "result": result,
        "unit": formula["units"].get("result"),
        "variables_used": variables
    }
