// mautrix-signal - A Matrix-signal puppeting bridge.
// Copyright (C) 2023 Scott Weber
//
// This program is free software: you can redistribute it and/or modify
// it under the terms of the GNU Affero General Public License as published by
// the Free Software Foundation, either version 3 of the License, or
// (at your option) any later version.
//
// This program is distributed in the hope that it will be useful,
// but WITHOUT ANY WARRANTY; without even the implied warranty of
// MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
// GNU Affero General Public License for more details.
//
// You should have received a copy of the GNU Affero General Public License
// along with this program.  If not, see <https://www.gnu.org/licenses/>.

package web

import (
	"bytes"
	"context"
	"crypto/tls"
	"crypto/x509"
	_ "embed"
	"encoding/json"
	"fmt"
	"io"
	"net/http"
	"net/url"
	"os"
	"runtime"
	"strings"

	"github.com/rs/zerolog"

	"go.mau.fi/mautrix-signal/pkg/libsignalgo"
)

const proxyUrlStr = "" // Set this to proxy requests
const caCertPath = ""  // Set this to trust a self-signed cert (ie. for mitmproxy)

var UserAgent = "signalmeow/0.1.0 libsignal/" + libsignalgo.Version + " go/" + strings.TrimPrefix(runtime.Version(), "go")
var SignalAgent = "MAU"

const (
	APIHostname     = "chat.signal.org"
	StorageHostname = "storage.signal.org"
	CDN1Hostname    = "cdn.signal.org"
	CDN2Hostname    = "cdn2.signal.org"
	CDN3Hostname    = "cdn3.signal.org"
)

var CDNHosts = []string{
	CDN1Hostname,
	CDN1Hostname,
	CDN2Hostname,
	CDN3Hostname,
}

//go:embed signal-root.crt.der
var signalRootCertBytes []byte
var signalTransport = &http.Transport{
	ForceAttemptHTTP2: true,
	TLSClientConfig: &tls.Config{
		RootCAs: x509.NewCertPool(),
	},
}
var SignalHTTPClient = &http.Client{
	Transport: signalTransport,
}

func init() {
	cert, err := x509.ParseCertificate(signalRootCertBytes)
	if err != nil {
		panic(err)
	}
	signalTransport.TLSClientConfig.RootCAs.AddCert(cert)

	if proxyUrlStr != "" {
		proxyURL, err := url.Parse(proxyUrlStr)
		if err != nil {
			panic(err)
		}
		signalTransport.Proxy = http.ProxyURL(proxyURL)
	}
	if caCertPath != "" {
		caCert, err := os.ReadFile(caCertPath)
		if err != nil {
			panic(err)
		}
		signalTransport.TLSClientConfig.RootCAs.AppendCertsFromPEM(caCert)
	}
}

type ContentType string

const (
	ContentTypeJSON              ContentType = "application/json"
	ContentTypeProtobuf          ContentType = "application/x-protobuf"
	ContentTypeOctetStream       ContentType = "application/octet-stream"
	ContentTypeOffsetOctetStream ContentType = "application/offset+octet-stream"
)

type HTTPReqOpt struct {
	Body        []byte
	Username    *string
	Password    *string
	ContentType ContentType
	Host        string
	Headers     map[string]string
	OverrideURL string // Override the full URL, if set ignores path and Host
}

var httpReqCounter = 0

