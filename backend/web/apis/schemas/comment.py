comment_schema = {
    "type": "object",
    "properties": {
        "content": {"type": "string", "minLength": 1},  # Ensure content is a non-empty string
        "rating": {"type": "number"},  # Ensure rating is a number
    },
    "anyOf": [  # At least one of content or rating must be provided
        {"required": ["content"]},
        {"required": ["rating"]}
    ],
    "additionalProperties": False  # Disallow extra properties
}
