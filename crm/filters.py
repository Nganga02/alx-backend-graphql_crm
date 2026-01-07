import django_filters as filters
from django.db import models
from .models import (
    Customer,
    Product,
    Order
)

COUNTRY_CODES = [
    ('+1', 'United States / Canada (+1)'),
    ('+234', 'Nigeria (+234)'),
    ('+254', 'Kenya (+254)'),
    ('+255', 'Tanzania (+255)')
]

class CustomerFilter(filters.FilterSet):
    """
    Cuastom filter to be applied to the Customer model by default
    """
    name_i_contains=filters.CharFilter(field_name='name', lookup_expr='icontains', label='nameIcontains')
    email_i_contains=filters.CharFilter(field_name='email', lookup_expr='icontains', label='emailIcontains)')

    phone_country_code = filters.ChoiceFilter(
        field_name='phone',
        choices=COUNTRY_CODES,
        method='filter_phone',
        label='PhoneCountryCode',
        empty_label='All countries'  # Optional: show all if none selected
    )
    class Meta:
        model=Customer
        fields=[]

    def filter_phone(self, queryset, name, value):
        """
        Filter customers whose phone starts with the selected country code.
        If no value (or empty), return all.
        """
        if value:
            return queryset.filter(phone__startswith=value)
        return queryset
    
class ProductFilter(filters.FilterSet):
    """
    Default custom filter for the Product model
    """
    name=filters.CharFilter(lookup_expr='icontains', label='nameIcontains)')

    #Acts on the price field
    price_gte=filters.NumberFilter(field_name='price', lookup_expr='gte', label='priceGte')
    price_lte=filters.NumberFilter(field_name='price', lookup_expr='lte', label='priceLte')

    #Acts on the stock field
    stock_lte=filters.NumberFilter(field_name='stock', lookup_expr='lte', label='stockLte')
    stock_gte=filters.NumberFilter(field_name='stock', lookup_expr='gte', label='stockGte')

    low_stock = filters.BooleanFilter(
        method='filter_low_stock',
        label='Low Stock (less than 10)',
        help_text='Show products with stock below 10'
    )

    ordering_by=filters.OrderingFilter(
        fields=['stock']
    )

    class Meta:
        name=Product
        fields=[]
        

    def filter_low_stock(self, queryset, name, value):
        """
        If value is True, return products with stock < 10.
        Otherwise, return unchanged queryset.
        """
        if value:
            return queryset.filter(stock__lt=10)
        return queryset 


class OrderFilter(filters.FilterSet):
    total_amount_gte=filters.NumberFilter(field_name='total_amount', lookup_expr='gte', label='totalAmountGte')
    total_amount_lte=filters.NumberFilter(field_name='total_amount', lookup_expr='lte', label='totalAmountLte')
    order_date=filters.DateTimeFromToRangeFilter()
    customer_name=filters.CharFilter(field_name='customer__name', lookup_expr='icontains', label='customerName')
    product_name=filters.CharFilter(field_name='product__name', lookup_expr='icontains', label='productName')

    class Meta:
        model=Order
        fields={
            'product__product_id'
        }
