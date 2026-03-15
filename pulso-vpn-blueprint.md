# ESCUDO VPN — Complete Technical Blueprint
## Pulso ISP-Integrated VPN Platform for Brazil

**Version:** 1.0 — March 2026
**Author:** Pulso / SVR LAB
**Classification:** Internal — Strategic Technical Plan

---

## 1. EXECUTIVE SUMMARY

Escudo VPN is a Rust-native, open-source VPN platform built for Brazil's 20,000+ small ISPs. Phase 1 launches as a direct-to-consumer product. Phase 2 adds white-label ISP integration. Phase 3 integrates into the Pulso telecom intelligence platform. The entire system runs on 2 servers at launch ($30/month) scaling to 65 servers at 1M users ($15K/month) with 90%+ gross margins.

---

## 2. ARCHITECTURE OVERVIEW

```
┌─────────────────────────────────────────────────────────┐
│                    USER DEVICES                          │
│  Android App │ iOS App │ Windows │ macOS │ Linux CLI     │
└──────┬──────────┬──────────┬──────────┬──────────┬──────┘
       │          │          │          │          │
       │     WireGuard Encrypted Tunnel (UDP/51820)│
       │     or QUIC Tunnel (UDP/443) [Phase 2]    │
       │          │          │          │          │
┌──────▼──────────▼──────────▼──────────▼──────────▼──────┐
│              VPN GATEWAY SERVERS                         │
│                                                          │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐     │
│  │  São Paulo   │  │  Fortaleza  │  │   Miami      │     │
│  │  Primary GW  │  │  NE Brazil  │  │  US Exit     │     │
│  │  boringtun   │  │  boringtun  │  │  boringtun   │     │
│  │  hickory-dns │  │  hickory-dns│  │  hickory-dns │     │
│  │  WG kernel   │  │  WG kernel  │  │  WG kernel   │     │
│  └──────┬───────┘  └──────┬──────┘  └──────┬───────┘     │
│         │                 │                 │             │
│         └────────┬────────┘                 │             │
│                  │                          │             │
│         IX.br Peering                  Transit           │
│         (near-zero cost)              ($6-24/mo)         │
└──────────────────┬──────────────────────────┬────────────┘
                   │                          │
┌──────────────────▼──────────────────────────▼────────────┐
│              MANAGEMENT PLANE                             │
│                                                           │
│  ┌──────────────────────────────────────────────────┐    │
│  │  API Server (Rust / Axum)                         │    │
│  │                                                    │    │
│  │  • User registration & auth (JWT + argon2)        │    │
│  │  • WireGuard key pair generation                   │    │
│  │  • Config distribution (QR code / file)            │    │
│  │  • Server health monitoring                        │    │
│  │  • Bandwidth accounting per user                   │    │
│  │  • ISP tenant management [Phase 2]                │    │
│  │  • Payment webhook handler (PIX)                   │    │
│  └──────────────────────┬────────────────────────────┘    │
│                         │                                 │
│  ┌──────────────────────▼────────────────────────────┐    │
│  │  PostgreSQL                                        │    │
│  │                                                    │    │
│  │  • users (id, email, password_hash, plan, status) │    │
│  │  • peers (id, user_id, public_key, server_id)     │    │
│  │  • servers (id, location, endpoint, public_key)   │    │
│  │  • sessions (user_id, connected_at, bytes_rx/tx)  │    │
│  │  • tenants (isp_id, name, branding) [Phase 2]     │    │
│  │  • payments (user_id, amount, pix_txid, status)   │    │
│  └───────────────────────────────────────────────────┘    │
└───────────────────────────────────────────────────────────┘
```

---

## 3. RUST CRATE DEPENDENCIES

### 3.1 Core Cargo.toml (Gateway Server)

