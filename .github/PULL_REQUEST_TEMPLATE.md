## Summary

Describe the user-facing or engineering change.

## Verification

- [ ] Quality gate passes
- [ ] Security workflow passes
- [ ] Relevant application or backtest tests pass
- [ ] Documentation/evidence updated when claims or metrics changed

## Safety and evidence boundaries

- [ ] No secrets, credentials, private portfolio data, or generated private reports committed
- [ ] Quantitative allocations remain separate from LLM commentary
- [ ] Historical-performance claims remain supported by the documented backtest
- [ ] No historical sentiment-performance claim is added without point-in-time news data
- [ ] Residual dependency risk is documented rather than hidden

## Deployment impact

Describe any Docker, AWS, ECR, Systems Manager, rollback, or data-persistence implications.
