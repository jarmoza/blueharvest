# Author: Jonathan Armoza
# Creation date: October 11, 2021
# Purpose: Reads in a Project Gutenberg-style text in txt format
# 		   and divides it into units provided by an input json metadata file

# TODO:
# (1) Modularize chapter grep script
# (2) Build json input parameters for each Huckleberry Finn edition
# (3) Run grep script over each text and insert components into the json file for each
# (4) Move utility functions to aolm_utilities.py
# (5) Proper github setup for Art of Literary Modeling repository

# Process for entering a new text:
# (1) Identify all file keys in metadata json file
# ex. below
# "frontmatter_endline": "Scene: The Mississippi Valley Time: Forty to fifty years ago",
# "chapter_prefix": "CHAPTER",
# "body_endline": "*** END OF THE PROJECT GUTENBERG EBOOK HUCKLEBERRY FINN ***",
# "body_component_prefix": "HUCKLEBERRYFINN_BODY_",
# "gutenberg_header_prefix": "GUTENBERG_HEADER_",
# "gutenberg_footer_prefix": "GUTENBERG_FOOTER_"

# Imports

# Standard library
from collections import OrderedDict
import json
import os
import sys


# Globals

# Debug
debug_separator = "========================================================================"

# Input/output paths
paths = {
	
	"input": "{0}{1}data{1}input{1}".format(os.getcwd(), os.sep),
	"output": "{0}{1}data{1}output{1}".format(os.getcwd(), os.sep)
}

# Known Huckleberry Finn edition text files
# paths["2021-02-21"] = "2021-02-21_HuckFinn.txt"
# paths["2016-08-17"] = "2016-08-17_HuckFinn.txt"
# paths["2021-02-21"] = "2021-02-21_HuckFinn.txt"

# Text file components
frontmatter_endline = "Scene: The Mississippi Valley Time: Forty to fifty years ago"
file_chapter_prefix = "CHAPTER"
file_bodyendline = "*** END OF THE PROJECT GUTENBERG EBOOK HUCKLEBERRY FINN ***"
filedata_gutenberg_prefix = "GUTENBERG_"
filedata_bodycomponent_prefix = "HUCKLEBERRYFINN_BODY_"
filedata_headercomponent_prefix = "HUCKLEBERRYFINN_FRONTMATTER_"

# Utility functions

# NOTE: Move to AOLM utilities file - J.Armoza 12-11-2021
def is_valid_file(p_filepath, p_tag):
	return p_filepath.endswith("." + p_tag) and os.path.isfile(p_filepath)

# NOTE: Move to AOLM utilities file - J.Armoza 12-11-2021
def print_debug_header(p_title, p_header_width=80, p_header_char="="):
	print(p_title + " " + (p_header_char * (p_header_width - len(p_title) - 1)))

# Primary functions

