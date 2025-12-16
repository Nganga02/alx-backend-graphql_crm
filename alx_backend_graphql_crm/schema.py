from graphene import ObjectType, String, Schema 



class Query(ObjectType):
    hello = String(first_name = String(default_value='GraphQL'))
    goodbye = String()

    def resolve_hello(root, info, first_name):
        return f'Hello {first_name}'
    
    def resolve_goodbye(root, info):
        return 'Goodbye'

schema = Schema(query=Query)