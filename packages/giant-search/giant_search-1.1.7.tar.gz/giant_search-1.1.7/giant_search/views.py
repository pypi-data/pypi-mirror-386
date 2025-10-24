from django.conf import settings

from watson.views import SearchView as WatsonSearchView

from giant_search.utils import SearchResultProcessor


class SearchView(WatsonSearchView):
    template_name = "search/results.html"
    paginate_by = getattr(settings, 'GIANT_SEARCH_PAGINATE_BY', 10)

    def get_queryset(self):
        search_result_queryset = super().get_queryset()
        return SearchResultProcessor(search_result_queryset).process()
