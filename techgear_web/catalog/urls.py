from django.contrib.auth import views as auth_views
from django.urls import path

from catalog import views

urlpatterns = [
    path("", views.catalog, name="catalog"),
    path("productos/<str:product_id>/", views.product_detail, name="product-detail"),
    path("pedidos/", views.orders, name="orders"),
    path("registro/", views.register, name="register"),
    path(
        "ingresar/",
        auth_views.LoginView.as_view(template_name="catalog/login.html"),
        name="login",
    ),
    path(
        "salir/",
        auth_views.LogoutView.as_view(),
        name="logout",
    ),
    path("gestion/productos/", views.admin_products, name="admin-products"),
    path(
        "gestion/productos/nuevo/",
        views.product_create,
        name="product-create",
    ),
    path(
        "gestion/productos/<str:product_id>/editar/",
        views.product_edit,
        name="product-edit",
    ),
    path(
        "gestion/productos/<str:product_id>/eliminar/",
        views.product_delete,
        name="product-delete",
    ),
]
