package main

import (
	"context"
	"encoding/json"
	"fmt"
	"math/rand"
	"sync"
	"time"

	"github.com/go-redis/redis/v8"
	"github.com/google/uuid"
)

// const (
// 	numWorkers       = 1
// 	numIterations    = 1
// 	redisHost        = "redis-18217.c32732.ap-south-1-mz.ec2.cloud.rlrcp.com"
// 	redisPort        = "18217"
// 	redisPassword    = "98BJB7EgQTR4HoWsLWzcEJPgv0EwAVgm"
// 	summaryIndexName = "idxsumm"
// 	query            = "tell me some details about trigovex company"
// )

const (
	numWorkers       = 256
	numIterations    = 50
	redisHost        = "localhost"
	redisPort        = "6379"
	summaryIndexName = "idxsumm"
	query            = "tell me some details about trigovex company"
)

var rdb *redis.Client

func init() {
	rdb = redis.NewClient(&redis.Options{
		Addr: fmt.Sprintf("%s:%s", redisHost, redisPort),
		// Password: redisPassword,
		DB: 0,
	})
}

func generateRandomString(length int) string {
	const charset = "abcdefghijklmnopqrstuvwxyz0123456789"
	seededRand := rand.New(rand.NewSource(time.Now().UnixNano()))
	b := make([]byte, length)
	for i := range b {
		b[i] = charset[seededRand.Intn(len(charset))]
	}
	return string(b)
}

func storeFileMetadata(docName, originalFilename, uploadTime string, roles []string, summary string, summaryEmbeddings []float32) {
	metadataKey := fmt.Sprintf("file_%s_metadata", docName)
	metadata := map[string]interface{}{
		"uploaded_time":      uploadTime,
		"original_filename":  originalFilename,
		"unique_filename":    docName,
		"roles":              roles,
		"summary":            summary,
		"summary_embeddings": summaryEmbeddings,
	}
	data, _ := json.Marshal(metadata)
	rdb.Set(context.Background(), metadataKey, data, 0)
}

func simulateUploadPDF() float64 {
	docName := generateRandomString(8)
	originalFilename := fmt.Sprintf("%s.pdf", docName)
	uploadTime := time.Now().Format("2006-01-02 15:04:05")
	roles := []string{"admin", "user"}
	summary := "Geopolitical forecasting tournaments have become increasingly popular..."
	summaryEmbeddings := make([]float32, 384) // Simulate embeddings

	startTime := time.Now()
	storeFileMetadata(docName, originalFilename, uploadTime, roles, summary, summaryEmbeddings)
	return time.Since(startTime).Seconds() * 1000
}

func performVectorSearchForDocuments(queryEmbedding []float32, roles []string) (float64, int) {
	vectorKey := uuid.New().String() + "_vector"
	roleFilter := ""
	for i, role := range roles {
		if i > 0 {
			roleFilter += " | "
		}
		roleFilter += fmt.Sprintf("@roles:{%s}", role)
	}

	// Store the vector embedding temporarily
	rdb.Set(context.Background(), vectorKey, queryEmbedding, 0)

	q := fmt.Sprintf("(%s)=>[KNN 5 @vector $query_vec AS vector_score]", roleFilter)
	params := map[string]interface{}{"query_vec": queryEmbedding}

	startTime := time.Now()
	rdb.Do(context.Background(), "FT.SEARCH", summaryIndexName, q, "PARAMS", "2", "query_vec", params).Result()
	responseTime := time.Since(startTime).Seconds() * 1000

	return responseTime, 1 // Simulated document count
}

func stressTestWorker(workerID int, wg *sync.WaitGroup, resultsChan chan<- map[string]interface{}) {
	defer wg.Done()
	totalResponseTime := 0.0
	readCount := 0
	writeCount := 0

	for i := 0; i < numIterations; i++ {
		operation := rand.Intn(2)
		if operation == 0 { // read operation
			queryEmbedding := make([]float32, 384) // Simulate embeddings
			responseTime, count := performVectorSearchForDocuments(queryEmbedding, []string{"admin", "user"})
			totalResponseTime += responseTime
			readCount += count
		} else { // write operation
			responseTime := simulateUploadPDF()
			totalResponseTime += responseTime
			writeCount++
		}

		time.Sleep(10 * time.Millisecond)
	}

	averageResponseTime := totalResponseTime / numIterations
	resultsChan <- map[string]interface{}{
		"Worker ID":             workerID,
		"Average Response Time": fmt.Sprintf("%.2f ms", averageResponseTime),
		"Reads":                 readCount,
		"Writes":                writeCount,
	}
}

func main() {
	start := time.Now()
	var wg sync.WaitGroup
	resultsChan := make(chan map[string]interface{}, numWorkers)

	for i := 0; i < numWorkers; i++ {
		wg.Add(1)
		go stressTestWorker(i, &wg, resultsChan)
	}

	wg.Wait()
	close(resultsChan)

	var results []map[string]interface{}
	for result := range resultsChan {
		results = append(results, result)
	}

	end := time.Now()
	fmt.Printf("Stress test completed in %.2f seconds.\n", end.Sub(start).Seconds())

	fmt.Println("Results:")
	for _, result := range results {
		fmt.Printf("Worker ID: %d\n", result["Worker ID"])
		fmt.Printf("Average Response Time: %s\n", result["Average Response Time"])
		fmt.Printf("Reads: %d\n", result["Reads"])
		fmt.Printf("Writes: %d\n", result["Writes"])
		fmt.Println("--------------------------")
	}
}
