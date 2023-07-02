import random
import string

from django.conf import settings
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.exceptions import ObjectDoesNotExist
from django.shortcuts import redirect
from django.shortcuts import render, get_object_or_404
from django.utils import timezone
from django.views.generic import ListView, DetailView, View

from .forms import CheckoutForm
from .models import CATEGORY_CHOICES, Item, OrderItem, Order, Address


def products(request):
    context = {"items": Item.objects.all()}
    return render(request, "products.html", context)


def is_valid_form(values):
    valid = True
    for field in values:
        if field == "":
            valid = False
    return valid


class CheckoutView(View):
    def get(self, *args, **kwargs):
        try:
            order = Order.objects.get(user=self.request.user, ordered=False)
            form = CheckoutForm()
            context = {
                "form": form,
                "order": order,
            }

            shipping_address_qs = Address.objects.filter(
                user=self.request.user, default=True
            )
            if shipping_address_qs.exists():
                context.update({"default_shipping_address": shipping_address_qs[0]})

            return render(self.request, "checkout.html", context)
        except ObjectDoesNotExist:
            messages.info(self.request, "You do not have an active order")
            return redirect("core:checkout")

    def post(self, *args, **kwargs):
        form = CheckoutForm(self.request.POST or None)
        try:
            order = Order.objects.get(user=self.request.user, ordered=False)
            orderI = OrderItem.objects.filter(user=self.request.user, ordered=False)
            if form.is_valid():
                use_default_shipping = form.cleaned_data.get("use_default_shipping")
                if use_default_shipping:
                    print("Using the defualt shipping address")
                    address_qs = Address.objects.filter(
                        user=self.request.user, default=True
                    )
                    if address_qs.exists():
                        shipping_address = address_qs[0]
                        order.shipping_address = shipping_address
                        order.save()
                    else:
                        messages.info(
                            self.request, "No default shipping address available"
                        )
                        return redirect("core:checkout")
                else:
                    print("User is entering a new shipping address")
                    shipping_address1 = form.cleaned_data.get("shipping_address")
                    shipping_address2 = form.cleaned_data.get("shipping_address2")
                    shipping_country = form.cleaned_data.get("shipping_country")
                    shipping_zip = form.cleaned_data.get("shipping_zip")

                    if is_valid_form(
                        [shipping_address1, shipping_country, shipping_zip]
                    ):
                        shipping_address = Address(
                            user=self.request.user,
                            street_address=shipping_address1,
                            apartment_address=shipping_address2,
                            country=shipping_country,
                            zip=shipping_zip,
                        )
                        shipping_address.save()

                        order.shipping_address = shipping_address
                        order.save()

                        set_default_shipping = form.cleaned_data.get(
                            "set_default_shipping"
                        )
                        if set_default_shipping:
                            shipping_address.default = True
                            shipping_address.save()

                    else:
                        messages.info(
                            self.request,
                            "Please fill in the required shipping address fields",
                        )

                payment_email = form.cleaned_data.get("email")
                payment_cpf = form.cleaned_data.get("cpf")
                order.email = payment_email
                order.cpf = payment_cpf
                order.ordered = True
                order.save()
                orderI.update(ordered=True)
                return redirect("/")

        except ObjectDoesNotExist:
            messages.warning(self.request, "You do not have an active order")
            return redirect("core:order-summary")


class HomeView(ListView):
    model = Item
    paginate_by = 10
    template_name = "home.html"


class OrderSummaryView(LoginRequiredMixin, View):
    def get(self, *args, **kwargs):
        try:
            order = Order.objects.get(user=self.request.user, ordered=False)
            context = {"object": order}
            return render(self.request, "order_summary.html", context)
        except ObjectDoesNotExist:
            messages.warning(self.request, "You do not have an active order")
            return redirect("/")


