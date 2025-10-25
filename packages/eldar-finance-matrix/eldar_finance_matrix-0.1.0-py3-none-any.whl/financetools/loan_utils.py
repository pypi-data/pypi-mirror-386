def simple_interest(principal, rate, time):
    """Sadə faiz"""
    return principal * rate/100 * time

def compound_interest(principal, rate, periods):
    """Mürəkkəb faiz"""
    return principal * ((1 + rate/100) ** periods)

def loan_payment(principal, rate, months):
    """Aylıq kredit ödənişi"""
    monthly_rate = rate / 12 / 100
    return principal * monthly_rate / (1 - (1 + monthly_rate) ** -months)
