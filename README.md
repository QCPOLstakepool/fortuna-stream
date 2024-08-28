# fortuna-stream
Twitter streams for the Cardano token TUNA

## Dependencies
```
mkdir $HOME/fortuna-stream
mkdir $HOME/git
```

### apt
```
sudo apt-get update -y && sudo apt-get install -y automake build-essential pkg-config libffi-dev libgmp-dev libssl-dev libtinfo-dev libsystemd-dev zlib1g-dev make g++ tmux git jq wget libncursesw5 libtool autoconf musl-tools libleveldb-dev
```

### Rust
```
curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh    (Press [Enter])
source $HOME/.cargo/env
rustup install stable
rustup default stable
rustup update
```

### bech32
```
cd $HOME/git
git clone https://github.com/IntersectMBO/bech32.git
cd bech32
git fetch --all --recurse-submodules --tags
cabal update
cabal configure -O0 -w ghc-8.10.7
rm -rf $HOME/git/bech32/dist-newstyle/build/x86_64-linux/ghc-8.10.7
cabal build bech32
sudo cp $(find $HOME/git/bech32/dist-newstyle/build -type f -name "bech32") /usr/local/bin/bech32
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
```
sudo apt update
sudo apt install software-properties-common
sudo add-apt-repository ppa:deadsnakes/ppa                     (Press [ENTER])
sudo apt update
sudo apt install python3.12 python3.12-dev python3.12-venv     (Press [Y])
```

#### Create venv
```
python3.12 -m venv .venv
source .venv/bin/activate
```

#### Install
`pip install -e .`

#### Run
`python -m fortuna_stream_sinks 127.0.0.1 30513`