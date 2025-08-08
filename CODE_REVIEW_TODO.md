# Code Review TODO List for Plan-Lint

## Summary
Plan-lint is a well-structured security-focused linter for LLM agent plans. The codebase is clean, follows good Python practices, and has a solid foundation. However, there are several areas where AI assistance could significantly improve the project.

## Critical Improvements Needed

### 🔴 High Priority (Security & Correctness)

1. **Fix Naive Cycle Detection** (`core.py:151-181`)
   - Current implementation won't catch all dependency cycles
   - Implement proper graph traversal algorithm
   - Add comprehensive tests for complex cycle scenarios

2. **Enhance Bounds Checking** (`core.py:46-108`)
   - Add support for nested parameter validation
   - Handle array bounds and complex data structures
   - Improve error messages with actual vs expected values

3. **Improve Secret Detection** (`core.py:112-149`)
   - Current regex approach has high false positive rate
   - Add entropy-based detection
   - Support custom sensitive data patterns
   - Implement allowlist for known safe patterns

### 🟡 Medium Priority (Performance & Usability)

4. **Optimize Validation Performance**
   - Add benchmarking suite
   - Implement parallel validation for independent checks
   - Cache compiled regex patterns
   - Profile and optimize hot paths

5. **Expand Test Coverage**
   - Current tests are basic, need edge case coverage
   - Add property-based testing with hypothesis
   - Test error paths and exception handling
   - Add integration tests for CLI

6. **Improve Rule System**
   - Current rule loading is basic file import
   - Need proper plugin architecture
   - Add rule configuration and parameters
   - Create rule testing framework

### 🟢 Low Priority (Nice to Have)

7. **Enhanced Documentation**
   - API documentation needs examples
   - Create rule development guide
   - Add architecture documentation
   - Include performance tuning guide

8. **Better Error Reporting**
   - Add error context and suggestions
   - Implement error grouping
   - Create machine-readable error format
   - Add fix suggestions

9. **Integration Features**
   - GitHub Actions native support
   - VS Code extension
   - Web API service
   - Framework integrations

## Technical Debt

1. **Type Annotations**: Several functions missing return type hints
2. **Error Handling**: Some try/except blocks too broad
3. **Code Duplication**: Similar validation logic repeated across rules
4. **Configuration**: Policy loading could be more flexible
5. **Logging**: Minimal logging for debugging

## Positive Aspects

✅ Clean code structure with good separation of concerns
✅ Uses modern Python features (type hints, dataclasses)
✅ Good use of Pydantic for data validation
✅ Thoughtful API design
✅ Security-first approach
✅ Extensible architecture

## Recommended Next Steps

1. **Immediate**: Fix cycle detection algorithm (critical bug)
2. **This Week**: Improve test coverage to 90%+
3. **This Month**: Implement performance optimizations
4. **This Quarter**: Build plugin architecture and integrations

## Metrics to Track

- Test coverage: Current ~60% → Target 90%
- Performance: Validate 1000 plans/second
- Rules: Expand from 2 to 10+ built-in rules
- Integrations: Add 3+ framework integrations
- Documentation: 100% API coverage

The codebase is in good shape overall, but needs these improvements to be production-ready for enterprise use.