package main

import (
	"encoding/json"
	"errors"
	"flag"
	"fmt"
	"os"
	"path/filepath"
	"sort"
	"strings"
)

var (
	version = "0.1.0-dev"
	commit  = "unknown"
	date    = "unknown"
)

type carryRef struct {
	APIVersion string `json:"apiVersion"`
	Kind       string `json:"kind"`
	Metadata   struct {
		Name    string `json:"name"`
		Version string `json:"version"`
	} `json:"metadata"`
	Spec struct {
		Surface    string `json:"surface"`
		ServiceRef string `json:"serviceRef"`
		Client     struct {
			PackageRef string `json:"packageRef"`
			Entrypoint string `json:"entrypoint"`
			Protocol   string `json:"protocol"`
		} `json:"client"`
		Launch struct {
			WorkspaceScopes []string `json:"workspaceScopes"`
			DefaultMode     string   `json:"defaultMode"`
			RequiresNetwork bool     `json:"requiresNetwork"`
		} `json:"launch"`
		Cache struct {
			Mode     string `json:"mode"`
			MaxBytes int64  `json:"maxBytes"`
			PathHint string `json:"pathHint"`
		} `json:"cache"`
		Policy struct {
			PolicyRef                string   `json:"policyRef"`
			RequiresSignedServiceRef bool     `json:"requiresSignedServiceRef"`
			DataClasses              []string `json:"dataClasses"`
		} `json:"policy"`
		Evidence struct {
			EmitInvocationReceipt bool   `json:"emitInvocationReceipt"`
			EmitPolicyCheck       bool   `json:"emitPolicyCheck"`
			ReceiptSink           string `json:"receiptSink"`
		} `json:"evidence"`
		Authority struct {
			SourceOSRole              string `json:"sourceosRole"`
			PlatformPromotionRequired bool   `json:"platformPromotionRequired"`
			MayReplaceServiceArtifact bool   `json:"mayReplaceServiceArtifact"`
		} `json:"authority"`
	} `json:"spec"`
}

type validationResult struct {
	Path    string   `json:"path"`
	Name    string   `json:"name,omitempty"`
	Surface string   `json:"surface,omitempty"`
	Status  string   `json:"status"`
	Errors  []string `json:"errors,omitempty"`
}

type evidence struct {
	Tool       string             `json:"tool"`
	Version    string             `json:"version"`
	Commit     string             `json:"commit"`
	BuildDate  string             `json:"buildDate"`
	Repo       string             `json:"repo"`
	Status     string             `json:"status"`
	Results    []validationResult `json:"results,omitempty"`
	ServiceRef []string           `json:"serviceRefs,omitempty"`
}

func usage() {
	fmt.Fprintf(os.Stderr, `sourceos-ai %s

Usage:
  sourceos-ai --version
  sourceos-ai doctor [--refs examples]
  sourceos-ai list [--refs examples]
  sourceos-ai validate [--refs examples]
  sourceos-ai self-test [--refs examples]
  sourceos-ai emit-evidence [--refs examples]
  sourceos-ai carry list [--refs examples]
  sourceos-ai carry validate [--refs examples]
  sourceos-ai carry doctor [--refs examples]

`, version)
}

func main() {
	if len(os.Args) == 1 {
		usage()
		os.Exit(2)
	}
	if os.Args[1] == "--version" || os.Args[1] == "version" {
		fmt.Printf("sourceos-ai %s commit=%s date=%s\n", version, commit, date)
		return
	}

	cmd := os.Args[1]
	switch cmd {
	case "doctor":
		refs := parseRefs(os.Args[2:])
		runDoctor(refs)
	case "list":
		refs := parseRefs(os.Args[2:])
		runList(refs)
	case "validate":
		refs := parseRefs(os.Args[2:])
		results := validateDir(refs)
		printJSON(results)
		if hasFailures(results) {
			os.Exit(1)
		}
	case "self-test":
		refs := parseRefs(os.Args[2:])
		runSelfTest(refs)
	case "emit-evidence":
		refs := parseRefs(os.Args[2:])
		runEvidence(refs)
	case "carry":
		runCarry(os.Args[2:])
	default:
		usage()
		os.Exit(2)
	}
}

func parseRefs(args []string) string {
	fs := flag.NewFlagSet("refs", flag.ExitOnError)
	refs := fs.String("refs", "examples", "directory containing *-carry-ref.json files")
	_ = fs.Parse(args)
	return *refs
}

func runCarry(args []string) {
	if len(args) == 0 {
		usage()
		os.Exit(2)
	}
	sub := args[0]
	refs := parseRefs(args[1:])
	switch sub {
	case "list":
		runList(refs)
	case "validate":
		results := validateDir(refs)
		printJSON(results)
		if hasFailures(results) {
			os.Exit(1)
		}
	case "doctor":
		runDoctor(refs)
	default:
		usage()
		os.Exit(2)
	}
}

