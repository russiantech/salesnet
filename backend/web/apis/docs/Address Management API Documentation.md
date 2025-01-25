Address Management API Documentation

This document provides details for the Address Management API routes, which allow users to manage their addresses, 
including creating, retrieving, updating, and deleting addresses. These routes are secured by JWT-based authentication and provide pagination where necessary.

1. Get User Addresses (with pagination)

Endpoint:  
`GET /addresses/<user_id>/user`

Description:  
This endpoint retrieves all addresses for a specified user. It supports pagination by allowing the client to specify the page number and page size.

Request Parameters:
- `page`: The page number for pagination (default is `1`).
- `page_size`: The number of items per page (default is `5`).

Response:
- Success (200):  
  Returns a list of addresses for the user, paginated.
  
  {
    "message": "Addresses fetched successfully.",
    "data": {
      "addresses": [ /* List of addresses */ ],
      "pagination": {
        "page": 1,
        "page_size": 5,
        "total": 10,
        "total_pages": 2
      }
    }
  }

- Error (500):  
  In case of unexpected errors.
  
  {
    "error": "Unexpected error: <error_message>",
    "status_code": 500
  }
  

2. List All or One Address for the Authenticated User

Endpoint:  
`GET /addresses` or `GET /addresses/<address_id>`

Description:  
This endpoint allows the authenticated user to list all their addresses or fetch a specific address by ID. 
Pagination is supported for the list of addresses.

Request Parameters:
- `page`: The page number for pagination (default is `1`).
- `page_size`: The number of items per page (default is `5`).

Response:
- Success (200):  
  - If a specific address is requested, returns that address.
  
  {
    "message": "Address fetched successfully.",
    "data": {
      "id": 1,
      "first_name": "John",
      "last_name": "Doe",
      "street_address": "123 Elm St",
      "city": "New York",
      "country": "USA",
      "zip_code": "10001",
      "phone_number": "+1234567890",
      "created_at": "2025-01-01T12:00:00Z"
    }
  }
  

- Error (404):  
  If the specified address is not found.
  
  {
    "message": "Address not found.",
    "status_code": 404
  }
  

3. Create a New Address

Endpoint:  
`POST /addresses`

Description:  
This endpoint allows the authenticated user to create a new address.

Request Body:
{
  "first_name": "John",
  "last_name": "Doe",
  "zip_code": "10001",
  "phone_number": "+1234567890",
  "address": "123 Elm St",
  "city": "New York",
  "country": "USA"
}

Response:
- Success (201):  
  Returns the newly created address with status `201`.
  
  {
    "message": "Address created successfully.",
    "data": {
      "id": 1,
      "first_name": "Edet",
      "last_name": "James",
      "street_address": "123 Elm St",
      "city": "New York",
      "country": "USA",
      "zip_code": "10001",
      "phone_number": "+1234567890",
      "created_at": "2025-01-01T12:00:00Z"
    }
  }
  

- Error (400):  
  If the request body doesn't meet validation requirements.
  
  {
    "message": "Validation error: <error_message>",
    "status_code": 400
  }
  

4. Update an Existing Address

Endpoint:  
`PUT /addresses/<address_id>`

Description:  
This endpoint allows the authenticated user to update an existing address.

Request Body:
{
  "first_name": "John",
  "last_name": "Doe",
  "zip_code": "10002",
  "phone_number": "+1234567890",
  "address": "124 Elm St",
  "city": "New York",
  "country": "USA"
}

Response:
- Success (200):  
  Returns the updated address.
  
  {
    "message": "Address updated successfully.",
    "data": {
      "id": 1,
      "first_name": "John",
      "last_name": "Doe",
      "street_address": "124 Elm St",
      "city": "New York",
      "country": "USA",
      "zip_code": "10002",
      "phone_number": "+1234567890",
      "created_at": "2025-01-01T12:00:00Z"
    }
  }
  

- Error (403):  
  If the user is not authorized to update the address (not the owner or admin).
  
  {
    "message": "Access forbidden: insufficient permissions.",
    "status_code": 403
  }
  

- Error (404):  
  If the address ID is not found.
  
  {
    "message": "Address not found",
    "status_code": 404
  }
  

5. Delete an Address

Endpoint:  
`DELETE /addresses/<address_id>`

Description:  
This endpoint allows the authenticated user to delete an existing address.

Response:
- Success (200):  
  Returns a success message.
  
  {
    "message": "Address deleted successfully."
  }
  

- Error (403):  
  If the user is not authorized to delete the address (not the owner or admin).
  
  {
    "message": "Permission denied.",
    "status_code": 403
  }
  

- Error (404):  
  If the address ID is not found.
  
  {
    "message": "Address not found",
    "status_code": 404
  }

Error Handling:
In the event of an unexpected error, the API will return a `500` status code along with a message indicating the error:

{
  "message": "Unexpected error: <error_message>",
  "status_code": 500
}


Authentication:
All endpoints require JWT-based authentication, which must be included in the request headers as follows:

Authorization: Bearer <JWT_TOKEN>

Validation:
Requests for creating or updating addresses will be validated using a predefined  schema (`address_schema`). If validation fails, a `400` status code will be returned along with the validation error message.

Conclusion:
This documentation covers all necessary routes for managing user addresses. 
It includes endpoint descriptions, request parameters, response formats, error handling, and authentication details. 
It is important to follow the structure and requirements outlined in the documentation to ensure successful interaction with the API.