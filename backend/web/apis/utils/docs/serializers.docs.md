To improve the **PageSerializer** and make it flexible and reusable for both single and multiple items across various resources/models, here are some key areas of improvement:

1. **Dynamic Resource Name**  
   The `resource_name` can be dynamically passed or inferred, so the serializer isn't tied to specific subclasses (like `AddressListSerializer`).

2. **Flexible Data Handling**  
   Allow flexibility in `get_summary` or data extraction by using an attribute name or a custom serialization function.

3. **Improved URL Building**  
   Use `url_for` from Flask to build URLs dynamically and avoid manual string concatenation for `next_page_url` and `prev_page_url`.

4. **Support for Single and Multiple Items**  
   Include logic to handle scenarios where no pagination is needed, i.e., when working with a single object or a non-paginated collection.

5. **Integration with Error and Success Response Helpers**  
   Combine it with `get_success_response` and `get_error_response` for seamless integration.

---

### Revised Implementation

```python
from flask import request, jsonify, url_for
from flask_sqlalchemy.pagination import QueryPagination


class PageSerializer:
    def __init__(self, pagination_obj=None, items=None, resource_name=None, summary_func=None, **kwargs):
        """
        Initialize PageSerializer to handle paginated or non-paginated data.

        :param pagination_obj: QueryPagination object for paginated results.
        :param items: Non-paginated list of items to serialize.
        :param resource_name: Name of the resource being serialized (e.g., 'addresses').
        :param summary_func: Function to extract summary from each resource (defaults to `.get_summary`).
        :param kwargs: Additional arguments for the summary function.
        """
        self.data = {}
        self.resource_name = resource_name or "items"  # Default name for resource
        self.summary_func = summary_func or (lambda item, **kw: item.get_summary(**kw))
        
        if pagination_obj:
            self._serialize_pagination(pagination_obj, **kwargs)
        elif items is not None:
            self._serialize_items(items, **kwargs)
        else:
            raise ValueError("Either `pagination_obj` or `items` must be provided.")

    def _serialize_pagination(self, pagination_obj, **kwargs):
        if not isinstance(pagination_obj, QueryPagination):
            raise TypeError(f"Expected Pagination object of {QueryPagination}, got {type(pagination_obj)}")
        
        self.items = [self.summary_func(resource, **kwargs) for resource in pagination_obj.items]
        self.data['total_items_count'] = pagination_obj.total
        self.data['offset'] = (pagination_obj.page - 1) * pagination_obj.per_page
        self.data['requested_page_size'] = pagination_obj.per_page
        self.data['current_page_number'] = pagination_obj.page
        self.data['total_pages_count'] = pagination_obj.pages
        self.data['has_next_page'] = pagination_obj.has_next
        self.data['has_prev_page'] = pagination_obj.has_prev

        # Construct URLs dynamically
        base_url = request.path
        self.data['next_page_url'] = (
            url_for(request.endpoint, page=pagination_obj.next_num, page_size=pagination_obj.per_page)
            if pagination_obj.has_next else None
        )
        self.data['prev_page_url'] = (
            url_for(request.endpoint, page=pagination_obj.prev_num, page_size=pagination_obj.per_page)
            if pagination_obj.has_prev else None
        )

    def _serialize_items(self, items, **kwargs):
        self.items = [self.summary_func(resource, **kwargs) for resource in items]
        self.data['total_items_count'] = len(items)
        self.data['offset'] = 0
        self.data['requested_page_size'] = len(items)
        self.data['current_page_number'] = 1
        self.data['total_pages_count'] = 1
        self.data['has_next_page'] = False
        self.data['has_prev_page'] = False
        self.data['next_page_url'] = None
        self.data['prev_page_url'] = None

    def get_data(self):
        return {
            'success': True,
            'page_meta': self.data,
            self.resource_name: self.items,
        }


def get_success_response(messages, data=None, status_code=200):
    msgs = messages if isinstance(messages, list) else [messages]
    response = {
        'success': True,
        'full_messages': msgs
    }
    if data:
        response.update(data)
    return jsonify(response), status_code


def get_error_response(messages, status_code=500):
    msgs = messages if isinstance(messages, list) else [messages]
    return jsonify({
        'success': False,
        'full_messages': msgs
    }), status_code
```

---

### Key Features in the Revised Version

1. **Dynamic Resource Name**  
   The `resource_name` can be set dynamically during initialization or defaults to `"items"`.

2. **Support for Single and Multiple Items**  
   The serializer works seamlessly for both paginated and non-paginated data.

3. **Dynamic URL Generation**  
   Uses `url_for` to generate URLs for pagination, making the URLs more robust.

4. **Custom Summary Function**  
   Allows passing a custom function for serializing each item, making it reusable for various models.

5. **Error Handling**  
   Ensures meaningful errors when invalid data is passed.

---

### Example Usage

#### For Paginated Data
```python
pagination = SomeModel.query.paginate(page=1, per_page=10)
serializer = PageSerializer(pagination_obj=pagination, resource_name="items")
response_data = serializer.get_data()
return get_success_response("Items fetched successfully", data=response_data)
```

#### For Non-Paginated Data
```python
items = SomeModel.query.all()
serializer = PageSerializer(items=items, resource_name="items")
response_data = serializer.get_data()
return get_success_response("Items fetched successfully", data=response_data)
```