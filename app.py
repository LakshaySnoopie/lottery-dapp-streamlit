import streamlit as st
from web3 import Web3
import json
import requests

st.title("🎲 Ethereum Lottery DApp – Final Fixed Version")

# ----------------------------------------------------
# Helper: checksum
# ----------------------------------------------------
def to_checksum(addr):
    try:
        return Web3.to_checksum_address(addr)
    except:
        return None

# ----------------------------------------------------
# Contract details
# ----------------------------------------------------
CONTRACT_ADDRESS = "0x11d9966187C67E26838997C82a8Ca412De9f1f7e"
MANAGER_ADDRESS = "0xf0c8bf5139cD5A7A0058A3854D769ac4CEC14eDa"

contract_address = to_checksum(CONTRACT_ADDRESS)
manager_address = to_checksum(MANAGER_ADDRESS)

contract_abi = json.loads("""
[
    {
        "inputs": [],
        "name": "selectWinner",
        "outputs": [],
        "stateMutability": "nonpayable",
        "type": "function"
    },
    {
        "stateMutability": "payable",
        "type": "receive"
    },
    {
        "inputs": [],
        "name": "getBalance",
        "outputs": [
            { "internalType": "uint256", "name": "", "type": "uint256" }
        ],
        "stateMutability": "view",
        "type": "function"
    },
    {
        "inputs": [],
        "name": "manager",
        "outputs": [
            { "internalType": "address", "name": "", "type": "address" }
        ],
        "stateMutability": "view",
        "type": "function"
    },
