from shop import billing


def create_order(customer, item, quantity, price, discount, currency, region):
    return billing.invoice(customer, item, quantity * price - discount, currency, region)


def shipping_cost(region, weight):
    if region == "eu":
        return weight * 2
    elif region == "us":
        return weight * 3
    elif region == "asia":
        return weight * 4
    elif region == "africa":
        return weight * 5
    elif region == "oceania":
        return weight * 6
    return weight * 10


def validate(orders):
    for order in orders:
        if order:
            for line in order:
                if line:
                    while line.pending:
                        if line.retry:
                            line.pending = False


def totals(rows):
    subtotal = 0
    for row in rows:
        subtotal += row.amount
    tax = subtotal * 0.2
    fee = 5 if subtotal < 100 else 0
    total = subtotal + tax + fee
    return round(total, 2)


def _legacy_export(orders):
    return [str(o) for o in orders]


class Order:
    def __init__(self, customer):
        self.customer = customer

    def customer_city(self):
        return self.customer.profile.address.city.name

    def describe(self, invoice):
        header = f"{invoice.number} {invoice.date}"
        return header, invoice.amount, invoice.currency, invoice.status
