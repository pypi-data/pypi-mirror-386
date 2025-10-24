from django.utils.translation import get_language
from watson.search import register


def register_for_search(model, **field_overrides):
    """
    Registers a given model with Watson using the Giant Search Adapter.
    """

    from giant_search.adapter import GiantSearchAdapter

    register(model, adapter_cls=GiantSearchAdapter, **field_overrides)


def is_cms_page(obj):
    """
    Determine if the given object is a Django CMS Page or Title model instance.
    """

    try:
        from cms.models import Title

        page_model = Title
    except ImportError:
        from cms.models import PageContent

        page_model = PageContent

    return isinstance(obj, page_model)


def is_cms_plugin(obj):
    """
    Determine if the given object is a Django CMS Plugin model instance.
    """

    from cms.models import CMSPlugin

    return isinstance(obj, CMSPlugin)


class SearchResultProcessor:
    def __init__(self, queryset):
        self.queryset = queryset
        self.seen_urls = []

    def process(self):
        """
        This method calls all of the processing methods that need to be run.
        """

        self.exclude_items_without_url()
        self.deduplicate()
        self.exclude_unpublished_items()

        return self.queryset

    def exclude_items_without_url(self):
        """
        Search Result items without a URL are pointless because there is nowhere for the user to go to.
        """

        self.queryset = self.queryset.exclude(url="")

    def deduplicate(self):
        """
        Ensures that the QuerySet does not contain multiple results for the same URL.
        """

        queryset = self.queryset

        for result in queryset:
            url = result.url
            if not self._is_valid_url(url):
                self.queryset = self.queryset.exclude(pk=result.pk)
            # Add the URL for this result to the seen URLs list so we don't add it again.
            self.seen_urls.append(url.strip("/"))

    def exclude_unpublished_items(self):
        """
        Remove any CMS Plugins or Plugin Cards attached to Pages that are not published.
        """

        queryset = self.queryset
        lang = get_language()
        pks_to_exclude = []

        for result in queryset:
            plugin = None
            if is_cms_plugin(result.object):
                plugin = result.object
            elif hasattr(result.object, "plugin") and is_cms_plugin(
                result.object.plugin
            ):
                plugin = result.object.plugin
            if hasattr(plugin, "page") and plugin.page and not plugin.page.is_published(get_language()):
                pks_to_exclude += [result.pk]

        if pks_to_exclude:
            self.queryset = self.queryset.exclude(pk__in=pks_to_exclude)

        return self.queryset

    def _is_valid_url(self, url):
        """
        Ensures that the URL given is valid and has not already been processed.
        """

        if not url or url.strip("/") in self.seen_urls:
            return False

        return True