func runList(refDir string) {
	refs, results := loadRefs(refDir)
	if hasFailures(results) {
		printJSON(results)
		os.Exit(1)
	}
	sort.Slice(refs, func(i, j int) bool { return refs[i].Metadata.Name < refs[j].Metadata.Name })
	items := make([]map[string]any, 0, len(refs))
	for _, ref := range refs {
		items = append(items, map[string]any{
			"name":       ref.Metadata.Name,
			"version":    ref.Metadata.Version,
			"surface":    ref.Spec.Surface,
			"serviceRef": ref.Spec.ServiceRef,
			"mode":       ref.Spec.Launch.DefaultMode,
			"authority":  ref.Spec.Authority.SourceOSRole,
		})
	}
	printJSON(map[string]any{"status": "ok", "count": len(items), "items": items})
}

func runDoctor(refDir string) {
	results := validateDir(refDir)
	status := "ok"
	if hasFailures(results) {
		status = "failed"
	}
	printJSON(map[string]any{
		"tool":    "sourceos-ai",
		"version": version,
		"status":  status,
		"checks":  results,
	})
	if status != "ok" {
		os.Exit(1)
	}
}

func runSelfTest(refDir string) {
	results := validateDir(refDir)
	status := "ok"
	if hasFailures(results) {
		status = "failed"
	}
	printJSON(map[string]any{"tool": "sourceos-ai", "selfTest": status, "validatedRefs": len(results)})
	if status != "ok" {
		os.Exit(1)
	}
}

func runEvidence(refDir string) {
	refs, results := loadRefs(refDir)
	status := "ok"
	if hasFailures(results) {
		status = "failed"
	}
	serviceRefs := make([]string, 0, len(refs))
	for _, ref := range refs {
		serviceRefs = append(serviceRefs, ref.Spec.ServiceRef)
	}
	sort.Strings(serviceRefs)
	printJSON(evidence{
		Tool:       "sourceos-ai",
		Version:    version,
		Commit:     commit,
		BuildDate:  date,
		Repo:       "SourceOS-Linux/sourceos-model-carry",
		Status:     status,
		Results:    results,
		ServiceRef: serviceRefs,
	})
	if status != "ok" {
		os.Exit(1)
	}
}

func validateDir(refDir string) []validationResult {
	_, results := loadRefs(refDir)
	return results
}

func loadRefs(refDir string) ([]carryRef, []validationResult) {
	paths, err := filepath.Glob(filepath.Join(refDir, "*-carry-ref.json"))
	if err != nil {
		return nil, []validationResult{{Path: refDir, Status: "failed", Errors: []string{err.Error()}}}
	}
	sort.Strings(paths)
	if len(paths) == 0 {
		return nil, []validationResult{{Path: refDir, Status: "failed", Errors: []string{"no *-carry-ref.json files found"}}}
	}
	refs := make([]carryRef, 0, len(paths))
	results := make([]validationResult, 0, len(paths))
	for _, path := range paths {
		ref, errs := loadRef(path)
		result := validationResult{Path: path, Name: ref.Metadata.Name, Surface: ref.Spec.Surface, Status: "ok"}
		if len(errs) > 0 {
			result.Status = "failed"
			result.Errors = errs
		} else {
			refs = append(refs, ref)
		}
		results = append(results, result)
	}
	return refs, results
}

func loadRef(path string) (carryRef, []string) {
	var ref carryRef
	bytes, err := os.ReadFile(path)
	if err != nil {
		return ref, []string{err.Error()}
	}
	if err := json.Unmarshal(bytes, &ref); err != nil {
		return ref, []string{err.Error()}
	}
	return ref, validateRef(ref)
}

func validateRef(ref carryRef) []string {
	var errs []string
	check := func(cond bool, msg string) {
		if !cond {
			errs = append(errs, msg)
		}
	}
	check(ref.APIVersion == "modelcarry.sourceos.dev/v1", "apiVersion must be modelcarry.sourceos.dev/v1")
	check(ref.Kind == "SourceOSCarryRef", "kind must be SourceOSCarryRef")
	check(ref.Metadata.Name != "", "metadata.name is required")
	check(ref.Metadata.Version != "", "metadata.version is required")
	check(ref.Spec.Surface != "", "spec.surface is required")
	check(strings.HasPrefix(ref.Spec.ServiceRef, "service://"), "spec.serviceRef must start with service://")
	check(ref.Spec.Client.PackageRef != "", "spec.client.packageRef is required")
	check(ref.Spec.Client.Entrypoint != "", "spec.client.entrypoint is required")
	check(ref.Spec.Policy.RequiresSignedServiceRef, "spec.policy.requiresSignedServiceRef must be true")
	check(ref.Spec.Authority.SourceOSRole == "carry-only", "spec.authority.sourceosRole must be carry-only")
	check(ref.Spec.Authority.PlatformPromotionRequired, "spec.authority.platformPromotionRequired must be true")
	check(!ref.Spec.Authority.MayReplaceServiceArtifact, "spec.authority.mayReplaceServiceArtifact must be false")
	for _, scope := range ref.Spec.Launch.WorkspaceScopes {
		check(scope != "system", "system workspace is not an allowed AI carry invocation scope")
	}
	return errs
}

func hasFailures(results []validationResult) bool {
	for _, result := range results {
		if result.Status != "ok" {
			return true
		}
	}
	return false
}

func printJSON(value any) {
	enc := json.NewEncoder(os.Stdout)
	enc.SetIndent("", "  ")
	if err := enc.Encode(value); err != nil {
		panic(errors.New("failed to encode JSON: " + err.Error()))
	}
}
