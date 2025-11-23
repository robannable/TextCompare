#!/bin/bash

# Colors for better readability
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

VENV_DIR="venv"

show_menu() {
    clear
    echo "======================================"
    echo "       TextCompare Setup Script       "
    echo "======================================"
    echo ""
    echo "1. Setup Virtual Environment"
    echo "2. Install Requirements"
    echo "3. Run Application"
    echo "4. Setup and Run (Complete Setup)"
    echo "5. Check Python Installation"
    echo "6. Check Ollama Installation"
    echo "7. Exit"
    echo ""
    echo -n "Enter your choice (1-7): "
}

setup_venv() {
    echo ""
    echo -e "${YELLOW}Setting up virtual environment...${NC}"

    if [ -d "$VENV_DIR" ]; then
        echo -e "${GREEN}Virtual environment already exists.${NC}"
    else
        python3 -m venv $VENV_DIR
        if [ $? -eq 0 ]; then
            echo -e "${GREEN}Virtual environment created successfully!${NC}"
        else
            echo -e "${RED}Error creating virtual environment.${NC}"
            read -p "Press Enter to continue..."
            return 1
        fi
    fi

    echo -e "${GREEN}Activating virtual environment...${NC}"
    source $VENV_DIR/bin/activate

    if [ $? -eq 0 ]; then
        echo -e "${GREEN}Virtual environment activated!${NC}"
        echo -e "${YELLOW}Python: $(which python)${NC}"
    else
        echo -e "${RED}Error activating virtual environment.${NC}"
        read -p "Press Enter to continue..."
        return 1
    fi

    read -p "Press Enter to continue..."
}

install_requirements() {
    echo ""
    echo -e "${YELLOW}Installing requirements...${NC}"

    # Activate venv if it exists
    if [ -d "$VENV_DIR" ]; then
        source $VENV_DIR/bin/activate
        echo -e "${GREEN}Virtual environment activated.${NC}"
    else
        echo -e "${YELLOW}Warning: Virtual environment not found. Installing globally.${NC}"
        echo -e "${YELLOW}Consider running option 1 first to create a venv.${NC}"
    fi

    python -m pip install --upgrade pip
    python -m pip install -r requirements.txt

    if [ $? -eq 0 ]; then
        echo -e "${GREEN}Requirements installed successfully!${NC}"
    else
        echo -e "${RED}Error installing requirements.${NC}"
    fi

    read -p "Press Enter to continue..."
}

run_application() {
    echo ""
    echo -e "${YELLOW}Starting TextCompare...${NC}"

    # Activate venv if it exists
    if [ -d "$VENV_DIR" ]; then
        source $VENV_DIR/bin/activate
        echo -e "${GREEN}Virtual environment activated.${NC}"
    else
        echo -e "${YELLOW}Warning: Virtual environment not found. Using system Python.${NC}"
    fi

    # Check if .env exists
    if [ ! -f ".env" ]; then
        echo -e "${YELLOW}Warning: .env file not found.${NC}"
        if [ -f ".env.example" ]; then
            echo -e "${YELLOW}Copying .env.example to .env...${NC}"
            cp .env.example .env
            echo -e "${GREEN}.env file created. Please edit it to add your API keys.${NC}"
        fi
    fi

    echo ""
    echo -e "${GREEN}Starting server on http://127.0.0.1:5000${NC}"
    echo -e "${YELLOW}Press Ctrl+C to stop the server${NC}"
    echo ""

    python app.py

    if [ $? -ne 0 ]; then
        echo -e "${RED}Error running the application.${NC}"
    fi

    echo ""
    read -p "Press Enter to continue..."
}

setup_and_run() {
    setup_venv
    if [ $? -eq 0 ]; then
        install_requirements
        if [ $? -eq 0 ]; then
            run_application
        fi
    fi
}

check_python() {
    echo ""
    echo -e "${YELLOW}Checking Python installation...${NC}"

    if command -v python3 &> /dev/null; then
        echo -e "${GREEN}Python 3 is installed:${NC}"
        python3 --version
        echo -e "${GREEN}Location: $(which python3)${NC}"
    else
        echo -e "${RED}Python 3 is not installed or not in PATH.${NC}"
        echo "Please install Python 3.8 or higher from your package manager:"
        echo "  Ubuntu/Debian: sudo apt install python3 python3-venv python3-pip"
        echo "  Fedora: sudo dnf install python3 python3-pip"
        echo "  Arch: sudo pacman -S python python-pip"
    fi

    echo ""
    if command -v pip3 &> /dev/null; then
        echo -e "${GREEN}pip3 is installed:${NC}"
        pip3 --version
    else
        echo -e "${YELLOW}pip3 is not installed.${NC}"
    fi

    read -p "Press Enter to continue..."
}

check_ollama() {
    echo ""
    echo -e "${YELLOW}Checking Ollama installation...${NC}"

    # Check if ollama command exists
    if command -v ollama &> /dev/null; then
        echo -e "${GREEN}Ollama CLI is installed:${NC}"
        ollama --version
    else
        echo -e "${YELLOW}Ollama CLI not found in PATH.${NC}"
    fi

    echo ""
    # Check if Ollama service is running
    if curl -s http://localhost:11434/api/tags > /dev/null 2>&1; then
        echo -e "${GREEN}Ollama service is running on localhost:11434${NC}"

        # List available models
        echo -e "${GREEN}Available models:${NC}"
        curl -s http://localhost:11434/api/tags | python3 -m json.tool 2>/dev/null | grep '"name"' || echo "Could not parse models"
    else
        echo -e "${RED}Ollama service is not running or not installed.${NC}"
        echo "Please install Ollama from https://ollama.com"
        echo ""
        echo "Installation command:"
        echo "  curl -fsSL https://ollama.com/install.sh | sh"
        echo ""
        echo "After installation, start the service and pull a model:"
        echo "  ollama pull llama3.1"
    fi

    read -p "Press Enter to continue..."
}

# Main loop
while true; do
    show_menu
    read choice

    case $choice in
        1)
            setup_venv
            ;;
        2)
            install_requirements
            ;;
        3)
            run_application
            ;;
        4)
            setup_and_run
            ;;
        5)
            check_python
            ;;
        6)
            check_ollama
            ;;
        7)
            echo ""
            echo -e "${GREEN}Thank you for using TextCompare!${NC}"
            echo ""
            exit 0
            ;;
        *)
            echo -e "${RED}Invalid choice. Please try again.${NC}"
            sleep 1
            ;;
    esac
done
