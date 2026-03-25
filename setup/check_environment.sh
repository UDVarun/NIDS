#!/bin/bash
# ============================================================
# NIDS Sentinel — Environment Checker & Auto-Installer
# Run this script as: bash setup/check_environment.sh
# ============================================================

set -e
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
NC='\033[0m'

echo -e "${CYAN}╔══════════════════════════════════════╗${NC}"
echo -e "${CYAN}║  NIDS Sentinel Environment Setup    ║${NC}"
echo -e "${CYAN}╚══════════════════════════════════════╝${NC}"
echo ""

install_apt() {
    local pkg=$1
    if dpkg -l "$pkg" &>/dev/null; then
        echo -e "${GREEN}✓ $pkg already installed${NC}"
    else
        echo -e "${YELLOW}⬇ Installing $pkg...${NC}"
        sudo apt-get install -y "$pkg"
        echo -e "${GREEN}✓ $pkg installed${NC}"
    fi
}

echo -e "${CYAN}[1/8] Updating package list...${NC}"
sudo apt-get update -qq

echo -e "${CYAN}[2/8] Checking Python 3.11...${NC}"
if python3 --version 2>&1 | grep -q "3.1[1-9]"; then
    echo -e "${GREEN}✓ Python 3.11+ found: $(python3 --version)${NC}"
else
    echo -e "${YELLOW}⬇ Installing Python 3.11...${NC}"
    sudo apt-get install -y python3.11 python3.11-pip python3.11-venv
fi

echo -e "${CYAN}[3/8] Installing system libraries for Scapy...${NC}"
install_apt "libpcap-dev"
install_apt "tcpdump"
install_apt "net-tools"
install_apt "nmap"
install_apt "hping3"

echo -e "${CYAN}[4/8] Setting up Python virtual environment...${NC}"
sudo apt-get install -y python3-pip python3-venv
python3 -m venv venv
source venv/bin/activate
pip install --upgrade pip setuptools wheel

echo -e "${CYAN}[5/8] Installing Python packages...${NC}"
pip install flask==3.0.0
pip install flask-cors==4.0.0
pip install scapy==2.5.0
pip install scikit-learn==1.4.0
pip install pandas==2.1.4
pip install numpy==1.26.3
pip install joblib==1.3.2
pip install gunicorn==21.2.0
pip install python-dotenv==1.0.0
echo -e "${GREEN}✓ All Python packages installed${NC}"

echo -e "${CYAN}[6/8] Checking Node.js...${NC}"
if node --version 2>&1 | grep -q "v2[0-9]"; then
    echo -e "${GREEN}✓ Node.js found: $(node --version)${NC}"
else
    echo -e "${YELLOW}⬇ Installing Node.js 20...${NC}"
    curl -fsSL https://deb.nodesource.com/setup_20.x | sudo -E bash -
    sudo apt-get install -y nodejs
fi

echo -e "${CYAN}[7/8] Checking Docker...${NC}"
if command -v docker &>/dev/null; then
    echo -e "${GREEN}✓ Docker found: $(docker --version)${NC}"
else
    echo -e "${YELLOW}⬇ Installing Docker...${NC}"
    curl -fsSL https://get.docker.com -o get-docker.sh
    sudo sh get-docker.sh
    sudo usermod -aG docker $USER
    echo -e "${GREEN}✓ Docker installed.${NC}"
fi

echo -e "${CYAN}[8/8] Checking Docker Compose...${NC}"
if command -v docker-compose &>/dev/null; then
    echo -e "${GREEN}✓ Docker Compose found: $(docker-compose --version)${NC}"
else
    echo -e "${YELLOW}⬇ Installing Docker Compose...${NC}"
    sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" \
        -o /usr/local/bin/docker-compose
    sudo chmod +x /usr/local/bin/docker-compose
    echo -e "${GREEN}✓ Docker Compose installed${NC}"
fi

echo ""
echo -e "${GREEN}╔══════════════════════════════════════╗${NC}"
echo -e "${GREEN}║  Environment setup complete! ✓       ║${NC}"
echo -e "${GREEN}╚══════════════════════════════════════╝${NC}"
echo ""
echo "Next step: Run 'bash setup/download_dataset.sh' then 'python backend/model/train.py'"
