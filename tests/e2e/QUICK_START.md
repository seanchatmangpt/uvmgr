# uvmgr Dogfooding E2E Test - Quick Start

## 🚀 Run the Complete Dogfooding Loop

```bash
# Option 1: Using the shell script (recommended)
./tests/e2e/dogfood.sh

# Option 2: Using uvmgr itself (true dogfooding!)
uvmgr run python tests/e2e/run_dogfood_loop.py

# Option 3: Run all e2e tests
uvmgr tests run tests/e2e/ -v
```

## 🧪 What Gets Tested

The dogfooding loop tests uvmgr using its own commands:

1. **Self-Testing**: uvmgr runs its own test suite
2. **Self-Building**: uvmgr builds its own wheel
3. **Full Cycle**: init → deps → test → lint → build
4. **Recursive Calls**: uvmgr calling uvmgr
5. **Performance**: Command execution benchmarks
6. **Error Recovery**: Graceful failure handling

## 📊 Results

After running, you'll find:
- `dogfood_report.json` - Detailed test results
- Performance metrics and timings
- Pass/fail status for each test

## 🎯 Success Criteria

✅ All commands work when called by uvmgr itself  
✅ No significant performance overhead  
✅ 100% pass rate in self-tests  
✅ Graceful error handling  

## 🐕 True Dogfooding

This is meta-testing at its finest - uvmgr testing itself with its own commands!