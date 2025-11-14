import streamlit as st
from web3 import Web3
import json

st.title("🎲 Ethereum Lottery DApp (Full Version)")


# ----------------------------------------------------
# Helper: Checksum validator
# ----------------------------------------------------
def to_checksum(addr):
    try:
        return Web3.to_checksum_address(addr)
    except:
        return None


# ----------------------------------------------------
# Contract details (your real values)
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
            {
                "internalType": "uint256",
                "name": "",
                "type": "uint256"
            }
        ],
        "name": "participants",
        "outputs": [
            {
                "internalType": "address payable",
                "name": "",
                "type": "address"
            }
        ],
        "stateMutability": "view",
        "type": "function"
    },
    {
        "inputs": [],
        "name": "random",
        "outputs": [
            {
                "internalType": "uint256",
                "name": "",
                "type": "uint256"
            }
        ],
        "stateMutability": "view",
        "type": "function"
    }
]
""")


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
# Section: Contract Info
# ----------------------------------------------------
st.subheader("📊 Contract Info")

# balance
try:
    balance = contract.functions.getBalance().call({"from": manager_address})
    st.write(f"**Contract Balance:** {web3.from_wei(balance, 'ether')} ETH")
except Exception:
    st.write("**Contract Balance:** (hidden – only manager can view)")

# random number call
try:
    randomness = contract.functions.random().call()
    st.write(f"**Random Value:** {randomness}")
except:
    st.write("**Random Value:** Cannot fetch.")

# participants count
participants_count = 0
try:
    # we brute-force until revert
    while True:
        contract.functions.participants(participants_count).call()
        participants_count += 1
except:
    pass

st.write(f"**Participants Count:** {participants_count}")


# ----------------------------------------------------
# ENTER LOTTERY
# ----------------------------------------------------
st.header("🎟 Enter Lottery (0.00001 ETH)")

user_addr_raw = st.text_input("Your wallet address")
user_pk = st.text_input("Private Key", type="password")

if st.button("Enter Lottery"):
    user_addr = to_checksum(user_addr_raw)

    if not user_addr or not user_pk:
        st.error("Please enter a valid address & private key.")
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

            st.success(f"🎉 Entered!\n\n**TX Hash:** `{tx_hash.hex()}`")

        except Exception as e:
            st.error(f"Error: {e}")


# ----------------------------------------------------
# MANAGER SELECT WINNER
# ----------------------------------------------------
st.header("🏆 Manager: Select Winner")

if st.button("Prepare Winner Transaction"):
    try:
        winner_txn = contract.functions.selectWinner().build_transaction({
            "from": manager_address,
            "nonce": web3.eth.get_transaction_count(manager_address),
            "gas": 300000,
            "gasPrice": web3.eth.gas_price
        })

        st.session_state["winner_txn"] = winner_txn
        st.success("Transaction prepared. Now enter manager key to send.")

    except Exception as e:
        st.error(f"Error preparing: {e}")

if "winner_txn" in st.session_state:
    mgr_pk = st.text_input("Manager Private Key (to send)", type="password")

    if st.button("Send Winner Transaction"):
        try:
            signed = web3.eth.account.sign_transaction(
                st.session_state["winner_txn"], mgr_pk
            )
            tx_hash = web3.eth.send_raw_transaction(signed.raw_transaction)

            st.success(f"🏆 Winner Selected!\n\n**TX Hash:** `{tx_hash.hex()}`")

            del st.session_state["winner_txn"]

        except Exception as e:
            st.error(f"Error sending: {e}")
