#!/usr/bin/env python3
import subprocess
import time
import os
import sys

from dotenv import load_dotenv
import os

# Load environment variables
load_dotenv()

def check_container_running(container_name=os.getenv("NEO4J_CONTAINER_NAME")):
    """Check if Neo4j container is already running"""
    try:
        result = subprocess.run(
            ["docker", "ps", "--filter", f"name={container_name}", "--format", "{{.Names}}"],
            capture_output=True,
            text=True
        )
        return container_name in result.stdout
    except Exception as e:
        print(f"Error checking container status: {e}")
        return False

def start_neo4j():
    """Start Neo4j using docker-compose in detached mode"""
    if check_container_running():
        print("Neo4j container is already running")
        return True

    try:
        # Start containers in detached mode
        subprocess.run(
            ["docker-compose", "up", "-d"],
            check=True
        )
        print("Starting Neo4j container...")
        
        # Wait for container to be healthy
        max_attempts = 12  # 2 minutes total (12 * 10 seconds)
        attempt = 0
        
        while attempt < max_attempts:
            result = subprocess.run(
                ["docker", "inspect", "--format", "{{.State.Health.Status}}", os.getenv("NEO4J_CONTAINER_NAME")],
                capture_output=True,
                text=True
            )
            
            if "healthy" in result.stdout.lower():
                print("Neo4j is ready!")
                return True
                
            print("Waiting for Neo4j to be ready...")
            time.sleep(10)
            attempt += 1
            
        print("Timeout waiting for Neo4j to be ready")
        return False
        
    except subprocess.CalledProcessError as e:
        print(f"Error starting Neo4j: {e}")
        return False

def stop_neo4j():
    """Stop Neo4j container"""
    try:
        subprocess.run(
            ["docker-compose", "down"],
            check=True
        )
        print("Neo4j container stopped")
        return True
    except subprocess.CalledProcessError as e:
        print(f"Error stopping Neo4j: {e}")
        return False

if __name__ == "__main__":
    if len(sys.argv) != 2 or sys.argv[1] not in ["start", "stop", "status"]:
        print("Usage: python manage_neo4j.py [start|stop|status]")
        sys.exit(1)
        
    command = sys.argv[1]
    
    if command == "start":
        success = start_neo4j()
        sys.exit(0 if success else 1)
    elif command == "stop":
        success = stop_neo4j()
        sys.exit(0 if success else 1)
    elif command == "status":
        running = check_container_running()
        print(f"Neo4j container is {'running' if running else 'not running'}")
        sys.exit(0 if running else 1)
