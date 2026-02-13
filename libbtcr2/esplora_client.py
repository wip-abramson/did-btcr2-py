import requests
from typing import Dict, Optional, List


class EsploraClient:
    def __init__(self, base_url: str = "https://mutinynet.com/api"):
        self.base_url = base_url
        self.session = requests.Session()

    def _make_request(
        self,
        method: str,
        endpoint: str,
        params: Optional[Dict] = None,
        json: Optional[Dict] = None
    ) -> Dict:
        """Helper method to make HTTP requests"""
        url = f"{self.base_url}/{endpoint}"
        response = self.session.request(method, url, params=params, json=json)
        response.raise_for_status()
        return response.json()

    def get_address(self, address: str) -> Dict:
        """
        Get address information.
        
        Args:
            address: The Bitcoin address to query
            
        Returns:
            Dict containing address information including:
            - chain_stats: Statistics for the main chain
            - mempool_stats: Statistics for the mempool
        """
        return self._make_request("GET", f"address/{address}")

    def get_address_utxos(self, address: str) -> List[Dict]:
        """
        Get unspent transaction outputs (UTXOs) for an address.
        
        Args:
            address: The Bitcoin address to query
            
        Returns:
            List of UTXOs, each containing:
            - txid: Transaction ID
            - vout: Output index
            - value: Amount in satoshis
            - status: Status of the UTXO
        """
        return self._make_request("GET", f"address/{address}/utxo")

    def get_address_transactions(self, address: str) -> List[Dict]:
        """
        Get all transactions for an address.
        
        Args:
            address: The Bitcoin address to query
            
        Returns:
            List of transactions, each containing:
            - txid: Transaction ID
            - version: Transaction version
            - locktime: Transaction locktime
            - vin: List of inputs
            - vout: List of outputs
            - size: Transaction size in bytes
            - weight: Transaction weight
            - fee: Transaction fee in satoshis
            - status: Transaction status
        """
        return self._make_request("GET", f"address/{address}/txs")

    def get_transaction(self, txid: str) -> Dict:
        """
        Get a transaction by its ID.
        
        Args:
            txid: The transaction ID to query
            
        Returns:
            Dict containing transaction information including:
            - txid: Transaction ID
            - version: Transaction version
            - locktime: Transaction locktime
            - vin: List of inputs
            - vout: List of outputs
            - size: Transaction size in bytes
            - weight: Transaction weight
            - fee: Transaction fee in satoshis
            - status: Transaction status
        """
        return self._make_request("GET", f"tx/{txid}")  
    
    def get_transaction_hex(self, txid: str) -> str:
        """
        Get a transaction hex by its ID.
        
        Args:
            txid: The transaction ID to query
            
        Returns: the hex string of the transaction
        """
        url = f"{self.base_url}/tx/{txid}/hex"
        response = self.session.get(url)
        response.raise_for_status()
        return response.text
    
    def broadcast_tx(self, tx_hex):
        """
        Broadcast a raw transaction to the network. 
        
        Args:
            tx_hex: The transaction should be provided as hex in the request body.
            
        Returns: The txid will be returned on success.
        """
        url = f"{self.base_url}/tx"
        response = self.session.post(url, tx_hex)
        response.raise_for_status()
        return response.text