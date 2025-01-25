# Validation shemas

product_schema = {
    "type": "object",
    "properties": {
        "id": {"type": "integer"},
        "name": {"type": "string", "maxLength": 255},
        "slug": {"type": "string", "maxLength": 255},
        "description": {"type": "string"},
        "price": {"type": "integer"},
        "stock": {"type": "integer"},
        "publish_on": {"type": "string", "format": "date-time"},
        "is_deleted": {"type": "boolean"},
        "created_at": {"type": "string", "format": "date-time"},
        "updated_at": {"type": "string", "format": "date-time"},
    },
    "required": ["name", "description", "price", "stock"]
}


product_schema_old = {
  "type": "object",
  "properties": {
    "id": {
      "type": "number",
      "description": "Unique identifier for the product."
    },
    "name": {
      "type": "string",
      "maxLength": 255,
      "description": "Name of the product (required)."
    },

    "description": {
      "type": "string",
      "description": "Detailed description of the product (required)."
    },
    "price": {
      "type": "number",
      "description": "Price of the product in the smallest currency unit (e.g., cents, required)."
    },
    
    "stock": {
      "type": "number",
      "description": "The stock quantity available for the product (required)."
    },
    "publish_on": {
      "type": "string",
      "format": "date-time",
      "description": "The date and time when the product is published."
    },
    "is_deleted": {
      "type": "boolean",
      "description": "Indicates if the product is deleted or not."
    },
    "created_at": {
      "type": "string",
      "format": "date-time",
      "description": "The date and time when the product was created."
    },
    "updated_at": {
      "type": "string",
      "format": "date-time",
      "description": "The date and time when the product was last updated."
    },
    "tags": {
      "type": "array",
      "description": "List of tags associated with the product.",
      "items": {
        "type": "object",
        "properties": {
          "id": {
            "type": "integer",
            "description": "ID of the tag."
          },
          "name": {
            "type": "string",
            "description": "Name of the tag."
          }
        },
        "required": ["id", "name"]
      }
    },
    "categories": {
      "type": "array",
      "description": "List of categories associated with the product.",
      "items": {
        "type": "object",
        "properties": {
          "id": {
            "type": "integer",
            "description": "ID of the category."
          },
          "name": {
            "type": "string",
            "description": "Name of the category."
          }
        },
        "required": ["id", "name"]
      }
    },
    "image_urls": {
      "type": "array",
      "description": "List of image URLs associated with the product.",
      "items": {
        "type": "string",
        "format": "uri",
        "description": "URL of the product image."
      }
    }
  },
  "required": ["name", "description", "price"]
}

product_schema2 = {
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



