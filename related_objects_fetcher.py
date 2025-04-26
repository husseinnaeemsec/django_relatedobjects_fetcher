from django.db.models import Model
from django.core.paginator import Paginator
from django.db.models.deletion import CASCADE, SET_NULL, DO_NOTHING, PROTECT

class PaginatorObject:
    """This class returns a list of objects instead of a KEY:VALUE dict to the paginator."""
    def __init__(self, key, value):
        self.data = {key: value}


class RelatedObjectsCollector:
    """
    Collects related objects of an instance and sets the data attribute for the values.

    `data`: Key-Value map of the related model and the related objects queryset.
    
    `paginator`: Returns a Django Paginator object. Each item in this paginator is a
    PaginatorObject wrapper that takes a model and related objects, setting them as
    key-value pairs for the data attribute.
    """
    per_page = 10
    _related_objects = {}
    
    def __init__(self, instance: Model):
        if not isinstance(instance, Model):
            raise TypeError(f"({instance._meta.model_name.title()}) must be an instance of the class, not the class itself")
        
        self.instance = instance
        self.meta = self.instance._meta
        self.related_objects = self.meta.related_objects
        self.is_empty = True
        self.can_be_deleted = True
        self.reason = ''
        
        # Collect related objects after setting the related_objects attribute
        self._collect_objects()
        # Change the public data attribute after collecting the data
        self.data = self._related_objects
    
    def _collect_objects(self):
        """ Collects related objects and determines if deletion is allowed. """
        objects = {}
        for relation in self.related_objects:
            # Get relation metadata
            on_delete = self._get_on_delete_action(relation)
            query_name = relation.get_accessor_name()
            related_model = relation.related_model
            
            if on_delete == 'protect':
                self._handle_protect(related_model)
                return  # Stop processing if deletion is protected
            
            # Collect related objects for ForeignKey, OneToOne fields with specific on_delete actions
            if relation.one_to_many or relation.one_to_one:
                if on_delete in {"delete", "set_null", "do_nothing", "protect"}:
                    if hasattr(self.instance, query_name):
                        query = list(getattr(self.instance, query_name).all())
                        
                        # If there are related instances with DO_NOTHING, prevent deletion
                        if len(query) and on_delete == 'do_nothing':
                            self._handle_do_nothing(related_model)
                            return
                        
                        # Add related objects to the collection
                        if query:
                            if related_model not in objects:
                                objects[related_model] = {on_delete: query}
                            else:
                                objects[related_model][on_delete].extend(query)

        # Set the related objects and create the paginator
        self._related_objects = objects
        self._create_paginator([PaginatorObject(model, related_items) for model, related_items in objects.items()])
        self.is_empty = len(self._related_objects.values()) == 0

    def _create_paginator(self, values):
        """ Generate new paginator for the related objects. """
        self.paginator = Paginator(values, self.per_page)
    
    def _get_on_delete_action(self, relation):
        """ Check the on_delete field from the relation object. """
        if relation.on_delete == CASCADE:
            return "delete"
        elif relation.on_delete == SET_NULL:
            return "set_null"
        elif relation.on_delete == DO_NOTHING:
            return "do_nothing"
        elif relation.on_delete == PROTECT:
            return "protect"
        return "unknown"
    
    def _handle_protect(self, related_model):
        """ Handles the PROTECT case when deletion is not allowed. """
        self.can_be_deleted = False
        self.reason = (
            f"The related model <strong>{related_model._meta.model_name}</strong> "
            f"has a relationship with the model <strong>{self.instance._meta.model_name}</strong>, "
            f"and this relationship is set to <strong>PROTECT</strong>, "
            f"which prevents the deletion of this instance."
        )
    
    def _handle_do_nothing(self, related_model):
        """ Handles the DO_NOTHING case when deletion is blocked. """
        self.can_be_deleted = False
        self.reason = (
            f"The instance of <strong>{self.instance._meta.model_name}</strong> you are trying to delete "
            f"has existing related instances in <strong>{related_model._meta.model_name}</strong>. "
            f"The relationship between these models is set to <strong>DO_NOTHING</strong>, "
            f"which means no action is taken on the related objects when the parent instance is deleted. "
            f"This will raise an error because the related instances still depend on the deleted object."
        )
