import type { Failure } from "../types";

interface FailureListProps {
  failures: Failure[];
}

export function FailureList({ failures }: FailureListProps) {
  if (failures.length === 0) {
    return (
      <div className="failure-list empty">
        <span className="success-icon">✓</span> All test cases passed!
      </div>
    );
  }

  return (
    <div className="failure-list">
      <h4>Failures ({failures.length})</h4>
      <div className="failures">
        {failures.slice(0, 10).map((failure, idx) => (
          <div key={idx} className="failure-item">
            <div className="failure-type">{failure.type}</div>
            <div className="failure-message">{failure.message}</div>
            <div className="failure-comparison">
              <span className="expected">
                Expected: <code>{JSON.stringify(failure.expected)}</code>
              </span>
              <span className="actual">
                Actual: <code>{JSON.stringify(failure.actual)}</code>
              </span>
            </div>
            {failure.inputs && (
              <div className="failure-inputs">
                <details>
                  <summary>Inputs</summary>
                  <pre>{JSON.stringify(failure.inputs, null, 2)}</pre>
                </details>
              </div>
            )}
          </div>
        ))}
        {failures.length > 10 && (
          <div className="more-failures">
            ... and {failures.length - 10} more failures
          </div>
        )}
      </div>
    </div>
  );
}
