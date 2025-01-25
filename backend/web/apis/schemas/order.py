order_schema = {
    "$schema": "http://json-schema.org/draft-07/schema#",
    "type": "object",
    "properties": {
        "address_id": {
            "type": ["integer", "null"]  # Allow null values
        },
        "address": {
            "type": "object",
            "properties": {
                "first_name": {
                    "type": "string",
                    "maxLength": 140
                },
                "last_name": {
                    "type": "string",
                    "maxLength": 140
                },
                "zip_code": {
                    "type": "string",
                    "maxLength": 140
                },
                "street_address": {  # Corrected from "address" to "street_address"
                    "type": "string",
                    "maxLength": 140
                },
                "country": {
                    "type": "string",
                    "maxLength": 140
                },
                "city": {
                    "type": "string",
                    "maxLength": 140
                }
            },
            "required": ["first_name", "last_name", "zip_code", "street_address", "country", "city"]
        },
        "cart_items": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "product_id": {  # Changed from "id" to "product_id"
                        "type": "integer"
                    },
                    "quantity": {
                        "type": "integer",
                        "minimum": 1
                    }
                },
                "required": ["product_id", "quantity"]  # Updated required fields
            },
            "minItems": 1
        }
    },
    "anyOf": [
        { "required": ["cart_items", "address_id"] },  # Requires cart_items and address_id
        { "required": ["cart_items", "address"] }       # Requires cart_items and address
    ]
}