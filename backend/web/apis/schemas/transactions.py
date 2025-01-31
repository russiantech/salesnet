pay_schema = {
    "type": "object",
    "properties": {
        "username": {"type": "string"},
        "email": {"type": "string", "format": "email"},
        "phone": {"type": "string"},
        "amount": {"type": "number"}
    },
    "required": ["amount", "email"]
}