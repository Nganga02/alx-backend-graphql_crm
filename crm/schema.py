import graphene
from graphene import relay
from graphene_django import DjangoObjectType
from graphene_django.filter import DjangoFilterConnectionField
from django.db import transaction, IntegrityError
from graphql import GraphQLError
from decimal import Decimal as PythonDecimal

from .models import (
    Customer,
    Product,
    Order
)
from .filters import (
    CustomerFilter,
    ProductFilter,
    OrderFilter
)

class FlexibleDecimal(graphene.Scalar):
    """A Decimal scalar that accepts strings, floats, and ints"""

    @staticmethod
    def serialize(dt):
        if isinstance(dt, PythonDecimal):
            return str(dt)
        return float(dt)

    @staticmethod
    def parse_literal(node):
        if isinstance(node, graphene.StringValue):
            return PythonDecimal(node.value)
        if isinstance(node, graphene.FloatValue) or isinstance(node, graphene.IntValue):
            return PythonDecimal(str(node.value))
        return None

    @staticmethod
    def parse_value(value):
        try:
            return PythonDecimal(str(value))
        except Exception:
            return None


#Declaring the objects types
class CustomerType(DjangoObjectType):
    class Meta:
        model= Customer
        fields= '__all__'
        interfaces=(relay.Node,)
        

class ProductType(DjangoObjectType):
    price = FlexibleDecimal()
    class Meta:
        model= Product
        fields= '__all__'
        interfaces=(relay.Node,)


class OrderType(DjangoObjectType):
    class Meta:
        model= Order
        fields= '__all__'
        interfaces=(relay.Node,)


#Declaring the input object types
class CustomerInput(graphene.InputObjectType):
    name = graphene.String(required=True)
    email = graphene.String(required=True)
    phone = graphene.String(required=False)

class ProductInput(graphene.InputObjectType):
    name=graphene.String(required=True)
    price= graphene.Float(required=True)
    stock=graphene.Int(required=False, default_value=0)

class OrderInput(graphene.InputObjectType):
    customer_id = graphene.ID(name="customerId", required=True)
    product_ids = graphene.List(graphene.ID, name="productIds", required=True)


# Mutation Responses
class CreateCustomerPayload(graphene.ObjectType):
    customer = graphene.Field(CustomerType)
    message = graphene.String()

class BulkCustomerResult(graphene.ObjectType):
    customers = graphene.List(CustomerType)
    errors = graphene.List(graphene.String)

class CreateProductPayload(graphene.ObjectType):
    product = graphene.Field(ProductType)

class CreateOrderPayload(graphene.ObjectType):
    order = graphene.Field(OrderType)



# Mutations
class CreateCustomer(graphene.Mutation):
    class Arguments:
        input = CustomerInput(required=True)

    Output = CreateCustomerPayload

    @staticmethod
    def mutate(root, info, input):
        try:
            customer = Customer.objects.create(
                name=input.name,
                email=input.email,
                phone=input.phone or None
            )
            return CreateCustomerPayload(
                customer=customer,
                message="Customer created successfully"
            )
        except IntegrityError:
            raise GraphQLError("Email already exists")
        except Exception as e:
            raise GraphQLError(str(e))
        

class BulkCreateCustomers(graphene.Mutation):
    class Arguments:
        input = graphene.List(CustomerInput, required=True)

    Output = BulkCustomerResult

    @staticmethod
    @transaction.atomic
    def mutate(root, info, input):
        created = []
        errors = []

        for idx, data in enumerate(input):
            try:
                customer = Customer(
                    name=data.name,
                    email=data.email,
                    phone=data.phone or None
                )
                customer.full_clean()  # Validate model fields
                customer.save()
                created.append(customer)
            except IntegrityError:
                errors.append(f"Row {idx+1}: Email '{data.email}' already exists")
            except Exception as e:
                errors.append(f"Row {idx+1}: {str(e)}")

        return BulkCustomerResult(customers=created, errors=errors or None)

class CreateProduct(graphene.Mutation):
    class Arguments:
        input = ProductInput(required=True)

    Output = CreateProductPayload

    @staticmethod
    def mutate(root, info, input):
        if input.price <= 0:
            raise GraphQLError("Price must be positive")
        if input.stock < 0:
            raise GraphQLError("Stock cannot be negative")

        product = Product.objects.create(
            name=input.name,
            price=input.price,
            stock=input.stock
        )
        return CreateProductPayload(product=product)

