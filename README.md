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
#### Build from source
```
cd $HOME/git
git clone https://github.com/txpipe/oura.git
cd oura
cargo install --path . --force
```

#### Configuration
Create file `$HOME/fortuna-stream/daemon.toml` with the following content (change `/home/relay/`):
```
[source]
type = "N2C"
socket_path = "/home/relay/cardano-my-node/db/socket"
min_depth = 6

[intersect]
type = "Point"
value = [133071753, "ca0e667649146da8141fcb92a92ddccb5db841c6cf9a2b534f0bf00e92dc3185"]

[cursor]
type = "File"
path = "/home/relay/fortuna-stream/oura.cursor"

[[filters]]
type = "SplitBlock"

[[filters]]
type = "ParseCbor"

[[filters]]
type = "Select"
skip_uncertain = true
predicate = "asset1up3fehe0dwpuj4awgcuvl0348vnsexd573fjgq"

[sink]
type = "Stdout"
```
