# RelatedObjectsCollector

## Overview

`RelatedObjectsCollector` is a utility class designed to dynamically collect and paginate related objects of a Django model instance before deletion. It ensures that only objects affected by the `on_delete` action (`CASCADE` or `SET_NULL`) are included. The class helps in notifying users about related objects that will be deleted or modified when the instance is removed.

## Features

- Automatically collects related objects for a given Django model instance.
- Filters only the related objects that will be deleted or set to `NULL`.
- Wraps collected objects in a `PaginatorObject` to maintain a structured output.
- Uses Django's `Paginator` for easy pagination of results.
- Provides a clean and structured way to analyze the impact of deletion.

## Installation

Ensure you have Django installed:

```bash
pip install django
```

## Usage

### Import and Initialize

```python
from mymodule import RelatedObjectsCollector
from myapp.models import MyModel

instance = MyModel.objects.get(id=1)
collector = RelatedObjectsCollector(instance)
```

### Access Collected Data

```python
print(collector.data)  # Dictionary of related objects
```

### Paginate Related Objects

```python
page_number = 1
page = collector.paginator.get_page(page_number)

for obj in page.object_list:
    print(obj.data)  # Each item contains a related model and its affected objects
```

## Classes

### `PaginatorObject`

A simple wrapper class to store related objects in a way that supports Django’s pagination.

#### Attributes:
- `data`: A dictionary containing `{model: related_objects}`

### `RelatedObjectsCollector`

Responsible for collecting and paginating related objects of a Django model instance.

#### Attributes:
- `data`: A dictionary containing `{related_model: {on_delete_action: related_objects_queryset}}`
- `paginator`: A Django `Paginator` instance for paginating the related objects.

#### Methods:
- `__collect_objects()`: Gathers related objects dynamically.
- `__paginator(values)`: Initializes a `Paginator` for collected objects.
- `get_on_delete_action(relation)`: Determines the `on_delete` behavior (`CASCADE`, `SET_NULL`).

## Example Output

```python
{
    <class 'myapp.models.Book'>: {
        "delete": [<Book: Django Mastery>, <Book: Advanced Django>]
    },
    <class 'myapp.models.Article'>: {
        "set_null": [<Article: Python Security>, <Article: Django Tips>]
    }
}
```

## License
This project is open-source and available under the MIT License.

