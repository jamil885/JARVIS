package httpapi

import (
	"context"
	"encoding/json"
	"net/http"
)

func contextWithID(r *http.Request, id string) context.Context {
	return context.WithValue(r.Context(), requestIDKey{}, id)
}

func writeJSON(w http.ResponseWriter, status int, body any) {
	w.Header().Set("Content-Type", "application/json")
	w.WriteHeader(status)
	_ = json.NewEncoder(w).Encode(body)
}
