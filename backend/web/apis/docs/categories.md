# Category Management API Documentation

This API provides endpoints for managing categories, including creating, retrieving, updating, and deleting categories. Categories may also include images uploaded via multipart form data.

## Base URL:
`/categories`

#1. **Create Category**

**Endpoint**: `POST /categories`  
**Description**: This endpoint allows the creation of a new category. A category can include a name, description, and images. Images should be uploaded as files in a `multipart/form-data` request.

#### Request Body:
- **Content-Type**: `application/json` or `multipart/form-data`
- **Request Payload (JSON)**:
  ```json
  {
    "name": "string",
    "description": "string (optional)"
  }
  ```

- **Request Payload (Multipart Form-Data)**:
  - `name` (required): The name of the category.
  - `description` (optional): A description of the category.
  - `images[]` (optional): A list of image files to be uploaded.

#### Response:
- **Success**:
  - **HTTP Status**: `201 Created`
  - **Body**:
    ```json
    {
      "message": "Category created successfully.",
      "data": {
        "id": 1,
        "name": "string",
        "description": "string",
        "images": [
          {
            "file_path": "string",
            "file_name": "string",
            "original_name": "string",
            "file_size": "integer"
          }
        ]
      }
    }
    ```

- **Error**:
  - **HTTP Status**: `400 Bad Request`
  - **Body**:
    ```json
    {
      "message": "Content-Type must be application/json or multipart/form-data"
    }
    ```
  
  Other possible errors include validation and database errors, for which appropriate messages will be provided.

---

### 2. **Get Categories**

**Endpoint**: `GET /categories`  
**Description**: This endpoint retrieves a paginated list of all categories. Pagination is supported via query parameters `page` and `per_page`.

#### Query Parameters:
- `page` (optional, default: 1): The page number to retrieve.
- `per_page` (optional, default: 10): The number of categories per page.

#### Response:
- **Success**:
  - **HTTP Status**: `200 OK`
  - **Body**:
    ```json
    {
      "message": "Categories fetched successfully.",
      "data": {
        "page": 1,
        "per_page": 10,
        "total": 100,
        "categories": [
          {
            "id": 1,
            "name": "string",
            "description": "string",
            "created_at": "string",
            "updated_at": "string"
          }
        ]
      }
    }
    ```

- **Error**:
  - **HTTP Status**: `500 Internal Server Error`
  - **Body**:
    ```json
    {
      "message": "Error fetching categories: string"
    }
    ```

---

### 3. **Get Single Category**

**Endpoint**: `GET /categories/{category_id}`  
**Description**: This endpoint retrieves details of a specific category identified by its `category_id`. It returns the category with its associated images and optionally includes product data.

#### Path Parameter:
- `category_id` (required): The ID of the category to retrieve.

#### Response:
- **Success**:
  - **HTTP Status**: `200 OK`
  - **Body**:
    ```json
    {
      "message": "Category fetched successfully.",
      "data": {
        "id": 1,
        "name": "string",
        "description": "string",
        "images": [
          {
            "file_path": "string",
            "file_name": "string",
            "original_name": "string",
            "file_size": "integer"
          }
        ],
        "products": [
          {
            "id": 1,
            "name": "string",
            "description": "string"
          }
        ]
      }
    }
    ```

- **Error**:
  - **HTTP Status**: `404 Not Found`
  - **Body**:
    ```json
    {
      "message": "Category not found."
    }
    ```

### 4. **Update Category**

**Endpoint**: `PUT /categories/{category_id}`  
**Description**: This endpoint allows an admin or dev user to update the details of a category identified by its `category_id`. Only the name and description can be updated.

#### Path Parameter:
- `category_id` (required): The ID of the category to update.

#### Request Body:
- **Content-Type**: `application/json`
- **Request Payload**:
  ```json
  {
    "name": "string (optional)",
    "description": "string (optional)"
  }
  ```

#### Response:
- **Success**:
  - **HTTP Status**: `200 OK`
  - **Body**:
    ```json
    {
      "message": "Category updated successfully."
    }
    ```

- **Error**:
  - **HTTP Status**: `404 Not Found`
  - **Body**:
    ```json
    {
      "message": "Category not found."
    }
    ```

  Other possible errors include database issues, leading to appropriate error responses.

---

### 5. **Delete Category**

**Endpoint**: `DELETE /categories/{category_id}`  
**Description**: This endpoint allows an admin or dev user to delete a category identified by its `category_id`.

#### Path Parameter:
- `category_id` (required): The ID of the category to delete.

#### Response:
- **Success**:
  - **HTTP Status**: `200 OK`
  - **Body**:
    ```json
    {
      "message": "Category deleted successfully."
    }
    ```

- **Error**:
  - **HTTP Status**: `404 Not Found`
  - **Body**:
    ```json
    {
      "message": "Category not found."
    }
    ```

  Other possible errors include database issues, leading to appropriate error responses.

---

## Authentication & Permissions:
- **JWT Authentication**: Required for the `PUT` and `DELETE` methods. Use the `jwt_required()` decorator to ensure the request is authorized.
- **Access Control**: The `access_required()` decorator ensures only users with roles `admin` or `dev` can update or delete categories.

---

## Error Handling:
- **Validation Errors**: If the incoming data doesn't conform to the defined schema, a `400 Bad Request` response is returned with a description of the error.
- **Database Errors**: On database issues (e.g., IntegrityError), a `500 Internal Server Error` is returned.
- **Unexpected Errors**: Any other errors are caught and returned as `500 Internal Server Error` with a description.

This documentation provides a comprehensive guide for interacting with the category management API, outlining the expected behaviors and responses for each endpoint.