import { useState, useEffect } from "react";
import type { ExperimentData, ProvisionResult } from "./types";
import { ExperimentSummary } from "./components/ExperimentSummary";
import { ProvisionCard } from "./components/ProvisionCard";
import { AccuracyChart } from "./components/AccuracyChart";
import { CodeViewer } from "./components/CodeViewer";
import { FailureList } from "./components/FailureList";
import { ConversationView } from "./components/ConversationView";
import "./App.css";

// Import the experiment data
import experimentData from "../../paper/data/runs/experiment_20251206_193620.json";

type TabType = "trajectory" | "conversation" | "code";

function App() {
  const [experiment] = useState<ExperimentData>(experimentData as unknown as ExperimentData);
  const [selectedProvision, setSelectedProvision] = useState<string | null>(null);
  const [selectedIteration, setSelectedIteration] = useState(1);
  const [activeTab, setActiveTab] = useState<TabType>("trajectory");

  // Select first provision by default
  useEffect(() => {
    const provisions = Object.keys(experiment.provisions);
    if (provisions.length > 0 && !selectedProvision) {
      setSelectedProvision(provisions[0]);
    }
  }, [experiment, selectedProvision]);

  const currentProvision: ProvisionResult | null = selectedProvision
    ? experiment.provisions[selectedProvision]
    : null;

  const hasTrajectory = currentProvision?.trajectory && currentProvision.trajectory.length > 0;
  const hasConversation = currentProvision?.conversation && currentProvision.conversation.length > 0;

  return (
    <div className="app">
      <header className="app-header">
        <h1>AI Encoding Trajectory Viewer</h1>
        <p>Visualize the reinforcement learning loop for tax law encoding</p>
      </header>

      <main className="app-main">
        <aside className="sidebar">
          <ExperimentSummary experiment={experiment} />

          <div className="provision-list">
            <h3>Provisions</h3>
            {Object.entries(experiment.provisions).map(([id, provision]) => (
              <ProvisionCard
                key={id}
                id={id}
                provision={provision}
                isSelected={selectedProvision === id}
                onClick={() => {
                  setSelectedProvision(id);
                  setSelectedIteration(1);
                }}
              />
            ))}
          </div>
        </aside>

        <section className="main-content">
          {currentProvision && (
            <>
              <div className="provision-header-detail">
                <h2>{selectedProvision}</h2>
                <div className="citation">{currentProvision.citation}</div>
                <div className="meta">
                  <span>Complexity: {currentProvision.complexity}</span>
                  <span>Phase: {currentProvision.phase}</span>
                  <span>{currentProvision.n_test_cases} test cases</span>
                </div>
              </div>

              <div className="tabs">
                <button
                  className={activeTab === "trajectory" ? "active" : ""}
                  onClick={() => setActiveTab("trajectory")}
                  disabled={!hasTrajectory}
                >
                  Trajectory
                </button>
                <button
                  className={activeTab === "conversation" ? "active" : ""}
                  onClick={() => setActiveTab("conversation")}
                  disabled={!hasConversation}
                >
                  Conversation
                </button>
                <button
                  className={activeTab === "code" ? "active" : ""}
                  onClick={() => setActiveTab("code")}
                >
                  Final Code
                </button>
              </div>

              <div className="tab-content">
                {activeTab === "trajectory" && hasTrajectory && (
                  <div className="trajectory-view">
                    <AccuracyChart
                      trajectory={currentProvision.trajectory!}
                      targetAccuracy={experiment.target_accuracy}
                    />

                    <CodeViewer
                      trajectory={currentProvision.trajectory!}
                      selectedIteration={selectedIteration}
                      onIterationChange={setSelectedIteration}
                    />

                    {currentProvision.trajectory![selectedIteration - 1] && (
                      <FailureList
                        failures={
                          currentProvision.trajectory![selectedIteration - 1].failures
                        }
                      />
                    )}
                  </div>
                )}

                {activeTab === "trajectory" && !hasTrajectory && (
                  <div className="no-data">
                    <p>No trajectory data available for this provision.</p>
                    <p>Run the experiment with the latest agent code to capture trajectories.</p>
                  </div>
                )}

                {activeTab === "conversation" && hasConversation && (
                  <ConversationView conversation={currentProvision.conversation!} />
                )}

                {activeTab === "conversation" && !hasConversation && (
                  <div className="no-data">
                    <p>No conversation data available for this provision.</p>
                  </div>
                )}

                {activeTab === "code" && (
                  <div className="final-code-view">
                    <h3>Final Submitted Code</h3>
                    <pre className="code-block">
                      <code>{currentProvision.final_code}</code>
                    </pre>
                  </div>
                )}
              </div>
            </>
          )}
        </section>
      </main>
    </div>
  );
}

export default App;
