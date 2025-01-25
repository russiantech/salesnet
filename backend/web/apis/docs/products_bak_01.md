### API Documentation for Product Management

This document describes the API endpoints for managing products, including retrieving, creating, updating, and deleting products. These endpoints support JWT authentication for secure access.

---
<!--  -->

## Endpoint
`GET /products/by_category/<int:category_id>`

### Description
This endpoint retrieves a list of products that are associated with a specific category, allowing for pagination of results.

### Authentication
- **JWT Required**: This endpoint requires a valid JSON Web Token (JWT) for access.

### Path Parameters
- **category_id**: 
  - **Type**: Integer
  - **Description**: The unique identifier of the category for which products are to be fetched.

### Query Parameters
- **page**: 
  - **Type**: Integer (optional)
  - **Default**: 1
  - **Description**: The page number to retrieve. This parameter is used for pagination.

- **page_size**: 
  - **Type**: Integer (optional)
  - **Default**: 5
  - **Description**: The number of products to return per page.

### Responses
- **Success (200)**:
  - **Description**: Returns a list of products associated with the specified category.
  - **Example Response**:
    ```json
    {
        "message": "Products fetched successfully.",
        "page_meta": {
            "current_page_number": 1,
            "has_next_page": false,
            "has_prev_page": false,
            "next_page_url": null,
            "prev_page_url": null,
            "offset": 0,
            "requested_page_size": 5,
            "total_items_count": 8,
            "total_pages_count": 2
        },
        "products": [
            {
                "id": 4,
                "name": "Vote marriage shake trade condition sure build.",
                "price": 110,
                "stock": 718,
                "image_urls": ["https://dummyimage.com/450x391"],
                "categories": [{"id": 2, "name": "Women"}, {"id": 4, "name": "Teenagers"}],
                "comments_count": 0,
                "tags": [{"id": 3, "name": "Jackets"}, {"id": 4, "name": "Shorts"}],
                "slug": "vote-marriage-shake-trade-condition-sure-build"
            }
            // Additional products...
        ]
    }
    ```

- **Error (404)**:
  - **Description**: Returned when the specified category does not exist.
  - **Example Response**:
    ```json
    {
        "message": "Category not found."
    }
    ```

- **Error (500)**:
  - **Description**: Returned when an unexpected error occurs during processing.
  - **Example Response**:
    ```json
    {
        "message": "An error occurred: [error details]"
    }
    ```

### Example Request
```http
GET /products/by_category/2?page=1&page_size=5
Authorization: Bearer <your_jwt_token>
```

### Implementation

```python
@product_bp.route('/products/by_category/<int:category_id>', methods=['GET'])
@jwt_required()
def get_products_by_category(category_id):
    try:
        """ 
        Fetch products associated with a specific category.
        Parameters:
        - category_id: The ID of the category to filter products.
        """
        # Check if the category exists
        category = Category.query.get(category_id)
        if not category:
            return error_response("Category not found.", status_code=404)

        # Pagination parameters: Default page = 1, page_size = 5
        page = request.args.get('page', 1, type=int)  # Ensure 'page' is an integer
        page_size = request.args.get('page_size', 5, type=int)  # Ensure 'page_size' is an integer

        # Fetch products associated with the category
        products = Product.query.filter(
            Product.categories.any(id=category_id)
            ).order_by(desc(Product.created_at)
            ).paginate(page=page, per_page=page_size)

        # Serialize the paginated result using PageSerializer
        data = PageSerializer(pagination_obj=products, resource_name="products", category_id=category_id)
        data = data.get_data()

        return success_response("Products fetched successfully.", data=data)

    except Exception as e:
        # Handle any unexpected errors
        traceback.print_exc()
        return error_response(f"An error occurred: {str(e)}", status_code=500)
```

### Notes
- Ensure that the JWT is included in the Authorization header for successful access to this endpoint.
- The pagination logic allows for efficient loading of products without overwhelming the client with data.
<!--  -->

### **GET /products**

#### Description
Fetches a list of products with pagination.

#### Query Parameters
- **page** (optional): The page number to retrieve (default: 1).
- **page_size** (optional): The number of products per page (default: 5).

#### Response Format
```json
{
    "status": "success",
    "message": "Products fetched successfully.",
    "data": {
        "page": 1,
        "page_size": 5,
        "total_pages": 10,
        "products": [
            {
                "id": 1,
                "name": "Product A",
                "slug": "product-a",
                "price": 100.00,
                "stock": 50,
                "tags": ["Tag1", "Tag2"],
                "categories": ["Category1", "Category2"],
                "created_at": "2024-01-06T12:00:00Z"
            },
            // More products...
        ]
    }
}
```

---

### **GET /products/<product_id>**

#### Description
Fetches a single product by its `product_id`, which can be either an integer ID or a slug.

