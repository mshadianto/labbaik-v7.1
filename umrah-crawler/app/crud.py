from sqlalchemy import text


async def search_hotels(session, city, checkin, checkout, adults, children, max_hotels):
    """Search hotels with best prices from offers."""
    q = text("""
      SELECT hm.hotel_id, hm.name, hm.city, hm.lat, hm.lon,
             hm.star_rating, hm.distance_to_haram_m, hm.distance_to_nabawi_m,
             hm.walk_time_to_haram_min, hm.walk_time_to_nabawi_min,
             MIN(o.price_total) AS best_price_total,
             MAX(o.fetched_at)  AS last_seen
      FROM hotels_master hm
      LEFT JOIN offers o ON o.hotel_id = hm.hotel_id
      WHERE hm.city = :city
      GROUP BY hm.hotel_id
      ORDER BY best_price_total NULLS LAST, last_seen DESC
      LIMIT :lim
    """)
    rows = (await session.execute(q, {"city": city, "lim": max_hotels})).mappings().all()
    return {
        "query": {
            "city": city,
            "checkin": str(checkin),
            "checkout": str(checkout),
            "adults": adults,
            "children": children
        },
        "results": list(rows)
    }


async def get_hotel_offers(session, hotel_id, limit):
    """Get recent offers for a specific hotel."""
    q = text("""
      SELECT offer_id, provider, room_name, board_type, refundability,
             price_total, price_per_night, taxes_fees, availability_status, fetched_at
      FROM offers
      WHERE hotel_id = :hid
      ORDER BY fetched_at DESC
      LIMIT :lim
    """)
    rows = (await session.execute(q, {"hid": hotel_id, "lim": limit})).mappings().all()
    return {"hotel_id": hotel_id, "offers": list(rows)}


async def get_calendar(session, hotel_id, start, end, provider):
    """Get availability calendar for a hotel."""
    if provider:
        q = text("""
            SELECT * FROM availability_calendar
            WHERE hotel_id=:hid AND provider=:p AND date BETWEEN :s AND :e
            ORDER BY date
        """)
        rows = (await session.execute(q, {"hid": hotel_id, "p": provider, "s": start, "e": end})).mappings().all()
    else:
        q = text("""
            SELECT * FROM availability_calendar
            WHERE hotel_id=:hid AND date BETWEEN :s AND :e
            ORDER BY provider, date
        """)
        rows = (await session.execute(q, {"hid": hotel_id, "s": start, "e": end})).mappings().all()
    return {"hotel_id": hotel_id, "start": str(start), "end": str(end), "rows": list(rows)}


async def get_transport(session, route, mode, limit):
    """Get transport schedule for a route."""
    q = text("""
      SELECT mode, operator, route, depart_time_local, arrive_time_local,
             duration_min, price_sar, class, availability, source_method, fetched_at
      FROM transport_schedule
      WHERE route=:r AND mode=:m
      ORDER BY fetched_at DESC
      LIMIT :lim
    """)
    rows = (await session.execute(q, {"r": route, "m": mode, "lim": limit})).mappings().all()
    return {"route": route, "mode": mode, "items": list(rows)}
