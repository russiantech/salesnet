from flask import request, jsonify, url_for
from flask_sqlalchemy.pagination import QueryPagination

class PageSerializer:
    def __init__(self, pagination_obj=None, items=None, resource_name=None, summary_func=None, context_id=None, **kwargs):
        """
        Initialize PageSerializer to handle paginated or non-paginated data.

        :param pagination_obj: 
            QueryPagination object for paginated results. This is used when you want to serialize a 
            set of results that are split across multiple pages.

        :param items: 
            Non-paginated list of items to serialize. This is used when you want to serialize a 
            single set of results without pagination.

        :param resource_name: 
            Name of the resource being serialized (e.g., 'users', 'products', 'addresses'). This 
            is used in the final output to identify the type of items being returned.

        :param summary_func: 
            Function to extract a summary from each resource (defaults to `.get_summary`). This 
            allows customization of how each item is represented in the serialized output.

        :param context_id: 
            Optional ID for URL construction (can be category_id, user_id, etc.). This ID is 
            included in pagination URLs to maintain context when navigating through results.

        :param kwargs: 
            Additional arguments for the summary function. These can be used to pass extra data 
            needed by the summary function during serialization.
        """
        self.data = {}
        self.resource_name = resource_name or "items"  # Default name for resource
        self.summary_func = summary_func or (lambda item, **kw: item.get_summary(**kw))
        self.context_id = context_id  # Store context_id for URL construction
        
        if pagination_obj:
            self._serialize_pagination(pagination_obj, **kwargs)
        elif items is not None:
            self._serialize_items(items, **kwargs)
        else:
            raise ValueError("Either `pagination_obj` or `items` must be provided.")

    def _serialize_pagination(self, pagination_obj, **kwargs):
        """
        Serialize paginated results into a structured format.

        :param pagination_obj: 
            The pagination object containing the current page of items and pagination metadata.
        
        :raises TypeError: 
            If the provided pagination_obj is not an instance of QueryPagination.
        """
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

        # Construct URLs dynamically, including context_id if provided
        base_url = request.path
        self.data['next_page_url'] = (
            url_for(request.endpoint, page=pagination_obj.next_num, page_size=pagination_obj.per_page, context_id=self.context_id)
            if pagination_obj.has_next else None
        )
        
        self.data['prev_page_url'] = (
            url_for(request.endpoint, page=pagination_obj.prev_num, page_size=pagination_obj.per_page, context_id=self.context_id)
            if pagination_obj.has_prev else None
        )

    def _serialize_items(self, items, **kwargs):
        """
        Serialize non-paginated items into a structured format.

        :param items: 
            A list of items to serialize.
        """
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
        """
        Return the serialized data in a structured format.

        :return: 
            A dictionary containing success status, pagination metadata, and the serialized items.
        """
        return {
            'success': True,
            'page_meta': self.data,
            self.resource_name: self.items,
        }

def success_response(messages, data=None, status_code=200, include_status_code=False):
    # Also allows a list of messages
    msgs = messages if not isinstance(messages, list) else [messages]
    response = {
        'success': True,
        'message': msgs
    }
    
    if data:
        response.update(data)
    
    # Include the status code as a member only if it's provided and needed
    if status_code is not None and include_status_code:
        response['status_code'] = status_code

    return response, status_code

# def success_response(messages, data=None, status_code=200):
#     # Also allows a list of messages
#     msgs = messages if not isinstance(messages, list) else [messages]
#     response = {
#         'success': True,
#         'message': msgs
#     }
#     if data:
#         response.update(data)
#     return jsonify(response), status_code

# def error_response(messages, status_code=500):
#     # Also allows a list of messages/errors
#     msgs = messages if not isinstance(messages, list) else [messages]
#     return jsonify({
#         'success': False,
#         'error': msgs
#     }), status_code

def error_response(messages, status_code=500, include_status_code=False):
    # Also allows a list of messages/errors
    msgs = messages if not isinstance(messages, list) else [messages]
    response = {
        'success': False,
        'error': msgs
    }
    
    # Include the status code as a member only if it's provided and needed
    if status_code is not None and include_status_code:
        response['status_code'] = status_code

    # response = jsonify(response)
    
    return response, status_code


# from flask import request, jsonify

# from flask_sqlalchemy.pagination import QueryPagination

# class PageSerializer_BAK(object):
#     def __init__(self, pagination_obj, **kwargs):
#         from flask_sqlalchemy import pagination  # Import within the method to avoid circular import issues
        
#         # if type(pagination_obj) is not QueryPagination: //even this works too
#         if not isinstance(pagination_obj, QueryPagination):
#             raise TypeError(f"Expected Pagination object of {QueryPagination}, got {type(pagination_obj)}")

#         self.data = {}
#         self.items = [resource.get_summary(**kwargs) for resource in pagination_obj.items]
#         self.data['total_items_count'] = pagination_obj.total
#         self.data['offset'] = (pagination_obj.page - 1) * pagination_obj.per_page
#         self.data['requested_page_size'] = pagination_obj.per_page
#         self.data['current_page_number'] = pagination_obj.page

#         self.data['prev_page_number'] = pagination_obj.prev_num or 1
#         self.data['total_pages_count'] = pagination_obj.pages

#         self.data['has_next_page'] = pagination_obj.has_next
#         self.data['has_prev_page'] = pagination_obj.has_prev

#         self.data['next_page_number'] = pagination_obj.next_num or self.data['current_page_number']
#         self.data['next_page_url'] = f"{request.path}?page={self.data['next_page_number']}&page_size={self.data['requested_page_size']}"
#         self.data['prev_page_url'] = f"{request.path}?page={self.data['prev_page_number']}&page_size={self.data['requested_page_size']}"

#     def get_data(self):
#         return {
#             'success': True,
#             'page_meta': self.data,
#             self.resource_name: self.items,
#         }


# def get_success_response(messages, data=None, status_code=200):
#     if type(messages) == list:
#         msgs = messages
#     elif type(messages) == str:
#         msgs = [messages]
#     else:
#         msgs = []

#     response = {
#         'success': True,
#         'full_messages': msgs
#     }

#     if data is not None:
#         response.update(data)

#     return jsonify(response), status_code

# def get_error_response(messages, status_code=500):
#     if type(messages) == list:
#         msgs = messages
#     elif type(messages) == str:
#         msgs = [messages]
#     else:
#         msgs = []

#     return jsonify({
#         'success': False,
#         'full_messages': msgs
#     }), status_code
