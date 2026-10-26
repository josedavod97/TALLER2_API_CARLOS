from functools import wraps

from django.contrib import messages
from django.contrib.auth import login
from django.contrib.auth.decorators import login_required, user_passes_test
from django.shortcuts import redirect, render
from django.http import HttpResponseForbidden

from catalog.api import CoreAPIError, request_core, require_core_token
from catalog.forms import OrderForm, ProductForm, RegistrationForm


def catalog(request):
    try:
        products = request_core("GET", "/products")
    except CoreAPIError as exc:
        products = []
        messages.error(request, str(exc))
    return render(request, "catalog/product_list.html", {"products": products})


def product_detail(request, product_id):
    try:
        product = request_core("GET", f"/products/{product_id}")
    except CoreAPIError as exc:
        messages.error(request, str(exc))
        return redirect("catalog")
    form = OrderForm(product, request.POST or None)
    if request.method == "POST":
        if not request.user.is_authenticated:
            return redirect("login")
        if request.user.is_staff:
            return HttpResponseForbidden("Las cuentas administradoras no realizan pedidos.")
        if form.is_valid():
            variant = product["variants"][int(form.cleaned_data["variant"])]
            try:
                require_core_token()
                request_core(
                    "POST",
                    "/orders",
                    params={"customer": request.user.username},
                    json={
                        "items": [
                            {
                                "product_id": product_id,
                                "size": variant["size"],
                                "color": variant["color"],
                                "quantity": form.cleaned_data["quantity"],
                            }
                        ]
                    },
                )
            except CoreAPIError as exc:
                messages.error(request, str(exc))
            else:
                messages.success(request, "Pedido registrado correctamente.")
                return redirect("orders")
    return render(
        request, "catalog/product_detail.html", {"product": product, "form": form}
    )


@login_required
def orders(request):
    try:
        require_core_token()
        customer_orders = request_core(
            "GET", "/orders", params={"customer": request.user.username}
        )
    except CoreAPIError as exc:
        customer_orders = []
        messages.error(request, str(exc))
    return render(request, "catalog/orders.html", {"orders": customer_orders})


def register(request):
    form = RegistrationForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        user = form.save()
        login(request, user)
        messages.success(request, "Tu cuenta de cliente está lista.")
        return redirect("catalog")
    return render(request, "catalog/register.html", {"form": form})


def staff_required(view_func):
    @wraps(view_func)
    @login_required
    @user_passes_test(lambda user: user.is_staff)
    def wrapped(request, *args, **kwargs):
        return view_func(request, *args, **kwargs)

    return wrapped


@staff_required
def admin_products(request):
    try:
        products = request_core("GET", "/products")
    except CoreAPIError as exc:
        products = []
        messages.error(request, str(exc))
    return render(request, "catalog/admin_products.html", {"products": products})


@staff_required
def product_create(request):
    form = ProductForm(request.POST or None)
    if request.method == "POST" and form.is_valid():
        try:
            require_core_token()
            payload = form.cleaned_data.copy()
            payload["price"] = float(payload["price"])
            if not payload["image_url"]:
                payload["image_url"] = None
            request_core("POST", "/products", json=payload)
        except CoreAPIError as exc:
            messages.error(request, str(exc))
        else:
            messages.success(request, "Producto creado.")
            return redirect("admin-products")
    return render(
        request, "catalog/product_form.html", {"form": form, "title": "Nuevo producto"}
    )


@staff_required
def product_edit(request, product_id):
    try:
        product = request_core("GET", f"/products/{product_id}")
    except CoreAPIError as exc:
        messages.error(request, str(exc))
        return redirect("admin-products")
    initial = product.copy()
    initial["variants"] = "\n".join(
        f"{variant['size']}, {variant['color']}, {variant['stock']}"
        for variant in product["variants"]
    )
    form = ProductForm(request.POST or None, initial=initial)
    if request.method == "POST" and form.is_valid():
        try:
            require_core_token()
            payload = form.cleaned_data.copy()
            payload["price"] = float(payload["price"])
            if not payload["image_url"]:
                payload["image_url"] = None
            request_core("PATCH", f"/products/{product_id}", json=payload)
        except CoreAPIError as exc:
            messages.error(request, str(exc))
        else:
            messages.success(request, "Producto actualizado.")
            return redirect("admin-products")
    return render(
        request, "catalog/product_form.html", {"form": form, "title": "Editar producto"}
    )


@staff_required
def product_delete(request, product_id):
    if request.method != "POST":
        return redirect("admin-products")
    try:
        require_core_token()
        request_core("DELETE", f"/products/{product_id}")
    except CoreAPIError as exc:
        messages.error(request, str(exc))
    else:
        messages.success(request, "Producto desactivado.")
    return redirect("admin-products")
