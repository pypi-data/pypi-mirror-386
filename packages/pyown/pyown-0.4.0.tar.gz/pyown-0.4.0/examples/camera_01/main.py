import asyncio
import logging

from pyown.client import Client
from pyown.items import Camera


async def run(host: str, port: int, password: str):
    client = Client(host=host, port=port, password=password)

    await client.start()

    # Camera 00 is at WHERE address 4000
    camera = Camera(client, "4000")

    # Activate the camera to receive video
    print("Activating camera...")
    await camera.receive_video()
    print("Camera activated!")
    print(f"Video stream available at: http://{host}/telecamera.php")

    # Adjust camera settings
    print("\nAdjusting camera settings...")
    await camera.zoom_in()
    await camera.increase_luminosity()
    await camera.increase_contrast()

    # Display a specific dial
    print("\nDisplaying dial 1-1...")
    await camera.display_dial(1, 1)

    # Wait a bit before freeing resources
    await asyncio.sleep(2)

    # Free video resources
    print("\nFreeing video resources...")
    await camera.free_resources()

    await client.close()


def main(host: str, port: int, password: str):
    # Set the logging level to DEBUG
    logging.basicConfig(
        level=logging.DEBUG,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    # Run the asyncio event loop
    asyncio.run(run(host, port, password))


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser()
    parser.add_argument("--host", type=str, help="The host to connect to", default="192.168.1.35")
    parser.add_argument("--port", type=int, help="The port to connect to", default=20000)
    parser.add_argument(
        "--password",
        type=str,
        help="The password to authenticate with",
        default="12345",
    )

    args = parser.parse_args()

    main(args.host, args.port, args.password)
