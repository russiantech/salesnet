
from sqlalchemy.sql import ClauseElement

def get_or_create(session, model, defaults=None, **kwargs):
    """
    Retrieve an instance of a model from the database or create it if it doesn't exist.

    Parameters:
    - session: SQLAlchemy session object
    - model: SQLAlchemy model class
    - defaults: Optional dictionary of default values for creating a new instance
    - kwargs: Attributes to filter the query and create the instance

    Returns:
    - Tuple of (instance, created), where `created` is a boolean indicating if a new instance was created.
    """
    # Query for an existing instance
    instance = session.query(model).filter_by(**kwargs).first()
    
    if instance:
        return instance, False  # Instance found, not created
    else:
        # Prepare parameters for the new instance
        params = {k: v for k, v in kwargs.items() if not isinstance(v, ClauseElement)}
        params.update(defaults or {})
        
        # Create and add the new instance
        instance = model(**params)
        session.add(instance)
        session.commit()  # Commit the session to save the new instance
        return instance, True  # New instance created


# def get_or_create(session, model, defaults=None, **kwargs):
#     instance = session.query(model).filter_by(**kwargs).first()
#     if instance:
#         return instance, False
#     else:
#         params = dict((k, v) for k, v in kwargs.iteritems() if not isinstance(v, ClauseElement))
#         params.update(defaults or {})
#         instance = model(**params)
#         session.add(instance)
#         return instance, True

# def get_or_create(session, model, **kwargs):
#     instance = session.query(model).filter_by(**kwargs).first()
#     if instance:
#         return instance, False
#     else:
#         instance = model(**kwargs)
#         session.add(instance)
#         session.commit()
#         return instance, True
