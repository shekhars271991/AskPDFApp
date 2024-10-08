import numpy as np
import time
import redis
import concurrent.futures
from sentence_transformers import SentenceTransformer
from redis.commands.search.query import Query
import json
from tabulate import tabulate


# Number of concurrent requests
NUM_WORKERS = 320

# Number of iterations per worker
NUM_ITERATIONS = 50

# REDIS_HOST = 'localhost'
# REDIS_PORT = 6379
# REDIS_DB = 0

# # cloud - QPS1
# REDIS_HOST="redis-18217.c32732.ap-south-1-mz.ec2.cloud.rlrcp.com"
# REDIS_PORT=18217
# REDIS_PASSWORD="98BJB7EgQTR4HoWsLWzcEJPgv0EwAVgm"
# REDIS_DB = 0



# cloud - QPS8
REDIS_HOST="redis-12961.c32734.ap-south-1-mz.ec2.cloud.rlrcp.com"
REDIS_PORT=12961
REDIS_PASSWORD="chuHwnfJ7lSiynWAhX2BrZSOTG0CamMv"
REDIS_DB = 0



SUMMARY_INDEX_NAME = "idxsumm"
QUERY = "tell me some details about trigovex company"

model = SentenceTransformer('all-MiniLM-L6-v2')

redis_client = redis.Redis(
    host=REDIS_HOST,
    port=REDIS_PORT,
    db=REDIS_DB,
)

redis_client = redis.Redis(
    host=REDIS_HOST,
    port=REDIS_PORT,
    db=REDIS_DB,
    password=REDIS_PASSWORD
)

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

        response_time = (end_time - start_time) * 1000  # Convert to milliseconds

        related_docs = []
        for doc in results.docs:
            if float(doc.vector_score) <= 0.8:
                roles = json.loads(doc.roles)
                related_docs.append({'id': doc.id, 'roles': roles[0]})

        return related_docs, response_time

    except Exception as e:
        print(f"Error in perform_vector_search_for_documents: {e}")
        return [], 0

def stress_test_worker(worker_id):
    total_response_time = 0
    worker_start_time = time.time()

    for _ in range(NUM_ITERATIONS):
        try:
            query_embedding = get_embeddings(QUERY)
            if query_embedding is None:
                continue

            roles = ["admin", "user"]
            _, response_time = perform_vector_search_for_documents(query_embedding, roles)
            total_response_time += response_time
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
        "Average Response Time (ms)": f"{average_response_time:.2f} ms"
    }

def write_results_to_file(filename, results, num_workers, num_iterations):
    try:
        # Calculate the overall average response time
        total_response_time = sum(float(result["Average Response Time (ms)"].split()[0]) for result in results)
        overall_average_response_time = total_response_time / len(results)

        # Write the results to the file
        with open(filename, "a") as f:
            f.write(f"Workers: {num_workers}, Iterations per worker: {num_iterations}, "
                    f"Overall Average Response Time (ms): {overall_average_response_time:.2f} ms\n")

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

        # Write the overall average response time to a file
        write_results_to_file("stress_test_results.txt", results, NUM_WORKERS, NUM_ITERATIONS)

    except Exception as e:
        print(f"Error in main: {e}")
