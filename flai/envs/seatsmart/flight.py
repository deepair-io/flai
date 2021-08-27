class Flight:
    '''
    Flight is a abstraction of an actual flight.
    A flight object can be initialized with a FlightBaseState
    object (check the definition in models)

    >> flight = Flight(FlightBaseState())
    '''

    def __init__(self, base_state):
        self.state = base_state  # TODO: assert it is fligt base state object
        self.base_count = self._count_seats(base_state)
        self.tickets = sum(self.base_count.values())
        self.zone_revenue = self._zone_dict_init(base_state.SeatMap)

    def _zone_dict_init(self, seatmap):
        d = {}
        for zone in seatmap.Zones:
            d[zone.Name] = 0
        return d

    def _seat_to_zonename(self, state, seat):
        name = state.SeatMap.Zones[0].Name
        for zone in state.SeatMap.Zones:
            if (seat.Row in zone.IncludeRows) and (seat.Col not in zone.ExcludeCols) and ((seat.Row, seat.Col) not in zone.ExcludeSeats):
                name = zone.Name
        return name

    def _count_seats(self, state):
        d = self._zone_dict_init(seatmap=state.SeatMap)

        for row in state.Grid:
            for seat in row:
                if (not seat.Blocked) and (not seat.Ghost) and (seat.Available):
                    # Valid available seat
                    d[self._seat_to_zonename(state=state, seat=seat)] += 1
        return d

    @property
    def availability(self):
        return self._count_seats(state=self.state)

    @property
    def sold(self):
        c = self._count_seats(state=self.state)
        return {key: self.base_count[key] - c.get(key, 0) for key in c}

    @property
    def ticket_sold(self):
        return sum(self.base_count.values()) - self.tickets

    @property
    def zone_price(self):
        d = {}
        for zone in self.state.SeatMap.Zones:
            d[zone.Name] = {}
            d[zone.Name]['MinPrice'] = zone.PriceRule.MinPrice
            d[zone.Name]['Price'] = zone.PriceRule.Price
            d[zone.Name]['MaxPrice'] = zone.PriceRule.MaxPrice
        return d

    @zone_price.setter
    def zone_price(self, x):
        for key in x:
            for zone in self.state.SeatMap.Zones:
                if key == zone.Name:
                    zone.PriceRule.Price = x[key]

    def sell_seat(self, row, col):
        seat = self.state.Grid[row][col]

        # Check for valid seat
        assert (not seat.Blocked), "Transaction failed. Seat {},{} is Blocked".format(
            row, col)
        assert (not seat.Ghost), "Transaction failed. Seat {},{} is Ghost".format(
            row, col)
        assert (seat.Available), "Transaction failed. Seat {},{} is not available".format(
            row, col)
        assert (self.tickets >= 0), "Transaction failed. All tickets are sold".format(
            row, col)

        # if the seat is valid then update the zone revenue
        zonename = self._seat_to_zonename(state=self.state, seat=seat)
        for zone in self.state.SeatMap.Zones:
            if zonename == zone.Name:
                seat_revenue = zone.PriceRule.Price
                self.zone_revenue[zonename] += seat_revenue

        # finally sell the seat
        self.state.Grid[row][col].Available = False
        return seat_revenue

    def sell_ticket(self, number=1):
        self.tickets -= number
        return True
