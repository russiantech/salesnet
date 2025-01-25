### Address Management API Documentation

This documentation outlines the implementation and usage of API endpoints for managing user addresses in a Flask application.

**GET /addresses**
Retrieve a paginated list of all addresses for the authenticated user.

- **URL:** `/addresses`
- **Method:** `GET`
- **Headers:**
  - `Authorization: Bearer <JWT_TOKEN>`
- **Query Parameters:**
  - `page`: Page number (default: 1)
  - `page_size`: Number of addresses per page (default: 5)
- **Response:**
  - **Success (200):**
    ```json
    {
      "message": "Addresses fetched successfully",
      "data": {
        "addresses": [...],
        "pagination": {
          "current_page": 1,
          "total_pages": 2,
          "total_items": 10
        }
      }
    }
    ```
  - **Error (401):** Unauthorized access.
  - **Error (500):** Unexpected server error.

#### **GET /addresses/<address_id>**
Retrieve details of a specific address by ID for the authenticated user.

- **URL:** `/addresses/<address_id>`
- **Method:** `GET`
- **Headers:**
  - `Authorization: Bearer <JWT_TOKEN>`
- **Response:**
  - **Success (200):**
    ```json
    {
      "message": "Address fetched successfully.",
      "data": { "address": { ... } }
    }
    ```
  - **Error (404):** Address not found.
  - **Error (500):** Unexpected server error.

#### **POST /addresses**
Create a new address for the authenticated user.

- **URL:** `/addresses`
- **Method:** `POST`
- **Headers:**
  - `Authorization: Bearer <JWT_TOKEN>`
  - `Content-Type: application/json`
- **Request Body:**
  ```json
  {
    "first_name": "John",
    "last_name": "Doe",
    "zip_code": "12345",
    "phone_number": "+1234567890",
    "address": "123 Sample Street",
    "city": "Sample City",
    "country": "Country X"
  }
  ```
- **Response:**
  - **Success (201):**
    ```json
    {
      "message": "Address created successfully.",
      "data": { "address": { ... } }
    }
    ```
  - **Error (400):** Validation error.
  - **Error (500):** Unexpected server error.

#### **PUT /addresses/<address_id>**
Update an existing address for the authenticated user.

- **URL:** `/addresses/<address_id>`
- **Method:** `PUT`
- **Headers:**
  - `Authorization: Bearer <JWT_TOKEN>`
  - `Content-Type: application/json`
- **Request Body:** (Any of the following fields can be updated)
  ```json
  {
    "first_name": "Jane",
    "city": "New City"
  }
  ```
- **Response:**
  - **Success (200):**
    ```json
    {
      "message": "Address updated successfully.",
      "data": { "address": { ... } }
    }
    ```
  - **Error (403):** Permission denied.
  - **Error (404):** Address not found.
  - **Error (400):** Validation error.
  - **Error (500):** Unexpected server error.

#### **DELETE /addresses/<address_id>**
Delete an existing address for the authenticated user.

- **URL:** `/addresses/<address_id>`
- **Method:** `DELETE`
- **Headers:**
  - `Authorization: Bearer <JWT_TOKEN>`
- **Response:**
  - **Success (204):**
    ```json
    {
      "message": "Address deleted successfully."
    }
    ```
  - **Error (403):** Permission denied.
  - **Error (404):** Address not found.
  - **Error (500):** Unexpected server error.

---

### Additional Notes
- **Authentication:** All endpoints require a valid JWT token.
- **Validation:** JSON payloads are validated using a predefined schema (`address_schema`).
- **Pagination:** Used for listing addresses with configurable `page` and `page_size`.
- **Error Handling:** Errors are returned in a consistent format with appropriate status codes and messages.