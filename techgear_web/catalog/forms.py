from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User


class RegistrationForm(UserCreationForm):
    email = forms.EmailField(required=True)

    class Meta(UserCreationForm.Meta):
        model = User
        fields = ("username", "email")


class ProductForm(forms.Form):
    name = forms.CharField(max_length=160)
    description = forms.CharField(widget=forms.Textarea)
    price = forms.DecimalField(min_value=0.01, max_digits=10, decimal_places=2)
    category = forms.CharField(max_length=100)
    variants = forms.CharField(
        widget=forms.Textarea(attrs={"rows": 5}),
        help_text="Una variante por línea, con el formato: talla, color, unidades. Ejemplo: M, Negro, 8",
    )
    image_url = forms.URLField(required=False)
    active = forms.BooleanField(required=False, initial=True)

    def clean_variants(self):
        variants = []
        seen = set()
        for line_number, line in enumerate(self.cleaned_data["variants"].splitlines(), 1):
            if not line.strip():
                continue
            parts = [part.strip() for part in line.split(",")]
            if len(parts) != 3 or not parts[0] or not parts[1]:
                raise forms.ValidationError(
                    f"Línea {line_number}: usa el formato talla, color, unidades."
                )
            try:
                stock = int(parts[2])
            except ValueError as exc:
                raise forms.ValidationError(
                    f"Línea {line_number}: las unidades deben ser un número entero."
                ) from exc
            if stock < 0:
                raise forms.ValidationError(
                    f"Línea {line_number}: las unidades no pueden ser negativas."
                )
            key = (parts[0].casefold(), parts[1].casefold())
            if key in seen:
                raise forms.ValidationError(
                    f"Línea {line_number}: esa combinación de talla y color está repetida."
                )
            seen.add(key)
            variants.append({"size": parts[0], "color": parts[1], "stock": stock})
        if not variants:
            raise forms.ValidationError("Agrega al menos una variante de talla y color.")
        return variants


class OrderForm(forms.Form):
    variant = forms.ChoiceField(label="Talla y color")
    quantity = forms.IntegerField(min_value=1, initial=1)

    def __init__(self, product, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["variant"].choices = [
            (
                str(index),
                f"{variant['size']} · {variant['color']} (stock: {variant['stock']})",
            )
            for index, variant in enumerate(product["variants"])
            if variant["stock"] > 0
        ]
        if not self.fields["variant"].choices:
            self.fields["variant"].disabled = True
