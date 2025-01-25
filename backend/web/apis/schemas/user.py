# Validation shemas
signin_schema = {
    "type": "object",
    "properties": {
        "username": {"type": "string"},
        "password": {"type": "string"},
        "remember": {"type": "boolean"}
    },
    "required": ["username", "password"]
}

signup_schema = {
    "type": "object",
    "properties": {
        "user_id": {"type": "number"},
        "name": {"type": "string"},
        "username": {"type": "string"},
        "email": {"type": "string", "format": "email"},
        "phone": {"type": "string"},
        "password": {"type": "string"},
        "image": {"type": ["string", "null"]},
        "gender": {"type": "string"},
        "about_me": {"type": "string"},
        "membership": {"type": "string"},
        "balance": {"type": "number"},
        "withdrawal_password": {"type": "string"},
        "valid_email": {"type": "boolean"},
        "ip": {"type": "string"},
    },
    "required": ["username", "phone", "email", "password"]
}

request_schema = {
    "type": "object",
    "properties": {
        "name": {"type": "string", "format": "string"},
        "email": {"type": "string", "format": "email"},
        "phone": {"type": "string"},
        "budget": {"type": "number"},
        "details": {"type": "string"},
        "concern": {"type": "string"}
    },
    "required": ["email", "details"]
}

validTokenSchema = {
    "type": "object",
    "properties": {
        "token": { "type": "string" },
        "password": { "type": "string" },
        "email": { "type": "string", "format": "email" }
    },
    "anyOf": [
        { "required": ["token"] },
        { "required": ["email"] }
    ]
}


# JSON schema for request validation
reset_password_email_schema = {
    "type": "object",
    "properties": {
        "email": {
            "type": "string",
            "format": "email",
        },
    },
    "required": ["email"],
    "additionalProperties": False,
}

# JSON Schema for password change validation
change_password_schema = {
    "type": "object",
    "properties": {
        "confirm_password": {"type": "string", "minLength": 5},
        "new_password": {"type": "string", "minLength": 5},
        "current_password": {"type": "string", "minLength": 5},
    },
    
    "required": ["confirm_password", "new_password", "current_password"]
}
