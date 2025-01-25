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

plan_schema = {
    "type": "object",
    "properties": {
        "plan_title": {"type": "string"},
        "plan_amount": {"type": "number"},
        "plan_currency": {"type": "string"},
        "plan_descr": {"type": "string"},
        "plan_type": {"type": "string"},
        "plan_duration": {"type": "string"},
        "plan_features": {"type": "array", "items": {"type": "string"}},
        "plan_avatar": {"type": "string"}
    },
    "required": ["plan_title", "plan_amount", "plan_currency", "plan_type", "plan_duration", "plan_features"]
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
