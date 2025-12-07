import { useState } from "react";
import ReactDiffViewer, { DiffMethod } from "react-diff-viewer-continued";
import type { TrajectoryStep } from "../types";

interface CodeViewerProps {
  trajectory: TrajectoryStep[];
  selectedIteration: number;
  onIterationChange: (iteration: number) => void;
}

export function CodeViewer({
  trajectory,
  selectedIteration,
  onIterationChange,
}: CodeViewerProps) {
  const [showDiff, setShowDiff] = useState(false);

  const currentStep = trajectory.find((s) => s.iteration === selectedIteration);
  const prevStep = trajectory.find((s) => s.iteration === selectedIteration - 1);

  const formatCode = (code: string | undefined) => {
    if (!code) return "";
    // Extract Python code from markdown if present
    if (code.includes("```python")) {
      const start = code.indexOf("```python") + 9;
      const end = code.indexOf("```", start);
      return code.slice(start, end).trim();
    }
    return code;
  };

  const currentCode = formatCode(currentStep?.code);
  const prevCode = formatCode(prevStep?.code);

  return (
    <div className="code-viewer">
      <div className="code-header">
        <div className="iteration-selector">
          <label>Iteration: </label>
          <select
            value={selectedIteration}
            onChange={(e) => onIterationChange(Number(e.target.value))}
          >
            {trajectory.map((step) => (
              <option key={step.iteration} value={step.iteration}>
                {step.iteration} - {(step.accuracy * 100).toFixed(0)}% accuracy
              </option>
            ))}
          </select>
        </div>

        {prevStep && (
          <button
            className={`diff-toggle ${showDiff ? "active" : ""}`}
            onClick={() => setShowDiff(!showDiff)}
          >
            {showDiff ? "Hide Diff" : "Show Diff"}
          </button>
        )}
      </div>

      {showDiff && prevStep ? (
        <div className="diff-container">
          <ReactDiffViewer
            oldValue={prevCode}
            newValue={currentCode}
            splitView={false}
            compareMethod={DiffMethod.WORDS}
            styles={{
              variables: {
                dark: {
                  diffViewerBackground: "#1a1a2e",
                  addedBackground: "#1e3a1e",
                  removedBackground: "#3a1e1e",
                  wordAddedBackground: "#2d5a2d",
                  wordRemovedBackground: "#5a2d2d",
                  addedGutterBackground: "#1e3a1e",
                  removedGutterBackground: "#3a1e1e",
                  gutterBackground: "#16161e",
                  gutterColor: "#666",
                  codeFoldGutterBackground: "#1a1a2e",
                  codeFoldBackground: "#16161e",
                },
              },
            }}
            useDarkTheme
          />
        </div>
      ) : (
        <pre className="code-block">
          <code>{currentCode}</code>
        </pre>
      )}

      {currentStep && (
        <div className="step-stats">
          <span className={`accuracy ${currentStep.accuracy >= 0.95 ? "success" : ""}`}>
            {(currentStep.accuracy * 100).toFixed(1)}% accuracy
          </span>
          <span className="cases">
            {currentStep.passed}/{currentStep.total} passed
          </span>
          {currentStep.mean_absolute_error > 0 && (
            <span className="mae">
              ${currentStep.mean_absolute_error.toFixed(2)} MAE
            </span>
          )}
        </div>
      )}
    </div>
  );
}
