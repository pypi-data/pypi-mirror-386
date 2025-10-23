from collections.abc import Callable
from typing import TYPE_CHECKING

from plain.exceptions import ImproperlyConfigured
from plain.http import Response, ResponseRedirect

from .templates import TemplateView

if TYPE_CHECKING:
    from plain.forms import BaseForm


class FormView(TemplateView):
    """A view for displaying a form and rendering a template response."""

    form_class: type["BaseForm"] | None = None
    success_url: Callable | str | None = None

    def get_form(self) -> "BaseForm":
        """Return an instance of the form to be used in this view."""
        if not self.form_class:
            raise ImproperlyConfigured(
                f"No form class provided. Define {self.__class__.__name__}.form_class or override "
                f"{self.__class__.__name__}.get_form()."
            )
        return self.form_class(**self.get_form_kwargs())

    def get_form_kwargs(self) -> dict:
        """Return the keyword arguments for instantiating the form."""
        return {
            "initial": {},
            "request": self.request,
        }

    def get_success_url(self, form: "BaseForm") -> str:
        """Return the URL to redirect to after processing a valid form."""
        if not self.success_url:
            raise ImproperlyConfigured("No URL to redirect to. Provide a success_url.")
        return str(self.success_url)  # success_url may be lazy

    def form_valid(self, form: "BaseForm") -> Response:
        """If the form is valid, redirect to the supplied URL."""
        return ResponseRedirect(self.get_success_url(form))

    def form_invalid(self, form: "BaseForm") -> Response:
        """If the form is invalid, render the invalid form."""
        context = {
            **self.get_template_context(),
            "form": form,
        }
        return self.get_template().render(context)

    def get_template_context(self) -> dict:
        """Insert the form into the context dict."""
        context = super().get_template_context()
        context["form"] = self.get_form()
        return context

    def post(self) -> Response:
        """
        Handle POST requests: instantiate a form instance with the passed
        POST variables and then check if it's valid.
        """
        form = self.get_form()
        if form.is_valid():
            return self.form_valid(form)
        else:
            return self.form_invalid(form)
