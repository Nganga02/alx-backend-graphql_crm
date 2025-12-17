import graphene
from graphene_django import DjangoObjectType
from django.db import transaction, IntegrityError
from graphql import GraphQLError
from decimal import Decimal as PythonDecimal

from .models import (
    Customer,
    Product,
    Order
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

class ProductType(DjangoObjectType):
    price = FlexibleDecimal()
    class Meta:
        model= Product
        fields= '__all__'

class OrderType(DjangoObjectType):
    class Meta:
        model= Order
        fields= '__all__'

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


# Query (if not already defined)
class Query(graphene.ObjectType):
    customers = graphene.List(CustomerType)
    products = graphene.List(ProductType) 
    orders = graphene.List(OrderType)

    def resolve_customers(root, info):
        return Customer.objects.all()

    def resolve_products(root, info):
        return Product.objects.all()

    def resolve_orders(root, info):
        return Order.objects.all()



# Mutation root
class Mutation(graphene.ObjectType):
    create_customer = CreateCustomer.Field()
    bulk_create_customers = BulkCreateCustomers.Field()
    create_product = CreateProduct.Field()
    create_order = CreateOrder.Field()