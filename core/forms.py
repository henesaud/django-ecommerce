from django import forms
from django_countries.fields import CountryField
from django_countries.widgets import CountrySelectWidget


PAYMENT_CHOICES = (("S", "Payment 1"), ("P", "Payment 2"))


class CheckoutForm(forms.Form):
    shipping_address = forms.CharField(required=False)
    shipping_address2 = forms.CharField(required=False)
    shipping_country = CountryField(blank_label="(select country)").formfield(
        required=False,
        widget=CountrySelectWidget(
            attrs={
                "class": "custom-select d-block w-100",
            }
        ),
    )
    shipping_zip = forms.CharField(required=False)
    payment_option = forms.ChoiceField(
        widget=forms.RadioSelect, choices=PAYMENT_CHOICES
    )
    cpf = forms.CharField(required=True, max_length=11)
    email = forms.EmailField()
