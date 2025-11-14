import streamlit as st
from web3 import Web3
import json

st.title("🎲 Ethereum Lottery DApp (Sepolia)")


# -------------------------------------------
#  CHECKSUM HELPER
# -------------------------------------------
def to_checksum(addr):
    try:
        return Web3.to_checksum_address(addr)
    except:
        st.error("❌ Invalid Ethereum address format")
        return None


# -------------------------------------------
#  CONTRACT CONFIG
# -------------------------------------------
INFURA_URL = "https://sepolia.infura.io/v3/89de1fce9a0d4110bd998cbb27a9de87"

contract_address_raw = "0x11d9966187C67E26838997C82a8Ca412De9f1f7e"
manager_address_raw = "0xf0c8bf5139cd5a7a0058a3854d769ac4cec14eda"

contract_address = to_checksum(contract_address_raw)
manager_address = to_checksum(manager_address_raw)

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
            {
                "internalType": "uint256",
                "name": "",
                "type": "uint256"
            }
        ],
        "stateMutability": "view",
        "type": "function"
    },
    {
        "inputs": [],
        "name": "manager",
        "outputs": [
            {
                "internalType": "address",
                "name": "",
                "type": "address"
            }
        ],
        "stateMutability": "view",
        "type": "function"
    },
    {
        "inputs": [
            { "internalType": "uint256", "name": "", "type": "uint256" }
        ],
        "name": "participants",
        "outputs": [
            { "internalType": "address payable", "name": "", "type": "address" }
        ],
        "stateMutability": "view",
        "type": "function"
    },
    {
        "inputs": [],
        "name": "random",
        "outputs": [
            { "internalType": "uint256", "name": "", "type": "uint256" }
        ],
        "stateMutability": "view",
        "type": "function"
    }
]
""")


# -------------------------------------------
#  CONNECT TO SEPOLIA
# -------------------------------------------
web3 = Web3(Web3.HTTPProvider(INFURA_URL))

if web3.is_connected():
    st.success("✅ Connected to Sepolia")
else:
    st.error("❌ Cannot connect to Sepolia")


contract = web3.eth.contract(address=contract_address, abi=contract_abi)


# -------------------------------------------
#  DISPLAY MANAGER + BALANCE + RANDOM
# -------------------------------------------
st.header("ℹ️ Contract Info")

# Manager
st.write(f"**Manager:** `{manager_address}`")

# Balance (must be called using manager address)
try:
    balance = contract.functions.getBalance().call({"from": manager_address})
    st.write(f"**Contract Balance:** {web3.from_wei(balance, 'ether')} ETH")
except:
    st.write("**Contract Balance:** 🔒 Manager-Only")

# Random
try:
    random_val = contract.functions.random().call()
    st.write(f"**Random Number:** {random_val}")
except:
    st.write("**Random Number:** ⚠️ Could not compute")


# -------------------------------------------
#  ENTER LOTTERY
# -------------------------------------------
st.header("🎟 Enter Lottery (Send 0.00001 ETH)")

user_addr_raw = st.text_input("Your Wallet Address")
user_pk = st.text_input("Your Private Key", type="password")

if st.button("Enter Lottery"):
    user_addr = to_checksum(user_addr_raw)

    if not user_addr or not user_pk:
        st.warning("Enter both wallet address and private key.")
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
            st.success(f"🎉 Entry sent!\nTX: `{tx_hash.hex()}`")
        except Exception as e:
            st.error(f"Error: {e}")


# -------------------------------------------
#  MANAGER SELECT WINNER
# -------------------------------------------
st.header("🏆 Manager: Select Winner")

# Prepare Transaction
if st.button("Prepare Winner Transaction"):
    try:
        winner_tx = contract.functions.selectWinner().build_transaction({
            "from": manager_address,
            "nonce": web3.eth.get_transaction_count(manager_address),
            "gas": 300000,
            "gasPrice": web3.eth.gas_price
        })
        st.session_state["winner_tx"] = winner_tx
        st.success("Winner transaction prepared. Enter private key to send.")
    except Exception as e:
        st.error(f"Error: {e}")

# Sign + Send
if "winner_tx" in st.session_state:
    manager_pk = st.text_input("Manager Private Key", type="password")

    if st.button("Send Winner Transaction"):
        try:
            signed = web3.eth.account.sign_transaction(
                st.session_state["winner_tx"], manager_pk
            )
            tx_hash = web3.eth.send_raw_transaction(signed.raw_transaction)
            st.success(f"🏆 Winner Selected!\nTX: `{tx_hash.hex()}`")

            del st.session_state["winner_tx"]

        except Exception as e:
            st.error(f"Sending Error: {e}")
