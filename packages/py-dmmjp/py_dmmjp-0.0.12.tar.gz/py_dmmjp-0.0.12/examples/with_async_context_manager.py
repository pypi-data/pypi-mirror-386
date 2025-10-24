#!/usr/bin/env python3

# pylint: disable=missing-function-docstring,missing-module-docstring,duplicate-code
# mypy: disable-error-code="arg-type"

"""
Usage of the py-dmm library with context manager
"""

import asyncio
import os
import sys

# Add the parent directory to the path to import py_dmm
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from py_dmmjp import AsyncDMMClient


async def main() -> None:
    api_key = os.getenv("DMM_API_KEY")
    affiliate_key = os.getenv("DMM_AFFILIATE_KEY")

    if not api_key:
        print("Please set the DMM_API_KEY environment variable")
        return

    if not affiliate_key:
        print("Please set the DMM_AFFILIATE_KEY environment variables")
        return

    async with AsyncDMMClient(
        api_key=api_key, affiliate_id=affiliate_key
    ) as dmm_client:
        floor_list = await dmm_client.get_floors()

        print(floor_list)

        services = []

        for site in floor_list:
            print(f"Site: {site.name} - {site.code}")

            for service in site.services:
                print(f"  Service: {service.name} - {service.code}")

                for floor in service.floors:
                    print(f"    Floor: {floor.name} - {floor.code}")

                    services.append((site.code, service.code, floor.code))

        # pylint: disable=W0612
        # be careful with rate limits when using asyncio.gather
        results = await asyncio.gather(
            *[
                dmm_client.get_products(
                    site=site_code, service=service_code, floor=floor_code, hits=5
                )
                for site_code, service_code, floor_code in services
            ]
        )

        for site_code, service_code, floor_code in services:
            products = await dmm_client.get_products(
                site=site_code, service=service_code, floor=floor_code, hits=5
            )

            print(
                f"({site_code} - {service_code} - {floor_code}): [{', '.join(product.content_id for product in products)}] "
            )


if __name__ == "__main__":
    asyncio.run(main())
