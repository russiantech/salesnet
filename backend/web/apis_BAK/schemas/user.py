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
        "username": {"type": "string"},
        "email": {"type": "string", "format": "email"},
        "phone": {"type": "string"},
        "password": {"type": "string"}
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

update_user_schema = {
    "type": "object",
    "properties": {
        "user_id": {"type": "number"},
        "username": {"type": "string"},
        "email": {"type": "string", "format": "email"},
        "password": {"type": "string"},
        "withdrawal_password": {"type": "string"},
        "phone": {"type": "string"},
        "name": {"type": "string"},
        "gender": {"type": "string"},
        "membership": {"type": "string"},
        "balance": {"type": "number"},
        "about": {"type": "string"},
        "verified": {"type": "boolean"},
        "ip": {"type": "string"},
        "image": {"type": ["string", "null"]}
    },
    "required": ["username", "email", "password", "withdrawal_password"]
}

validTokenSchema = {
    "type": "object",
    "properties": {
        "token": {"type": "string"},
        "email": {"type": "string", "format": "email"}
    },
    "required": ["token", "email"]
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

# JSON Schema for password reset validation
reset_password_schema = {
    "type": "object",
    "properties": {
        "password": {"type": "string", "minLength": 5},
    },
    
    "required": ["password"]
}
