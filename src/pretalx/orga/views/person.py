import urllib

from django.contrib import messages
from django.shortcuts import redirect
from django.urls import reverse
from django.utils.functional import cached_property
from django.utils.http import url_has_allowed_host_and_scheme
from django.utils.translation import gettext_lazy as _
from django.views.generic import TemplateView, View
from django_context_decorator import context
from rest_framework.authtoken.models import Token

from pretalx.common.text.phrases import phrases
from pretalx.common.views import is_form_bound
from pretalx.person.forms import LoginInfoForm, OrgaProfileForm


class UserSettings(TemplateView):
    form_class = LoginInfoForm
    template_name = "orga/user.html"

    def get_success_url(self) -> str:
        return reverse("orga:user.view")

    @context
    @cached_property
    def login_form(self):
        return LoginInfoForm(
            user=self.request.user,
            data=self.request.POST if is_form_bound(self.request, "login") else None,
        )

    @context
    @cached_property
    def profile_form(self):
        return OrgaProfileForm(
            instance=self.request.user,
            data=self.request.POST if is_form_bound(self.request, "profile") else None,
        )

    @context
    def token(self):
        return Token.objects.filter(
            user=self.request.user
        ).first() or Token.objects.create(user=self.request.user)

    def post(self, request, *args, **kwargs):
        if self.login_form.is_bound and self.login_form.is_valid():
            self.login_form.save()
            messages.success(request, phrases.base.saved)
            request.user.log_action("pretalx.user.password.update")
        elif self.profile_form.is_bound and self.profile_form.is_valid():
            self.profile_form.save()
            messages.success(request, phrases.base.saved)
            request.user.log_action("pretalx.user.profile.update")
        elif request.POST.get("form") == "token":
            request.user.regenerate_token()
            messages.success(request, phrases.cfp.token_regenerated)
        else:
            messages.error(self.request, phrases.base.error_saving_changes)
            return self.get(request, *args, **kwargs)
        return redirect(self.get_success_url())


class SubuserView(View):
    def dispatch(self, request, *args, **kwargs):
        request.user.is_administrator = request.user.is_superuser
        request.user.is_superuser = False
        request.user.save(update_fields=["is_administrator", "is_superuser"])
        messages.success(
            request, _("You are now an administrator instead of a superuser.")
        )
        params = request.GET.copy()
        url = urllib.parse.unquote(params.pop("next", [""])[0])
        if url and url_has_allowed_host_and_scheme(url, allowed_hosts=None):
            return redirect(url + ("?" + params.urlencode() if params else ""))
        return redirect(reverse("orga:event.list"))
