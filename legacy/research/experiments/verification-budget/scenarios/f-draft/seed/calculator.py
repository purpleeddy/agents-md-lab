def total(amount, discount=0):
    if discount:
        return amount - discount
    return amount + 1
