def make_rule():
    limit = 10

    def fits(minutes):
        return minutes <= limit

    limit = 30
    return fits


rule = make_rule()
print(rule(20))
