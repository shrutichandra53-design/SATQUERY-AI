from satellite import get_satellite_image


result = get_satellite_image(
    latitude=28.4744,
    longitude=77.5040
)


if result:

    print("SATELLITE IMAGE FOUND!")

    print(
        "Scene:",
        result["scene_id"]
    )

    print(
        "Date:",
        result["date"]
    )

    print(
        "Cloud cover:",
        result["cloud_cover"]
    )

    print(
        "Image URL:",
        result["image_url"]
    )

else:

    print("No satellite image found.")