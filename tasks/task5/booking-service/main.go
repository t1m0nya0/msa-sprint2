package main

import (
	"fmt"
	"log"
	"net/http"
	"os"
)

func main() {
	enableFeatureX := os.Getenv("ENABLE_FEATURE_X") == "true"
	version := os.Getenv("VERSION")
	if version == "" {
		version = "v1"
	}
	failHealth := os.Getenv("FAIL_HEALTH") == "true"

	http.HandleFunc("/ping", func(w http.ResponseWriter, r *http.Request) {
		if failHealth {
			http.Error(w, "unhealthy", http.StatusInternalServerError)
			return
		}
		if version == "v2" && r.Header.Get("X-Feature-Enabled") == "true" {
			fmt.Fprint(w, "pong-v2-feature")
			return
		}
		if version == "v2" {
			fmt.Fprintf(w, "pong-%s", version)
			return
		}
		fmt.Fprint(w, "pong")
	})

	http.HandleFunc("/ready", func(w http.ResponseWriter, r *http.Request) {
		if failHealth {
			http.Error(w, "not ready", http.StatusServiceUnavailable)
			return
		}
		fmt.Fprint(w, "ready")
	})

	if enableFeatureX {
		http.HandleFunc("/feature", func(w http.ResponseWriter, r *http.Request) {
			fmt.Fprint(w, "Feature X is enabled!")
		})
	}

	log.Printf("booking-service %s listening on :8080 (featureX=%v)", version, enableFeatureX)
	log.Fatal(http.ListenAndServe(":8080", nil))
}
