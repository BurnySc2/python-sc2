import os

if __name__ == "__main__":
    # name each individual .proto file if *.proto doesn't work, sperated by space
    os.system('protoc --python_out=./sc2/ ./s2clientprotocol/*.proto')
