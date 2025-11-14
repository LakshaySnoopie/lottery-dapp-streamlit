import streamlit as st
from web3 import Web3
import json
import requests

st.title("🎲 Ethereum Lottery DApp – SAFE VERSION (No Triple Quotes)")


def to_checksum(addr):
    try:
        return Web3.to_checksum_address(addr)
    except:
        return None


CONTRACT_ADDRESS = "0x11d9966187C67E26838997C82a8Ca412De9f1f7e"
MANAGER_ADDRESS = "0xf0c8bf5139cD5A7A0058A3854D769ac4CEC14eDa"

contract_address = to_checksum(CONTRACT_ADDRESS)
manager_address = to_checksum(MANAGER_ADDRESS)

# ----------------------------------------------------
# FIXED ABI — NO TRIPLE QUOTES ANYWHERE
# ----------------------------------------------------
contract_abi = [
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
    }
]

# ----------------------------------------------------
# Connect to Sepolia
# ----------------------------------------------------
INFURA_URL = "https://sepolia.infura.io/v3/89de1fce9a0d4110bd998cbb27a9de87"
web3 = Web3(Web3.HTTPProvider(INFURA_URL))

if not web3.is_connected():
    st.error("❌ Could not connect to Sepolia")
    st.stop()
else:
    st.success("✅ Connected to Sepolia")

contract = web3.eth.contract(address=contract_address, abi=contract_abi)

# ----------------------------------------------------
# Contract Info
# ----------------------------------------------------
st.subheader("📊 Contract Info")

try:
    bal = contract.functions.getBalance().call({"from": manager_address})
    st.write(f"**Contract Balance:** {web3.from_wei(bal, 'ether')} ETH")
except:
    st.write("**Contract Balance:** (private to manager)")

# participant count
count = 0
try:
    while True:
        contract.functions.participants(count).call()
        count += 1
except:
    pass

st.write(f"**Participants:** {count}")

# ----------------------------------------------------
# Enter lottery
# ----------------------------------------------------
st.header("🎟 Enter Lottery (0.00001 ETH)")

user_addr_raw = st.text_input("Your wallet address")
user_pk = st.text_input("Private Key", type="password")

if st.button("Enter Lottery"):
    user_addr = to_checksum(user_addr_raw)

    if not user_addr or not user_pk:
        st.error("Enter valid address and private key")
    else:
        try:
            txn = {
                "from": user_addr,
                "to": contract_address,
                "value": web3.to_wei(0.00001, "ether"),
                "nonce": web3.eth.get_transaction_count(user_addr),
                "gas": 300000,
                "gasPrice": web3.eth.gas_price
            }

            signed = web3.eth.account.sign_transaction(txn, user_pk)
            tx_hash = web3.eth.send_raw_transaction(signed.raw_transaction)

            st.success(f"🎉 Entered!\n**TX Hash:** {tx_hash.hex()}")

        except Exception as e:
            st.error(f"Error: {e}")

# ----------------------------------------------------
# Winner selection
# ----------------------------------------------------
st.header("🏆 Manager: Select Winner")

if st.button("Prepare Winner Transaction"):
    try:
        tx = contract.functions.selectWinner().build_transaction({
            "from": manager_address,
            "nonce": web3.eth.get_transaction_count(manager_address),
            "gas": 300000,
            "gasPrice": web3.eth.gas_price
        })

        st.session_state["winner_tx"] = tx
        st.success("Winner transaction prepared.")

    except Exception as e:
        st.error(f"Error: {e}")

if "winner_tx" in st.session_state:
    mgr_pk = st.text_input("Manager Private Key", type="password")

    if st.button("Send Winner Transaction"):
        try:
            signed = web3.eth.account.sign_transaction(st.session_state["winner_tx"], mgr_pk)
            tx_hash = web3.eth.send_raw_transaction(signed.raw_transaction)

            st.success(f"🏆 Winner Selected!\n**TX Hash:** {tx_hash.hex()}")

            del st.session_state["winner_tx"]

        except Exception as e:
            st.error(f"Error: {e}")

# ----------------------------------------------------
# TX Checker
# ----------------------------------------------------
st.subheader("🔍 Verify Transaction")

tx_input = st.text_input("Enter transaction hash")

def check_tx(tx):
    url = (
        "https://api-sepolia.etherscan.io/api"
        "?module=proxy&action=eth_getTransactionByHash"
        f"&txhash={tx}&apikey=YourApiKeyToken"
    )
    return requests.get(url).json()

if st.button("Check TX"):
    if len(tx_input) != 66:
        st.error("Invalid TX hash format")
    else:
        result = check_tx(tx_input)
        if result.get("result"):
            st.success("Valid Sepolia Transaction")
            st.json(result["result"])
        else:
            st.error("No transaction found")
