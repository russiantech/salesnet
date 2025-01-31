page_schema = {
    "type": "object",
    "properties": {
        "id": {"type": "integer"},
        "name": {"type": "string", "maxLength": 255},
        "username": {"type": "string", "maxLength": 255},
        "avatar": {"type": "string", "maxLength": 255},
        "slug": {"type": "string", "maxLength": 255},
        "description": {"type": "string"},
        "email": {"type": "string", "format": "email"},
        "phone": {"type": "string"},
        "password": {"type": "string"},
        "image": {"type": ["string", "null"]},
        "about_me": {"type": "string"},
        "balance": {"type": "number"},
        "withdrawal_password": {"type": "string"},
        "valid_email": {"type": "boolean"},
        "publish_on": {"type": "string", "format": "date-time"},
        "is_deleted": {"type": "boolean"},
        "socials": {
            "type": "object",
            "properties": {
                "facebook": {"type": "string"},
                "instagram": {"type": "string"},
                "x": {"type": "string"},
                "linkedin": {"type": "string"},
                "whatsapp": {"type": "string"}
            },
            "additionalProperties": False
        },
        "address": {
            "type": "object",
            "properties": {
                "state": {"type": "string"},
                "city": {"type": "string"},
                "street": {"type": "string"},
                "zipcode": {"type": "string"}
            },
            "additionalProperties": False
        },
        "bank": {
            "type": "object",
            "properties": {
                "bank_name": {"type": "string"},
                "account_number": {"type": "number"},
                'ifsc_code':{"type": "string"},
            },
            "additionalProperties": False
        }
    },
    "required": ["name", "description", "username", "email", "password"]
}

page_update_schema = {
    "type": "object",
    "properties": {
        "id": {"type": "integer"},
        "name": {"type": "string", "maxLength": 255},
        "username": {"type": "string", "maxLength": 255},
        "avatar": {"type": "string", "maxLength": 255},
        "slug": {"type": "string", "maxLength": 255},
        "description": {"type": "string"},
        "email": {"type": "string", "format": "email"},
        "phone": {"type": "string"},
        "password": {"type": "string"},
        "image": {"type": ["string", "null"]},
        "about_me": {"type": "string"},
        "balance": {"type": "number"},
        "withdrawal_password": {"type": "string"},
        "valid_email": {"type": "boolean"},
        "publish_on": {"type": "string", "format": "date-time"},
        "is_deleted": {"type": "boolean"},
        "socials": {
            "type": "object",
            "properties": {
                "facebook": {"type": "string"},
                "instagram": {"type": "string"},
                "x": {"type": "string"},
                "linkedin": {"type": "string"},
                "whatsapp": {"type": "string"}
            },
            "additionalProperties": False
        },
        "address": {
            "type": "object",
            "properties": {
                "state": {"type": "string"},
                "city": {"type": "string"},
                "street": {"type": "string"},
                "zipcode": {"type": "string"}
            },
            "additionalProperties": False
        },
        "bank": {
            "type": "object",
            "properties": {
                "bank_name": {"type": "string"},
                "account_number": {"type": "number"},
                "ifsc_code": {"type": "string"}
            },
            "additionalProperties": False
        }
    },
    "required": ["name", "description"]  #// 'username' and 'password' are not required for updates
}

page_schema_former = {
    "type": "object",
    "properties": {
        "id": {"type": "integer"},
        "name": {"type": "string", "maxLength": 255},
        "username": {"type": "string", "maxLength": 255},
        "avatar": {"type": "string", "maxLength": 255},
        "slug": {"type": "string", "maxLength": 255},
        "description": {"type": "string"},
        "email": {"type": "string", "format": "email"},
        "phone": {"type": "string"},
        "password": {"type": "string"},
        "image": {"type": ["string", "null"]},
        "about_me": {"type": "string"},
        "balance": {"type": "number"},
        "withdrawal_password": {"type": "string"},
        "valid_email": {"type": "boolean"},
        
        "publish_on": {"type": "string", "format": "date-time"},
        "is_deleted": {"type": "boolean"}
    },
    
    "required": ["name", "description"]
}
