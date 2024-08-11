import random
import string
import numpy as np
import time
import redis
import concurrent.futures
from sentence_transformers import SentenceTransformer
from redis.commands.search.query import Query
import json
from tabulate import tabulate

# Number of concurrent requests
NUM_WORKERS = 256

# Number of iterations per worker
NUM_ITERATIONS = 50

# REDIS_HOST = 'localhost'
# REDIS_PORT = 6379
# REDIS_DB = 0

# cloud - QPS1
REDIS_HOST="redis-18217.c32732.ap-south-1-mz.ec2.cloud.rlrcp.com"
REDIS_PORT=18217
REDIS_PASSWORD="98BJB7EgQTR4HoWsLWzcEJPgv0EwAVgm"
REDIS_DB = 0

# # cloud - QPS8
# REDIS_HOST="redis-12961.c32734.ap-south-1-mz.ec2.cloud.rlrcp.com"
# REDIS_PORT=12961
# REDIS_PASSWORD="chuHwnfJ7lSiynWAhX2BrZSOTG0CamMv"
# REDIS_DB = 0

SUMMARY_INDEX_NAME = "idxsumm"
QUERY = "tell me some details about trigovex company"

model = SentenceTransformer('all-MiniLM-L6-v2')

redis_client = redis.Redis(
    host=REDIS_HOST,
    port=REDIS_PORT,
    db=REDIS_DB,
    password=REDIS_PASSWORD
)

def set_json(key, path, value):
    return redis_client.json().set(key, path, value)

def generate_random_string(length=8):
    return ''.join(random.choices(string.ascii_lowercase + string.digits, k=length))

def store_file_metadata(doc_name, original_filename, upload_time, roles, summary, summary_embeddings):
    metadata_key = f"file_{doc_name}_metadata"
    metadata = {
        "uploaded_time": upload_time,
        "original_filename": original_filename,
        "unique_filename": doc_name,
        "roles": roles,
        "summary": summary,
        "summary_embeddings": summary_embeddings.tolist()  # Convert numpy array to list
    }
    set_json(metadata_key, '.', metadata)

def get_embeddings(chunks):
    try:
        embeddings = model.encode(chunks)
        return embeddings
    except Exception as e:
        print(f"Error in get_embeddings: {e}")
        return None

def perform_vector_search_for_documents(query_embedding, roles):
    try:
        vector = np.array(query_embedding, dtype=np.float32).tobytes()
        role_filter = ""
        for i, role in enumerate(roles):
            if i > 0:
                role_filter += " | "
            role_filter += f"@roles:{{{role}}}"

        q = Query(f'({role_filter})=>[KNN 5 @vector $query_vec AS vector_score]')\
                    .sort_by('vector_score')\
                    .return_fields('vector_score','roles')\
                    .dialect(4)

        params = {"query_vec": vector}

        start_time = time.time()
        results = redis_client.ft(SUMMARY_INDEX_NAME).search(q, query_params=params)
        end_time = time.time()

        response_time = (end_time - start_time)
        # print(response_time)
        related_docs = []
        for doc in results.docs:
            if float(doc.vector_score) <= 0.8:
                roles = json.loads(doc.roles)
                related_docs.append({'id': doc.id, 'roles': roles[0]})

        return related_docs, response_time

    except Exception as e:
        print(f"Error in perform_vector_search_for_documents: {e}")
        return [], 0