#### URL Parameters
- **product_id** (required): The product ID or slug.

#### Response Format
```json
{
    "status": "success",
    "message": "Product fetched successfully.",
    "data": {
        "id": 1,
        "name": "Product A",
        "slug": "product-a",
        "description": "This is a description of Product A.",
        "price": 100.00,
        "stock": 50,
        "tags": ["Tag1", "Tag2"],
        "categories": ["Category1", "Category2"],
        "created_at": "2024-01-06T12:00:00Z"
    }
}
```

---

### **GET /products/by_id/<product_id>**

#### Description
Fetches a product by its `product_id` (numeric ID).

#### URL Parameters
- **product_id** (required): The product ID.

#### Response Format
```json
{
    "status": "success",
    "message": "Product fetched successfully.",
    "data": {
        "id": 1,
        "name": "Product A",
        "slug": "product-a",
        "price": 100.00,
        "stock": 50
    }
}
```

---

### **POST /products**

#### Description
Creates a new product.

#### Request Body (JSON or Form Data)
- **name** (required): The name of the product.
- **description** (optional): A detailed description of the product.
- **price** (required): The price of the product.
- **stock** (required): The available stock for the product.
- **tags[]** (optional): A list of tags associated with the product.
  - Each tag has a `name` (required) and `description` (optional).
- **categories[]** (optional): A list of categories associated with the product.
  - Each category has a `name` (required) and `description` (optional).
- **page_id** (optional): The ID of the page to associate with the product.
- **images[]** (optional): A list of images to upload for the product. Files must be sent via `multipart/form-data`.

#### Sample Request (JSON)
```json
{
    "name": "Product A",
    "description": "This is Product A.",
    "price": 100.00,
    "stock": 50,
    "tags[0][name]": "Tag1",
    "tags[0][description]": "Description for Tag1",
    "categories[0][name]": "Category1",
    "categories[0][description]": "Description for Category1"
}
```

#### Response Format
```json
{
    "status": "success",
    "message": "Product created successfully",
    "data": {
        "id": 1,
        "name": "Product A",
        "slug": "product-a",
        "price": 100.00,
        "stock": 50,
        "tags": ["Tag1"],
        "categories": ["Category1"],
        "created_at": "2024-01-06T12:00:00Z"
    }
}
```

---

### **PUT /products/<product_slug>**

#### Description
Updates an existing product based on its slug.

#### URL Parameters
- **product_slug** (required): The slug of the product to update.

#### Request Body (JSON or Form Data)
- **name** (optional): The new name of the product.
- **description** (optional): The new description of the product.
- **price** (optional): The new price of the product.
- **stock** (optional): The new stock count of the product.
- **tags[]** (optional): A list of tags to update for the product.
- **categories[]** (optional): A list of categories to update for the product.

#### Sample Request (JSON)
```json
{
    "name": "Updated Product A",
    "description": "Updated description of Product A.",
    "price": 120.00,
    "tags[0][name]": "NewTag",
    "categories[0][name]": "NewCategory"
}
```

#### Response Format
```json
{
    "status": "success",
    "message": "Product updated successfully",
    "data": {
        "id": 1,
        "name": "Updated Product A",
        "slug": "updated-product-a",
        "price": 120.00,
        "stock": 50,
        "tags": ["NewTag"],
        "categories": ["NewCategory"],
        "created_at": "2024-01-06T12:00:00Z"
    }
}
```

---

### **DELETE /products/<product_slug>**

#### Description
Deletes a product by its slug.

#### URL Parameters
- **product_slug** (required): The slug of the product to delete.

#### Response Format
```json
{
    "status": "success",
    "message": "Product deleted successfully"
}
```

---

### **DELETE /products/<product_id>**

#### Description
Deletes a product by its numeric `product_id`.

#### URL Parameters
- **product_id** (required): The numeric ID of the product to delete.

#### Response Format
```json
{
    "status": "success",
    "message": "Product deleted successfully"
}
```

---

### Authentication
All the product-related endpoints (except for the `GET` requests with a specific product ID) require **JWT-based authentication**. Ensure that you include a valid JWT token in the `Authorization` header when making requests.

Example:
```http
Authorization: Bearer <your-jwt-token>
```

---

### Error Responses

In case of errors, the API will return a JSON response with an error message and status code:

```json
{
    "status": "error",
    "message": "Product not found.",
    "data": null
}
```

Status codes:
- **400**: Bad request (e.g., invalid data or missing required fields).
- **404**: Not found (e.g., product not found).
- **500**: Internal server error (e.g., unexpected errors).

---

### File Uploads

For endpoints that support file uploads (such as `POST /products` for product images), ensure that you send the data as `multipart/form-data`. 
The images will be saved on the server and associated with the product.

- **images[]**: The list of images to upload.
  - **File Name**: The original name of the file.
  - **File Size**: The file size in bytes.

