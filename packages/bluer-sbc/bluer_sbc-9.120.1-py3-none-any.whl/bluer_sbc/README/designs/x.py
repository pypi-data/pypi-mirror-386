from bluer_objects import README
from bluer_objects.README.items import ImageItems
from bluer_objects.README.consts import assets_url


assets2_x = assets_url(
    suffix="x",
    volume=2,
)

marquee = README.Items(
    [
        {
            "name": "x",
            "marquee": f"{assets2_x}/TBA.jpg",
            "url": "./bluer_sbc/docs/x.md",
        }
    ]
)

items = ImageItems(
    {
        f"{assets2_x}/TBA.jpg": "",
        f"{assets2_x}/TBA.jpg": "",
    }
)
