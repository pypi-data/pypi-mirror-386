from django.forms import widgets


class CarbonTextarea(widgets.Textarea):
    template_name = "django_zooy/carbon/widgets/textarea.html"