```toml
[package]
name = "escudo-gateway"
version = "0.1.0"
edition = "2021"

[dependencies]
# WireGuard tunnel
boringtun = "0.6"

# Async runtime
tokio = { version = "1", features = ["full"] }

# Networking
socket2 = "0.5"

# DNS resolver with ad-blocking
hickory-server = "0.25"
hickory-resolver = "0.25"
hickory-proto = "0.25"

# Crypto
ring = "0.17"
x25519-dalek = "2"
rand = "0.8"

# Logging
tracing = "0.1"
tracing-subscriber = "0.3"

# Config
serde = { version = "1", features = ["derive"] }
serde_json = "1"
toml = "0.8"

# Metrics
prometheus = "0.13"
```

### 3.2 Core Cargo.toml (API Server)

```toml
[package]
name = "escudo-api"
version = "0.1.0"
edition = "2021"

[dependencies]
# Web framework
axum = { version = "0.7", features = ["macros"] }
tower = "0.4"
tower-http = { version = "0.5", features = ["cors", "trace"] }

# Async runtime
tokio = { version = "1", features = ["full"] }

# Database
sqlx = { version = "0.8", features = ["runtime-tokio", "postgres", "uuid", "chrono"] }

# Auth
jsonwebtoken = "9"
argon2 = "0.5"

# WireGuard key generation
boringtun = "0.6"
x25519-dalek = "2"
rand = "0.8"
base64 = "0.22"

# QR code generation for mobile config
qrcode = "0.14"
image = "0.25"

# Serialization
serde = { version = "1", features = ["derive"] }
serde_json = "1"

# TLS
rustls = "0.23"

# Config
dotenvy = "0.15"

# Logging
tracing = "0.1"
tracing-subscriber = "0.3"

# UUID
uuid = { version = "1", features = ["v4", "serde"] }

# Time
chrono = { version = "0.4", features = ["serde"] }
```

### 3.3 Phase 2 Additional Crates

```toml
# QUIC tunneling (obfuscation-resistant)
quinn = "0.11"

# Obfuscation protocols
# shoes crate or custom impl of VLESS+REALITY

# Post-quantum crypto
aws-lc-rs = "1"  # ML-KEM (Kyber) for PQC key exchange

# DNS-over-HTTPS/TLS
hickory-dns = { version = "0.25", features = ["dns-over-https", "dns-over-tls"] }

# TLS with PQC
rustls = { version = "0.23", features = ["aws-lc-rs"] }
# rustls already supports X25519MLKEM768 hybrid PQC
```

---

## 4. PROJECT STRUCTURE

