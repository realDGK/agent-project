# Document Schema Automation Tools

This document describes the automation tools implemented for validating and managing document type schemas in the Agent Project.

## Overview

The automation suite consists of four main components:
1. **MCP Database Connectivity** - Ensures all databases are accessible
2. **Batch Validation Runner** - Validates all document type schemas
3. **CI/CD Pipeline** - Automated validation on GitHub
4. **Pre-push Hooks** - Local validation before code push

## Part A: MCP Wiring and Smoke Test

### Files
- `docker-compose.mcp.override.yml` - MCP service configuration
- `.env.mcp` - Database connection settings
- `scripts/smoke_mcp.py` - Database connectivity test

### Usage
```bash
# Run the smoke test
python3 scripts/smoke_mcp.py

# Expected output: All 4 databases should connect successfully
# - PostgreSQL ✅
# - Neo4j ✅  
# - Qdrant ✅
# - Redis ✅
```

### Configuration
Edit `.env.mcp` to update database credentials:
```env
POSTGRES_HOST=localhost
POSTGRES_PASSWORD=your_password_here
NEO4J_PASSWORD=your_password_here
# etc...
```

## Part B: Batch Runner CLI

### Purpose
Validates all document type directories for:
- Required `schema_additions.json` files
- Valid JSON syntax
- Proper schema structure
- Optional `few_shot_examples.json` and `specialist_schema.json`

### Usage
```bash
# Validate all document types
python3 scripts/batch_runner.py

# Validate with verbose output
python3 scripts/batch_runner.py --verbose

# Validate specific document types
python3 scripts/batch_runner.py --types bankruptcy-petitions tax-appeals

# Generate detailed report
python3 scripts/batch_runner.py --report validation-report.json

# Stop on first failure
python3 scripts/batch_runner.py --fail-fast
```

### Output
The runner provides:
- ✅ **Passed** - All validations successful
- ⚠️ **Warning** - Non-critical issues (e.g., empty optional files)
- ❌ **Failed** - Critical validation failures

### File Naming Support
The validator supports both naming patterns:
- Standard: `schema_additions.json`
- Legacy numeric: `305_schema_additions.json`

## Part C: GitHub Actions CI

### Workflows
Located in `.github/workflows/validate-schemas.yml`

### Features
1. **Schema Validation Job**
   - Runs on push/PR to main/develop branches
   - Validates all document schemas
   - Uploads validation report as artifact
   - Comments on PR with failure details

2. **MCP Connectivity Job**
   - Runs on push to main
   - Spins up test databases
   - Validates connectivity to all 4 databases

### Triggers
- Push to `main` or `develop` branches
- Pull requests to `main`
- Manual trigger via GitHub Actions UI
- Only runs when schema-related files change

## Part D: Local Pre-push Hook

### Setup
```bash
# One-time setup
./scripts/setup-hooks.sh
```

### Features
- Validates schemas before allowing push
- Only runs when schema files are modified
- Non-blocking MCP connectivity test
- Clear error messages with fix instructions

### Bypass (Emergency Only)
```bash
# Skip pre-push validation
git push --no-verify
```

### Disable/Re-enable
```bash
# Temporarily disable hooks
git config core.hooksPath .git/hooks

# Re-enable hooks
./scripts/setup-hooks.sh
```

## Directory Structure
```
agent-project/
├── .github/
│   └── workflows/
│       └── validate-schemas.yml      # CI/CD pipeline
├── .githooks/
│   └── pre-push                      # Local validation hook
├── scripts/
│   ├── batch_runner.py               # Batch validation tool
│   ├── smoke_mcp.py                  # Database connectivity test
│   └── setup-hooks.sh                # Hook configuration script
├── config/
│   ├── schema.json                   # Master schema file
│   └── prompts/
│       └── document_types/           # Document type directories (slug-based)
├── .env.mcp                          # Database credentials
└── docker-compose.mcp.override.yml   # MCP service config
```

## Troubleshooting

### Database Connection Failures
1. Check Docker is running: `docker ps`
2. Start services: `./deploy-multi-db.sh up dev`
3. Verify credentials in `.env.mcp`
4. Check network connectivity

### Schema Validation Failures
1. Run verbose mode: `python3 scripts/batch_runner.py --verbose`
2. Check specific type: `--types [document-type-slug]`
3. Validate JSON syntax: `python3 -m json.tool [file]`
4. Review error messages in report

### CI/CD Issues
1. Check GitHub Actions tab for logs
2. Download artifacts for detailed reports
3. Ensure requirements.txt is up to date
4. Verify workflow file syntax

### Pre-push Hook Issues
1. Check hook is executable: `ls -la .githooks/pre-push`
2. Verify hook path: `git config core.hooksPath`
3. Test manually: `.githooks/pre-push`
4. Use `--no-verify` to bypass in emergencies

## Best Practices

1. **Always run validation before committing schema changes**
   ```bash
   python3 scripts/batch_runner.py --types [your-changed-types]
   ```

2. **Keep schemas consistent**
   - Use the same field types across similar documents
   - Follow existing naming conventions
   - Document complex fields with descriptions

3. **Monitor CI/CD**
   - Check GitHub Actions after pushing
   - Review PR comments for validation results
   - Fix failures promptly to avoid blocking others

4. **Database management**
   - Keep `.env.mcp` credentials secure
   - Don't commit passwords to the repository
   - Use strong passwords in production

## Next Steps

Future enhancements could include:
- Automatic schema migration tools
- Schema versioning and rollback
- Field-level validation rules
- Integration with document processing pipeline
- Performance benchmarking for large batches