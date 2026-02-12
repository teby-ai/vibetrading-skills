#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Hyperliquid API Client using direct HTTP requests
Based on: https://hyperliquid.gitbook.io/hyperliquid-docs/for-developers/api/exchange-endpoint
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
    
    # API endpoints
    BASE_URL = "https://api.hyperliquid.xyz"
    TESTNET_BASE_URL = "https://api.hyperliquid-testnet.xyz"
    
    def __init__(self, api_key, account_address, testnet = False):
        """
        Initialize Hyperliquid API client
        
        Args:
            api_key: Hyperliquid API key
            account_address: Hyperliquid account address
            testnet: Whether to use testnet (default: False)
        """
        self.api_key = api_key
        self.account_address = account_address
        self.testnet = testnet
        
        # Setup base URL
        self.base_url = self.TESTNET_BASE_URL if testnet else self.BASE_URL
        
        # Setup logging
        self.logger = logging.getLogger(__name__)
        
        # Session for connection pooling
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'VibeTrading/1.0',
            'Content-Type': 'application/json'
        })
        
        self.logger.info("Hyperliquid API client initialized (testnet: {testnet})")
    
    def _generate_signature(self, data):
        """
        Generate HMAC signature for authenticated requests
        
        Args:
            data: Request data to sign
            
        Returns:
            HMAC signature
        """
        message = json.dumps(data, separators=(',', ':'))
        signature = hmac.new(
            self.api_key.encode('utf-8'),
            message.encode('utf-8'),
            hashlib.sha256
        ).hexdigest()
        return signature
    
    def _make_request(self, endpoint, method = "POST", 
                     data = None, auth = False):
        """
        Make HTTP request to Hyperliquid API
        
        Args:
            endpoint: API endpoint
            method: HTTP method (GET, POST)
            data: Request data
            auth: Whether authentication is required
            
        Returns:
            API response as dictionary
        """
        url = "{self.base_url}{endpoint}"
        
        headers = {}
        if auth and data:
            # Add signature for authenticated requests
            signature = self._generate_signature(data)
            headers['X-API-Signature'] = signature
        
        try:
            if method.upper() == "GET":
                response = self.session.get(url, headers=headers, params=data)
            else:
                response = self.session.post(url, headers=headers, json=data)
            
            response.raise_for_status()
            return response.json()
            
        except requests.exceptions.RequestException as e:
            self.logger.error("API request failed: {e}")
            if hasattr(e, 'response') and e.response is not None:
                self.logger.error("Response: {e.response.text}")
            return {"error"(e)}
    
    # ===== Exchange Info Endpoints =====
    
    def get_exchange_info(self):
        """
        Get exchange information
        
        Returns:
            Exchange info including universe and meta data
        """
        endpoint = "/info"
        data = {"type": "meta"}
        return self._make_request(endpoint, "POST", data)
    
    def get_all_mids(self):
        """
        Get all mid prices
        
        Returns:
            Dictionary of symbol -> mid price
        """
        endpoint = "/info"
        data = {"type": "allMids"}
        return self._make_request(endpoint, "POST", data)
    
    def get_user_state(self):
        """
        Get user state (positions, balances, etc.)
        
        Returns:
            User state information
        """
        endpoint = "/info"
        data = {
            "type": "clearinghouseState",
            "user": self.account_address
        }
        return self._make_request(endpoint, "POST", data)
    
    def get_open_orders(self):
        """
        Get user's open orders
        
        Returns:
            List of open orders
        """
        endpoint = "/info"
        data = {
            "type": "openOrders",
            "user": self.account_address
        }
        response = self._make_request(endpoint, "POST", data)
        return response if isinstance(response, list) else []
    
    # ===== Trading Endpoints =====
    
    def place_order(self, order):
        """
        Place a new order
        
        Args:
            order: Order parameters
            
        Returns:
            Order response
        """
        endpoint = "/exchange"
        data = {
            "action": {
                "type": "order",
                "orders": [order]
            },
            "nonce"(time.time() * 1000),
            "signature": {
                "r": "",
                "s": "",
                "v": 0
            }
        }
        
        # Add signature for authenticated request
        signature = self._generate_signature(data)
        data["signature"] = signature
        
        return self._make_request(endpoint, "POST", data, auth=True)
    
    def cancel_order(self, coin, oid):
        """
        Cancel an order
        
        Args:
            coin: Trading symbol
            oid: Order ID
            
        Returns:
            Cancellation response
        """
        endpoint = "/exchange"
        data = {
            "action": {
                "type": "cancel",
                "cancels": [{"coin": coin, "oid": oid}]
            },
            "nonce"(time.time() * 1000),
            "signature": {
                "r": "",
                "s": "",
                "v": 0
            }
        }
        
        # Add signature for authenticated request
        signature = self._generate_signature(data)
        data["signature"] = signature
        
        return self._make_request(endpoint, "POST", data, auth=True)
    
    # ===== Market Data Endpoints =====
    
    def get_candles(self, coin, interval, start_time, 
                   end_time):
        """
        Get candle data
        
        Args:
            coin: Trading symbol
            interval: Candle interval (e.g., "1m", "5m", "1h", "1d")
            start_time: Start timestamp in milliseconds
            end_time: End timestamp in milliseconds
            
        Returns:
            List of candle data
        """
        endpoint = "/info"
        data = {
            "type": "candleSnapshot",
            "req": {
                "coin": coin,
                "interval"erval,
                "startTime": start_time,
                "endTime": end_time
            }
        }
        return self._make_request(endpoint, "POST", data)
    
    def get_funding_history(self, coin, start_time, 
                           end_time):
        """
        Get funding rate history
        
        Args:
            coin: Trading symbol
            start_time: Start timestamp in milliseconds
            end_time: End timestamp in milliseconds
            
        Returns:
            List of funding rate data
        """
        endpoint = "/info"
        data = {
            "type": "fundingHistory",
            "req": {
                "coin": coin,
                "startTime": start_time,
                "endTime": end_time
            }
        }
        return self._make_request(endpoint, "POST", data)
    
    # ===== Utility Methods =====
    
    def health_check(self):
        """
        Check API connectivity
        
        Returns:
            True if API is accessible, False otherwise
        """
        try:
            info = self.get_exchange_info()
            return "universe" in info and "meta" in info
        except Exception as e:
            self.logger.error("Health check failed: {e}")
            return False
    
    def get_price(self, symbol):
        """
        Get current price for a symbol
        
        Args:
            symbol: Trading symbol
            
        Returns:
            Current price or 0 if not found
        """
        try:
            mids = self.get_all_mids()
            if symbol in mids:
                return float(mids[symbol])
        except Exception as e:
            self.logger.error("Error getting price for {symbol}: {e}")
        
        return 0.0
    
    def get_balance(self, asset = "USDC"):
        """
        Get account balance
        
        Args:
            asset: Asset symbol (default: "USDC")
            
        Returns:
            Balance amount
        """
        try:
            user_state = self.get_user_state()
            
            if asset == "USDC":
                # Get withdrawable USDC
                return float(user_state.get("withdrawable", 0))
            else:
                # Get specific asset balance
                asset_positions = user_state.get("assetPositions", [])
                for position in asset_positions:
                    if position.get("position", {}).get("coin") == asset:
                        return float(position.get("position", {}).get("szi", 0))
        
        except Exception as e:
            self.logger.error("Error getting balance for {asset}: {e}")
        
        return 0.0

