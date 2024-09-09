# fortuna-stream
Stay informed of the latest events happening on-chain for $TUNA. 

Developed by [@QCPOLstakepool](https://x.com/QCPOLstakepool)

# Tracked Events
- [x] Block minted
- [x] Conversion V1 to V2
- [x] Difficulty change
- [ ] DEX trade

# TODO
- Move to Docker
- Expose a public API
- Discord bot

## Installation

### Dependencies
```
mkdir $HOME/fortuna-stream
mkdir $HOME/git

sudo apt-get update -y && sudo apt-get install -y automake build-essential pkg-config libffi-dev libgmp-dev libssl-dev libtinfo-dev libsystemd-dev zlib1g-dev make g++ tmux git jq wget libncursesw5 libtool autoconf musl-tools libleveldb-dev
```

#### Rust
```
curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh    (Press [Enter])
source $HOME/.cargo/env
rustup install stable
rustup default stable
rustup update
```

#### Oura (2.0.0-alpha.4)
```
cd $HOME/git
git clone https://github.com/txpipe/oura.git
cd oura
git checkout e24b023d27a90083a466a21dfca39a23401e2407
cargo install --path . --force
```

Run Oura with configuration: [oura.toml](oura.toml) 

#### Python (3.12)
```
sudo apt update
sudo apt install software-properties-common
sudo add-apt-repository ppa:deadsnakes/ppa                     (Press [ENTER])
sudo apt update
sudo apt install python3.12 python3.12-dev python3.12-venv     (Press [Y])

python3.12 -m venv .venv
source .venv/bin/activate
```

### Cron
Create cron: `0,30 * * * * curl -X POST http://127.0.0.1:30513/api/events/queued/send`

### Install
`pip install -e .`

# Run
`python -m fortuna_stream_sinks 127.0.0.1 30513`