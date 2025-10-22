import sys
import os
import subprocess

def main():
    if len(sys.argv) < 2:
        print("Usage: python -m sounava <filename.py>")
        sys.exit(1)
    
    filename = sys.argv[1]
    
    if not os.path.exists(filename):
        print(f"Error: File '{filename}' not found")
        sys.exit(1)
    
    if not filename.endswith('.py'):
        print(f"Error: '{filename}' is not a Python file")
        sys.exit(1)
    
    print(f"Starting {filename} with sounava")
    
    try:
        subprocess.run([sys.executable, filename], check=True)
    except subprocess.CalledProcessError as e:
        print(f"Error running {filename}: {e}")
        sys.exit(1)
    except KeyboardInterrupt:
        print("\nStopped by user")
    except Exception as e:
        print(f"Unexpected error: {e}")

if __name__ == "__main__":
    main()