import streamlit as st
from web3 import Web3
import json

st.title("🎲 Ethereum Lottery DApp")

def to_checksum(address):
    try:
        return Web3.to_checksum_address(address)
    except:
        st.error("❌ Invalid Ethereum address format")
        return None

-
contract_address_raw = "0x11d9966187C67E26838997C82a8Ca412De9f1f7e"
manager_address_raw  = "0xf0c8bf5139cd5a7a0058a3854d769ac4cec14eda"

contract_address = to_checksum(contract_address_raw)
manager_address  = to_checksum(manager_address_raw)

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
        "inputs": [],
        "stateMutability": "nonpayable",
        "type": "constructor"
    },
    {
        "stateMutability": "payable",
        "type": "receive"
    },
    {
        "inputs": [],
        "name": "getBalance",
        "outputs": [
            {"internalType": "uint256", "name": "", "type": "uint256"}
        ],
        "stateMutability": "view",
        "type": "function"
    },
    {
        "inputs": [],
        "name": "manager",
        "outputs": [
            {"internalType": "address", "name": "", "type": "address"}
        ],
        "stateMutability": "view",
        "type": "function"
    },
    {
        "inputs": [
            {"internalType": "uint256", "name": "", "type": "uint256"}
        ],
        "name": "participants",
        "outputs": [
            {"internalType": "address payable", "name": "", "type": "address"}
        ],
        "stateMutability": "view",
        "type": "function"
    },
    {
        "inputs": [],
        "name": "random",
        "outputs": [
            {"internalType": "uint256", "name": "", "type": "uint256"}
        ],
        "stateMutability": "view",
        "type": "function"
    }
]
""")

infura_url = "https://sepolia.infura.io/v3/89de1fce9a0d4110bd998cbb27a9de87"
web3 = Web3(Web3.HTTPProvider(infura_url))

if not web3.is_connected():
    st.error("❌ Failed to connect to Sepolia")
else:
    st.success("✅ Connected to Sepolia")

contract = web3.eth.contract(address=contract_address, abi=contract_abi)

st.header("🎟 Enter Lottery (Send 0.00001 ETH)")

user_address_raw = st.text_input("Your wallet address")
private_key = st.text_input("Private Key", type="password")

if st.button("Enter Lottery"):
    user_address = to_checksum(user_address_raw)

    if user_address and private_key:
        try:
            txn = {
                "from": user_address,
                "to": contract_address,
                "value": web3.to_wei(0.00001, "ether"),
                "nonce": web3.eth.get_transaction_count(user_address),
                "gas": 300000,
                "gasPrice": web3.eth.gas_price
            }

            signed_txn = web3.eth.account.sign_transaction(txn, private_key)
            tx_hash = web3.eth.send_raw_transaction(signed_txn.raw_transaction)

            st.success(f"🎉 Entered Lottery! TX Hash:\n{tx_hash.hex()}")

        except Exception as e:
            st.error(f"Error: {e}")
    else:
        st.warning("Enter your wallet address AND private key.")


st.header("🏆 Manager: Select Winner")

if st.button("Select Winner"):
    try:
        txn = contract.functions.selectWinner().build_transaction({
            "from": manager_address,
            "nonce": web3.eth.get_transaction_count(manager_address),
            "gas": 300000,
            "gasPrice": web3.eth.gas_price
        })

        st.warning("⚠️ Enter manager PRIVATE KEY to confirm")

        manager_pk = st.text_input("Manager Private Key", type="password")

        if manager_pk:
            signed_txn = web3.eth.account.sign_transaction(txn, manager_pk)
            tx_hash = web3.eth.send_raw_transaction(signed_txn.raw_transaction)

            st.success(f"🏆 Winner Selected! TX Hash:\n{tx_hash.hex()}")

    except Exception as e:
        st.error(f"Error: {e}")