def read_components(p_text_filepath, p_metadata_filepath, p_display_components=False):

	# 0. Stores chapter first and lines, in chapter-order
	file_data = OrderedDict()

	# 1. Read in text file
	with open(p_text_filepath, "r") as text_file:
		text_lines = text_file.readlines()

	# 2. Read in metadata file for text file
	with open(p_metadata_filepath, "r") as metadata_file:
		metadata_json = json.load(metadata_file)

	# A. Check to see if text has already been transformed into json, and if it has, clear them for a new reading
	if len(metadata_json["components"]) > 0:
		metadata_json["components"] = {}

	# 3. Save the metadata file keys 

	# A. Text file keys for reading
	input_keys = {
	
		"component_input_prefix": metadata_json["keys"]["body"]["component_input_prefix"],
		"body_endline": metadata_json["keys"]["body"]["endline"],
		"frontmatter_endline": metadata_json["keys"]["frontmatter"]["endline"],
	}
	
	# B. Json file keys for writing
	output_keys = {
	
		"component_output_prefix": metadata_json["keys"]["body"]["component_output_prefix"],
		"gutenberg_header_prefix": "GUTENBERG_HEADER",
		"gutenberg_footer_prefix": "GUTENBERG_FOOTER"
	}

	# 2. Look for each component start and end line

	# A. Save the file header
	header_content = []
	index = 0
	while frontmatter_endline != text_lines[index].strip():
		header_content.append(text_lines[index].strip())
		index += 1
	header_content.append(text_lines[index].strip())
	file_data[output_keys["gutenberg_header_prefix"]] = header_content

	# B. Save each component to the file data dictionary, including the file footer
	body_content = []
	body_endline_found = False
	component_key = ""
	footer_content = []
	start_line = ""
	for index in range(index + 1, len(text_lines) - 1):

		# I. Look for the chapter prefix
		if input_keys["component_input_prefix"] in text_lines[index]:

			# a. Create a new line list for body content
			body_content = []

			# b. Save the chapter prefix-containing line as a key
			component_key = output_keys["component_output_prefix"] + text_lines[index].strip()
			# print(f"Chapter key: {component_key}")

			# c. Look for the actual start of the chapter
			index += 1
			while 0 == len(text_lines[index].strip()):
				index += 1

			# d. Save the chapter start line
			start_line = text_lines[index].strip()
			body_content.append(start_line)
			index += 1
			# print(f"Start line: {start_line}")

			# e. Look for the chapter end line
			while input_keys["body_endline"] != text_lines[index].strip():

				# i. Strip whitespace from the line
				cleaned_line = text_lines[index].strip()

				# ii. If a new component header is found stop reading for the previous body component
				if input_keys["component_input_prefix"] in cleaned_line:
					index -= 1
					file_data[component_key] = body_content
					break

				# iii. Save non-blank lines as part of the current body component
				if len(cleaned_line) > 0:
					body_content.append(cleaned_line)

				# iv. Go to the next line
				index += 1

			# f. Save the last entry in the ordered dictionary if found
			if input_keys["body_endline"] == text_lines[index].strip():

				# i. Save the last line as part of the last body component
				# as part of the footer.
				# (This will be a Gutenberg marker indicating the end of content.)
				footer_content.append(text_lines[index].strip())

				# ii. Indicate body reading is done and can move on to footer
				body_endline_found = True

				# iii. Save the last body component
				file_data[component_key] = body_content

		# II. Read the footer if the body has ended
		elif body_endline_found:

			# Read footer
			footer_content.append(text_lines[index].strip())

	# C. Save the footer
	file_data[output_keys["gutenberg_footer_prefix"]] = footer_content

	# DEBUG: Print ordered dictionary
	if p_display_components:
		for key in file_data:
			print(f"\"{key}\": [\n")
			print(f"\t\"{file_data[key][0]}\",")
			print(f"\t\"{file_data[key][1]}\",")
			print("],\n")

	return file_data

def output_stats(p_metadata_filepath):

	# 0. Read in the metadata json
	with open(p_metadata_filepath, "r") as metadata_file:
		metadata_json = json.load(metadata_file)

	# 1. Show base filename on the terminal
	print(os.path.splitext(os.path.basename(p_metadata_filepath))[0].upper())

	# 2. Output file keys to the terminal
	print_debug_header("File keys")
	for key in metadata_json["keys"]:
		print("{0}: {1}".format(key, metadata_json["keys"][key]))

	# 2. Output stats on text file components to the terminal
	print_debug_header("File component stats")
	print("Header length (lines): {0}".format(len(metadata_json["components"]["GUTENBERG_HEADER"])))
	print("Body components (count): {0}".format(len(metadata_json["components"]) - 2))
	print("Footer length (lines): {0}".format(len(metadata_json["components"]["GUTENBERG_FOOTER"])))

def write_components_to_metadata(p_file_data, p_metadata_filepath):

	# 0. Read in the metadata json
	with open(p_metadata_filepath, "r") as metadata_file:
		metadata_json = json.load(metadata_file)

	# 1. Save the header, components and footer in the old json file data
	for key in p_file_data:
		metadata_json["components"][key] = p_file_data[key]

	# 2. Write out the new json data to the metadata json file
	with open(p_metadata_filepath, "w") as output_file:
		json.dump(metadata_json, output_file)

def main(p_txt_filename):

	# 0. Text file path and metadata json file path inferred form text filename
	text_filepath = paths["input"] + p_txt_filename
	metadata_filepath = paths["input"] + os.path.splitext(p_txt_filename)[0] + ".json"

	# 0. Check for valid input text file and corresponding metadata json file
	if not is_valid_file(text_filepath, "txt") or \
	   not is_valid_file(metadata_filepath, "json"):
		print("Invalid filename input: {0}".format(p_txt_filename))
		return

	# 1. Read file components into ordered dictionary
	file_data = read_components(text_filepath, metadata_filepath)

	# 2. Output text components into the metadata file
	write_components_to_metadata(file_data, metadata_filepath)

	# 3. Output stats based on script run
	output_stats(metadata_filepath)
		

if "__main__" == __name__:
	if len(sys.argv) > 1:
		main(sys.argv[1] if len(sys.argv) > 1 else "")
