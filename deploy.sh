#!/bin/bash

# Healthcare Agent - Docker Deployment Script
# This script automates the deployment process

set -e  # Exit on error

echo "🏥 Healthcare Agent - Docker Deployment"
echo "========================================"
echo ""

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Function to print colored output
print_success() {
    echo -e "${GREEN}✓ $1${NC}"
}

print_error() {
    echo -e "${RED}✗ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠ $1${NC}"
}

print_info() {
    echo -e "${YELLOW}ℹ $1${NC}"
}

# Check if Docker is installed
if ! command -v docker &> /dev/null; then
    print_error "Docker is not installed. Please install Docker first."
    exit 1
fi

# Check if Docker Compose is installed
if ! command -v docker-compose &> /dev/null; then
    print_error "Docker Compose is not installed. Please install Docker Compose first."
    exit 1
fi

print_success "Docker and Docker Compose are installed"
echo ""

# Check if .env file exists
if [ ! -f .env ]; then
    print_warning ".env file not found. Creating from template..."
    
    if [ -f env.template ]; then
        cp env.template .env
        print_info "Please edit .env file with your configuration"
        print_warning "Especially set JWT_SECRET_KEY before continuing!"
        echo ""
        read -p "Press Enter to continue after editing .env file..."
    else
        print_error "env.template not found. Cannot create .env file."
        exit 1
    fi
else
    print_success ".env file found"
fi

# Check if JWT_SECRET_KEY is set
if grep -q "JWT_SECRET_KEY=your-super-secret-jwt-key-change-this-in-production" .env; then
    print_warning "JWT_SECRET_KEY is still set to default value!"
    print_info "Generating a random JWT secret key..."
    
    # Generate random key
    NEW_KEY=$(python3 -c "import secrets; print(secrets.token_urlsafe(32))" 2>/dev/null || openssl rand -base64 32)
    
    # Update .env file
    if [[ "$OSTYPE" == "darwin"* ]]; then
        # macOS
        sed -i '' "s|JWT_SECRET_KEY=your-super-secret-jwt-key-change-this-in-production|JWT_SECRET_KEY=$NEW_KEY|g" .env
    else
        # Linux
        sed -i "s|JWT_SECRET_KEY=your-super-secret-jwt-key-change-this-in-production|JWT_SECRET_KEY=$NEW_KEY|g" .env
    fi
    
    print_success "Generated and set new JWT_SECRET_KEY"
fi
echo ""

# Ask user what to do
echo "What would you like to do?"
echo "1) Fresh deployment (build and start)"
echo "2) Start existing containers"
echo "3) Stop containers"
echo "4) Restart containers"
echo "5) View logs"
echo "6) Clean up everything (including data)"
echo "7) Initialize/Seed database"
echo ""
read -p "Enter your choice (1-7): " choice

case $choice in
    1)
        print_info "Starting fresh deployment..."
        echo ""
        
        print_info "Building Docker images (this may take 5-10 minutes)..."
        docker-compose build
        print_success "Build completed"
        echo ""
        
        print_info "Starting all services..."
        docker-compose up -d
        print_success "All services started"
        echo ""
        
        print_info "Waiting for services to be healthy (30 seconds)..."
        sleep 30
        
        print_info "Checking service status..."
        docker-compose ps
        echo ""
        
        print_success "Deployment complete!"
        echo ""
        print_info "Access the application at:"
        echo "  Frontend:  http://localhost:3000"
        echo "  Backend:   http://localhost:8000"
        echo "  API Docs:  http://localhost:8000/docs"
        echo "  GraphQL:   http://localhost:8000/graphql"
        echo ""
        print_warning "Don't forget to seed the database! Run this script again and select option 7"
        ;;
        
    2)
        print_info "Starting containers..."
        docker-compose up -d
        print_success "Containers started"
        docker-compose ps
        ;;
        
    3)
        print_info "Stopping containers..."
        docker-compose down
        print_success "Containers stopped"
        ;;
        
    4)
        print_info "Restarting containers..."
        docker-compose restart
        print_success "Containers restarted"
        docker-compose ps
        ;;
        
    5)
        print_info "Showing logs (Press Ctrl+C to exit)..."
        docker-compose logs -f
        ;;
        
    6)
        print_warning "This will remove all containers, networks, and DATA!"
        read -p "Are you sure? (yes/no): " confirm
        if [ "$confirm" = "yes" ]; then
            print_info "Cleaning up..."
            docker-compose down -v
            print_success "Cleanup complete"
        else
            print_info "Cleanup cancelled"
        fi
        ;;
        
    7)
        print_info "Initializing database..."
        echo ""
        
        # Check if backend is running
        if ! docker-compose ps | grep healthcare_backend | grep -q "Up"; then
            print_error "Backend container is not running. Please start the services first (option 1 or 2)"
            exit 1
        fi
        
        print_info "Creating admin user..."
        docker-compose exec -T backend python seed_admin.py
        print_success "Admin user created"
        echo ""
        
        read -p "Do you want to seed initial data from CSV files? (yes/no): " seed_csv
        if [ "$seed_csv" = "yes" ]; then
            print_info "Seeding data from CSV files..."
            docker-compose exec -T backend python seed_from_csv.py
            print_success "CSV data seeded"
        fi
        echo ""
        
        print_success "Database initialization complete!"
        ;;
        
    *)
        print_error "Invalid choice"
        exit 1
        ;;
esac

echo ""
print_info "For more options, check DEPLOYMENT.md"

