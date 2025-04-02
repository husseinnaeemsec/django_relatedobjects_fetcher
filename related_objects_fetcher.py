from django.db.models import Model
from django.core.paginator import Paginator
from django.db.models.deletion import CASCADE,SET_NULL

class PaginatorObject:
    """ This class only for returning a list off objects insted of KEY:VALUE dict to the paginator  """
    def __init__(self,key,value):
        self.data = {
            key:value
        }


class RelatedObjectsCollector:
    
    """
    ### Collects related objects of an instance and sets the data attribute for the values 
    
    data: Key,Value map of the related model and the related objects queryset
    
    paginator: returns a Django Paginator object each itme in this Paginator is a PaginatorObject wrapper that takes model,related_objects and sets them as 
    
    key,value for the data attribute Note*: the data attibute mentioned is on the PaginatorObject class not the one that is in the RelatedObjectsCollector 
    
    """
    
    per_page = 10
    __data = {}
    
    def __init__(self,instance:Model):
        # Make sure that the instance is actuly an instance of the model 
        assert isinstance(instance,Model),f"({instance._meta.model_name.title()}) must be an instance of the class not the class itself"
        self.instance = instance
        self.meta = self.instance._meta
        self.related_objects = self.meta.related_objects
        # Collect data after setting the related_objects attribute
        self.__collect_objects()
        # Change the public data attribute value affter collecting the data 
        self.data = self.__data
        
    
    def __collect_objects(self):
        objects = {}
        for relation in self.related_objects:
            # Get relation metadata
            on_delete = self.get_on_delete_action(relation)
            query_name = relation.get_accessor_name()
            related_model = relation.related_model
            # Only apply the collectation of related objects if the related_model has a relationship of ForeignKey,OneToOne fields 
            if relation.one_to_many or relation.one_to_one:
                # Only collect data that will be deleted or set_null for the instance field 
                if on_delete == "delete" or on_delete == "set_null":
                    if hasattr(self.instance,query_name):
                        query = list(getattr(self.instance,query_name).all())
                        if not related_model in objects:
                            objects[related_model]  = {
                                on_delete:query
                            }
                        else:
                            objects[related_model][on_delete].extend(query)
                            
            
        
        self.__data = objects
        self.__paginator( [PaginatorObject(model,related_items) for model,related_items in objects.items()  ]  )
    
    
    def __paginator(self,values):
        ''' Generate new paginator  '''
        self.paginator = Paginator(values,self.per_page)
        


    def get_on_delete_action(self,relation):
        
        ''' Check the on_delete field from the relation object  '''
        
        if relation.on_delete == CASCADE:
            return "delete"
        
        elif relation.on_delete == SET_NULL:
            return "set_null"
        
        return "unknown"

