# app.py - updated Streamlit frontend (copy entire file)
import streamlit as st
from web3 import Web3
import json
import time
from urllib.parse import quote_plus

st.set_page_config(page_title="Lottery DApp", layout="wide")
st.title("🎲 Lottery DApp — Admin & Demo (Sepolia)")

# -------------------------
# CONFIG - update these
# -------------------------
INFURA_PROJECT_ID = "89de1fce9a0d4110bd998cbb27a9de87"  # replace if you use different RPC
INFURA_URL = f"https://sepolia.infura.io/v3/89de1fce9a0d4110bd998cbb27a9de87"

# after deploying updated contract, paste its address here:
contract_address_raw = "0xcbA756ADbDD00cD47F56E2691711567FE0725d97"  # REPLACE with new deployed address if you redeploy

# -------------------------
# ABI matching the Solidity above
# -------------------------
contract_abi = json.loads("""
[
    {"inputs":[],"name":"selectWinner","outputs":[],"stateMutability":"nonpayable","type":"function"},
    {"inputs":[],"stateMutability":"nonpayable","type":"constructor"},
    {"stateMutability":"payable","type":"receive"},
    {"inputs":[],"name":"getBalance","outputs":[{"internalType":"uint256","name":"","type":"uint256"}],"stateMutability":"view","type":"function"},
    {"inputs":[],"name":"getContractBalance","outputs":[{"internalType":"uint256","name":"","type":"uint256"}],"stateMutability":"view","type":"function"},
    {"inputs":[],"name":"getPlayersCount","outputs":[{"internalType":"uint256","name":"","type":"uint256"}],"stateMutability":"view","type":"function"},
    {"inputs":[],"name":"getPlayers","outputs":[{"internalType":"address payable[]","name":"","type":"address[]"}],"stateMutability":"view","type":"function"},
    {"inputs":[],"name":"manager","outputs":[{"internalType":"address","name":"","type":"address"}],"stateMutability":"view","type":"function"},
    {"inputs":[{"internalType":"uint256","name":"","type":"uint256"}],"name":"participants","outputs":[{"internalType":"address payable","name":"","type":"address"}],"stateMutability":"view","type":"function"},
    {"inputs":[],"name":"random","outputs":[{"internalType":"uint256","name":"","type":"uint256"}],"stateMutability":"view","type":"function"},
    {"anonymous":false,"inputs":[{"indexed":true,"internalType":"address","name":"winner","type":"address"},{"indexed":false,"internalType":"uint256","name":"amount","type":"uint256"}],"name":"WinnerSelected","type":"event"},
    {"anonymous":false,"inputs":[{"indexed":true,"internalType":"address","name":"participant","type":"address"}],"name":"Entered","type":"event"}
]
""")

# -------------------------
# helpers
# -------------------------
def to_checksum(addr):
    try:
        return Web3.to_checksum_address(addr)
    except:
        return None

def etherscan_tx_url(tx_hash):
    return f"https://sepolia.etherscan.io/tx/{tx_hash}"

def etherscan_addr_url(addr):
    return f"https://sepolia.etherscan.io/address/{addr}"

# -------------------------
# connect web3
# -------------------------
w3 = Web3(Web3.HTTPProvider(INFURA_URL))
if not w3.is_connected():
    st.error("❌ Could not connect to Sepolia RPC. Check INFURA_URL / project id.")
    st.stop()

contract_address = to_checksum(contract_address_raw)
contract = w3.eth.contract(address=contract_address, abi=contract_abi)

# -------------------------
# Layout: left = controls, right = status
# -------------------------
col1, col2 = st.columns([1, 2])

