def make_budget_rule(limit):
    def fits(minutes):
        return (minutes >= 0) and (minutes <= limit)

    return fits


small_rule = make_budget_rule(20)
large_rule = make_budget_rule(40)
print(small_rule(25))
print(large_rule(25))
print(small_rule(20))
print(small_rule is large_rule)
