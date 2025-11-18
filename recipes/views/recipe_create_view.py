from django.conf import settings
from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.forms import inlineformset_factory
from django.views.generic.edit import FormView
from django.urls import reverse
from recipes.forms import RecipeForm, IngredientForm, InstructionForm
from recipes.models import Recipe, Ingredient, Instruction


IngredientFormSet = inlineformset_factory(
    Recipe,
    Ingredient,
    form=IngredientForm,
    extra=1,
    can_delete=True,
    min_num=1,
    validate_min=True,
)

InstructionFormSet = inlineformset_factory(
    Recipe,
    Instruction,
    form=InstructionForm,
    extra=1,
    can_delete=True,
    min_num=1,
    validate_min=True,
)


class RecipeCreateView(LoginRequiredMixin, FormView):
    """
    Allow authenticated users to create a new recipe.

    Access is restricted to logged-in users
    via `LoginRequiredMixin`.
    """

    form_class = RecipeForm
    template_name = "recipe_create.html"

    def get_context_data(self, **kwargs):
        """Add ingredient and instruction formsets to context."""
        context = super().get_context_data(**kwargs)
        if self.request.method == "POST":
            context["ingredient_formset"] = IngredientFormSet(
                self.request.POST, instance=None
            )
            context["instruction_formset"] = InstructionFormSet(
                self.request.POST, instance=None
            )
        else:
            context["ingredient_formset"] = IngredientFormSet(instance=None)
            context["instruction_formset"] = InstructionFormSet(instance=None)
        return context

    def form_valid(self, form):
        """
        Handle valid recipe form submissions.

        If successful, the method continues to the success URL defined by `get_success_url()`.
        """
        recipe = form.save(commit=False)
        recipe.author = self.request.user
        recipe.save()

        ingredient_formset = IngredientFormSet(self.request.POST, instance=recipe)
        instruction_formset = InstructionFormSet(self.request.POST, instance=recipe)

        if ingredient_formset.is_valid() and instruction_formset.is_valid():
            ingredient_formset.save()
            instruction_formset.save()
            messages.add_message(self.request, messages.SUCCESS, "Recipe created!")
            return super().form_valid(form)
        else:
            # If formset is invalid, delete the recipe and re-render the form with errors
            recipe.delete()
            return self.form_invalid(form)

    def form_invalid(self, form):
        """Handle invalid form submissions."""
        context = self.get_context_data(form=form)
        if self.request.method == "POST":
            # Create unsaved recipe instance for formset validation
            # This allows formsets to validate even if recipe form has errors
            try:
                recipe = form.save(commit=False)
                recipe.author = self.request.user
            except (ValueError, AttributeError):
                # If form is too invalid to create instance, create a minimal one
                recipe = Recipe(author=self.request.user)

            # Don't save yet, just use for formset validation
            ingredient_formset = IngredientFormSet(self.request.POST, instance=recipe)
            instruction_formset = InstructionFormSet(self.request.POST, instance=recipe)
            context["ingredient_formset"] = ingredient_formset
            context["instruction_formset"] = instruction_formset
        return self.render_to_response(context)

    def get_success_url(self):
        """
        Determine the redirect URL after successful recipe creation.
        """
        return reverse(settings.REDIRECT_URL_WHEN_LOGGED_IN)
