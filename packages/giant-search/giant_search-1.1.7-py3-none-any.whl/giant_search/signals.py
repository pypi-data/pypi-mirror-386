from importlib import import_module

from django.apps import apps
from django.conf import settings
from django.db.backends.signals import connection_created
from django.db.models import QuerySet
from django.dispatch import receiver
from watson.search import is_registered

from giant_search.utils import register_for_search

DB_ENGINE = settings.DATABASES['default']['ENGINE']

db_backend = import_module(DB_ENGINE + ".base")


@receiver(connection_created, sender=db_backend.DatabaseWrapper)
def initial_connection_to_db(sender, **kwargs):
    # Get a list of all models that implement the SearchableMixin
    for app in apps.all_models.values():
        for model in app.values():
            if hasattr(model, "is_searchable"):
                # We have search_fields, try to register the model.
                register_kwargs = {"model": model.get_search_queryset()}

                # If the model defines which fields should be searchable,
                #   pass them to the register() call.
                try:
                    search_fields = model.get_search_fields()
                    if search_fields:
                        register_kwargs["fields"] = search_fields
                except AttributeError:
                    pass

                # Do not register more than once:
                model_ = register_kwargs['model']
                if isinstance(model_, QuerySet):
                    model_ = model_.model
                if not is_registered(model_):
                    register_for_search(**register_kwargs)

    # Register Page Titles / PageContents
    try:
        from cms.models import Title
    except ImportError:
        from cms.models import PageContent
        from cms.utils.i18n import get_public_languages

        languages = get_public_languages(site_id=settings)
        if not is_registered(PageContent):
            qs = PageContent.objects.filter(language__in=languages)
            # if qs.exists() and  hasattr(qs.first(), 'versions'):
            #     qs.filter(versions__state='published')
            register_for_search(qs)
    else:
        if not is_registered(Title):
            register_for_search(
                Title.objects.filter(published=True, publisher_is_draft=False)
            )