```
escudo-vpn/
├── Cargo.toml                    # Workspace root
├── LICENSE                       # Apache-2.0
├── README.md
│
├── crates/
│   ├── escudo-gateway/           # VPN gateway server
│   │   ├── Cargo.toml
│   │   └── src/
│   │       ├── main.rs           # Entry point, config loading
│   │       ├── tunnel.rs         # WireGuard tunnel management via boringtun
│   │       ├── nat.rs            # IP forwarding + iptables NAT rules
│   │       ├── dns.rs            # Hickory DNS resolver + ad-blocking
│   │       ├── blocklist.rs      # Hagezi blocklist loader (hash set)
│   │       ├── metrics.rs        # Prometheus metrics endpoint
│   │       ├── health.rs         # Health check endpoint
│   │       └── config.rs         # Gateway configuration
│   │
│   ├── escudo-api/               # Management API server
│   │   ├── Cargo.toml
│   │   └── src/
│   │       ├── main.rs           # Axum server entry point
│   │       ├── routes/
│   │       │   ├── mod.rs
│   │       │   ├── auth.rs       # POST /register, POST /login, POST /refresh
│   │       │   ├── vpn.rs        # POST /connect, GET /servers, GET /config
│   │       │   ├── account.rs    # GET /me, PUT /me, DELETE /me
│   │       │   ├── payment.rs    # POST /webhook/pix
│   │       │   └── admin.rs      # Server management, user management
│   │       ├── models/
│   │       │   ├── mod.rs
│   │       │   ├── user.rs
│   │       │   ├── peer.rs
│   │       │   ├── server.rs
│   │       │   └── payment.rs
│   │       ├── db.rs             # PostgreSQL connection pool (sqlx)
│   │       ├── auth.rs           # JWT creation/validation, password hashing
│   │       ├── wireguard.rs      # Key generation, config file builder
│   │       ├── qr.rs             # QR code generator for mobile config
│   │       └── config.rs         # API configuration
│   │
│   ├── escudo-common/            # Shared types and utilities
│   │   ├── Cargo.toml
│   │   └── src/
│   │       ├── lib.rs
│   │       ├── types.rs          # Shared types (UserId, ServerId, etc.)
│   │       ├── crypto.rs         # Key generation, encoding utilities
│   │       └── error.rs          # Error types
│   │
│   └── escudo-cli/               # Admin CLI tool
│       ├── Cargo.toml
│       └── src/
│           └── main.rs           # Server provisioning, user management
│
├── migrations/                   # SQLx migrations
│   ├── 001_create_users.sql
│   ├── 002_create_servers.sql
│   ├── 003_create_peers.sql
│   ├── 004_create_payments.sql
│   └── 005_create_sessions.sql
│
├── deploy/                       # Deployment scripts
│   ├── setup-gateway.sh          # Gateway server setup (Ubuntu + WG)
│   ├── setup-api.sh              # API server setup
│   ├── wireguard-server.conf     # Template WG server config
│   ├── blocklist-update.sh       # Cron script to update Hagezi lists
│   └── systemd/
│       ├── escudo-gateway.service
│       └── escudo-api.service
│
├── apps/                         # Mobile and desktop apps
│   ├── android/                  # Kotlin + WireGuard Android library
│   │   └── ...
│   ├── ios/                      # Swift + NetworkExtension framework
│   │   └── ...
│   └── desktop/                  # Tauri (Rust backend + web frontend)
│       └── ...
│
├── web/                          # Landing page + user portal
│   ├── index.html                # Marketing landing page
│   ├── portal/                   # User dashboard (account, config download)
│   └── admin/                    # ISP admin dashboard [Phase 2]
│
└── docs/
    ├── ARCHITECTURE.md
    ├── API.md                    # REST API documentation
    ├── DEPLOYMENT.md
    └── ISP-INTEGRATION.md        # White-label integration guide [Phase 2]
```

---

## 5. DATABASE SCHEMA

