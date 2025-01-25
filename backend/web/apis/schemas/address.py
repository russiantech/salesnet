address_schema = {
    "type": "object",
    "properties": {
      "first_name": { "type": "string" },
      "last_name": { "type": "string" },
      "zip_code": { "type": "string" },
      "phone_number": { "type": "string" },
      "address": { "type": "string" },
      "city": { "type": "string" },
      "country": { "type": "string" }
    },
    
    "required": ["first_name", "last_name", "zip_code", "phone_number", "address", "city", "country"]
  }
