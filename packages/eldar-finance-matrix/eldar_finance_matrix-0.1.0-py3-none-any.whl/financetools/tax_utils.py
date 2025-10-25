def calculate_vat(price, vat_percent):
    """Vergi əlavə edir"""
    return price * (1 + vat_percent/100)

def net_income(gross, tax_percent):
    """Maaşdan vergi çıxır"""
    return gross * (1 - tax_percent/100)
