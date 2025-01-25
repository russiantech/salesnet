**API Documentation for Creating and Managing Product Comments**

**Endpoint: Create a Comment for a Product**

- **URL:** `/api/products/<product_slug>/comments`
- **Method:** `POST`
- **Authentication:** JWT Required (User must be logged in)
- **Request Body:**
  ```json
  {
    "content": "Updated my review after using this product more. It's even better than I thought!",
    "rating": 4
  }


- **Path Parameters:**
  - `product_slug`: The unique identifier for the product (slug). Example: `safe-toward-guy-bed-sell-gas`

- **Request Body Parameters:**
  - `content` (string): The review text for the product.
  - `rating` (integer, optional): The rating of the product (from 1 to 5). If not provided, it defaults to `None`.

- **Success Response (201):**
  - **Status:** `201 Created`
  - **Body:**
  ```json
  {
    "comment": [{
      "content": "Updated my review after using this product more. It's even better than I thought!",
      "created_at": "Thu, 02 Jan 2025 17:33:01 GMT",
      "id": 36,
      "rating": 4
    }],
    "message": "Comment created successfully.",
    "page_meta": {
      "current_page_number": 1,
      "has_next_page": false,
      "has_prev_page": false,
      "next_page_url": null,
      "offset": 0,
      "prev_page_url": null,
      "requested_page_size": 1,
      "total_items_count": 1,
      "total_pages_count": 1
    },
    "success": true
  }
  ```

- **Error Response (400):**
  - **Status:** `400 Bad Request`
  - **Body:**
  ```json
  {
    "message": "Validation error: Content is required.",
    "success": false
  }
  ```

- **Error Response (404):**
  - **Status:** `404 Not Found`
  - **Body:**
  ```json
  {
    "message": "Product not found.",
    "success": false
  }
  ```

- **Error Response (500):**
  - **Status:** `500 Internal Server Error`
  - **Body:**
  ```json
  {
    "message": "Database error: <Error Message>",
    "success": false
  }
  ```

---

#**Endpoint: List Comments for a Product**

- **URL:** `/api/products/<product_slug>/comments`
- **Method:** `GET`
- **Authentication:** Optional
- **Query Parameters:**
  - `page`: (integer, optional) Page number of the results. Defaults to `1`.
  - `page_size`: (integer, optional) Number of results per page. Defaults to `5`.

- **Path Parameters:**
  - `product_slug`: The unique identifier for the product (slug). Example: `safe-toward-guy-bed-sell-gas`

- **Success Response (200):**
  - **Status:** `200 OK`
  - **Body:**
  ```json
  {
    "comment": [{
      "content": "Updated my review after using this product more. It's even better than I thought!",
      "created_at": "Thu, 02 Jan 2025 17:33:01 GMT",
      "id": 36,
      "rating": 4
    }],
    "message": "Comments fetched successfully.",
    "page_meta": {
      "current_page_number": 1,
      "has_next_page": false,
      "has_prev_page": false,
      "next_page_url": null,
      "offset": 0,
      "prev_page_url": null,
      "requested_page_size": 1,
      "total_items_count": 1,
      "total_pages_count": 1
    },
    "success": true
  }
  ```

- **Error Response (404):**
  - **Status:** `404 Not Found`
  - **Body:**
  ```json
  {
    "message": "Product not found.",
    "success": false
  }
  ```

---

#**Endpoint: Update an Existing Comment**

- **URL:** `/api/comments/<int:comment_id>`
- **Method:** `PUT`
- **Authentication:** JWT Required (User must be logged in)
- **Path Parameters:**
  - `comment_id`: The unique ID of the comment to be updated.

- **Request Body:**
  ```json
  {
    "content": "Updated my review after using this product more. It's even better than I thought!",
    "rating": 4
  }
  ```

- **Success Response (200):**
  - **Status:** `200 OK`
  - **Body:**
  ```json
  {
    "comment": [{
      "content": "Updated my review after using this product more. It's even better than I thought!",
      "created_at": "Thu, 02 Jan 2025 17:33:01 GMT",
      "id": 36,
      "rating": 4
    }],
    "message": "Comment updated successfully.",
    "success": true
  }
  ```

- **Error Response (403):**
  - **Status:** `403 Forbidden`
  - **Body:**
  ```json
  {
    "message": "Permission denied.",
    "success": false
  }
  ```

- **Error Response (404):**
  - **Status:** `404 Not Found`
  - **Body:**
  ```json
  {
    "message": "Comment not found.",
    "success": false
  }
  ```

- **Error Response (500):**
  - **Status:** `500 Internal Server Error`
  - **Body:**
  ```json
  {
    "message": "Unexpected error: <Error Message>",
    "success": false
  }
  ```

---

#**Endpoint: Delete a Comment**

- **URL:** `/api/comments/<int:comment_id>`
- **Method:** `DELETE`
- **Authentication:** JWT Required (User must be logged in)
- **Path Parameters:**
  - `comment_id`: The unique ID of the comment to be deleted.

- **Success Response (200):**
  - **Status:** `200 OK`
  - **Body:**
  ```json
  {
    "message": "Comment deleted successfully.",
    "success": true
  }
  ```

- **Error Response (403):**
  - **Status:** `403 Forbidden`
  - **Body:**
  ```json
  {
    "message": "Permission denied.",
    "success": false
  }
  ```

- **Error Response (404):**
  - **Status:** `404 Not Found`
  - **Body:**
  ```json
  {
    "message": "Comment not found.",
    "success": false
  }
  ```

- **Error Response (500):**
  - **Status:** `500 Internal Server Error`
  - **Body:**
  ```json
  {
    "message": "Unexpected error: <Error Message>",
    "success": false
  }
  ```

---

**Note:**
- Ensure that the product exists before submitting comments.
- Only users with valid JWT tokens can create or update comments. Admin users or the original commenter have permissions to modify comments.