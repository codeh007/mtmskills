package release

import (
	"bufio"
	"crypto/sha256"
	"encoding/hex"
	"fmt"
	"io"
	"os"
	"strings"
)

func VerifyChecksum(filePath, checksumPath string) error {
	expected, err := readExpectedChecksum(checksumPath)
	if err != nil {
		return err
	}
	actual, err := FileSHA256(filePath)
	if err != nil {
		return err
	}
	if !strings.EqualFold(expected, actual) {
		return fmt.Errorf("checksum mismatch: expected %s, got %s", expected, actual)
	}
	return nil
}

func FileSHA256(filePath string) (string, error) {
	file, err := os.Open(filePath)
	if err != nil {
		return "", err
	}
	defer file.Close()

	hash := sha256.New()
	if _, err := io.Copy(hash, file); err != nil {
		return "", err
	}
	return hex.EncodeToString(hash.Sum(nil)), nil
}

func readExpectedChecksum(checksumPath string) (string, error) {
	file, err := os.Open(checksumPath)
	if err != nil {
		return "", err
	}
	defer file.Close()

	scanner := bufio.NewScanner(file)
	if !scanner.Scan() {
		if err := scanner.Err(); err != nil {
			return "", err
		}
		return "", fmt.Errorf("checksum file is empty")
	}
	fields := strings.Fields(scanner.Text())
	if len(fields) == 0 {
		return "", fmt.Errorf("checksum file is empty")
	}
	checksum := strings.TrimSpace(fields[0])
	if len(checksum) != sha256.Size*2 {
		return "", fmt.Errorf("invalid sha256 checksum length: %d", len(checksum))
	}
	return checksum, nil
}
