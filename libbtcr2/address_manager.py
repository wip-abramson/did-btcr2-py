from buidl.tx import TxIn, Tx, TxOut
from buidl.script import address_to_script_pubkey
from buidl.helper import str_to_bytes

class AddressManager():

    def __init__(self, esplora_client, network, script_pubkey, signing_key):
        self.esplora_client = esplora_client
        self.network = network
        self.script_pubkey = script_pubkey
        self.address = script_pubkey.address(network)
        self.signing_key = signing_key
        self.utxo_tx_ins = self.fetch_utxos()
        self.tx_fee = 4000
    
    def fetch_utxos(self):
        tx_ins = []
        try:
            utxos = self.esplora_client.get_address_utxos(self.address)
            
            print("utxos", utxos)
            # utxos = [utxo for utxo in utxos if utxo["status"]["confirmed"]]
            for utxo in utxos:
                txid = bytes.fromhex(utxo["txid"])
                prev_index = utxo["vout"]
                print("txid", txid)
                print("prev_index", prev_index)
                print("value", utxo["value"])
                print("utxo", utxo)
                txin = TxIn(prev_tx=txid, prev_index=prev_index)
                txin._script_pubkey = self.script_pubkey
                txin._value = utxo["value"]
                tx_ins.append(txin)
            print(f"Found {len(utxos)} UTXOs for {self.address}")
        except Exception as e:
            print(f"Error fetching UTXOs: {e}")
        return tx_ins
    
    def add_funding_tx(self, funding_tx):
        print("Adding funding TX")
        for index, tx_out in enumerate(funding_tx.tx_outs):
            addr = tx_out.script_pubkey.address(network=self.network)
            print(self.address, addr)
            if self.address == addr:
                print("Found funding TXOUT")
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
        if amount > 21000000 * 100000000:  # Max Bitcoin supply in satoshis
            raise ValueError("Amount exceeds maximum Bitcoin supply")
            
        if len(self.utxo_tx_ins) == 0:
            self.utxo_tx_ins = self.fetch_utxos()
            if len(self.utxo_tx_ins) == 0:
                raise Exception(f"No UTXOs, fund address {self.address}")
        
        # Select UTXOs to spend
        tx_ins = []
        total_value = 0
        for tx_in in self.utxo_tx_ins:
            print(f"UTXO value: {tx_in.value()} satoshis")
            total_value += tx_in.value()
            tx_ins.append(tx_in)
            
            if total_value >= amount + tx_fee:
                break

        print(f"Selected UTXOs with total value: {total_value} satoshis")
        print(f"Required amount: {amount} satoshis")
        print(f"Transaction fee: {tx_fee} satoshis")

        if total_value < amount + tx_fee:
            raise Exception(
                f"Insufficient funds. Need {amount + tx_fee} satoshis, "
                f"but only have {total_value} satoshis"
            )

        # Calculate refund amount
        refund_amount = total_value - amount - tx_fee
        if refund_amount < 0:
            raise Exception(
                "Transaction fee would make refund amount negative"
            )

        # Create transaction outputs
        print(f"Creating output for {amount} satoshis to {address}")
        txout = TxOut(amount=amount, script_pubkey=script_pubkey)
        print(f"Creating refund output for {refund_amount} satoshis to {self.address}")
        refund_out = TxOut(
            amount=refund_amount,
            script_pubkey=self.script_pubkey
        )

        print("Transaction details:")
        print(f"Inputs: {len(tx_ins)} UTXOs totaling {total_value} satoshis")
        print(f"Outputs: {amount} satoshis to {address} + {refund_amount} satoshis refund")
        print(f"Fee: {tx_fee} satoshis")

        # Create and sign transaction
        tx = Tx(
            version=1,
            tx_ins=tx_ins,
            tx_outs=[txout, refund_out],
            network=self.network,
            segwit=True
        )

        for index in range(len(tx.tx_ins)):
            tx.sign_input(index, self.signing_key)

        # Broadcast transaction
        tx_hex = tx.serialize().hex()
        try:
            tx_id = self.esplora_client.broadcast_tx(tx_hex)
            print(f"Sent {amount} to {address} with txid {tx_id}")
            # Refresh UTXOs after successful broadcast
            new_utxo_txin = TxIn(prev_tx=tx.hash(), prev_index=0)
            new_utxo_txin._script_pubkey = refund_out.script_pubkey
            new_utxo_txin._value = refund_out.amount
            self.utxo_tx_ins.append(new_utxo_txin)

            return tx_id
        except Exception as e:
            print(f"Failed to broadcast transaction: {e}")
            print(f"Transaction hex: {tx_hex}")
            raise

