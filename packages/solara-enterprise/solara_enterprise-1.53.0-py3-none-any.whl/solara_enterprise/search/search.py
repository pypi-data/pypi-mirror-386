import ipyvue
import solara
import traitlets


class SearchWidget(ipyvue.VueTemplate):
    template_file = (__file__, "search.vue")
    forceUpdateList = traitlets.Int(0).tag(sync=True)
    item = traitlets.Any().tag(sync=True)
    query = traitlets.Unicode("", allow_none=True).tag(sync=True)
    search_open = traitlets.Bool(False).tag(sync=True)
    failed = traitlets.Bool(False).tag(sync=True)
    cdn = traitlets.Unicode(None, allow_none=True).tag(sync=True)

    @traitlets.default("cdn")
    def _cdn(self):
        import solara.settings

        if not solara.settings.assets.proxy:
            return solara.settings.assets.cdn


@solara.component
def Search():
    return SearchWidget.element()