# ===== Simplified Client Interface =====

class HyperliquidClient:
    """Simplified Hyperliquid client for strategy templates"""
    
    def __init__(self, api_key, account_address, testnet = False):
        """
        Initialize simplified client
        
        Args:
            api_key: Hyperliquid API key
            account_address: Hyperliquid account address
            testnet: Whether to use testnet
        """
        self.api = HyperliquidAPI(api_key, account_address, testnet)
        self.logger = logging.getLogger(__name__)
    
    def place_limit_order(self, symbol, is_buy, size, 
                         price, reduce_only = False):
        """
        Place a limit order
        
        Args:
            symbol: Trading symbol
            is_buy: True for buy, False for sell
            size: Order size
            price: Limit price
            reduce_only: Whether order is reduce-only
            
        Returns:
            Order result
        """
        order = {
            "coin": symbol,
            "is_buy": is_buy,
            "sz"(size),
            "limit_px"(price),
            "order_type": {"limit": {"ti": "Gtc"}},
            "reduce_only": reduce_only
        }
        
        self.logger.info("Placing limit order: {symbol} {'BUY' if is_buy else 'SELL'} {size} @ {price}")
        return self.api.place_order(order)
    
    def place_market_order(self, symbol, is_buy, size,
                          reduce_only = False):
        """
        Place a market order
        
        Args:
            symbol: Trading symbol
            is_buy: True for buy, False for sell
            size: Order size
            reduce_only: Whether order is reduce-only
            
        Returns:
            Order result
        """
        order = {
            "coin": symbol,
            "is_buy": is_buy,
            "sz"(size),
            "order_type": {"market": {}},
            "reduce_only": reduce_only
        }
        
        self.logger.info("Placing market order: {symbol} {'BUY' if is_buy else 'SELL'} {size}")
        return self.api.place_order(order)
    
    def place_order(self, symbol, is_buy, size,
                   order_type = "market", price[float] = None,
                   reduce_only = False):
        """
        Generic order placement
        
        Args:
            symbol: Trading symbol
            is_buy: True for buy, False for sell
            size: Order size
            order_type: "market" or "limit"
            price: Price (required for limit orders)
            reduce_only: Whether order is reduce-only
            
        Returns:
            Order result
        """
        if order_type == "market":
            return self.place_market_order(symbol, is_buy, size, reduce_only)
        elif order_type == "limit":
            if price is None:
                return {"error": "Price required for limit orders"}
            return self.place_limit_order(symbol, is_buy, size, price, reduce_only)
        else:
            return {"error": "Unsupported order type: {order_type}"}
    
    def get_price(self, symbol):
        """Get current price"""
        return self.api.get_price(symbol)
    
    def get_balance(self, asset = "USDC"):
        """Get account balance"""
        return self.api.get_balance(asset)
    
    def get_open_orders(self, symbol[str] = None):
        """Get open orders"""
        orders = self.api.get_open_orders()
        if symbol:
            return [order for order in orders if order.get("coin") == symbol]
        return orders
    
    def cancel_order(self, order_id):
        """Cancel an order"""
        # Need to get symbol first
        orders = self.get_open_orders()
        for order in orders:
            if order.get("oid") == order_id:
                symbol = order.get("coin")
                result = self.api.cancel_order(symbol, order_id)
                return "error" not in result
        
        self.logger.error("Order {order_id} not found")
        return False
    
    def cancel_all_orders(self, symbol[str] = None):
        """Cancel all orders"""
        orders = self.get_open_orders(symbol)
        
        for order in orders:
            order_id = order.get("oid")
            if order_id:
                self.cancel_order(order_id)
        
        self.logger.info("Cancelled {len(orders)} orders")
        return True
    
    def health_check(self):
        """Check API connectivity"""
        return self.api.health_check()