```sql
-- 001_create_users.sql
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

CREATE TABLE users (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    email VARCHAR(255) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    plan VARCHAR(20) DEFAULT 'basic' NOT NULL,    -- basic, premium
    status VARCHAR(20) DEFAULT 'active' NOT NULL,  -- active, suspended, cancelled
    tenant_id UUID,                                 -- NULL = direct customer, ISP UUID = white-label
    max_devices INTEGER DEFAULT 5,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    expires_at TIMESTAMPTZ                          -- subscription expiry
);

-- 002_create_servers.sql
CREATE TABLE servers (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name VARCHAR(100) NOT NULL,                     -- 'sp-01', 'miami-01'
    location VARCHAR(100) NOT NULL,                 -- 'São Paulo', 'Miami'
    country_code CHAR(2) NOT NULL,                  -- 'BR', 'US'
    endpoint VARCHAR(255) NOT NULL,                 -- '203.0.113.1:51820'
    public_key VARCHAR(44) NOT NULL,                -- WireGuard server public key (base64)
    private_key_encrypted BYTEA NOT NULL,           -- encrypted at rest
    dns_ip VARCHAR(45) DEFAULT '10.0.0.1',          -- internal DNS resolver IP
    subnet VARCHAR(18) DEFAULT '10.0.0.0/16',       -- VPN subnet
    max_peers INTEGER DEFAULT 10000,
    current_peers INTEGER DEFAULT 0,
    status VARCHAR(20) DEFAULT 'active',
    load_percent SMALLINT DEFAULT 0,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- 003_create_peers.sql
CREATE TABLE peers (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    server_id UUID NOT NULL REFERENCES servers(id),
    device_name VARCHAR(100),                       -- 'Carlos iPhone', 'Laptop'
    public_key VARCHAR(44) NOT NULL,                -- client WireGuard public key
    preshared_key_encrypted BYTEA,                  -- PSK for PQC [Phase 2]
    allowed_ip VARCHAR(18) NOT NULL,                -- assigned IP in VPN subnet
    last_handshake TIMESTAMPTZ,
    bytes_received BIGINT DEFAULT 0,
    bytes_transmitted BIGINT DEFAULT 0,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    is_active BOOLEAN DEFAULT true,
    UNIQUE(server_id, allowed_ip),
    UNIQUE(server_id, public_key)
);

-- 004_create_payments.sql
CREATE TABLE payments (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES users(id),
    amount_cents INTEGER NOT NULL,                  -- amount in centavos
    currency CHAR(3) DEFAULT 'BRL',
    method VARCHAR(20) NOT NULL,                    -- 'pix', 'card'
    pix_txid VARCHAR(255),                          -- PIX transaction ID
    status VARCHAR(20) DEFAULT 'pending',           -- pending, confirmed, failed, refunded
    period_start DATE,
    period_end DATE,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    confirmed_at TIMESTAMPTZ
);

-- 005_create_tenants.sql (Phase 2 — ISP white-label)
CREATE TABLE tenants (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    isp_name VARCHAR(255) NOT NULL,
    cnpj VARCHAR(14) UNIQUE,                        -- ISP's CNPJ
    contact_email VARCHAR(255) NOT NULL,
    branding_json JSONB DEFAULT '{}',               -- logo URL, colors, app name
    api_key_hash VARCHAR(255) NOT NULL,             -- for ISP API access
    billing_model VARCHAR(20) DEFAULT 'per_user',   -- per_user, flat_rate
    price_per_user_cents INTEGER DEFAULT 150,       -- R$1.50 default
    status VARCHAR(20) DEFAULT 'active',
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Indexes
CREATE INDEX idx_peers_user_id ON peers(user_id);
CREATE INDEX idx_peers_server_id ON peers(server_id);
CREATE INDEX idx_payments_user_id ON payments(user_id);
CREATE INDEX idx_users_tenant_id ON users(tenant_id);
CREATE INDEX idx_users_email ON users(email);
```

---

## 6. API ENDPOINTS

### 6.1 Authentication

```
POST   /api/v1/auth/register      # Create account (email + password)
POST   /api/v1/auth/login          # Login → JWT token
POST   /api/v1/auth/refresh        # Refresh JWT token
POST   /api/v1/auth/logout         # Invalidate token
```

### 6.2 VPN Operations

```
GET    /api/v1/servers              # List available servers + load
POST   /api/v1/connect              # Generate WG config for a server
       Body: { "server_id": "uuid", "device_name": "My Phone" }
       Returns: { "config": "...", "qr_code_base64": "..." }

GET    /api/v1/peers                # List user's connected devices
DELETE /api/v1/peers/:id            # Remove a device/peer
GET    /api/v1/config/:peer_id      # Re-download config for a peer
GET    /api/v1/config/:peer_id/qr   # Get QR code image for peer config
```

### 6.3 Account

```
GET    /api/v1/account              # Get account info + usage stats
PUT    /api/v1/account              # Update email/password
DELETE /api/v1/account              # Delete account + all peers
GET    /api/v1/account/usage        # Bandwidth usage history
```

### 6.4 Payments

```
POST   /api/v1/payments/pix         # Generate PIX payment QR code
POST   /api/v1/webhooks/pix         # PIX payment confirmation (from provider)
GET    /api/v1/payments              # Payment history
```

### 6.5 ISP Admin (Phase 2)

```
POST   /api/v1/admin/tenants        # Register new ISP tenant
GET    /api/v1/admin/tenants/:id     # Get ISP details
POST   /api/v1/tenant/users         # ISP provisions a user (RADIUS integration)
DELETE /api/v1/tenant/users/:id      # ISP deprovisions a user
GET    /api/v1/tenant/stats          # ISP dashboard data (user count, bandwidth)
GET    /api/v1/tenant/billing        # ISP billing summary
```

