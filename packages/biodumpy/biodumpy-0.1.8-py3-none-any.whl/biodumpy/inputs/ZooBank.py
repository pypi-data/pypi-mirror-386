import requests

from bs4 import BeautifulSoup
from tqdm import tqdm
from biodumpy import Input, BiodumpyException


class ZooBank(Input):
	"""
	Query the Official Registry of Zoological Nomenclature (ZooBank) database to retrieve scientific bibliographic
	information.

	Parameters
	----------
	query : list
	    The list of taxa to query.
	dataset_size : str, optional
	    This parameter is useful for managing the download of bibliographic information based on the number of
	    scientific articles stored in ZooBank for each taxon. You can set this parameter to either 'small' or 'large'.
	    We recommend choosing 'small' if the number of articles for a given taxon is lower than 200, or 'large' if
	    it exceeds 200.
	    Default is 'small'.
	info : bool, optional
	    If set to True, the function will download additional article information not included in the main research,
	    such as the DOI.
	    Default is False.

	Example
	-------
	>>> from biodumpy import Biodumpy
	>>> from biodumpy.inputs import ZooBank
	# Taxa list
	>>> taxa = ['Alytes muletensis', 'Bufotes viridis', 'Hyla meridionalis', 'Anax imperator']
	# Set the module and start the download
	>>> bdp = Biodumpy([ZooBank(bulk=True, dataset_size='small', info=False)])
	>>> bdp.start(taxa, output_path='./downloads/{date}/{module}/{name}')
	"""

	def __init__(self, dataset_size: str = "small", info: bool = False, **kwargs):
		super().__init__(**kwargs)
		self.dataset_size = dataset_size
		self.info = info

		robot_input = input(
			"\nBefore using the ZooBank module, please confirm that you are not a robot at: https://zoobank.org/\n"
			"Be considerate and avoid overloading the system; download responsibly.\n\n"
			"If you have visited the page, type 'yes' to continue with the download.\n"
		)

		if self.dataset_size not in ["small", "large"]:
			raise ValueError("Invalid dataset_size. Expected 'small' or 'large'.")

		if self.output_format != "json":
			raise ValueError("Invalid output_format. Expected 'json'.")

		if robot_input != "yes":
			raise ValueError("Please visit the ZooBank website and confirm that you are not a robot.")

	def _download(self, query, **kwargs) -> list:
		payload = []

		if self.dataset_size == "small":
			response = requests.get(f"https://zoobank.org/References.json?search_term={query}")

			if response.status_code != 200:
				raise BiodumpyException(f"Reference request. Error {response.status_code}")

			payload = response.json()
			referenceuuid = [item["referenceuuid"] for item in payload]

		else:
			print("Searching in ZooBank...")
			response_pub = requests.get(f"https://zoobank.org/Search?search_term={query}")

			if response_pub.status_code != 200:
				raise BiodumpyException(f"Term search request. Error {response_pub.status_code}")

			html_content = response_pub.text

			# Parsing the HTML content with BeautifulSoup
			soup = BeautifulSoup(html_content, "html.parser")
			referenceuuid = [entry["href"].replace("/References/", "") for entry in soup.find_all(class_="biblio-entry") if "href" in entry.attrs]

			for ref in tqdm(referenceuuid, desc="Fetching paper info"):
				response_pub = requests.get(f"https://zoobank.org/References.json/{ref}")
				if response_pub.status_code == 200:  # Check if the request was successful
					try:
						json_content = response_pub.json()[0]
						payload.append(json_content)
					except Exception as e:
						print(f"An error occurred: {e} .... referenceuuid: {ref}")
				else:
					print(f"Failed to retrieve data for {ref}")

		if self.info and referenceuuid != [""]:
			for refuid in referenceuuid:
				index = next((i for i, entry in enumerate(payload) if entry.get("referenceuuid") == refuid), None)

				response_id = requests.get(f"https://zoobank.org/Identifiers.json/{refuid}")
				try:
					response_id_json = response_id.json()
					payload[index]["info"] = response_id_json
				except requests.exceptions.JSONDecodeError as e:
					print(f"Failed to parse JSON with reference uid{refuid}:", e)

		return payload
