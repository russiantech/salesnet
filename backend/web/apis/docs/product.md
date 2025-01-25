Documentation of the product API endpoints, detailing their structure, valid data, and interaction methods.

---

# Product API Documentation

## Overview
The Product API provides endpoints to manage products in the system, allowing users to create, retrieve, update, and delete products. All endpoints require user authentication via JWT.

### Base URL
```
/products
```

## Endpoints

### 1. Retrieve a List of Products
**Method:** `GET`  
**URL:** `/products`  
**Authentication:** Required

#### Query Parameters:
- `page` (optional, integer): The page number to retrieve (default is 1).
- `page_size` (optional, integer): The number of products per page (default is 5).

#### Response:
- **Success:** Returns a paginated list of products.
- **Error:** Returns an error message if an exception occurs.

#### Example Request:
```
GET /products?page=1&page_size=5
```

---

### 2. Retrieve a Product by ID
**Method:** `GET`  
**URL:** `/products/<product_id>/product`  
**Authentication:** Required

#### Path Parameters:
- `product_id` (required, integer): The ID of the product to retrieve.

#### Response:
- **Success:** Returns the product details.
- **Error:** Returns an error if the product is not found.

#### Example Request:
```
GET /products/123/product
```

---

### 3. Retrieve a Product by Slug
**Method:** `GET`  
**URL:** `/products/<product_slug>/slug`  
**Authentication:** Required

#### Path Parameters:
- `product_slug` (required, string): The slug of the product to retrieve.

#### Response:
- **Success:** Returns the product details.
- **Error:** Returns an error if the product is not found.

#### Example Request:
```
GET /products/sample-product/slug
```

---

### 4. Fetch Products by User
**Method:** `GET`  
**URL:** `/products/<user_id>/user`  
**Authentication:** Required

#### Path Parameters:
- `user_id` (required, integer): The ID of the user whose products to fetch.

#### Query Parameters:
- `page` (optional, integer): The page number to retrieve (default is 1).
- `page_size` (optional, integer): The number of products per page (default is 5).

#### Response:
- **Success:** Returns a paginated list of products associated with the user.
- **Error:** Returns an error if the user is not found.

#### Example Request:
```
GET /products/456/user?page=1&page_size=5
```

---

### 5. Fetch Products by Page
**Method:** `GET`  
**URL:** `/products/<page_id>/page`  
**Authentication:** Required

#### Path Parameters:
- `page_id` (required, integer): The ID of the page to filter products.

#### Query Parameters:
- `page` (optional, integer): The page number to retrieve (default is 1).
- `page_size` (optional, integer): The number of products per page (default is 5).

#### Response:
- **Success:** Returns a paginated list of products associated with the page.
- **Error:** Returns an error if the page is not found.

#### Example Request:
```
GET /products/789/page?page=1&page_size=5
```

---

### 6. Fetch Products by Category
**Method:** `GET`  
**URL:** `/products/<int:category_id>/category`  
**Authentication:** Required

#### Path Parameters:
- `category_id` (required, integer): The ID of the category to filter products.

#### Query Parameters:
- `page` (optional, integer): The page number to retrieve (default is 1).
- `page_size` (optional, integer): The number of products per page (default is 5).

#### Response:
- **Success:** Returns a paginated list of products associated with the category.
- **Error:** Returns an error if the category is not found.

#### Example Request:
```
GET /products/12/category?page=1&page_size=5
```

---

### 7. Create a New Product
**Method:** `POST`  
**URL:** `/products`  
**Authentication:** Required

#### Request Body:
- Must be in JSON or `multipart/form-data` format.
- **Required Fields:**
  - `name` (string): The name of the product.
  - `description` (string): A description of the product.
  - `price` (integer): The price of the product.
  - `stock` (integer): The stock quantity of the product.
- **Optional Fields:**
  - `tags[]` (array): An array of tags for the product.
  - `categories[]` (array): An array of categories for the product.
  - `images[]` (file): An array of images to upload.

#### Response:
- **Success:** Returns the created product details.
- **Error:** Returns an error if validation fails or if the product already exists.

#### Example Request:
```
POST /products
Content-Type: application/json

{
  "name": "Sample Product",
  "description": "This is a sample product.",
  "price": 100,
  "stock": 50,
  "tags": [{"name": "tag1", "description": "First tag"}],
  "categories": [{"name": "category1", "description": "First category"}]
}
```

---

### 8. Update an Existing Product
**Method:** `PUT`  
**URL:** `/products/<product_slug>`  
**Authentication:** Required

#### Path Parameters:
- `product_slug` (required, string): The slug of the product to update.

#### Request Body:
- Must be in JSON or `multipart/form-data` format.
- **Optional Fields:**
  - `name` (string): The name of the product.
  - `description` (string): A description of the product.
  - `price` (integer): The price of the product.
  - `stock` (integer): The stock quantity of the product.
  - `tags[]` (array): An array of tags for the product.
  - `categories[]` (array): An array of categories for the product.

#### Response:
- **Success:** Returns the updated product details.
- **Error:** Returns an error if the product is not found or validation fails.

#### Example Request:
```
PUT /products/sample-product
Content-Type: application/json

{
  "price": 120,
  "stock": 30,
  "tags": [{"name": "updated-tag", "description": "Updated tag"}],
  "categories": [{"name": "updated-category", "description": "Updated category"}]
}
```

---

### 9. Delete a Product
**Method:** `DELETE`  
**URL:** `/products/<identifier>`  
**Authentication:** Required

#### Path Parameters:
- `identifier` (required, string): The product slug or ID.

#### Response:
- **Success:** Returns a message indicating the product was deleted.
- **Error:** Returns an error if the product is not found.

#### Example Request:
```
DELETE /products/sample-product
```

---

## Error Handling
All endpoints return JSON responses with the following structure in case of errors:
```json
{
  "error": "Error message.",
  "status_code": HTTP_STATUS_CODE
}
```

## Success Response Structure
Successful responses include a message and data:
```json
{
  "message": "Success message.",
  "data": {
    // response data here
  }
}


This documentation provides a clear structure for interacting with the product API, detailing required and optional parameters for each endpoint. Adjust the examples and descriptions further based on your specific implementation and business logic!