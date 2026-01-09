from celery import shared_task
from gql import Client, gql
from gql.transport.requests import RequestsHTTPTransport
from datetime import datetime, date
import os



@shared_task(bind=True, autoretry_for=(Exception,), retry_backoff=30, retry_kwargs={"max_retries": 3})
def generate_crm_report():
    transport=RequestsHTTPTransport(
        url='http://localhost:8000/graphql/',
    )

    client=Client(
        transport=transport
    )

    LOG_PATH="/tmp/crm_report_log.txt"
    timestamp = datetime.now().isoformat()
    customer_count = 0
    total_orders = 0
    total_revenue = 0

    today = date.today().isoformat()
    if os.path.exists(LOG_PATH):
        with open(LOG_PATH, "r") as f:
            if any(today in line for line in f):
                print("CRM report already generated for today.")
                return

    customers_query=gql(
        """
        query{
            allCustomers{
                edges{
                    node{
                    }
                }
            }
        }
    """
    )

    orders_query=gql(
        """
        query{
            allOrders{
                edges{
                    node{
                    total_amount
                    }
                }
            }
        }
    """
    )

    customers_payload=client.execute(
        customers_query
    )

    orders_payload=client.execute(
        orders_query
    )

    for _ in customers_payload.get("allCustomers", {}).get("edges", {}):
        customer_count+=1

    
    for edge in orders_payload.get("allOrders", {}).get("edges", {}):
        total_orders+=1
        total_revenue+=edge.get("node", {}).get("total_amount")
    
    with open(LOG_PATH, "a") as log_file:
        log_file.write(
            f"{timestamp} - Report: {customer_count} customers, \
                {total_orders}, {total_revenue} revenue")
