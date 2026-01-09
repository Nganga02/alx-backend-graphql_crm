from gql import gql, Client
from gql.transport.requests import RequestsHTTPTransport
from datetime import datetime



transport=RequestsHTTPTransport(
    url='http://localhost:8000/graphql',
)

client=Client(transport=transport)


mutation_query=gql(
    """
    mutation{
        updateLowStockProducts{
            success
            updatedCount
            message
            products {
            name
            stock
            }
        }
    }
"""
)
log_path = '/tmp/low_stock_updates_log.txt'
try:
    result=client.execute(mutation_query)
    timestamp=datetime.now().isoformat()

    payload = result["updateLowStockProducts"]

    if payload["success"] and payload["updatedCount"] > 0:
        with open(log_path, "a") as log_file:
            for product in payload["products"]:
                log_file.write(
                    f"[{timestamp}] Updated {product['name']} stock to {product['stock']}\n"
                )

except Exception as e:
    print("An Error occured: {e}")


