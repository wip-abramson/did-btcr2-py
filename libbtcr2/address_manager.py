import logging

from buidl.tx import Tx, TxIn, TxOut

from .constants import DEFAULT_TX_FEE, MAX_BTC_SUPPLY_SATOSHIS

logger = logging.getLogger(__name__)


class AddressManager:
    def __init__(self, esplora_client, network, script_pubkey, signing_key, tx_fee=DEFAULT_TX_FEE):
        self.esplora_client = esplora_client
        self.network = network
        self.script_pubkey = script_pubkey
        self.address = script_pubkey.address(network)
        self.signing_key = signing_key
        self.utxo_tx_ins = self.fetch_utxos()
        self.tx_fee = tx_fee

    def fetch_utxos(self):
        tx_ins = []
        try:
            utxos = self.esplora_client.get_address_utxos(self.address)

            logger.debug("utxos: %s", utxos)
            # utxos = [utxo for utxo in utxos if utxo["status"]["confirmed"]]
            for utxo in utxos:
                txid = bytes.fromhex(utxo["txid"])
                prev_index = utxo["vout"]
                logger.debug("txid: %s", txid)
                logger.debug("prev_index: %s", prev_index)
                logger.debug("value: %s", utxo["value"])
                logger.debug("utxo: %s", utxo)
                txin = TxIn(prev_tx=txid, prev_index=prev_index)
                txin._script_pubkey = self.script_pubkey
                txin._value = utxo["value"]
                tx_ins.append(txin)
            logger.info("Found %d UTXOs for %s", len(utxos), self.address)
        except Exception as e:
            logger.error("Error fetching UTXOs: %s", e)
        return tx_ins

    def add_funding_tx(self, funding_tx):
        logger.info("Adding funding TX")
        for index, tx_out in enumerate(funding_tx.tx_outs):
            addr = tx_out.script_pubkey.address(network=self.network)
            logger.debug("Comparing addresses: %s %s", self.address, addr)
            if self.address == addr:
                logger.info("Found funding TXOUT")
                tx_in = TxIn(prev_tx=funding_tx.hash(), prev_index=index)
                tx_in._script_pubkey = tx_out.script_pubkey
                tx_in._value = tx_out.amount
                self.utxo_tx_ins.append(tx_in)

    def send_to_address(self, script_pubkey, amount):
        address = script_pubkey.address(network=self.network)
        tx_fee = self.tx_fee  # satoshis

        # Validate amount
        if amount <= 0:
            raise ValueError("Amount must be greater than 0")
        if amount > MAX_BTC_SUPPLY_SATOSHIS:
            raise ValueError("Amount exceeds maximum Bitcoin supply")

        if len(self.utxo_tx_ins) == 0:
            self.utxo_tx_ins = self.fetch_utxos()
            if len(self.utxo_tx_ins) == 0:
                raise Exception(f"No UTXOs, fund address {self.address}")

        # Select UTXOs to spend
        tx_ins = []
        total_value = 0
        for tx_in in self.utxo_tx_ins:
            logger.debug("UTXO value: %d satoshis", tx_in.value())
            total_value += tx_in.value()
            tx_ins.append(tx_in)

            if total_value >= amount + tx_fee:
                break

        logger.info("Selected UTXOs with total value: %d satoshis", total_value)
        logger.info("Required amount: %d satoshis", amount)
        logger.info("Transaction fee: %d satoshis", tx_fee)

        if total_value < amount + tx_fee:
            raise Exception(
                f"Insufficient funds. Need {amount + tx_fee} satoshis, "
                f"but only have {total_value} satoshis"
            )

        # Calculate refund amount
        refund_amount = total_value - amount - tx_fee
        if refund_amount < 0:
            raise Exception("Transaction fee would make refund amount negative")

        # Create transaction outputs
        logger.info("Creating output for %d satoshis to %s", amount, address)
        txout = TxOut(amount=amount, script_pubkey=script_pubkey)
        logger.info("Creating refund output for %d satoshis to %s", refund_amount, self.address)
        refund_out = TxOut(amount=refund_amount, script_pubkey=self.script_pubkey)

        logger.info("Transaction details:")
        logger.info("Inputs: %d UTXOs totaling %d satoshis", len(tx_ins), total_value)
        logger.info(
            "Outputs: %d satoshis to %s + %d satoshis refund", amount, address, refund_amount
        )
        logger.info("Fee: %d satoshis", tx_fee)

        # Create and sign transaction
        tx = Tx(
            version=1, tx_ins=tx_ins, tx_outs=[txout, refund_out], network=self.network, segwit=True
        )

        for index in range(len(tx.tx_ins)):
            tx.sign_input(index, self.signing_key)

        # Broadcast transaction
        tx_hex = tx.serialize().hex()
        try:
            tx_id = self.esplora_client.broadcast_tx(tx_hex)
            logger.info("Sent %d to %s with txid %s", amount, address, tx_id)
            # Refresh UTXOs after successful broadcast
            new_utxo_txin = TxIn(prev_tx=tx.hash(), prev_index=0)
            new_utxo_txin._script_pubkey = refund_out.script_pubkey
            new_utxo_txin._value = refund_out.amount
            self.utxo_tx_ins.append(new_utxo_txin)

            return tx_id
        except Exception as e:
            logger.error("Failed to broadcast transaction: %s", e)
            logger.debug("Transaction hex: %s", tx_hex)
            raise
