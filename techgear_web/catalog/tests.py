from django.test import SimpleTestCase

from catalog.forms import OrderForm, ProductForm


class ProductFormTests(SimpleTestCase):
    def test_product_form_parses_stock_per_size_and_color(self):
        form = ProductForm(
            data={
                "name": "Camisa esencial",
                "description": "Camisa de algodón",
                "price": "29.90",
                "category": "Camisas",
                "variants": "M, Negro, 8\nL, Negro, 4",
                "image_url": "",
                "active": "on",
            }
        )

        self.assertTrue(form.is_valid(), form.errors)
        self.assertEqual(
            form.cleaned_data["variants"],
            [
                {"size": "M", "color": "Negro", "stock": 8},
                {"size": "L", "color": "Negro", "stock": 4},
            ],
        )

    def test_product_form_rejects_duplicate_variants(self):
        form = ProductForm(
            data={
                "name": "Camisa esencial",
                "description": "Camisa de algodón",
                "price": "29.90",
                "category": "Camisas",
                "variants": "M, Negro, 8\nm, negro, 4",
                "image_url": "",
            }
        )

        self.assertFalse(form.is_valid())
        self.assertIn("variants", form.errors)

    def test_order_form_only_offers_variants_with_stock(self):
        product = {
            "variants": [
                {"size": "M", "color": "Negro", "stock": 3},
                {"size": "L", "color": "Negro", "stock": 0},
            ]
        }

        form = OrderForm(product)

        self.assertEqual(form.fields["variant"].choices, [("0", "M · Negro (stock: 3)")])
