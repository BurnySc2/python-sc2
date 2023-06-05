import os

if __name__ == "__main__":
    os.system('protoc --python_out=./sc2/ ./s2clientprotocol/*.proto')
    # name each individual .proto file if *.proto doesn't work, sperated by space
    #os.system('protoc --python_out=./sc2/ s2clientprotocol/common.proto s2clientprotocol/data.proto s2clientprotocol/debug.proto s2clientprotocol/error.proto s2clientprotocol/query.proto s2clientprotocol/raw.proto s2clientprotocol/sc2api.proto s2clientprotocol/score.proto s2clientprotocol/spatial.proto s2clientprotocol/ui.proto')
    