---

## 7. GATEWAY SERVER — CORE FLOW

### 7.1 How a Connection Works

```
1. User opens app, taps "Connect to Brazil"

2. App calls POST /api/v1/connect { server_id: "sp-01" }

3. API server:
   a. Generates X25519 key pair for client
   b. Assigns next available IP from server's subnet (e.g., 10.0.1.42/32)
   c. Stores peer record in PostgreSQL
   d. Calls gateway server's internal API to add peer:
      POST http://gateway-internal:9090/peers
      { public_key: "...", allowed_ip: "10.0.1.42/32", preshared_key: "..." }
   e. Gateway runs: wg set wg0 peer <pubkey> allowed-ips 10.0.1.42/32
   f. Returns WireGuard config to app:
      [Interface]
      PrivateKey = <client_private_key>
      Address = 10.0.1.42/32
      DNS = 10.0.0.1

      [Peer]
      PublicKey = <server_public_key>
      Endpoint = <server_public_ip>:51820
      AllowedIPs = 0.0.0.0/0
      PersistentKeepalive = 25

4. App activates WireGuard tunnel with this config

5. All user traffic now flows:
   Phone → encrypted → Server:51820 → decrypt → NAT → internet
   Internet → Server → encrypt → Phone

6. DNS queries go to 10.0.0.1 (Hickory DNS on gateway)
   → Checked against Hagezi blocklist
   → Blocked domains return NXDOMAIN (ads/malware disappear)
   → Clean domains resolved via DoH to upstream (Cloudflare/Quad9)
```

### 7.2 Gateway Server Setup Script

```bash
#!/bin/bash
# deploy/setup-gateway.sh
# Run on a fresh Ubuntu 24.04 VPS

set -e

echo "=== Escudo VPN Gateway Setup ==="

# 1. Update system
apt update && apt upgrade -y

# 2. Install WireGuard (kernel module, already in Ubuntu 24.04)
apt install -y wireguard wireguard-tools

# 3. Enable IP forwarding
cat >> /etc/sysctl.conf << EOF
net.ipv4.ip_forward = 1
net.ipv6.conf.all.forwarding = 1
EOF
sysctl -p

# 4. Generate server keys
SERVER_PRIVATE=$(wg genkey)
SERVER_PUBLIC=$(echo "$SERVER_PRIVATE" | wg pubkey)

echo "Server Private Key: $SERVER_PRIVATE"
echo "Server Public Key:  $SERVER_PUBLIC"
echo ""
echo "SAVE THESE KEYS! The private key cannot be recovered."

# 5. Create WireGuard config
INTERFACE=$(ip -4 route show default | awk '{print $5}')

cat > /etc/wireguard/wg0.conf << EOF
[Interface]
Address = 10.0.0.1/16
ListenPort = 51820
PrivateKey = $SERVER_PRIVATE
PostUp = iptables -t nat -A POSTROUTING -o $INTERFACE -j MASQUERADE
PostUp = iptables -A FORWARD -i wg0 -j ACCEPT
PostUp = iptables -A FORWARD -o wg0 -m state --state RELATED,ESTABLISHED -j ACCEPT
PostDown = iptables -t nat -D POSTROUTING -o $INTERFACE -j MASQUERADE
PostDown = iptables -D FORWARD -i wg0 -j ACCEPT
PostDown = iptables -D FORWARD -o wg0 -m state --state RELATED,ESTABLISHED -j ACCEPT

# Peers will be added dynamically via API
EOF

# 6. Set permissions
chmod 600 /etc/wireguard/wg0.conf

# 7. Enable and start WireGuard
systemctl enable wg-quick@wg0
systemctl start wg-quick@wg0

# 8. Open firewall
ufw allow 51820/udp    # WireGuard
ufw allow 22/tcp        # SSH (restrict to your IP in production)
ufw --force enable

# 9. Verify
echo ""
echo "=== WireGuard Status ==="
wg show

echo ""
echo "=== Setup Complete ==="
echo "Server Public Key: $SERVER_PUBLIC"
echo "Server Endpoint:   $(curl -s ifconfig.me):51820"
echo ""
echo "To add a client peer:"
echo "  wg set wg0 peer <CLIENT_PUBLIC_KEY> allowed-ips 10.0.0.2/32"
```

