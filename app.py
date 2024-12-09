from flask import Flask, render_template, request, jsonify
import json
import os
import dns.resolver

import datetime
app = Flask(__name__)

# File to store DNS records
DNS_RECORDS_FILE = "dns_records.json"

# Load or initialize DNS records
if os.path.exists(DNS_RECORDS_FILE):
    with open(DNS_RECORDS_FILE, "r") as file:
        dns_records = json.load(file)
else:
    dns_records = {
        "A": [],
        "AAAA": [],
        "CNAME": [],
        "MX": [],
        "TXT": []
    }

@app.route("/")
def home():
    return render_template("index.html", dns_records=dns_records)

@app.route("/add_record", methods=["POST"])
def add_record():
    record_type = request.form["record_type"]
    name = request.form["name"]
    value = request.form["value"]
    
    if record_type in dns_records:
        dns_records[record_type].append({"name": name, "value": value})
        save_records()
        return jsonify({"status": "success", "message": "Record added successfully"})
    else:
        return jsonify({"status": "error", "message": "Invalid record type"})

@app.route("/delete_record", methods=["POST"])
def delete_record():
    record_type = request.form["record_type"]
    name = request.form["name"]
    
    if record_type in dns_records:
        dns_records[record_type] = [
            record for record in dns_records[record_type] if record["name"] != name
        ]
        save_records()
        return jsonify({"status": "success", "message": "Record deleted successfully"})
    else:
        return jsonify({"status": "error", "message": "Invalid record type"})


@app.route("/dig_test", methods=["POST"])
def dig_test():
    record_type = request.form["record_type"]
    name = request.form["name"]

    response_data = {
        "query": {"type": record_type, "name": name},
        "timestamp": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "source": "",
        "records": [],
        "ttl": None,
        "server": None
    }

    # Check if the record exists in local DNS records
    local_results = [
        {"name": record["name"], "value": record["value"], "type": record_type}
        for record in dns_records.get(record_type, []) if record["name"] == name
    ]
    if local_results:
        response_data["source"] = "local"
        response_data["records"] = local_results
        return jsonify({"status": "success", "response": response_data})

    # If not found locally, query external DNS
    try:
        response_data["source"] = "external"
        resolver = dns.resolver.Resolver()
        resolver.timeout = 5
        resolver.lifetime = 10
        answers = resolver.resolve(name, record_type)
        response_data["server"] = resolver.nameservers[0]
        response_data["ttl"] = answers.ttl
        response_data["records"] = [{"name": name, "value": str(rdata), "type": record_type} for rdata in answers]
        return jsonify({"status": "success", "response": response_data})
    except Exception as e:
        response_data["source"] = "error"
        response_data["error_message"] = str(e)
        return jsonify({"status": "error", "response": response_data})


def save_records():
    """Save DNS records to a JSON file."""
    with open(DNS_RECORDS_FILE, "w") as file:
        json.dump(dns_records, file, indent=4)

if __name__ == "__main__":
    app.run(debug=True)
