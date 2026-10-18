package main

import (
	"log"
	"net/http"
	"os"
	"time"

	"github.com/jamil885/JARVIS/internal/httpapi"
)

func main() {
	addr := os.Getenv("JARVIS_LISTEN_ADDR")
	if addr == "" {
		addr = "127.0.0.1:8080"
	}
	server := &http.Server{
		Addr:              addr,
		Handler:           httpapi.NewHandler(nil),
		ReadHeaderTimeout: 5 * time.Second,
	}
	log.Printf("jarvis core listening on %s", addr)
	log.Fatal(server.ListenAndServe())
}
