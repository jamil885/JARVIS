package httpapi

import (
	"encoding/json"
	"errors"
	"net/http"
	"net/http/httptest"
	"testing"
)

func TestLive(t *testing.T) {
	response := httptest.NewRecorder()
	NewHandler(nil).ServeHTTP(response, httptest.NewRequest(http.MethodGet, "/api/v1/health/live", nil))
	if response.Code != http.StatusOK {
		t.Fatalf("status = %d", response.Code)
	}
	if response.Header().Get("X-Request-ID") == "" {
		t.Fatal("missing request ID")
	}
	var body map[string]string
	if err := json.Unmarshal(response.Body.Bytes(), &body); err != nil {
		t.Fatal(err)
	}
	if body["status"] != "alive" {
		t.Fatalf("unexpected body: %v", body)
	}
}

func TestReadinessFailsClosed(t *testing.T) {
	for _, ready := range []Readiness{nil, func() error { return errors.New("down") }} {
		response := httptest.NewRecorder()
		NewHandler(ready).ServeHTTP(response, httptest.NewRequest(http.MethodGet, "/api/v1/health/ready", nil))
		if response.Code != http.StatusServiceUnavailable {
			t.Fatalf("status = %d", response.Code)
		}
		var body struct {
			Error struct {
				Code      string `json:"code"`
				RequestID string `json:"request_id"`
			} `json:"error"`
		}
		if err := json.Unmarshal(response.Body.Bytes(), &body); err != nil {
			t.Fatal(err)
		}
		if body.Error.Code != "DEPENDENCY_NOT_READY" || body.Error.RequestID != response.Header().Get("X-Request-ID") {
			t.Fatalf("unexpected error: %v", body)
		}
	}
}

func TestReadinessSucceeds(t *testing.T) {
	response := httptest.NewRecorder()
	NewHandler(func() error { return nil }).ServeHTTP(response, httptest.NewRequest(http.MethodGet, "/api/v1/health/ready", nil))
	if response.Code != http.StatusOK {
		t.Fatalf("status = %d", response.Code)
	}
}
