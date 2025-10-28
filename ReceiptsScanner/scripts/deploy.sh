#!/bin/bash
# Deployment script for Receipt Scanner

set -e

echo "🚀 Receipt Scanner Deployment Script"
echo "======================================"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Functions
print_success() {
    echo -e "${GREEN}✓ $1${NC}"
}

print_error() {
    echo -e "${RED}✗ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠ $1${NC}"
}

check_prerequisites() {
    echo ""
    echo "Checking prerequisites..."
    
    # Check Docker
    if command -v docker &> /dev/null; then
        print_success "Docker is installed"
    else
        print_error "Docker is not installed"
        exit 1
    fi
    
    # Check Docker Compose
    if command -v docker-compose &> /dev/null; then
        print_success "Docker Compose is installed"
    else
        print_error "Docker Compose is not installed"
        exit 1
    fi
    
    # Check .env file
    if [ -f .env ]; then
        print_success ".env file exists"
    else
        print_warning ".env file not found. Creating from .env.example..."
        cp .env.example .env
        print_warning "Please edit .env file with your configuration"
        exit 1
    fi
}

create_directories() {
    echo ""
    echo "Creating necessary directories..."
    
    mkdir -p data models training_data logs
    mkdir -p prometheus grafana/dashboards grafana/provisioning
    
    print_success "Directories created"
}

build_images() {
    echo ""
    echo "Building Docker images..."
    
    docker-compose build
    
    print_success "Docker images built"
}

start_services() {
    echo ""
    echo "Starting services..."
    
    docker-compose up -d
    
    print_success "Services started"
}

wait_for_services() {
    echo ""
    echo "Waiting for services to be ready..."
    
    # Wait for Redis
    echo -n "Redis: "
    for i in {1..30}; do
        if docker-compose exec -T redis redis-cli ping &> /dev/null; then
            print_success "Ready"
            break
        fi
        sleep 1
    done
    
    # Wait for MinIO
    echo -n "MinIO: "
    for i in {1..30}; do
        if curl -f http://localhost:9000/minio/health/live &> /dev/null; then
            print_success "Ready"
            break
        fi
        sleep 1
    done
    
    # Wait for API
    echo -n "API: "
    for i in {1..30}; do
        if curl -f http://localhost:8000/health &> /dev/null; then
            print_success "Ready"
            break
        fi
        sleep 1
    done
}

initialize_minio() {
    echo ""
    echo "Initializing MinIO..."
    
    chmod +x scripts/init_minio.sh
    ./scripts/init_minio.sh
    
    print_success "MinIO initialized"
}

train_initial_model() {
    echo ""
    echo "Training initial ML model..."
    
    docker-compose exec -T api python -m ml.train
    
    print_success "Initial model trained"
}

show_access_info() {
    echo ""
    echo "======================================"
    echo "🎉 Deployment completed successfully!"
    echo "======================================"
    echo ""
    echo "Access your application at:"
    echo ""
    echo "  📱 Streamlit UI:     http://localhost:8501"
    echo "  🔧 API Docs:         http://localhost:8000/docs"
    echo "  📊 Prometheus:       http://localhost:9090"
    echo "  📈 Grafana:          http://localhost:3000"
    echo "     Username: admin"
    echo "     Password: admin"
    echo "  🌸 Flower (Celery): http://localhost:5555"
    echo "  📦 MinIO Console:    http://localhost:9001"
    echo "     Username: minioadmin"
    echo "     Password: minioadmin"
    echo ""
    echo "Useful commands:"
    echo "  View logs:          docker-compose logs -f"
    echo "  Stop services:      docker-compose down"
    echo "  Restart services:   docker-compose restart"
    echo "  Backup data:        ./scripts/backup_data.sh"
    echo ""
}

# Main deployment flow
main() {
    check_prerequisites
    create_directories
    build_images
    start_services
    wait_for_services
    initialize_minio
    
    # Ask about training
    read -p "Train initial ML model now? (y/n) " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        train_initial_model
    else
        print_warning "Skipping model training. Run later with: docker-compose exec api python -m ml.train"
    fi
    
    show_access_info
}

# Run main function
main