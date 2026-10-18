from shop import orders


def invoice(customer, item, amount, currency, region):
    return {"customer": customer, "item": item, "amount": amount,
            "currency": currency, "shipping": orders.shipping_cost(region, 1)}


def sum_lines(lines):
    subtotal = 0
    for line in lines:
        subtotal += line.amount
    tax = subtotal * 0.2
    fee = 5 if subtotal < 100 else 0
    total = subtotal + tax + fee
    return round(total, 2)


class InvoiceBean:
    def get_number(self):
        return self._number

    def set_number(self, value):
        self._number = value

    def get_amount(self):
        return self._amount

    def set_amount(self, value):
        self._amount = value


class Formatter:
    def __init__(self, invoice):
        self.invoice = invoice

    def render(self):
        return f"Invoice {self.invoice}"
