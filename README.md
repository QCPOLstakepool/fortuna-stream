# fortuna-stream
Twitter streams for the Cardano token TUNA

## Dependencies
```
mkdir $HOME/fortuna-stream
mkdir $HOME/git
```

### apt
```
sudo apt-get update -y && sudo apt-get install -y automake build-essential pkg-config libffi-dev libgmp-dev libssl-dev libtinfo-dev libsystemd-dev zlib1g-dev make g++ tmux git jq wget libncursesw5 libtool autoconf musl-tools
```

### Rust
```
curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh    (Press [Enter])
source $HOME/.cargo/env
rustup install stable
rustup default stable
rustup update
```

## Installation
### Oura (2.0.0-alpha.2)
```
cd $HOME/git
git clone https://github.com/txpipe/oura.git
cd oura
cargo install --path . --force
```

Run Oura with configuration: [oura.toml](oura.toml) 

### Python (3.12)
TODO

#### Create venv
TODO

#### Install
`pip install -e .`

#### Run
`python -m fortuna-stream-sinks 127.0.0.1 31065`