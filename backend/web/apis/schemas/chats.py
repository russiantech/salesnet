
chat_schema = {
    "type": "object",
    "properties": {
        "to_username": { "type": "string" },
        "from_username": { "type": "string" },
        "text": { "type": "string" },
        "sticker": { "type": "string" },
        "media": { "type": "string" },
        "user_id": { "type": "string" },
        "last_seen": { "type": "string" },
    },
    "required": ["to_username", "from_username"],
    "anyOf": [
        { 
        "required": ["text"],
        },
        { 
        "required": ["media"],
        },
        { 
        "required": ["sticker"],
        },
        { 
        "required": ["text", "sticker"]
        },
        {
        "required": ["text", "media"]
        },
        {
        "required": ["sticker", "media"]
        }
    ]
}

# Centralized event schemas
chat_event_schemas = {
    'save_chat_request': {
        "type": "object",
        "properties": {
            "to_username": {"type": "string"},
            "from_username": {"type": "string"},
            "text": {
                "type": ["string", "null"]  # Allow text to be a string or null
            },
            "sticker": {
                "type": ["string", "null"]  # Allow sticker to be a string or null
            },
            "media_url": {
                "type": ["string", "null"]  # Allow media_url to be a string or null
            }
        },
        "required": ["to_username", "from_username"],
        "anyOf": [
            {"required": ["text"], "not": {"required": ["sticker", "media_url"]}},  # Only text provided
            {"required": ["sticker"], "not": {"required": ["text", "media_url"]}},  # Only sticker provided
            {"required": ["media_url"], "not": {"required": ["text", "sticker"]}},  # Only media_url provided
            {"required": ["text", "sticker"]},  # Both text and sticker provided
            {"required": ["text", "media_url"]},  # Both text and media_url provided
            {"required": ["sticker", "media_url"]}  # Both sticker and media_url provided
        ],
        "additionalProperties": False  # Prevents extra properties
    }
}

chat_event_schemas = {
    
    # 'save_chat_request': {
    #     "type": "object",
    #     "properties": {
    #         "to_username": {"type": "string"},
    #         "from_username": {"type": "string"},
    #         "text": {"type": "string"},
    #         "sticker": {"type": "string"},
    #         "media_url": {"type": "string"}
    #     },
    #     "required": ["to_username", "from_username"],
    #     "anyOf": [
    #         {"required": ["text"]},
    #         {"required": ["media"]},
    #         {"required": ["sticker"]},
    #         {"required": ["text", "sticker"]},
    #         {"required": ["text", "media"]},
    #         {"required": ["sticker", "media_url"]}
    #     ]
    # },
    'save_chat_request': {
        "type": "object",
        "properties": {
            "to_username": {"type": "string"},
            "from_username": {"type": "string"},
            "text": {
                "type": ["string", "null"]  # Allow text to be a string or null
            },
            "sticker": {
                "type": ["string", "null"]  # Allow sticker to be a string or null
            },
            "media_url": {
                "type": ["string", "null"]  # Allow media_url to be a string or null
            }
        },
        "required": ["to_username", "from_username"],
        "anyOf": [
            {"required": ["text"], "not": {"required": ["sticker", "media_url"]}},  # Only text provided
            {"required": ["sticker"], "not": {"required": ["text", "media_url"]}},  # Only sticker provided
            {"required": ["media_url"], "not": {"required": ["text", "sticker"]}},  # Only media_url provided
            {"required": ["text", "sticker"]},  # Both text and sticker provided
            {"required": ["text", "media_url"]},  # Both text and media_url provided
            {"required": ["sticker", "media_url"]}  # Both sticker and media_url provided
        ],
        # "additionalProperties": False  # Prevents extra properties
    },
    
    'fetch_chat_request': {
        "type": "string",
        "required": ["username"]
    },
    
    'remove_chat_request': {
        "type": "object",
        "properties": {
            "chat_id": {"type": "integer"},
            "user_id": {"type": "integer"}
        },
        "required": ["chat_id", "user_id"]
    },
    'update_chat_request': {
        "type": "object",
        "properties": {
            "from_username": {"type": "integer"},
            "chat_id": {"type": "integer"},
            "chat_content": {"type": "string"}
        },
        "required": ["chat_id", "chat_content", "from_username"]
    },
    'typing_request': {
        "type": "object",
        "properties": {
            "to_username": {"type": "string"},
            "from_username": {"type": "string"}
        },
        "required": ["to_username", "from_username"]
    },
}