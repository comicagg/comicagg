from django.conf import settings
from django.views.generic.base import TemplateView

class BaseTemplateView(TemplateView):
    def get_context_data(self, **kwargs):
        context = super(BaseTemplateView, self).get_context_data(**kwargs)
        context.update({
            'mediaurl' : settings.MEDIA_URL
        })
        return context