func SendHTTPRequest(ctx context.Context, method string, path string, opt *HTTPReqOpt) (*http.Response, error) {
	// Set defaults
	if opt == nil {
		opt = &HTTPReqOpt{}
	}
	if opt.Host == "" {
		opt.Host = APIHostname
	}
	if len(path) > 0 && path[0] != '/' {
		path = "/" + path
	}
	urlStr := "https://" + opt.Host + path
	if opt.OverrideURL != "" {
		urlStr = opt.OverrideURL
	}
	log := zerolog.Ctx(ctx).With().
		Str("action", "send HTTP request").
		Str("method", method).
		Str("url", urlStr).
		Logger()
	ctx = log.WithContext(ctx)

	req, err := http.NewRequestWithContext(ctx, method, urlStr, bytes.NewReader(opt.Body))
	if err != nil {
		log.Err(err).Msg("Error creating request")
		return nil, err
	}
	if opt.Headers != nil {
		for k, v := range opt.Headers {
			req.Header.Add(k, v)
		}
	}
	if opt.ContentType != "" {
		req.Header.Set("Content-Type", string(opt.ContentType))
	} else {
		req.Header.Set("Content-Type", string(ContentTypeJSON))
	}
	req.Header.Set("Content-Length", fmt.Sprintf("%d", len(opt.Body)))
	req.Header.Set("User-Agent", UserAgent)
	req.Header.Set("X-Signal-Agent", SignalAgent)
	if opt.Username != nil && opt.Password != nil {
		req.SetBasicAuth(*opt.Username, *opt.Password)
	}

	httpReqCounter++
	log = log.With().Int("request_number", httpReqCounter).Logger()
	log.Trace().Msg("Sending HTTP request")
	resp, err := SignalHTTPClient.Do(req)
	if err != nil {
		log.Err(err).Msg("Error sending request")
		return nil, err
	}
	log.Debug().Int("status_code", resp.StatusCode).Msg("received HTTP response")
	return resp, nil
}

// DecodeHTTPResponseBody checks status code, reads an http.Response's Body and decodes it into the provided interface.
func DecodeHTTPResponseBody(ctx context.Context, out any, resp *http.Response) error {
	defer resp.Body.Close()

	// Check if status code indicates success
	if resp.StatusCode < 200 || resp.StatusCode >= 300 {
		// Read the whole body and log it
		body, _ := io.ReadAll(resp.Body)
		zerolog.Ctx(ctx).Debug().
			Str("body", string(body)).
			Int("status_code", resp.StatusCode).
			Msg("unexpected status code")
		return fmt.Errorf("Unexpected status code: %d %s", resp.StatusCode, resp.Status)
	}

	decoder := json.NewDecoder(resp.Body)
	if err := decoder.Decode(&out); err != nil {
		return fmt.Errorf("JSON decoding failed: %w", err)
	}

	return nil
}

func GetAttachment(ctx context.Context, path string, cdnNumber uint32, opt *HTTPReqOpt) (*http.Response, error) {
	log := zerolog.Ctx(ctx).With().
		Str("action", "get_attachment").
		Str("path", path).
		Uint32("cdn_number", cdnNumber).
		Logger()
	if opt == nil {
		opt = &HTTPReqOpt{}
	}
	if opt.Host == "" {
		if int(cdnNumber) > len(CDNHosts) {
			log.Warn().Msg("Invalid CDN index")
			opt.Host = CDN1Hostname
		} else {
			opt.Host = CDNHosts[cdnNumber]
		}
		if cdnNumber == 0 {
			// This is basically a fallback if cdnNumber is not set
			// but it also seems to be the right host if cdnNumber == 0
			opt.Host = CDNHosts[0]
		} else if cdnNumber > 0 && int(cdnNumber) <= len(CDNHosts) {
			// Pull CDN hosts from array (cdnNumber is 1-indexed, but we have a placeholder host at index 0)
			// (the 1-indexed is just an assumption, other clients seem to only explicitly handle cdnNumber == 0 and 2)
			opt.Host = CDNHosts[cdnNumber]
		} else {
			opt.Host = CDNHosts[0]
			log.Warn().Msg("Invalid CDN index")
		}
	}
	log.Debug().Str("host", opt.Host).Msg("getting attachment")
	urlStr := "https://" + opt.Host + path
	req, err := http.NewRequest(http.MethodGet, urlStr, nil)
	if err != nil {
		return nil, err
	}

	//const SERVICE_REFLECTOR_HOST = "europe-west1-signal-cdn-reflector.cloudfunctions.net"
	//req.Header.Add("Host", SERVICE_REFLECTOR_HOST)
	req.Header.Add("Content-Type", "application/octet-stream")
	req.Header.Set("User-Agent", UserAgent)

	httpReqCounter++
	log = log.With().
		Int("request_number", httpReqCounter).
		Str("url", urlStr).
		Logger()

	log.Debug().Msg("Sending Attachment HTTP request")
	resp, err := SignalHTTPClient.Do(req)
	if err != nil {
		return nil, err
	}
	log.Debug().
		Int("status_code", resp.StatusCode).
		Int64("content_length", resp.ContentLength).
		Msg("Received Attachment HTTP response")

	return resp, err
}
