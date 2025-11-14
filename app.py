import streamlit as st
from web3 import Web3
import json
import requests
import re

st.title("🎲 Ethereum Lottery DApp – Corrected Final Version")

# -----------------------
# Helpers
# -----------------------
def to_checksum(addr):
    try:
        return Web3.to_checksum_address(addr)
    except:
        return None

def is_valid_tx_hash(tx: str) -> bool:
    if not isinstance(tx, str):
        return False
    tx = tx.strip().lower()
    # accept 64-hex or 0x + 64-hex
    return bool(re.fullmatch(r"(0x)?[a-f0-9]{64}", tx))

def check_tx_on_sepolia(tx: str):
    # Ensure 0x prefix for etherscan API
    tx_clean = tx.strip()
    if not tx_clean.startswith("0x"):
        tx_clean = "0x" + tx_clean
    url = (
        "https://api-sepolia.etherscan.io/api"
        "?module=proxy&action=eth_getTransactionByHash"
        f"&txhash={tx_clean}&apikey=YourApiKeyToken"
    )
    r = requests.get(url, timeout=10)
    return r.json()

# -----------------------
# Config — fill these with your values
# -----------------------
CONTRACT_ADDRESS = "0x8de587E7cae5003A087Cb51ea47408183E347388"
MANAGER_ADDRESS = "0xf0c8bf5139cD5A7A0058A3854D769ac4CEC14eDa"
INFURA_URL = "https://sepolia.infura.io/v3/89de1fce9a0d4110bd998cbb27a9de87"

contract_address = to_checksum(CONTRACT_ADDRESS)
manager_address = to_checksum(MANAGER_ADDRESS)

# -----------------------
# ABI as Python list (no triple quotes)
# -----------------------
contract_abi = [
    {"inputs": [], "name": "selectWinner", "outputs": [], "stateMutability": "nonpayable", "type": "function"},
    {"stateMutability": "payable", "type": "receive"},
    {"inputs": [], "name": "getBalance", "outputs": [{"internalType": "uint256", "name": "", "type": "uint256"}], "stateMutability": "view", "type": "function"},
    {"inputs": [], "name": "manager", "outputs": [{"internalType": "address", "name": "", "type": "address"}], "stateMutability": "view", "type": "function"},
    {"inputs": [{"internalType": "uint256", "name": "", "type": "uint256"}], "name": "participants", "outputs": [{"internalType": "address payable", "name": "", "type": "address"}], "stateMutability": "view", "type": "function"},
    {"inputs": [], "name": "random", "outputs": [{"internalType": "uint256", "name": "", "type": "uint256"}], "stateMutability": "view", "type": "function"}
]

# -----------------------
# Connect to Sepolia
# -----------------------
web3 = Web3(Web3.HTTPProvider(INFURA_URL))
if not web3.is_connected():
    st.error("❌ Could not connect to Sepolia RPC. Check INFURA_URL / Project ID.")
    st.stop()
else:
    st.success("✅ Connected to Sepolia")

contract = web3.eth.contract(address=contract_address, abi=contract_abi)

# -----------------------
# Contract Info
# -----------------------
st.subheader("📊 Contract Info")

# Manager (on-chain)
try:
    onchain_manager = contract.functions.manager().call()
    st.write(f"**On-chain manager:** `{onchain_manager}`")
except Exception as e:
    st.write("Could not read manager on-chain.")
    onchain_manager = None

# Balance (manager-only getter - call with from)
try:
    balance = contract.functions.getBalance().call({"from": manager_address})
    st.write(f"**Contract Balance:** {web3.from_wei(balance, 'ether')} ETH")
except Exception:
    st.write("**Contract Balance:** (hidden — manager only or call failed)")

# Random preview
try:
    rand_val = contract.functions.random().call()
    st.write(f"**random() preview:** {rand_val}")
except Exception:
    st.write("**random() preview:** (not available)")

# Participants count (safe brute-force until revert)
count = 0
try:
    while True:
        contract.functions.participants(count).call()
        count += 1
except Exception:
    pass
st.write(f"**Participants count:** {count}")

st.markdown("---")

# -----------------------
# Enter Lottery
# -----------------------
st.header("🎟 Enter Lottery (0.00001 ETH)")

user_addr_raw = st.text_input("Your wallet address (checksum or raw)")
user_pk = st.text_input("Your private key (needed to send tx)", type="password")

if st.button("Enter Lottery"):
    user_addr = to_checksum(user_addr_raw)
    if not user_addr:
        st.error("Enter a valid Ethereum address.")
    elif not user_pk or not isinstance(user_pk, str) or len(user_pk.strip()) == 0:
        st.error("Enter your private key (for demo only).")
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
            st.success(f"🎉 Entered! TX Hash: `{tx_hash.hex()}`")
        except Exception as e:
            st.error(f"Error sending entry transaction: {e}")

st.markdown("---")

# -----------------------
# Manager: Select Winner (two-step)
# -----------------------
st.header("🏆 Manager: Select Winner")

if st.button("Prepare Winner Transaction"):
    try:
        tx = contract.functions.selectWinner().build_transaction({
            "from": manager_address,
            "nonce": web3.eth.get_transaction_count(manager_address),
            "gas": 400000,
            "gasPrice": web3.eth.gas_price,
            "chainId": 11155111
        })
        st.session_state["winner_tx"] = tx
        st.success("Prepared winner transaction and saved in session.")
    except Exception as e:
        st.error(f"Error preparing transaction: {e}")

if "winner_tx" in st.session_state:
    mgr_pk = st.text_input("Manager private key (to sign & send)", type="password")
    if st.button("Sign & Send Winner Transaction"):
        if not mgr_pk:
            st.error("Enter manager private key to sign & send.")
        else:
            try:
                signed = web3.eth.account.sign_transaction(st.session_state["winner_tx"], mgr_pk)
                tx_hash = web3.eth.send_raw_transaction(signed.raw_transaction)
                st.success(f"🏆 Winner tx broadcasted! TX Hash: `{tx_hash.hex()}`")
                del st.session_state["winner_tx"]
            except Exception as e:
                st.error(f"Error signing/sending winner tx: {e}")

st.markdown("---")

# -----------------------
# Transaction verification (Sepolia)
# -----------------------
st.subheader("🔍 Verify a transaction on Sepolia")

tx_input = st.text_input("Paste TX hash (with or without 0x)")

if st.button("Check TX"):
    tx_raw = (tx_input or "").strip()
    if not is_valid_tx_hash(tx_raw):
        st.error("❌ Invalid TX hash format. Paste 0x + 64 hex or just 64 hex characters.")
    else:
        try:
            result = check_tx_on_sepolia(tx_raw)
            if result and result.get("result"):
                st.success("✅ Found transaction on Sepolia")
                st.json(result["result"])
            else:
                st.error("❌ No transaction found on Sepolia (not mined or wrong hash).")
        except Exception as e:
            st.error(f"Error contacting Etherscan API: {e}")

st.caption("Tip: If you deployed and interacted on Sepolia, verify transactions on https://sepolia.etherscan.io")



