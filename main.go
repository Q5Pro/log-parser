// log-parser: Nginx/Apache/syslog formatındaki log dosyalarını ayrıştırır,
// istatistik üretir ve filtreli çıktı verir.
//
// Kullanım:
//   log-parser nginx.log
//   log-parser --filter 404 nginx.log
//   log-parser --stats nginx.log
//   log-parser --top-ips 10 nginx.log
package main

import (
	"bufio"
	"fmt"
	"os"
	"regexp"
	"sort"
	"strconv"
	"strings"
)

type Entry struct {
	IP     string
	Status int
	Size   int
	Method string
	Path   string
	Line   string
}

var nginxRe = regexp.MustCompile(`^(\S+) - \S+ \[[^\]]+\] "(\S+) (\S+)[^"]*" (\d+) (\d+)`)

func parse(line string) *Entry {
	m := nginxRe.FindStringSubmatch(line)
	if m == nil {
		return &Entry{Line: line, Status: 0}
	}
	status, _ := strconv.Atoi(m[4])
	size, _ := strconv.Atoi(m[5])
	return &Entry{IP: m[1], Method: m[2], Path: m[3], Status: status, Size: size, Line: line}
}

func main() {
	var filter string
	var topIPs bool
	var topN = 10
	var statsOnly bool
	var files []string

	args := os.Args[1:]
	for i := 0; i < len(args); i++ {
		switch args[i] {
		case "--filter":
			if i+1 < len(args) { filter = args[i+1]; i++ }
		case "--stats":
			statsOnly = true
		case "--top-ips":
			topIPs = true
			if i+1 < len(args) { topN, _ = strconv.Atoi(args[i+1]); i++ }
		default:
			files = append(files, args[i])
		}
	}

	if len(files) == 0 {
		fmt.Fprintln(os.Stderr, "Kullanım: log-parser [--filter KOD] [--stats] [--top-ips N] <dosya...>")
		os.Exit(1)
	}

	var entries []*Entry
	for _, f := range files {
		fh, err := os.Open(f)
		if err != nil { fmt.Fprintln(os.Stderr, err); continue }
		sc := bufio.NewScanner(fh)
		for sc.Scan() { entries = append(entries, parse(sc.Text())) }
		fh.Close()
	}

	if statsOnly || topIPs {
		statusCnt := map[int]int{}
		ipCnt := map[string]int{}
		total := 0
		for _, e := range entries {
			total++
			statusCnt[e.Status]++
			if e.IP != "" { ipCnt[e.IP]++ }
		}
		fmt.Printf("Toplam satır: %d\n\nDurum kodları:\n", total)
		type kv struct{ k int; v int }
		var sc []kv
		for k,v := range statusCnt { sc = append(sc, kv{k,v}) }
		sort.Slice(sc, func(i,j int) bool { return sc[i].v > sc[j].v })
		for _, kv := range sc { fmt.Printf("  %d: %d\n", kv.k, kv.v) }

		if topIPs {
			type sv struct{ s string; v int }
			var ip []sv
			for k,v := range ipCnt { ip = append(ip, sv{k,v}) }
			sort.Slice(ip, func(i,j int) bool { return ip[i].v > ip[j].v })
			fmt.Printf("\nEn Fazla İstek Yapan %d IP:\n", topN)
			for i, kv := range ip {
				if i >= topN { break }
				fmt.Printf("  %-20s %d istek\n", kv.s, kv.v)
			}
		}
		return
	}

	for _, e := range entries {
		if filter != "" && !strings.Contains(strconv.Itoa(e.Status), filter) && !strings.Contains(e.Line, filter) {
			continue
		}
		fmt.Println(e.Line)
	}
}
