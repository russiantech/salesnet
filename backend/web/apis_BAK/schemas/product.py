# Validation shemas

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


product_schema = {
#   "$schema": "http://json-schema.org/draft-07/schema#",
  "type": "object",
  "required": ["name", "description", "price", "stock"],
  "properties": {
    "id": {
      "type": "integer",
      "readOnly": True
    },
    "name": {
      "type": "string",
      "maxLength": 255
    },
    "slug": {
      "type": "string",
      "pattern": "^[a-zA-Z0-9-_]+$",
      "maxLength": 255
    },
    "description": {
      "type": "string",
      "minLength": 1
    },
    "price": {
      "type": "integer",
      "minimum": 0
    },
    "stock": {
      "type": "integer",
      "minimum": 0
    },
    "created_at": {
      "type": "string",
      "format": "date-time",
      "readOnly": True
    },
    "updated_at": {
      "type": "string",
      "format": "date-time",
      "readOnly": True
    },
    "publish_on": {
      "type": "string",
      "format": "date-time"
    },
    "tags": {
      "type": "array",
      "items": {
        "type": "integer"
      }
    },
    "categories": {
      "type": "array",
      "items": {
        "type": "integer"
      }
    },
    "comments": {
      "type": "array",
      "items": {
        "type": "object",
        "properties": {
          "id": { "type": "integer" },
          "content": { "type": "string" },
          "created_at": {
            "type": "string",
            "format": "date-time"
          }
        },
        "required": ["id", "content", "created_at"]
      }
    }
  },
  "additionalProperties": False
}