with col1:
    st.subheader("Manager actions")

    # show on-chain manager
    onchain_manager = contract.functions.manager().call()
    st.write("On-chain manager:", onchain_manager)
    st.write("Your manager address (paste):")
    manager_addr_input = st.text_input("Manager address to use (checksum or raw)")
    manager_addr = to_checksum(manager_addr_input) if manager_addr_input else None

    st.markdown("---")
    st.write("Prepare winner transaction (two-step to avoid Streamlit re-render issues)")

    if st.button("Prepare Winner Tx"):
        try:
            nonce = w3.eth.get_transaction_count(onchain_manager)
            tx = contract.functions.selectWinner().build_transaction({
                "from": onchain_manager,
                "nonce": nonce,
                "gas": 400000,
                "gasPrice": w3.eth.gas_price,
                "chainId": 11155111
            })
            st.session_state["winner_tx"] = tx
            st.success("Winner transaction prepared and saved in session. Now sign & send it (below).")
        except Exception as e:
            st.error("Error preparing tx: " + str(e))

    st.markdown("**Sign & send prepared tx**")
    manager_private_key = st.text_input("Manager private key (paste here for demo only)", type="password")

    if "winner_tx" in st.session_state:
        if st.button("Sign & Send Winner Tx"):
            if not manager_private_key:
                st.error("Enter manager private key to sign")
            else:
                try:
                    # sign & send
                    signed = w3.eth.account.sign_transaction(st.session_state["winner_tx"], manager_private_key)
                    tx_hash = w3.eth.send_raw_transaction(signed.rawTransaction)
                    st.success("Winner tx broadcasted: " + tx_hash.hex())
                    st.write("View on Etherscan:", etherscan_tx_url(tx_hash.hex()))
                    # clear session
                    del st.session_state["winner_tx"]
                except Exception as e:
                    st.error("Error sending tx: " + str(e))

    st.markdown("---")
    st.subheader("Enter Lottery (demo)")

    st.write("To enter, send exactly 0.00001 ETH to the contract address from any Sepolia account.")
    st.code(contract_address)
    st.write("You can click this link to open Sepolia Etherscan transfer UI:")
    st.markdown(f"[Send TX on Etherscan]({etherscan_addr_url(contract_address)})")

with col2:
    st.subheader("Contract status & info (live)")

    # balance
    try:
        balance = w3.from_wei(contract.functions.getContractBalance().call(), "ether")
        st.metric("Contract balance (ETH)", f"{balance}")
    except Exception as e:
        st.error("Could not read contract balance: " + str(e))

    # participants count
    try:
        count = contract.functions.getPlayersCount().call()
        st.write("Participants count:", count)
    except Exception as e:
        st.error("Could not read participants count: " + str(e))

    # participant list (if small)
    if count > 0:
        if count <= 50:  # avoid huge output
            players = contract.functions.getPlayers().call()
            st.write("Participants:")
            for i, p in enumerate(players):
                st.write(f"{i+1}. {p} — [Etherscan]({etherscan_addr_url(p)})")
        else:
            st.write("Too many participants to show (>", 50, ")")

    # random preview
    try:
        r = contract.functions.random().call()
        st.write("random() preview (not secure):", r)
    except Exception as e:
        st.error("Error calling random(): " + str(e))

    # recent events: WinnerSelected (last 10)
    st.markdown("---")
    st.subheader("Recent events (WinnerSelected)")

    try:
        latest = w3.eth.get_block('latest').number
        from_block = latest - 2500 if latest >= 2500 else 0
        events = contract.events.WinnerSelected().createFilter(fromBlock=from_block).get_all_entries()
        if events:
            for ev in reversed(events[-10:]):
                winner = ev.args.winner
                amount = w3.from_wei(ev.args.amount, "ether")
                txhash = ev.transactionHash.hex()
                st.write(f"Winner: {winner} — {amount} ETH — [tx]({etherscan_tx_url(txhash)})")
        else:
            st.write("No WinnerSelected events found in recent range.")
    except Exception as e:
        st.info("Could not read events: " + str(e))

st.markdown("---")
st.caption("Note: random() is insecure for production — use Chainlink VRF for provable randomness.")