### 7.3 Quick Test — Add Your Phone as a Client

```bash
#!/bin/bash
# Run this ON THE SERVER after setup-gateway.sh

# Generate client keys
CLIENT_PRIVATE=$(wg genkey)
CLIENT_PUBLIC=$(echo "$CLIENT_PRIVATE" | wg pubkey)
SERVER_PUBLIC=$(wg show wg0 public-key)
SERVER_IP=$(curl -s ifconfig.me)

# Add peer to server
wg set wg0 peer "$CLIENT_PUBLIC" allowed-ips 10.0.0.2/32

# Generate client config
CLIENT_CONFIG="[Interface]
PrivateKey = $CLIENT_PRIVATE
Address = 10.0.0.2/32
DNS = 1.1.1.1

[Peer]
PublicKey = $SERVER_PUBLIC
Endpoint = $SERVER_IP:51820
AllowedIPs = 0.0.0.0/0
PersistentKeepalive = 25"

echo "$CLIENT_CONFIG"
echo ""
echo "=== QR Code (scan with WireGuard app) ==="

# Install qrencode for QR
apt install -y qrencode
echo "$CLIENT_CONFIG" | qrencode -t ansiutf8
```

---

## 8. PHASED ROADMAP

### Phase 1: MVP — Direct to Consumer (Months 1-6)

**Goal:** 100 paying customers, working Android app, 2-3 servers

| Month | Deliverable | Team |
|-------|-------------|------|
| 1 | Gateway server (WireGuard + DNS ad-blocking), REST API (register, login, connect, config generation), PostgreSQL schema | 1 Rust dev |
| 2 | Android app (Kotlin + WireGuard library): login, server list, connect/disconnect, auto-config via API | 1 Mobile dev |
| 3 | Landing page, PIX payment integration (Efí Bank or OpenPix), Play Store listing, beta test with 20 friends | Carlos |
| 4 | Bug fixes, performance tuning, add Lisbon exit node, iOS app start | All 3 |
| 5 | iOS app complete, ad-blocking via Hickory DNS + Hagezi blocklist, basic analytics dashboard | All 3 |
| 6 | Public launch push, 100+ paying customers target, iterate on feedback | All 3 |

**Cost:** R$50-75K/month × 6 = R$300-450K (~$55-82K USD)
**Infrastructure:** $15-30/month (2-3 VPS)
**Revenue at 100 users × R$8:** R$800/month

### Phase 2: White-Label ISP Module (Months 7-12)

**Goal:** 10 ISPs onboarded, 1,000+ VPN users, multi-tenant architecture

