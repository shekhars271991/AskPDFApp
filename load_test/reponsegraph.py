import matplotlib.pyplot as plt

# Data for QPS 8
workers = [1, 8, 16, 32, 64, 128, 256]
response_time_qps8 = [305.41, 333.28, 351.59, 446.58, 590.37, 942.87, 1673.89]

# Data for QPS 1
response_time_qps1 = [284.30, 339.03, 352.32, 411.62, 591.16, 956.79, 1702.22]

# Plotting the data
plt.figure(figsize=(10, 6))
plt.plot(workers, response_time_qps8, marker='o', label='QPS 8')
plt.plot(workers, response_time_qps1, marker='o', label='QPS 1')

plt.xlabel('Number of Workers')
plt.ylabel('Overall Average Response Time (ms)')
plt.title('Overall Average Response Time vs Number of Workers')
plt.xticks(workers)
plt.legend()
plt.grid(True)
plt.show()