// Package httpapi provides the initial HTTP surface of the JARVIS Go core.
// The Go core is not yet a replacement for the persistent Python sessions API.
package httpapi

import (
	"crypto/rand"
	"encoding/hex"
	"encoding/json"
	"net/http"
)

// Readiness is injected to make dependency checks testable without PostgreSQL.
type Readiness func() error

type errorDetail struct {
	Code      string `json:"code"`
	Message   string `json:"message"`
	RequestID string `json:"request_id"`
	Retryable bool   `json:"retryable"`
}

func NewHandler(ready Readiness) http.Handler {
	mux := http.NewServeMux()
	mux.HandleFunc("GET /api/v1/health/live", func(w http.ResponseWriter, r *http.Request) {
		writeJSON(w, http.StatusOK, map[string]string{"status": "alive", "service": "jarvis-core"})
	})
	mux.HandleFunc("GET /api/v1/health/ready", func(w http.ResponseWriter, r *http.Request) {
		if ready == nil || ready() != nil {
			id, _ := r.Context().Value(requestIDKey{}).(string)
			writeJSON(w, http.StatusServiceUnavailable, map[string]any{
				"error": errorDetail{
					Code: "DEPENDENCY_NOT_READY", Message: "Core dependencies are not configured",
					RequestID: id, Retryable: true,
				},
			})
			return
		}
		writeJSON(w, http.StatusOK, map[string]string{"status": "ready", "service": "jarvis-core"})
	})
	return requestIDMiddleware(mux)
}

type requestIDKey struct{}

func requestIDMiddleware(next http.Handler) http.Handler {
	return http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		var entropy [16]byte
		if _, err := rand.Read(entropy[:]); err != nil {
			http.Error(w, "Internal server error", http.StatusInternalServerError)
			return
		}
		id := hex.EncodeToString(entropy[:])
		w.Header().Set("X-Request-ID", id)
		next.ServeHTTP(w, r.WithContext(contextWithID(r, id)))
	})
}