def simulate_upload_pdf():
    try:
        doc_name = generate_random_string()
        original_filename = f"{doc_name}.pdf"
        upload_time = time.strftime('%Y-%m-%d %H:%M:%S')
        roles = ["admin", "user"]
        summary = "Geopolitical forecasting tournaments have become increasingly popular over the last decade, notable providers including the Good Judgment Project and Metaculus. A typical question from Metaculus is that of Figure 1, “Will Donald Trump be president of the USA in 2019?”. From when the question opened (May 17, 2017), forecasters submitted probability forecasts on a scale of 0 to 1), until the question was resolved on Feb 1, 2019, although here we show only the first seven months’ forecasts. After resolution, the forecasts are scored. If forecasts are considered “static”, taking no account of when the forecast is submitted, a simple proper probability score, such as the Brier (quadratic) or Log (logarithmic) score, can be used. Proper scores are optimized by, and therefore incentivize forecasters to submit their best estimates of, the true probability – although propriety fails if rewards are not proportional to the score, for example if the prize goes to the overall winner. But prescience is clearly valuable, and Metaculus, for example, weights the score by how long it was submitted before resolution. Indeed it is clear just from a visual inspection that such a forecasting problem is dynamical. The distribution of forecasts is not stationary; it changes both smoothly and sharply at certain points, as does the density of forecasts submitted. The reason is obvious: news occurs much in this way, and new information is continually informing the forecasting process."
        summary_embeddings = get_embeddings(summary)
        
        if summary_embeddings is None:
            return 0
        
        store_file_metadata(doc_name, original_filename, upload_time, roles, summary, summary_embeddings)
        
        return time.time() - time.mktime(time.strptime(upload_time, '%Y-%m-%d %H:%M:%S'))

    except Exception as e:
        print(f"Error in simulate_upload_pdf: {e}")
        return 0

def stress_test_worker(worker_id):
    total_response_time = 0
    read_count = 0
    write_count = 0
    worker_start_time = time.time()

    for _ in range(NUM_ITERATIONS):
        try:
            operation = random.choice(["read", "write"])
            if operation == "read":
                query_embedding = get_embeddings(QUERY)
                if query_embedding is None:
                    continue

                roles = ["admin", "user"]
                _, response_time = perform_vector_search_for_documents(query_embedding, roles)
                read_count += 1
            else:  # write operation
                response_time = simulate_upload_pdf()
                write_count += 1

            total_response_time += response_time * 1000  # Convert to milliseconds
            time.sleep(0.01)
        except Exception as e:
            print(f"Error in stress_test_worker {worker_id}: {e}")

    average_response_time = total_response_time / NUM_ITERATIONS
    worker_end_time = time.time()

    # Return the details for the current thread
    return {
        "Worker ID": worker_id,
        "Start Time": time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(worker_start_time)),
        "End Time": time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(worker_end_time)),
        "Average Response Time (ms)": f"{average_response_time:.2f} ms",
        "Reads": read_count,
        "Writes": write_count
    }

def write_results_to_file(filename, results, num_workers, num_iterations):
    try:
        # Calculate the overall average response time correctly
        total_response_time = sum(float(result["Average Response Time (ms)"].split()[0]) for result in results)
        overall_average_response_time = total_response_time / len(results)

        # Calculate total reads and writes
        total_reads = sum(result["Reads"] for result in results)
        total_writes = sum(result["Writes"] for result in results)

        # Write the results to the file
        with open(filename, "a") as f:
            f.write(f"Workers: {num_workers}, Iterations per worker: {num_iterations}, "
                    f"Overall Average Response Time (ms): {overall_average_response_time:.2f} ms\n")
            f.write(f"Total Reads: {total_reads}, Total Writes: {total_writes}\n")

        print(f"Results written to {filename}.")
    except Exception as e:
        print(f"Error writing results to file: {e}")

if __name__ == "__main__":
    try:
        start_time = time.time()

        # Run the stress test with multiple workers
        results = []
        with concurrent.futures.ThreadPoolExecutor(max_workers=NUM_WORKERS) as executor:
            futures = [executor.submit(stress_test_worker, i) for i in range(NUM_WORKERS)]
            for future in concurrent.futures.as_completed(futures):
                results.append(future.result())

        end_time = time.time()
        print(f"Stress test completed in {end_time - start_time:.2f} seconds.")

        # Display the results in a tabular format
        print(tabulate(results, headers="keys", tablefmt="pretty"))

        # Write the overall average response time and counts to a file
        write_results_to_file("stress_test_results_mixed.txt", results, NUM_WORKERS, NUM_ITERATIONS)

    except Exception as e:
        print(f"Error in main: {e}")
