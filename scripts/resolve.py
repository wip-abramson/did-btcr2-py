import asyncio
import json

from libbtcr2.resolver import Btcr2Resolver


async def resolve_did():

    networkDefinitions = {
        "regtest": {
            "btc_network": "regtest",
            "esplora_api": "http://localhost:3000",
        },
        "mutinynet": {
            "btc_network": "signet",
            "esplora_api": "https://mutinynet.com/api",
        },
        "signet": {
            "btc_network": "signet",
            "esplora_api": "https://mempool.space/signet/api",
        },
    }

    # test_folder_path = (
    #     "TestVectors/regtest/"
    #     "k1qgp5h79scv4sfqkzak5g6y89dsy3cq0pd2nussu2cm3zjfhn4ekwrucc4q7t7"
    # )
    # test_folder_path = (
    #     "TestVectors/signet/"
    #     "x1qyj23twdpn927d5ky2f5ulgmr9uudq2pd08gxy05fdjzxvfclzn2zazps8w"
    # )
    test_folder_path = (
        "TestVectors/mutinynet/k1q5pa5tq86fzrl0ez32nh8e0ks4tzzkxnnmn8tdvxk04ahzt70u09dag02h0cp"
    )

    with open(f"{test_folder_path}/did.txt") as f:
        # Read the contents of the file into a variable
        did_to_resolve = f.read()
        # Print the names
        print(did_to_resolve)

    with open(f"{test_folder_path}/resolutionOptions.json") as f:
        resolution_options = json.load(f)
        print(resolution_options)

    # with open(f"{test_folder_path}/targetDidDocument.json") as f:
    #     initial_document = json.load(f)
    #     print(initial_document)

    resolver = Btcr2Resolver(networkDefinitions=networkDefinitions, logging=True)
    print(resolver.logging)
    resolution_result = await resolver.resolve(did_to_resolve, resolution_options)

    print("Resolved Document")
    print(json.dumps(resolution_result, indent=2))

    with open(f"{test_folder_path}/resolutionResult.json", "w") as f:
        json.dump(resolution_result, f, indent=2)


asyncio.run(resolve_did())
