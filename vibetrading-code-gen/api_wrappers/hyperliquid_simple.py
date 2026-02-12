#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Simplified Hyperliquid API Client based on official documentation
https://hyperliquid.gitbook.io/hyperliquid-docs/for-developers/api/exchange-endpoint
"""

import time
import hmac
import hashlib
import json
import requests

class HyperliquidSimple:
    """Simplified Hyperliquid API client"""
    
    def __init__(self, private_key, address, testnet=False):
        """
        Initialize with private key and wallet address
        
        Args:
            private_key: Your private key for signing
            address: Your wallet address
            testnet: Use testnet (True) or mainnet (False)
        """
        self.private_key = private_key
        self.address = address
        
        if testnet:
            self.base_url = "https://api.hyperliquid-testnet.xyz"
        else:
            self.base_url = "https://api.hyperliquid.xyz"
    
    def _sign(self, message):
        """Sign a message with private key"""
        message_str = json.dumps(message, separators=(',', ':'))
        signature = hmac.new(
            self.private_key.encode(),
            message_str.encode(),
            hashlib.sha256
        ).hexdigest()
        return signature
    
    def post(self, endpoint, data, auth=False):
        """Make POST request to API"""
        url = f"{self.base_url}{endpoint}"
        headers = {"Content-Type": "application/json"}
        
        if auth:
            # Add authentication headers
            timestamp = str(int(time.time() * 1000))
            signature = self._sign({"timestamp": timestamp})
            
            headers.update({
                "X-API-KEY": self.private_key,
                "X-SIGNATURE": signature,
                "X-TIMESTAMP": timestamp
            })
        
        try:
            response = requests.post(url, headers=headers, json=data)
            response.raise_for_status()
            return response.json()
        except Exception as e:
            print(f"API error: {e}")
            if hasattr(e, 'response') and e.response:
                print(f"Response: {e.response.text[:200]}")
            return {"error": str(e)}
    
    def get_info(self):
        """Get exchange info"""
        return self.post("/info", {})
    
    def get_ticker(self, symbol):
        """Get ticker price for symbol"""
        data = {"type": "ticker", "symbol": symbol}
        response = self.post("/exchange", data)
        
        if "error" not in response and "data" in response:
            return response["data"][0].get("lastPrice", 0)
        return 0
    
    def place_order(self, symbol, is_buy, size, price=None):
        """
        Place an order
        
        Args:
            symbol: Trading symbol
            is_buy: True for buy, False for sell
            size: Order size
            price: Limit price (None for market)
        """
        order_type = {"limit": {"tif": "Gtc"}} if price else {"market": {}}
        
        order = {
            "a": self.address,
            "b": is_buy,
            "p": str(price) if price else "0",
            "s": str(size),
            "r": order_type,
            "t": {"limit": {"tif": "Gtc"}} if price else {"market": {}},
            "c": symbol,
        }
        
        # Simplified order format based on docs
        request_data = {
            "action": {
                "type": "order",
                "orders": [order]
            },
            "nonce": int(time.time() * 1000),
            "signature": self._sign({
                "action": {"type": "order", "orders": [order]},
                "nonce": int(time.time() * 1000)
            })
        }
        
        return self.post("/exchange", request_data, auth=True)
    
    def cancel_all_orders(self, symbol):
        """Cancel all orders for symbol"""
        request_data = {
            "action": {
                "type": "cancelAll",
                "symbol": symbol
            },
            "nonce": int(time.time() * 1000),
            "signature": self._sign({
                "action": {"type": "cancelAll", "symbol": symbol},
                "nonce": int(time.time() * 1000)
            })
        }
        
        return self.post("/exchange", request_data, auth=True)

# Test the API
if __name__ == "__main__":
    print("Testing Hyperliquid API...")
    
    # Create client (use testnet for testing)
    client = HyperliquidSimple(
        private_key="test_key",
        address="test_address",
        testnet=True  # Use testnet for testing
    )
    
    # Test info endpoint
    print("\n1. Testing /info endpoint...")
    info = client.get_info()
    if "error" not in info:
        print("✅ Info endpoint works")
    else:
        print(f"❌ Info error: {info.get('error')}")
    
    # Test ticker
    print("\n2. Testing ticker...")
    price = client.get_ticker("BTC")
    print(f"BTC price: ${price}")
    
    print("\n✅ API test complete")