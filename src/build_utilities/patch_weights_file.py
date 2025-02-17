#!/usr/bin/python3

import sys, os, json

def usage():
    print("\nUSAGE: ./patch_weights_file.py <command> [arguments...]\n")

    print("--- nuke ---")
    print("Nuke will remove all weights assigned to a vertex group, leaving an empty array for that group in the weights file.\n")
    print("./patch_weights_file.py nuke <vertex_group_name> <weights file>\n")

    print("--- fill ---")
    print("Fill will replace all weights assigned to a vertex group with a given value, leaving an array of the same size but where all weight entries are the same.\n")
    print("./patch_weights_file.py fill <vertex_group_name> <replacement value> <weights file>\n")

    print("--- patch ---")
    print("Patch will read weights for one group from a source file and use those to replace the same group in the destination file.\n")
    print("./patch_weights_file.py patch <vertex_group_name> <weights file to read from> <weights file to write to>\n")
    
    print("")
    sys.exit(1)

expected_len = 2
if "python" in sys.argv[0]:
    expected_len = expected_len + 1
    
if not sys.argv or len(sys.argv) < expected_len:
    usage()
    
command = sys.argv[expected_len - 1]

commands = {"nuke": 2, "fill": 3, "patch": 3}

if command not in commands.keys():
    usage()

args = list(sys.argv)

for i in range(expected_len):
    args.pop(0)

if len(args) < commands[command]:
    print("ERROR: Expected " + str(commands[command]) + " arguments to command " + command + ", but got " + str(len(args)) + "\n")
    usage()

weights_file = args[commands[command]-1]    

if not os.path.exists(weights_file):
    print(weights_file + " does not exist")
    sys.exit(1)

current_weights_data = dict()

with open(weights_file, "r") as json_file:
    current_weights_data = json.load(json_file)
     
vertex_group = args[0]
if not vertex_group in current_weights_data["weights"]:
    print("ERROR: the " + vertex_group + " group does not exist in the given weights file")
    sys.exit(1)
    
if command == "nuke":
    current_weights_data["weights"][vertex_group] = []
    
if command == "fill":
    for weight_spec in current_weights_data["weights"][vertex_group]:
        weight_spec[1] = float(args[1])
        
with open("result.json", "w") as json_file:
    json.dump(current_weights_data, json_file, indent=4, sort_keys=True)
