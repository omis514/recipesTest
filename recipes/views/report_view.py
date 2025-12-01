from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from recipes.models import Recipe
from recipes.forms import ReportForm


@login_required
def report_recipe(request, pk):
    """View to handle recipe reporting form."""
    recipe = get_object_or_404(Recipe, pk=pk)

    if request.method == "POST":
        form = ReportForm(request.POST)
        if form.is_valid():
            report = form.save(commit=False)
            report.recipe = recipe
            report.reporter = request.user
            report.save()
            messages.add_message(
                request,
                messages.SUCCESS,
                "Thank you for your report. We will review it shortly.",
            )
            return redirect("recipe_detail", pk=recipe.pk)
    else:
        form = ReportForm()

    context = {
        "form": form,
        "recipe": recipe,
    }
    return render(request, "report_recipe.html", context)
