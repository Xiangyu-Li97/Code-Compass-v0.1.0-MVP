#!/bin/bash

cd "$(dirname "$0")"

echo "=========================================="
echo "Running All Tests"
echo "=========================================="
echo ""

FAILED=0

for test_file in tests/test_*.py; do
    test_name=$(basename "$test_file")
    echo "▶ Running $test_name..."
    
    if python3 "$test_file" > /tmp/test_output.txt 2>&1; then
        echo "  ✅ PASSED"
    else
        echo "  ❌ FAILED"
        cat /tmp/test_output.txt
        FAILED=1
    fi
    echo ""
done

echo "=========================================="
if [ $FAILED -eq 0 ]; then
    echo "✅ All tests passed!"
else
    echo "❌ Some tests failed!"
    exit 1
fi
echo "=========================================="