class DashboardView(LoginRequiredMixin, View):
    def get(self, *args, **kwargs):
        try:
            orderItem = OrderItem.objects.filter(user=self.request.user, ordered=True)

            cat_price = dict(CATEGORY_CHOICES)
            cat_quantity = dict(CATEGORY_CHOICES)

            cat_price.update({}.fromkeys(cat_price, 0))
            cat_quantity.update({}.fromkeys(cat_quantity, 0))
            total_sale = 0
            for order_item in orderItem:
                if order_item.ordered is True:
                    cat_price[order_item.item.category] += (
                        order_item.sellPrice * order_item.quantity
                    )
                    cat_quantity[order_item.item.category] += order_item.quantity
            context = {
                "price": list(cat_price.values()),
                "quant": list(cat_quantity.values()),
                "categories": list(dict(CATEGORY_CHOICES).values()),
            }
            return render(self.request, "dashboard.html", context)
        except ObjectDoesNotExist:
            messages.warning(
                self.request,
                "There is no sale; Your e-commerce sucks. Hire AionSolution to get profits.",
            )
            return redirect("/")


class ItemDetailView(DetailView):
    model = Item
    template_name = "product.html"


@login_required
def add_to_cart(request, slug):
    item = get_object_or_404(Item, slug=slug)

    order_item, created = OrderItem.objects.get_or_create(
        item=item, user=request.user, ordered=False, sellPrice=item.price
    )
    order_qs = Order.objects.filter(user=request.user, ordered=False)
    if order_qs.exists():
        order = order_qs[0]
        if item.stock == 0:
            messages.info(request, "No enough stock!")
            return redirect("core:order-summary")
        else:
            # check if the order item is in the order
            if order.items.filter(item__slug=item.slug).exists():
                order_item.quantity += 1
                order_item.save()
                item.stock -= 1
                item.save()
                messages.info(request, "This item quantity was updated.")
                return redirect("core:order-summary")
            else:
                order.items.add(order_item)
                item.stock -= 1
                item.save()
                messages.info(request, "This item was added to your cart.")
                return redirect("core:order-summary")
    else:
        ordered_date = timezone.now()
        order = Order.objects.create(user=request.user, ordered_date=ordered_date)
        order.items.add(order_item)
        messages.info(request, "This item was added to your cart.")
        return redirect("core:order-summary")


@login_required
def remove_from_cart(request, slug):
    item = get_object_or_404(Item, slug=slug)
    order_qs = Order.objects.filter(user=request.user, ordered=False)
    if order_qs.exists():
        order = order_qs[0]
        # check if the order item is in the order
        if order.items.filter(item__slug=item.slug).exists():
            order_item = OrderItem.objects.filter(
                item=item, user=request.user, ordered=False
            )[0]
            order.items.remove(order_item)
            item.stock += order_item.quantity
            order_item.delete()
            item.save()
            messages.info(request, "This item was removed from your cart.")
            return redirect("core:order-summary")
        else:
            messages.info(request, "This item was not in your cart")
            return redirect("core:product", slug=slug)
    else:
        messages.info(request, "You do not have an active order")
        return redirect("core:product", slug=slug)


@login_required
def remove_single_item_from_cart(request, slug):
    item = get_object_or_404(Item, slug=slug)
    order_qs = Order.objects.filter(user=request.user, ordered=False)
    if order_qs.exists():
        order = order_qs[0]
        # check if the order item is in the order
        if order.items.filter(item__slug=item.slug).exists():
            order_item = OrderItem.objects.filter(
                item=item, user=request.user, ordered=False
            )[0]
            if order_item.quantity > 1:
                order_item.quantity -= 1
                order_item.save()
            else:
                order.items.remove(order_item)
            item.stock += 1
            item.save()
            messages.info(request, "This item quantity was updated.")
            return redirect("core:order-summary")
        else:
            messages.info(request, "This item was not in your cart")
            return redirect("core:product", slug=slug)
    else:
        messages.info(request, "You do not have an active order")
        return redirect("core:product", slug=slug)
