from django.contrib import admin

from .models import Item, OrderItem, Order, Address


class AddressAdmin(admin.ModelAdmin):
    list_display = [
        'user',
        'street_address',
        'apartment_address',
        'country',
        'zip',
        'default'
    ]
    list_filter = ['default', 'country']
    search_fields = ['user', 'street_address', 'apartment_address', 'zip']


""" class OrderAdmin(admin.ModelAdmin):
    list_display = ['user',
                    'ordered',
                    'received',
                    'shipping_address',
                    'payment',
                    ]
    list_display_links = [
        'user',
        'shipping_address',
        'payment',
    ]
    list_filter = ['ordered',
                   ]
    search_fields = [
        'user__username',
        'ref_code'
    ]
 """

admin.site.register(Item)
admin.site.register(OrderItem)
admin.site.register(Order)

admin.site.register(Address, AddressAdmin)