class CreateOrder(graphene.Mutation):
    class Arguments:
        input = OrderInput(required=True)

    Output = CreateOrderPayload

    @staticmethod
    def mutate(root, info, input):
        if not input.product_ids:
            raise GraphQLError("At least one product must be selected")

        try:
            customer = Customer.objects.get(pk=input.customer_id)
        except Customer.DoesNotExist:
            raise GraphQLError("Invalid customer ID")

        products = []
        for pid in input.product_ids:
            try:
                products.append(Product.objects.get(pk=pid))
            except Product.DoesNotExist:
                raise GraphQLError(f"Invalid product ID: {pid}")

        order = Order.objects.create(customer=customer)
        order.products.set(products)
        order.save()  # Triggers total_amount calculation

        return CreateOrderPayload(order=order)


class UpdateLowStockProducts(graphene.Mutation):
    class Arguments:
        # You can add arguments later if needed (e.g., amount_to_add)
        pass

    # Return fields
    success = graphene.Boolean()
    updated_count = graphene.Int()
    products = graphene.List(ProductType)
    message = graphene.String()

    @staticmethod
    def mutate(root, info):
        low_stock_products = list(Product.objects.filter(stock__lt=10))

        if not low_stock_products:
            return UpdateLowStockProducts(
                success=True,
                updated_count=0,
                products=[],
                message="No products with low stock found."
            )

        try:
            updated_products = []
            for product in low_stock_products:
                product.stock += 10  
                product.save()
                updated_products.append(product)

            return UpdateLowStockProducts(
                success=True,
                updated_count=len(updated_products),
                products=updated_products,
                message=f"Successfully restocked {len(updated_products)} product(s)."
            )

        except Exception as e:
            raise GraphQLError(f"Failed to update stock: {str(e)}")



# Query (if not already defined)
class Query(graphene.ObjectType):
    """
    Query class responsible for graphql querying
    """
    customers = DjangoFilterConnectionField(
        CustomerType,
        filterset_class=CustomerFilter,
        description="Filterable list of customers"
    )
    products = DjangoFilterConnectionField(
        ProductType,
        filterset_class=ProductFilter,  
        description="Filterable and paginated list of products"
    ) 
    orders = DjangoFilterConnectionField(
        OrderType,
        filterset_class=OrderFilter,
        description="Filterable and paginated list of orders"
    )
    all_customers = DjangoFilterConnectionField(
        CustomerType,
        filterset_class=CustomerFilter,
    )
    all_products = DjangoFilterConnectionField(
        ProductType,
        filterset_class=ProductFilter,
    )
    all_orders = DjangoFilterConnectionField(
        OrderType,
        filterset_class=OrderFilter,
    )

    def resolve_customers(self, info, **kwargs):
        qs = Customer.objects.all()
        filterset = CustomerFilter(data=kwargs, queryset=qs, request=info.context)
        return filterset.qs

    def resolve_products(self, info, **kwargs):
        qs = Product.objects.all()
        filterset = ProductFilter(data=kwargs, queryset=qs, request=info.context)
        return filterset.qs

    def resolve_orders(self, info, **kwargs):
        qs = Order.objects.all()
        filterset = OrderFilter(data=kwargs, queryset=qs, request=info.context)
        return filterset.qs

    # Resolvers with ordering support
    def resolve_all_customers(self, info, order_by=None, **kwargs):
        qs = Customer.objects.all()
        if order_by:
            qs = qs.order_by(*order_by)
        return CustomerFilter(data=kwargs, queryset=qs, request=info.context).qs

    def resolve_all_products(self, info, order_by=None, **kwargs):
        qs = Product.objects.all()
        if order_by:
            qs = qs.order_by(*order_by)
        return ProductFilter(data=kwargs, queryset=qs).qs

    def resolve_all_orders(self, info, order_by=None, **kwargs):
        qs = Order.objects.all()
        if order_by:
            qs = qs.order_by(*order_by)
        return OrderFilter(data=kwargs, queryset=qs).qs



# Mutation root
class Mutation(graphene.ObjectType):
    create_customer = CreateCustomer.Field()
    bulk_create_customers = BulkCreateCustomers.Field()
    create_product = CreateProduct.Field()
    create_order = CreateOrder.Field()
    update_low_stock_products=UpdateLowStockProducts.Field()