import requests

from biodumpy import Input, BiodumpyException


class COL(Input):
	"""
	Query the Catalogue of Life (COL) database to retrieve nomenclature information of a list of taxa.

	Parameters
	----------
	query : list
	    The list of taxa to query.
	dataset_key : int
		The dataset key to query. Please visit https://www.catalogueoflife.org/data/metadata to check the latest ChecklistBank release.
		Default is 9923.
	check_syn : bool, optional
	    If True, the function returns only the accepted nomenclature of a taxon.
	    See Detail section for further information.
	    Default is False.

	Details
	-------
	When check_syn is set to True, the resulting JSON will include only the nomenclature of the accepted taxon.
	For instance, if check_syn is True, the output for the species Bufo roseus will only show the nomenclature for
	Bufotes viridis. Conversely, if check_syn is set to False, the JSON will include the nomenclature for both
	Bufo roseus and Bufotes viridis.

	Example
	-------
	>>> from biodumpy import Biodumpy
	>>> from biodumpy.inputs import COL
	# List of taxa
	>>> taxa = ['Alytes muletensis', 'Bufotes viridis', 'Hyla meridionalis', 'Anax imperator', 'Bufo roseus', 'Stollia betae']
	# Start the download
	>>> bdp = Biodumpy([COL(bulk=True, check_syn=False)])
	>>> bdp.start(taxa, output_path='./downloads/{date}/{module}/{name}')
	"""

	ACCEPTED_TERMS = ["accepted", "provisionally accepted"]

	def __init__(self, check_syn: bool = False, dataset_key: int = None, **kwargs):
		super().__init__(**kwargs)
		self.check_syn = check_syn
		self.dataset_key = dataset_key

		if self.output_format != "json":
			raise ValueError("Invalid output_format. Expected 'json'.")

		if self.dataset_key is None:
			raise ValueError("Please provide a valid dataset_key, or visit https://www.catalogueoflife.org/data/changelog to use the latest ChecklistBank.")

	def _download(self, query, **kwargs) -> list:
		response = requests.get(
			f"https://api.checklistbank.org/dataset/{self.dataset_key}/nameusage/search?",
			params={"q": query, "content": "SCIENTIFIC_NAME", "type": "EXACT", "offset": 0, "limit": 10},
		)

		if response.status_code != 200:
			raise BiodumpyException(f"Taxonomy request. Error {response.status_code}")

		payload = response.json()

		if payload["empty"]:
			payload = [{"origin_taxon": query, "taxon_id": None, "status": None, "usage": None, "classification": None}]
		else:
			result = response.json()["result"]

			# Multiple IDs
			if len(result) > 1:
				ids = [item.get("id") for item in result if "id" in item]

				# Generate web links for each ID
				web_links = "\n".join([f"https://www.checklistbank.org/dataset/{self.dataset_key}/taxon/{id_}" for id_ in ids])
				id_input = input(f"\n Please enter the correct taxon ID of {query} \n ID: {ids}; Skip \n\nWeb links:\n{web_links}\nInsert the ID: \n")

				# Check if id_input is contained in ids (if the user write a wrong id)
				if id_input not in ids and id_input != "Skip":
					id_input = input(f"\n Please enter the CORRECT taxon ID of {query} \n ID: {ids}; Skip \n\nWeb links:\n{web_links}\nInsert the ID: \n")
				else:
					result = [item for item in result if item["id"] == id_input]

				if id_input == "Skip":
					result = [{"id": None, "usage": None, "status": None, "classification": None}]

			id = result[0].get("id")
			usage = result[0].get("usage")
			status = usage.get("status") if usage else None

			classification = result[0].get("classification")
			if self.check_syn and status not in COL.ACCEPTED_TERMS:
				synonym_id = usage.get("id") if usage else None
				classification = [item for item in classification if item["id"] != synonym_id] if classification else None

			payload = [{"origin_taxon": query, "taxon_id": id, "status": status, "usage": usage, "classification": classification}]

		return payload
