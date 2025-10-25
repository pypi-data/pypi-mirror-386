def calculate_discount(price, percent):
    """Endirim tətbiq edir"""
    return price * (1 - percent/100)

def calculate_percentage(part, total):
    """Faiz hesablayır"""
    return (part/total)*100
