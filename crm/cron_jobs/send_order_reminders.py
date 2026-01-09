from gql import gql, Client
from gql.transport.requests import RequestsHTTPTransport
from datetime import timedelta, datetime

transport = RequestsHTTPTransport(
    url='http://localhost:8000/graphql',
)


client = Client(transport=transport)
timeframe=datetime.now()-timedelta(days=7)



query=gql(
    """
    query($after: Datetime!){
        allOrders(order_date_after: $after){
        edges{
            node{
                id
                customer{
                    email
                    }
                }
            }
        }
    }
"""
)

variables = {
    "after": timeframe.isoformat()
}

result=client.execute(query, variable_values=variables)
print(result)

log_path = "/tmp/order_reminders_log.txt"
timestamp = datetime.now().isoformat()

with open(log_path, "a") as log_file:
    for edge in result.get("allOrders", {}).get("edges", []):
        order = edge.get("node", {})
        order_id = order.get("id")
        email = order.get("customer", {}).get("email")
        log_file.write(f"[{timestamp}] Order ID: {order_id}, Customer Email: {email}\n")

print("Order reminders processed!")