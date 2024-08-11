# from app import create_app

# app = create_app()

# if __name__ == "__main__":
#     app.run(debug=True)

import datetime
import os
import platform

from dotenv import load_dotenv

load_dotenv()

from flask import Blueprint, Flask, jsonify, request
from flask_cors import CORS

from app.utils.crawler import get_crawl_status, start_crawl
from app.utils.pinecone import search_with_query
from app.utils.resources import global_resources
from openai import OpenAI

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))


app = Flask(__name__)
CORS(app)

global_resources.init_pinecone()
global_resources.load_embedding_models()


@app.route("/", methods=["GET"])
def default_server_status():
    server_info = {
        "server": "running",
        "time": datetime.datetime.now().isoformat() + "Z",
        "platform": platform.system(),
        "platform_version": platform.version(),
        "architecture": platform.architecture()[0],
    }
    return jsonify(server_info), 200


@app.route("/crawl", methods=["POST"])
def crawl():
    data = request.json
    start_url = data.get("start_url")
    depth = data.get("depth", 2)  # Default depth is 2 if not provided
    print(start_url)

    response, status_code = start_crawl(start_url, depth)
    return jsonify(response), status_code


@app.route("/crawl-status", methods=["GET"])
def status():
    task_id = request.args.get("task_id")
    response, status_code = get_crawl_status(task_id)
    return jsonify(response), status_code


import json
from web3 import Web3

app = Flask(__name__)

# b64677a9958b450084777c0a529447b1

w3 = Web3(Web3.HTTPProvider("https://optimism-sepolia.infura.io/v3/b64677a9958b450084777c0a529447b1"))

contract_address = "0x79271D3adD1886E11Ce3a5fE09EA26Ef07E7010A"
with open('abi.json', 'r') as abi_file:
    contract_abi = json.load(abi_file)

contract = w3.eth.contract(address=contract_address, abi=contract_abi)

@app.route('/mint_as_nft', methods=['POST'])
def test():
    tx = contract.functions.mint("0x7EED0188B8E25Ea6a121071980a13333098EA7A0").build_transaction({
        'chainId': 3,
        'gas': 2000000,
        'gasPrice': w3.to_wei('1', 'gwei'),
        'nonce': w3.eth.get_transaction_count("0x7EED0188B8E25Ea6a121071980a13333098EA7A0"),
    })
    signed_tx = w3.eth.account.signTransaction(tx, private_key="PRIVATE_KEY") # implement the signing function
    tx_hash = w3.eth.sendRawTransaction(signed_tx.rawTransaction)
    print(tx_hash.hex())
    return tx_hash.hex()


@app.route("/search", methods=["POST"])
def search():
    data = request.json
    query = data.get("query")
    print(query)

    if not query:
        return jsonify({"error": "Query is required"}), 400

    results = search_with_query(query)
    
    first_3_results = results.matches[:3]
    # text looks like this: 'metadata': {'task_id': '4eec4872-b8a2-4cc5-80b8-1092512cd5af',
            #   'text': '
    # iterate over the first 3 results and get the text
    print(first_3_results)
# first_3_results looks like this: [{'id': '4db458af-9142-410d-8407-b7bd1d0f96b9',
#  'metadata': {'task_id': '4eec4872-b8a2-4cc5-80b8-1092512cd5af',
#               'text': 'ensurepip — Bootstrapping the pip installer — Python '
    result_text = ""
    for result in first_3_results:
        result_text += result['metadata']['text']
    print(result_text)
            
    # for result in first_3_results:
    #     print(result)
        
    #     print(result.metadata.url)
    #     print(result.metadata.task_id)
    
    prompt = f"""
    Answer the question that the user might have asked based on the following text:
    {result_text}
    1. analyze the question which is {query}
    2. analyze the text
    3. answer the question based on the text provided.
    4. if the answer consists of code, provide the code snippet in ``` ``` format.
    5. if the answer consists of a link, provide the link.
    6. if the answer consists of a list, provide the list.
    7. if the answer consists of a table, provide the table.
    8. Only provide the answer to the question asked.
    """
    
    response = client.chat.completions.create(
        model="gpt-4",
        messages=[
            {"role": "system", "content": prompt},
            {"role": "user", "content": query}
        ],
        max_tokens=1000,
    )
    answer = response.choices[0].message.content
    print(answer)
    
    # return answer in json format
    return jsonify({"answer": answer}), 200


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8000, debug=True)

