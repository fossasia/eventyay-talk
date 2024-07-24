from django import forms
from allauth.socialaccount.models import SocialApp
from django.contrib.sites.models import Site
from django.conf import settings


from pretalx.common.forms.fields import SizeFileField
from pretalx.submission.models import Resource


class SSOClientForm(forms.ModelForm):
    def __init__(self, provider_id, *args, **kwargs):
        social_app = SocialApp.objects.filter(provider=provider_id).first()
        kwargs["instance"] = social_app
        super().__init__(*args, **kwargs)
        self.fields['secret'].required = True  # Secret is required

    class Meta:
        model = SocialApp
        fields = ["client_id", "secret"]

    def clean(self):
        cleaned_data = super().clean()
        return cleaned_data

    def save(self, organiser=None):
        self.instance.name = organiser
        self.instance.provider = organiser
        super().save()
        self.instance.sites.add(Site.objects.get(pk=settings.SITE_ID))
