up:
	docker compose -f docker-compose.yml up -d

down:
	docker compose -f docker-compose.yml down

up-mcp:
	docker compose -f docker-compose.yml -f docker-compose.mcp.override.yml up -d --build

down-mcp:
	docker compose -f docker-compose.yml -f docker-compose.mcp.override.yml down

config-mcp:
	docker compose -f docker-compose.yml -f docker-compose.mcp.override.yml config

extract-one:
	python3 scripts/extract_one.py $(slug) $(file)

extract-gemini:
	python3 scripts/extract_one_gemini.py $(slug) $(file)
