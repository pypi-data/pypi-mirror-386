import pytest
import tempfile
import os
import json

import io
from contextlib import redirect_stdout

from biodumpy import Biodumpy
from biodumpy.inputs import COL

# set a trap and redirect stdout. Remove the print of the function. In this wat the test output is cleanest.
trap = io.StringIO()


# Remember to check the latest dataset_key
def col_query(query, check_syn, dataset_key, dir_module="COL"):
	# Create temporary directory
	with tempfile.TemporaryDirectory() as temp_dir:
		# Construct the dynamic path using formatted strings
		dynamic_path = os.path.join(temp_dir)

	# Start biodumpy function
	bdp = Biodumpy([COL(bulk=True, check_syn=check_syn, dataset_key=dataset_key)])
	bdp.start(elements=query, output_path=f"{dynamic_path}/downloads/{{date}}/{{module}}/{{name}}")

	# Retrieve a file path
	dir_date = os.listdir(f"{dynamic_path}/downloads/")[0]
	file_list = os.listdir(f"{dynamic_path}/downloads/{dir_date}/{dir_module}")[0]

	# Open file
	file = os.path.join(f"{dynamic_path}/downloads/{dir_date}/{dir_module}/{file_list}")
	with open(file, "r") as f:
		data = json.load(f)

	return data


def test_col_initialization():
	# Test default initialization
	col = COL(dataset_key=309120)

	assert col.output_format == "json"
	assert col.sleep == 3

	# Objective: Verify that the class raises a ValueError when an invalid value is provided for the
	# output_format parameter.
	with pytest.raises(ValueError, match="Invalid output_format. Expected 'json'."):
		COL(output_format="xml")

	with pytest.raises(ValueError, match="Please provide a valid dataset_key, or visit https://www.catalogueoflife.org/data/changelog to use the latest ChecklistBank."):
		COL(dataset_key=None)


@pytest.mark.parametrize("query, check_syn, dataset_key", [(["Bufo roseus"], True, 309120), (["Bufo roseus"], False, 309120)])
def test_download(query, check_syn, dataset_key):
	with redirect_stdout(trap):
		data = col_query(query=query, check_syn=check_syn, dataset_key=dataset_key)

	# Check if data is not empty
	assert len(data) > 0, "data length is 0"

	# Check the main structure of the JSON file
	data = data[0]

	assert "origin_taxon" in data, "origin_taxon is not in data"
	assert data["origin_taxon"] == "Bufo roseus", "origin_taxon is not in Bufo roseus"

	assert "taxon_id" in data, "taxon_id is not in data"
	assert data["taxon_id"] is not None, "taxon_id should not be None"

	assert "status" in data, "status is not in data"
	assert data["status"] == "synonym", "status is not in synonym"

	assert "usage" in data, "usage is not in data"
	usage = data["usage"]
	assert "created" in usage, "created is not in usage"
	assert "createdBy" in usage, "createdBy is not in usage"
	assert "modified" in usage, "modified is not in usage"
	assert "modifiedBy" in usage, "modifiedBy is not in usage"
	assert "datasetKey" in usage, "datasetKey is not in usage"
	assert usage["datasetKey"] == dataset_key, f"datasetKey is not {dataset_key}"
	assert "id" in usage, "id is not in usage"
	assert usage["id"] == "NPDX", "id is not NPDX"
	assert "sectorKey" in usage, "sectorKey is not in usage"
	assert "name" in usage, "name is not in usage"
	assert "status" in usage, "status is not in usage"
	assert usage["status"] == "synonym", "status is not synonym"
	assert "origin" in usage, "origin is not in usage"
	assert "parentId" in usage, "parentId is not in usage"
	assert usage["parentId"] == "NPMS", "parentId is not NPMS"
	assert "accepted" in usage, "accepted is not in usage"
	assert "label" in usage, "label is not in usage"
	assert usage["label"] == "Bufo roseus Merrem, 1820", "label is not Bufo roseus Merrem, 1820"
	assert "labelHtml" in usage, "labelHtml is not in usage"
	assert "merged" in usage, "merged is not in usage"

	assert "classification" in data, "classification is not in data"
	classification = data["classification"]
	assert "id" in classification[0], "id is not in classification"
	assert "name" in classification[0], "name is not in classification"
	assert "rank" in classification[0], "rank is not in classification"
	assert "label" in classification[0], "label is not in classification"
	assert "labelHtml" in classification[0], "label is not in classification"
