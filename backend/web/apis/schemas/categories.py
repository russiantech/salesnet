category_schema = {
  "$schema": "http://json-schema.org/draft-07/schema#",
  "type": "object",
  "properties": {
    "id": {
      "type": "integer",
      "description": "Unique identifier for the category"
    },
    "parent_id": {
      "type": "integer",
      "description": "ID of the parent category, if this is a subcategory"
    },
    "name": {
      "type": "string",
      "maxLength": 140,
      "description": "The name of the category"
    },

    "description": {
      "type": "string",
      "maxLength": 255,
      "description": "A short description of the category"
    },
    "is_deleted": {
      "type": "boolean",
      "description": "Flag indicating whether the category is marked for deletion"
    },

    "image_urls": {
      "type": "array",
      "items": {
        "type": "string",
        "description": "File path of an image related to the category"
      },
      "description": "List of image URLs related to the category"
    },
    "children": {
      "type": "array",
      "items": {
        "$ref": "#"
      },
      "description": "List of child categories, if any"
    },
    
    "parent": {
      "type": "array",
      "items": {
        "$ref": "#"
      },
      "description": "List containing the parent category, if any"
    },
    "products": {
      "type": "array",
      "items": {
        "type": "object",
        "description": "Product object with details"
      },
      "description": "List of products associated with the category"
    }
  },
  "required": [
    "name",
    "description"
  ]
}

category_schema_old = {
  "$schema": "http://json-schema.org/draft-07/schema#",
  "type": "object",
  "properties": {
    "id": {
      "type": "integer",
      "description": "Unique identifier for the category"
    },
    "parent_id": {
      "type": "integer",
      "description": "ID of the parent category, if this is a subcategory"
    },
    "name": {
      "type": "string",
      "maxLength": 140,
      "description": "The name of the category"
    },
    "slug": {
      "type": "string",
      "maxLength": 140,
      "description": "The slug used for the URL path"
    },
    "description": {
      "type": "string",
      "maxLength": 255,
      "description": "A short description of the category"
    },
    "is_deleted": {
      "type": "boolean",
      "description": "Flag indicating whether the category is marked for deletion"
    },
    "created_at": {
      "type": "string",
      "format": "date-time",
      "description": "Timestamp when the category was created"
    },
    "updated_at": {
      "type": "string",
      "format": "date-time",
      "description": "Timestamp when the category was last updated"
    },
    "image_urls": {
      "type": "array",
      "items": {
        "type": "string",
        "description": "File path of an image related to the category"
      },
      "description": "List of image URLs related to the category"
    },
    "children": {
      "type": "array",
      "items": {
        "$ref": "#"
      },
      "description": "List of child categories, if any"
    },
    "parent": {
      "type": "array",
      "items": {
        "$ref": "#"
      },
      "description": "List containing the parent category, if any"
    },
    "products": {
      "type": "array",
      "items": {
        "type": "object",
        "description": "Product object with details"
      },
      "description": "List of products associated with the category"
    }
  },
  "required": [
    "name",
    "slug",
    "is_deleted",
    "created_at",
    "updated_at"
  ]
}
