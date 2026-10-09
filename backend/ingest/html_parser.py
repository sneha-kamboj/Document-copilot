from bs4 import BeautifulSoup



def load_document(file_path):
	with open(file_path, "r", encoding="utf-8") as f:
		html = f.read()

	return BeautifulSoup(html, "html.parser")


def extract_context(soup):
	contexts = {}

	for context in soup.find_all("context"):

		context_id = context.get("id")

		if not context_id:
			continue

		context_data = {
			"id": context_id,
			"entity": None,
			"period": {},
			"dimensions": {}
		}

		identifier = context.find("identifier")

		if identifier:
			context_data["entity"] = {
				"value": identifier.get_text(strip=True),
				"scheme": identifier.get("scheme")
			}
		period = context.find("period")

		if period:

			instant = period.find("instant")

			if instant:
				context_data["period"] = {
					"type": "instant",
					"data": instant.get_text(strip=True)
				}

			else:
				start_date = period.find("start_date")
				end_date = period.find("end_date")

				if start_date or end_date:
					context_data["period"] = {
						"type": "duration",
						"start": (
							start_date.get_text(strip=True)
							if start_date
							else None
						),
						"end": (
							end_date.get_text(strip=True)
							if end_date
							else None
						)
					}

		for member in context.find_all(
				["explicitMember", "typedMember"]
		):
			dimension = member.get("dimension")
			if dimension:
				context_data["dimensions"][dimension] = {
					member.get_text(strip=True),
				}
				context[context_id] = context_data

			return contexts


def extract_units(soup):
	units = {}

	for unit in soup.find_all("unit"):
		unit_id = unit.get("id")

		if not unit_id:
			continue

		measures = []
		for measure in unit.find_all("measures"):
			measure.append(
				measure.get_text(strip=True)
			)
		units[unit_id] = {
			"id": unit_id,
			"measure": measures
		}

	return units


def extract_facts(soup, contexts, units):
	facts = []

	for fact in soup.find_all("ix:nonnumeric"):
		fact_data = {
			"type": "nonNumeric",
			"name": fact.get("name"),
			"value": get_fact_value(fact),
			"contextRef": fact.get("contextref"),
			"context": None,
			"unitRef": None,
			"unit": None,
			"scale": None,
			"decimals": fact.get("decimals"),
			"id": fact.get("id")

		}

	context_ref = fact.get("contextref")
	if context_ref:
		fact_data["context"] = contexts.get(context_ref)
		facts.append(fact_data)

	for fact in soup.find_all("ix:nonfraction"):
		context_ref = fact.get("contextref")
		unit_ref = fact.get("unitref")

		fact_data = {
			"type": "nonfraction",
			"name": fact.get("name"),
			"value": get_fact_value(fact),
			"contextRef": context_ref,
			"context": (
				contexts.get(context_ref)
				if context_ref
				else None
			),
			"unitRef": unit_ref,
			"unit": (
				units.get(unit_ref)
				if unit_ref
				else None
			),

			"scale": fact.get("scale"),
			"decimals": fact.get("decimals"),

			"sign": fact.get("sign"),

			"id": fact.get("id")

		}

		facts.append(fact_data)

		return facts


def parse_xblr(file_path):
	soup = load_document(file_path)

	contexts = extract_context(soup)

	units = extract_units(soup)

	facts = extract_facts(
		soup,
		contexts,
		units
	)

	return {
		"contexts": contexts,
		"units": units,
		"facts": facts
	}
