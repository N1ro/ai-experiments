# Tech Task Context

## Stack
- Java 21, Maven
- REST Assured (given/when/then DSL)
- JUnit 5 with @DisplayName on every test
- Records for DTOs, Text Blocks for JSON bodies

## Standards
- DTOs: always `record`, never POJO with getters/setters
- GET requests: use `accept(ContentType.JSON)` not `contentType()`
- POST/PUT: always set `contentType(ContentType.JSON)` when sending a JSON body
- Assertions: always assert body content, not just status code
- Concurrent tests: use `Executors.newVirtualThreadPerTaskExecutor()`

## Run tests
```bash
mvn test -pl <module-name> -Dtest=<ClassName> -DfailIfNoTests=false
```

## Agents available
- `code-writer`  — write new REST Assured tests (Java 21 idiomatic)
- `code-reviewer` — review code for CRITICAL/WARNING/PASS findings
- `code-tester`  — add test coverage for a feature/endpoint

## Important
Any code change is NOT complete until tests are verified green.
Run Maven before reporting done.
