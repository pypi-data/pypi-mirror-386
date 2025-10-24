# Giant Search

This library provides a nice abstraction layer on top of the `django-watson` search library. It allows developers to
easily index and search across Django CMS Page Title objects without any additional configuration, as well as a simple
mixin class to make indexing other model types, such as CMS plugin classes simple.

## Installation

Install `giant-search` via your chosen Python dependency manager, `poetry`, `pip` etc.

## Configuration

1. Add `watson` to `INSTALLED_APPS` in `settings.py`
2. Add `giant_search` to `INSTALLED_APPS` in `settings.py`
3. Add the search application URLs to your project's `urls.py`, for example: `path("search/", include("giant_search.urls",
   namespace="search")),`

## Registering items as searchable

### Django CMS Page Titles

**Short version: you don't need to do anything.**

The library will index all published `Title` objects, if using django-cms3, or `PageContent` if 
using django- cms4. 
This allows end users to find pages via their title.
This behaviour cannot currently be overridden, however in a future version, we might check 
if the Page has the NoIndex Page Extension and honour the setting within.

### Other models

We provide a convenient mixin class, `SearchableMixin` that you can add to any model to allow it to be searched. Don't 
forget to add the import line `from giant_search.mixins import SearchableMixin` at the top of the models file.

As a developer, there are several configuration options that you can define to customise what gets indexed, and the data
that is presented in the search result listing:

### Third party models

While the `SearchableMixin` takes care of first party models, you usually can't implement this on third party models.
However, you can still make them searchable.

In one of your main apps (usually `core`), add a call to register the model. Here is an example:

```python
from django.apps import AppConfig

from giant_search.utils import register_for_search

class CoreAppConfig(AppConfig):
   name = "core"
   verbose_name = "Core"

   def ready(self):
      from third_party_library.models import ThirdPartyModel
      register_for_search(ThirdPartyModel)
```

Third party models will always have their string representation set as the search result title. The model **must**
implement the `get_absolute_url` method, otherwise, the search result will not have a valid URL and the model will be
indexed, but will _not_ show up in search results.

#### Overriding the search QuerySet

By default, `giant-search` will get all instances of a particular model to index.

You can override this in your model class, perhaps to return only published items:

```python
@classmethod
def get_search_queryset(cls) -> QuerySet:
        return cls.objects.published()
```

If you want to define which fields on your model should be searched, you can implement a `get_search_fields` method on
your model like so:

```python
from giant_search.mixins import SearchableMixin


class ExampleModel(SearchableMixin, models.Model):
    name = models.CharField(max_length=255)
    content = models.CharField(max_legth=255)

    @staticmethod
    def get_search_fields() -> tuple:
        """
        Override this method to provide a tuple containing the fields to search.
        If the method returns an empty tuple, all text fields will be indexed as per Watson's defaults.
        """

        return "name", "content"
```

## Defining search result title, description and URL

When Watson performs a search, it returns a list of `SearchEntry` instances, which has some fields that can be used on
the front end to display search results to end users. For example, `title`, `description` and `url`.

The title field is the title of the search result, the description is optional and provides a bit more context about the
search result and the URL is required and is where the user should be taken to upon clicking the search result.

In order to specify where Watson should get the values from for these fields, you can define the following on your
model (remember, it must inherit from the `SearchableMixin`)

Here is an example:

```python
from giant_search.mixins import SearchableMixin


class ExampleModel(SearchableMixin, models.Model):
    name = models.CharField(max_length=255)
    summary = models.CharField(max_length=255)
    content = RichTextField()
    
    def __str__(self):
        return self.name
        
    def get_search_result_title(self) -> str:
        return str(self)

    def get_search_result_description(self) -> str:
        return self.summary

```

The important parts in this example are `get_search_result_title` and `get_search_result_description`

Note that in this example, we don't define `get_search_result_url`. If you don't define `get_search_result_url` then
Giant Search will call the `get_absolute_url` method on the model, if it has that method. If the model does not
implement, `get_absolute_url` and does not implement `get_search_result_url` then it won't have a URL and will not be
shown in the search results.

If your model is a Django CMS Plugin instance, you probably want to implement `get_absolute_url()` and have it call
`self.page.get_public_url()`.

```python
def get_absolute_url(self) -> str:
    try:
        return self.page.get_public_url()
    except AttributeError:
        return ""
```

### Pagination

By default the search results will render 10 items per page. If you want to customise this simply add
`GIANT_SEARCH_PAGINATE_BY` to your project's settings, along with the desired integer number of items to paginate by.
This assumes your project has a registered simple_tag entitled `show_pagination` containing pagination logic. 

## Existing Data

If implementing this library upon existing data, changes to search results will only take effect after the 
model instance is saved again.

## Package Publishing

First build the package, 
Do remmember to update the version number in pyproject and add the summary of changes to 
   CHANGELOG.md

```dotenv
   $ poetry build
```

PyPi now prefers API Token authorisation. 
```dotenv
   $ poetry config pypi-token.pypi <token>
```
And finally
```dotenv
   $ poetry publish
```
