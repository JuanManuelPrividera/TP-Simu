from sim.model.order import Order


def test_create_lots_preserves_order_configuration_and_scales_materials() -> None:
    order = Order(
        id=7,
        arrival_time=3.5,
        page_count=240,
        unit_count=130,
        book_type="B",
        priority=4,
        material_profile={0: 0.2, 1: 0.1, 4: 0.05},
    )

    lots = order.create_lots(50)

    assert [lot.units_in_lot for lot in lots] == [50, 50, 30]
    assert all(lot.page_count == 240 for lot in lots)
    assert all(lot.book_type == "B" for lot in lots)
    assert all(lot.priority == 4 for lot in lots)
    assert lots[0].material_requirements == {0: 10.0, 1: 5.0, 4: 2.5}
    assert lots[2].material_requirements == {0: 6.0, 1: 3.0, 4: 1.5}
