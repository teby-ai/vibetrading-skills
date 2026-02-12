#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Hyperliquid API Client using direct HTTP requests
Based on: https://hyperliquid.gitbook.io/hyperliquid-docs/for-developers/api/exchange-endpoint

Fixed version with corrected syntax errors
"""

import os
import time
import json
import hmac
import hashlib
import logging
from datetime import datetime
import requests

class HyperliquidAPI:
    """Hyperliquid API client using direct HTTP requests"""
    
    def __init__(self, api_key, account_address, testnet=False):
        """
        Initialize Hyperliquid API client
        
        Args:
            api_key: API key for authentication
            account_address: Account address for signing
            testnet: Use testnet (True) or mainnet (False)
        """
        self.api_key = api_key
        self.account_address = account_address
        self.testnet = testnet
        
        # Set base URL based on network
        if testnet:
            self.base_url = "https://api.hyperliquid-testnet.xyz"
        else:
            self.base_url = "https://api.hyperliquid.xyz"
        
        # Setup logging
        self.logger = logging.getLogger(__name__)
        self.logger.info("Hyperliquid API client initialized (testnet: {})".format(testnet))
    
    def _generate_signature(self, message):
        """Generate HMAC signature for authentication"""
        try:
            # Convert message to string if it's a dict
            if isinstance(message, dict):
                message_str = json.dumps(message, separators=(',', ':'))
            else:
                message_str = str(message)
            
            # Create HMAC signature
            signature = hmac.new(
                self.api_key.encode(),
                message_str.encode(),
                hashlib.sha256
            ).hexdigest()
            
            return signature
        except Exception as e:
            self.logger.error("Error generating signature: {}".format(e))
            return None
    
    def _make_request(self, endpoint, method="POST", data=None, auth=False):
        """
        Make HTTP request to Hyperliquid API
        
        Args:
            endpoint: API endpoint
            method: HTTP method (GET, POST)
            data: Request data
            auth: Whether to include authentication
            
        Returns:
            Response data as dictionary
        """
        url = "{}{}".format(self.base_url, endpoint)
        headers = {
            "Content-Type": "application/json"
        }
        
        # Add authentication if required
        if auth and self.api_key:
            timestamp = str(int(time.time() * 1000))
            signature = self._generate_signature(timestamp)
            
            if signature:
                headers["X-API-KEY"] = self.api_key
                headers["X-SIGNATURE"] = signature
                headers["X-TIMESTAMP"] = timestamp
        
        try:
            self.logger.debug("Making {} request to {}".format(method, url))
            
            if method.upper() == "GET":
                response = requests.get(url, headers=headers, params=data)
            else:
                response = requests.post(url, headers=headers, json=data)
            
            response.raise_for_status()
            return response.json()
            
        except requests.exceptions.RequestException as e:
            self.logger.error("API request failed: {}".format(e))
            return {"error": str(e)}
        except Exception as e:
            self.logger.error("Unexpected error: {}".format(e))
            return {"error": str(e)}
    
    def health_check(self):
        """Check API health"""
        try:
            # According to Hyperliquid docs, /info should be POST with empty data
            response = self._make_request("/info", method="POST", data={})
            return "error" not in response
        except Exception as e:
            self.logger.error("Health check failed: {}".format(e))
            return False
    
    def get_price(self, symbol):
        """Get current price for a symbol"""
        try:
            data = {
                "type": "ticker",
                "symbol": symbol
            }
            
            response = self._make_request("/exchange", method="POST", data=data)
            
            if "error" not in response:
                # Parse response to extract price
                if "data" in response and response["data"]:
                    ticker_data = response["data"][0]
                    return float(ticker_data.get("lastPrice", 0))
            
            self.logger.error("Failed to get price for {}".format(symbol))
            return 0.0
            
        except Exception as e:
            self.logger.error("Error getting price: {}".format(e))
            return 0.0
    
    def place_order(self, symbol, is_buy, size, order_type="limit", price=None):
        """
        Place an order
        
        Args:
            symbol: Trading symbol (e.g., "BTC", "ETH", "HYPE")
            is_buy: True for buy, False for sell
            size: Order size
            order_type: "limit" or "market"
            price: Price for limit orders
            
        Returns:
            Order response
        """
        try:
            # Prepare order data
            order = {
                "symbol": symbol,
                "isBuy": is_buy,
                "limitPx": str(price) if price else "0",
                "sz": str(size),
                "orderType": {"limit": {"tif": "Gtc"}} if order_type == "limit" else {"market": {}}
            }
            
            # Prepare request data
            request_data = {
                "action": {
                    "type": "order",
                    "orders": [order]
                },
                "nonce": int(time.time() * 1000),
                "signature": {
                    "r": "",
                    "s": "",
                    "v": 0
                }
            }
            
            # Generate signature
            signature_message = {
                "action": request_data["action"],
                "nonce": request_data["nonce"]
            }
            
            signature = self._generate_signature(signature_message)
            if signature:
                request_data["signature"] = signature
            
            # Make authenticated request
            response = self._make_request("/exchange", method="POST", data=request_data, auth=True)
            
            if "error" not in response:
                self.logger.info("Order placed: {} {} {} {} at {}".format(
                    "BUY" if is_buy else "SELL", size, symbol,
                    order_type, price if price else "market"
                ))
            
            return response
            
        except Exception as e:
            self.logger.error("Error placing order: {}".format(e))
            return {"error": str(e)}
    
    def cancel_all_orders(self, symbol):
        """Cancel all orders for a symbol"""
        try:
            request_data = {
                "action": {
                    "type": "cancelAll",
                    "symbol": symbol
                },
                "nonce": int(time.time() * 1000),
                "signature": {
                    "r": "",
                    "s": "",
                    "v": 0
                }
            }
            
            # Generate signature
            signature_message = {
                "action": request_data["action"],
                "nonce": request_data["nonce"]
            }
            
            signature = self._generate_signature(signature_message)
            if signature:
                request_data["signature"] = signature
            
            response = self._make_request("/exchange", method="POST", data=request_data, auth=True)
            
            if "error" not in response:
                self.logger.info("All orders cancelled for {}".format(symbol))
                return True
            else:
                self.logger.error("Failed to cancel orders: {}".format(response.get("error")))
                return False
                
        except Exception as e:
            self.logger.error("Error cancelling orders: {}".format(e))
            return False
    
    def get_open_orders(self, symbol):
        """Get open orders for a symbol"""
        try:
            data = {
                "type": "openOrders",
                "symbol": symbol
            }
            
            response = self._make_request("/exchange", method="POST", data=data, auth=True)
            
            if "error" not in response and "data" in response:
                return response["data"]
            else:
                return []
                
        except Exception as e:
            self.logger.error("Error getting open orders: {}".format(e))
            return []
    
    def get_account_info(self):
        """Get account information"""
        try:
            response = self._make_request("/info", method="POST", data={}, auth=True)
            
            if "error" not in response:
                return response
            else:
                self.logger.error("Failed to get account info: {}".format(response.get("error")))
                return {}
                
        except Exception as e:
            self.logger.error("Error getting account info: {}".format(e))
            return {}
    
    def get_balance(self):
        """Get account balance"""
        try:
            account_info = self.get_account_info()
            
            if "data" in account_info and "balances" in account_info["data"]:
                return account_info["data"]["balances"]
            else:
                return {}
                
        except Exception as e:
            self.logger.error("Error getting balance: {}".format(e))
            return {}
    
    def get_positions(self):
        """Get open positions"""
        try:
            data = {
                "type": "positions"
            }
            
            response = self._make_request("/exchange", method="POST", data=data, auth=True)
            
            if "error" not in response and "data" in response:
                return response["data"]
            else:
                return []
                
        except Exception as e:
            self.logger.error("Error getting positions: {}".format(e))
            return []


# Alias for backward compatibility
HyperliquidClient = HyperliquidAPI