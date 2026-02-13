from buidl.tx import TxIn, TxOut, Tx
from buidl.script import ScriptPubKey, address_to_script_pubkey
from .address_manager import AddressManager

class BeaconManager(AddressManager):

    def __init__(self, network, beacon_id, signing_key, script_pubkey, esplora_client):
        self.beacon_id = beacon_id
        super().__init__(esplora_client, network, script_pubkey, signing_key)
        
        
    def construct_beacon_signal(self, commitment_bytes):
        if len(self.utxo_tx_ins) == 0:
            raise Exception(f"No UTXOs, fund beacon address {self.address}")
        
        tx_in = self.utxo_tx_ins.pop(0)

        script_pubkey = ScriptPubKey([0x6a, commitment_bytes])

        beacon_signal_txout = TxOut(0, script_pubkey)

        tx_fee = self.tx_fee

        refund_amount = tx_in.value() - tx_fee

        refund_script_pubkey = self.script_pubkey
        refund_out = TxOut(amount=refund_amount, script_pubkey=refund_script_pubkey)
        tx_ins = [tx_in]

        tx_outs = [refund_out, beacon_signal_txout]
        pending_beacon_signal = Tx(version=1, tx_ins=tx_ins, tx_outs=tx_outs, network=self.network,segwit=True)

        new_utxo_txin = TxIn(prev_tx=pending_beacon_signal.hash(), prev_index=0)
        new_utxo_txin._script_pubkey = refund_out.script_pubkey
        new_utxo_txin._value = refund_out.amount
        self.utxo_tx_ins.append(new_utxo_txin)

        return pending_beacon_signal

    def sign_beacon_signal(self, pending_signal):

        signing_res = pending_signal.sign_input(0, self.signing_key)
        print(signing_res)
        if not signing_res:
            raise Exception("Invalid Beacon Key, unable to sign signal")
        
        return pending_signal

    # TODO: only works on regtest
    # async def fund_beacon_address(self):
    #     result = await self.bitcoin_rpc.acall("send", {"outputs": { self.address: 0.2}})
    #     result2 = await self.bitcoin_rpc.acall("send", {"outputs": { self.address: 0.2}})
    #     result3 = await self.bitcoin_rpc.acall("send", {"outputs": { self.address: 0.2}})


    #     funding_txid = result["txid"]
    #     funding_tx_hex = await self.bitcoin_rpc.acall("getrawtransaction", {"txid": funding_txid})
    #     funding_tx = Tx.parse_hex(funding_tx_hex)
        
    #     self.add_funding_tx(funding_tx)