| Month | Deliverable |
|-------|-------------|
| 7-8 | Multi-tenant API (tenant registration, per-ISP user provisioning, branded config generation) |
| 9 | ISP admin dashboard (user count, bandwidth stats, billing summary) |
| 10 | RADIUS integration module (authenticate VPN users against ISP's existing RADIUS server) |
| 11 | Branded Android app builder (ISP logo, colors, app name via build pipeline) |
| 12 | First 10 ISP pilots, Abrint presence, Windows desktop app (Tauri) |

**Additional hires:** +1 frontend dev, +1 sales/BD for ISP relationships
**Cost:** R$120-180K/month × 6 = R$720K-1.08M
**Revenue at 1,000 users:** R$8K/month (direct) + ISP platform fees

### Phase 3: Pulso Integration + Advanced Features (Months 13-24)

| Quarter | Deliverable |
|---------|-------------|
| Q1 (M13-15) | Pulso module integration (one-click VPN enable for ISPs using Pulso), QUIC tunneling via quinn for DPI resistance |
| Q2 (M16-18) | Post-quantum crypto (ML-KEM via aws-lc-rs in WireGuard PSK), obfuscation protocols (VLESS+REALITY via shoes), macOS app |
| Q3 (M19-21) | Own ASN + IX.br peering in São Paulo, Fortaleza servers, dedicated IPs feature, RAM-only server architecture |
| Q4 (M22-24) | Security audit (independent firm), multi-hop, split tunneling, international expansion prep (Argentina, Indonesia) |

---

## 9. COST MODEL

### 9.1 Infrastructure Scaling

| Users | Servers | Specs | Monthly Cost |
|-------|---------|-------|-------------|
| 1-500 | 2 VPS | 1 vCPU / 2GB each (Vultr SP + Miami) | $30 |
| 500-2K | 3 VPS | Add Lisbon exit | $45 |
| 2K-5K | 4 VPS | Add SP backup for redundancy | $90 |
| 5K-10K | 5 VPS | Add Fortaleza for NE Brazil latency | $130 |
| 10K-50K | 8-12 | Upgrade SP to 8-core dedicated, add Brasília | $400-800 |
| 50K-100K | 15-20 | Bare metal SP × 2, VPS everywhere else | $1,500-2,500 |
| 100K-500K | 25-40 | Own ASN, IX.br peering, bare metal at 5 locations | $5K-10K |
| 500K-1M | 50-70 | Full IX.br presence, international exits × 5 | $10K-15K |

### 9.2 Revenue Model

**Direct-to-consumer:**
- R$8.90/month (basic — VPN + ad blocking)
- R$14.90/month (premium — VPN + ad blocking + dedicated IP + multi-hop)
- 7-day free trial, 30-day money-back guarantee
- Payment: PIX Automático (primary), credit card (secondary)

**ISP white-label (Phase 2+):**
- Platform fee: R$1.50/user/month (basic), R$2.50/user/month (premium)
- ISP retail: R$4.90-8.90/month to end customer
- ISP margin: R$3.40-6.40/user/month (pure profit for ISP)
- Setup fee: R$0 (to reduce friction)
- Minimum commitment: none (pay as you go)

### 9.3 Break-even Analysis

**Monthly fixed costs (team + overhead):**
- Phase 1: R$75K/month (3 people PJ + overhead)
- Phase 2: R$150K/month (6 people + overhead)
- Phase 3: R$250K/month (10 people + overhead)

**Break-even users (direct @ R$8.90):**
- Phase 1: 8,427 users (R$75K ÷ R$8.90)
- Phase 2: 16,854 users
- Phase 3: 28,090 users

**Break-even users (ISP channel @ R$1.50):**
- Phase 2: 100,000 users (R$150K ÷ R$1.50)
- Phase 3: 166,667 users

**Blended model (50% direct @ R$8.90, 50% ISP @ R$1.50 = R$5.20 avg):**
- Phase 2: 28,846 users
- Phase 3: 48,077 users

---

## 10. SECURITY ARCHITECTURE

### 10.1 Zero-Knowledge Design

- **No traffic logs.** Gateway servers forward packets without recording destinations, URLs, or content.
- **No DNS logs.** Hickory DNS resolves and blocks without logging queries.
- **Minimal account data.** Email, hashed password (argon2id), subscription status. No name, no CPF, no address.
- **No connection timestamps.** We do not record when users connect or disconnect.
- **Bandwidth accounting is aggregate only.** Total bytes per billing period, not per-session.
- **Server private keys encrypted at rest** using a key derived from a hardware-bound secret or HSM.

### 10.2 Encryption Stack

| Layer | Algorithm | Implementation |
|-------|-----------|----------------|
| Tunnel | ChaCha20-Poly1305 (WireGuard) | boringtun / kernel WG |
| Key Exchange | Curve25519 (ECDH) | x25519-dalek |
| Handshake | Noise IK pattern | snow crate |
| PQC (Phase 3) | ML-KEM-768 (Kyber) via PSK | aws-lc-rs |
| DNS | DoH / DoT to upstream | hickory-dns |
| API TLS | TLS 1.3 | rustls |
| Passwords | Argon2id | argon2 crate |
| Tokens | JWT (ES256) | jsonwebtoken crate |

### 10.3 Threat Model

| Threat | Mitigation |
|--------|------------|
| ISP snooping on user traffic | All traffic encrypted in WG tunnel |
| Court-ordered platform block | QUIC tunneling on port 443 (Phase 2), VLESS+REALITY obfuscation (Phase 3) |
| Server seizure | No logs to find, RAM-only architecture (Phase 3), encrypted private keys |
| MITM on API | TLS 1.3 via rustls, certificate pinning in apps |
| Quantum harvest-now-decrypt-later | PQC hybrid key exchange (Phase 3) |
| User credential breach | Argon2id hashing, JWT short-lived tokens, no PII beyond email |
| DNS leak | Forced DNS through tunnel (Hickory DNS on gateway), kill switch in app |
| IPv6 leak | IPv6 disabled on tunnel interface, kill switch blocks IPv6 outside tunnel |

---

## 11. LGPD COMPLIANCE CHECKLIST

| Requirement | Implementation |
|-------------|----------------|
| Legal basis for processing | Contractual necessity (Art. 7, II) — processing required to provide VPN service |
| Data minimization | Only collect email + payment info. No name, CPF, address, browsing data |
| Transparency | Clear privacy policy in Portuguese explaining what we collect and why |
| Right of access (Art. 18, II) | GET /api/v1/account returns all stored data |
| Right of deletion (Art. 18, VI) | DELETE /api/v1/account removes all data within 15 days |
| Data portability (Art. 18, V) | GET /api/v1/account/export returns JSON of all user data |
| DPO appointment | Required — can be lightweight for small-scale processing |
| Breach notification | ANPD within "reasonable time" + affected users |
| International transfers | Exit node traffic crosses borders — covered by standard contractual clauses |

---

## 12. IMMEDIATE NEXT STEPS (This Week)

1. **Today:** Set up WireGuard on the Vultr SP server, connect your phone, verify it works
2. **This week:** Write the basic Axum API (register, login, generate WG config, return QR code)
3. **Next week:** Deploy API on a second VPS or on the same box temporarily, test full flow
4. **Week 3-4:** Start Android app (Kotlin + WireGuard library), basic UI
5. **Month 2:** Add Hickory DNS with Hagezi blocklist on gateway, PIX payment integration
6. **Month 3:** Play Store beta, invite 20 testers

---

## 13. KEY OPEN-SOURCE REPOS TO STUDY

| Repo | URL | Relevance |
|------|-----|-----------|
| boringtun | github.com/cloudflare/boringtun | WireGuard implementation we wrap |
| defguard | github.com/DefGuard/defguard | Rust VPN platform reference architecture |
| firezone | github.com/firezone/firezone | VPN management platform (Elixir, but great UX reference) |
| mullvad-vpn-app | github.com/mullvad/mullvadvpn-app | Best open-source VPN app (Rust + mobile), kill switch reference |
| hickory-dns | github.com/hickory-dns/hickory-dns | DNS resolver with DoH/DoT/DoQ |
| shoes | github.com/cfal/shoes | Multi-protocol proxy (VLESS, Shadowsocks, Hysteria2, REALITY) |
| quinn | github.com/quinn-rs/quinn | QUIC implementation for obfuscated tunneling |
| innernet | github.com/tonarino/innernet | WireGuard network manager in Rust |
| wg-dynamic | Various | Dynamic WireGuard peer management reference |
| hagezi/dns-blocklists | github.com/hagezi/dns-blocklists | Ad/malware/tracker blocklists |
| WireGuard Android | github.com/WireGuard/wireguard-android | Official Android app (reference for our branded app) |

---

*This document is the complete technical blueprint for building, launching, and scaling the Escudo VPN platform. Every component uses production-ready open-source Rust crates. No cryptographic primitives need to be written from scratch. The first working prototype can be achieved in an afternoon. The first paying customer can be achieved in 8 weeks.*
