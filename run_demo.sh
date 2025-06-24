#!/bin/bash

echo "🎯 RabbitMQ Complete Demo Suite"
echo "=================================="
echo "This script provides easy access to all RabbitMQ demonstrations"
echo ""

# Function to check if Docker is running
check_docker() {
    if ! docker info > /dev/null 2>&1; then
        echo "❌ Docker is not running. Please start Docker first."
        exit 1
    fi
}

# Function to install Python dependencies
install_deps() {
    echo "📦 Installing Python dependencies..."
    pip install -r requirements.txt
    echo "✅ Dependencies installed"
}

# Function to show menu
show_menu() {
    echo "📋 Available Demos:"
    echo "1. 🔄 Basic Exchange Patterns (Direct, Fanout, Topic)"
    echo "2. 🏗️  RabbitMQ Cluster Demo (3-node HA cluster)"
    echo "3. 🧪 Cluster Integration Test (Comprehensive validation)"
    echo "4. 📊 Performance Benchmarks"
    echo "5. 🛑 Stop All Services"
    echo "6. 🔧 Setup/Install Dependencies"
    echo "7. ℹ️  Help & Documentation"
    echo "8. 🚪 Exit"
    echo ""
}

# Basic exchange demo
run_basic_demo() {
    echo "🚀 Starting Basic Exchange Demo..."
    echo "This will start a single RabbitMQ instance and run exchange examples"
    echo ""
    
    # Start basic RabbitMQ
    ./start.sh
    
    echo ""
    echo "🎮 Run these commands in separate terminals:"
    echo "  python demo.py                    # Interactive demo"
    echo "  cd examples/direct && python producer.py error 'Test error'"
    echo "  cd examples/direct && python consumer.py error"
    echo ""
    read -p "Press Enter when ready to continue..."
}

# Cluster demo
run_cluster_demo() {
    echo "🏗️ Starting RabbitMQ Cluster Demo..."
    echo "This will start a 3-node cluster with HAProxy load balancer"
    echo ""
    
    cd cluster
    ./start_cluster.sh
    
    echo ""
    echo "🎮 Available cluster demos:"
    echo "  python cluster_demo.py           # Interactive cluster demo"
    echo "  python producer.py 50            # Send messages through load balancer"
    echo "  python consumer.py               # HA consumer with failover"
    echo "  python failover_test.py          # Comprehensive failover testing"
    echo ""
    echo "🌐 Management interfaces:"
    echo "  http://localhost:15675           # Load balanced management"
    echo "  http://localhost:8404            # HAProxy statistics"
    echo ""
    read -p "Press Enter when ready to continue..."
    cd ..
}

# Integration test
run_integration_test() {
    echo "🧪 Running Cluster Integration Test..."
    echo "This comprehensive test validates all cluster components"
    echo ""
    
    cd cluster
    
    # Check if cluster is running
    if ! docker ps | grep -q rabbitmq1; then
        echo "⚠️  Cluster not running. Starting cluster first..."
        ./start_cluster.sh
        echo "⏳ Waiting for cluster to stabilize..."
        sleep 15
    fi
    
    python integration_test.py
    cd ..
}

# Performance benchmarks
run_performance_test() {
    echo "📊 Running Performance Benchmarks..."
    echo "This will test message throughput and latency"
    echo ""
    
    cd cluster
    
    # Check if cluster is running
    if ! docker ps | grep -q rabbitmq1; then
        echo "⚠️  Cluster not running. Starting cluster first..."
        ./start_cluster.sh
        echo "⏳ Waiting for cluster to stabilize..."
        sleep 15
    fi
    
    echo "🚀 Running throughput test..."
    python producer.py 1000
    
    echo ""
    echo "📈 For detailed performance analysis, run:"
    echo "  python integration_test.py       # Includes performance metrics"
    echo ""
    cd ..
}

# Stop all services
stop_all_services() {
    echo "🛑 Stopping All RabbitMQ Services..."
    
    # Stop basic RabbitMQ
    if [ -d "settings" ]; then
        echo "📦 Stopping basic RabbitMQ..."
        cd settings
        docker-compose down 2>/dev/null || true
        cd ..
    fi
    
    # Stop cluster
    if [ -d "cluster" ]; then
        echo "🏗️  Stopping RabbitMQ cluster..."
        cd cluster
        ./stop_cluster.sh 2>/dev/null || true
        cd ..
    fi
    
    echo "✅ All services stopped"
}

# Setup and install
setup_environment() {
    echo "🔧 Setting up Environment..."
    
    check_docker
    
    # Make scripts executable
    chmod +x start.sh 2>/dev/null || true
    chmod +x cluster/*.sh 2>/dev/null || true
    
    # Install Python dependencies
    install_deps
    
    # Pull Docker images
    echo "🐳 Pulling Docker images..."
    docker pull rabbitmq:3.11-management
    docker pull haproxy:2.4
    
    echo "✅ Environment setup complete!"
}

# Help and documentation
show_help() {
    echo "📚 RabbitMQ Demo Help & Documentation"
    echo "====================================="
    echo ""
    echo "🎯 OVERVIEW:"
    echo "This demo suite covers everything from basic RabbitMQ concepts"
    echo "to production-ready clustering with high availability."
    echo ""
    echo "📖 DOCUMENTATION:"
    echo "  • Main README: README.md"
    echo "  • Cluster Guide: cluster/README.md"
    echo "  • Exchange Examples: examples/*/README.md"
    echo ""
    echo "🔗 USEFUL LINKS:"
    echo "  • RabbitMQ Official Docs: https://rabbitmq.com/documentation.html"
    echo "  • Clustering Guide: https://rabbitmq.com/clustering.html"
    echo "  • Management Plugin: https://rabbitmq.com/management.html"
    echo ""
    echo "🐛 TROUBLESHOOTING:"
    echo "  • Check Docker is running: docker ps"
    echo "  • View container logs: docker logs rabbitmq1"
    echo "  • Reset everything: ./run_demo.sh → option 5"
    echo ""
    echo "🎮 RECOMMENDED LEARNING PATH:"
    echo "  1. Start with Basic Exchange Demo (option 1)"
    echo "  2. Read documentation and try examples manually"
    echo "  3. Move to Cluster Demo (option 2) for production concepts"
    echo "  4. Run Integration Test (option 3) to validate setup"
    echo ""
}

# Main script
main() {
    # Check prerequisites
    check_docker
    
    while true; do
        show_menu
        read -p "🎯 Select option (1-8): " choice
        echo ""
        
        case $choice in
            1)
                run_basic_demo
                ;;
            2)
                run_cluster_demo
                ;;
            3)
                run_integration_test
                ;;
            4)
                run_performance_test
                ;;
            5)
                stop_all_services
                ;;
            6)
                setup_environment
                ;;
            7)
                show_help
                ;;
            8)
                echo "👋 Thanks for using RabbitMQ Demo Suite!"
                exit 0
                ;;
            *)
                echo "❌ Invalid option. Please try again."
                ;;
        esac
        
        echo ""
        echo "Press Enter to return to main menu..."
        read
        echo ""
    done
}

# Run main function
main
