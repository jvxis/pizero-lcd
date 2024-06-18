import requests

# Fetch the JSON data from the URL
url = "http://jvx-minibolt.local/status/json"
response = requests.get(url)
data = response.json()

# Store the values of the keys into variables
bitcoind = data.get("bitcoind")
chain = data.get("chain")
channel_balance = data.get("channel_balance")
current_block_height = data.get("current_block_height")
economyFee = data.get("economyFee")
fastestFee = data.get("fastestFee")
halfHourFee = data.get("halfHourFee")
hourFee = data.get("hourFee")
message = data.get("message")
minimumFee = data.get("minimumFee")
node_alias = data.get("node_alias")
node_lnd_version = data.get("node_lnd_version")
num_active_channels = data.get("num_active_channels")
num_inactive_channels = data.get("num_inactive_channels")
num_pending_channels = data.get("num_pending_channels")
number_of_channels = data.get("number_of_channels")
number_of_peers = data.get("number_of_peers")
number_of_peers_lnd = data.get("number_of_peers_lnd")
pruned = data.get("pruned")
pub_key = data.get("pub_key")
subversion = data.get("subversion")
sync_percentage = data.get("sync_percentage")
synced_to_chain = data.get("synced_to_chain")
synced_to_graph = data.get("synced_to_graph")
total_balance = data.get("total_balance")
version = data.get("version")
wallet_balance = data.get("wallet_balance")

# Print the variables to verify the values
print("bitcoind:", bitcoind)
print("chain:", chain)
print("channel_balance:", channel_balance)
print("current_block_height:", current_block_height)
print("economyFee:", economyFee)
print("fastestFee:", fastestFee)
print("halfHourFee:", halfHourFee)
print("hourFee:", hourFee)
print("message:", message)
print("minimumFee:", minimumFee)
print("node_alias:", node_alias)
print("node_lnd_version:", node_lnd_version)
print("num_active_channels:", num_active_channels)
print("num_inactive_channels:", num_inactive_channels)
print("num_pending_channels:", num_pending_channels)
print("number_of_channels:", number_of_channels)
print("number_of_peers:", number_of_peers)
print("number_of_peers_lnd:", number_of_peers_lnd)
print("pruned:", pruned)
print("pub_key:", pub_key)
print("subversion:", subversion)
print("sync_percentage:", sync_percentage)
print("synced_to_chain:", synced_to_chain)
print("synced_to_graph:", synced_to_graph)
print("total_balance:", total_balance)
print("version:", version)
print("wallet_balance:", wallet_balance)
