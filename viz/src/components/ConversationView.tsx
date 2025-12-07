import type { ConversationEntry } from "../types";

interface ConversationViewProps {
  conversation: ConversationEntry[];
}

export function ConversationView({ conversation }: ConversationViewProps) {
  return (
    <div className="conversation-view">
      <h3>Conversation Log</h3>
      <div className="conversation-entries">
        {conversation.map((entry, idx) => (
          <div key={idx} className={`conversation-entry ${entry.role}`}>
            <div className="entry-header">
              <span className="turn">Turn {entry.turn}</span>
              <span className="role">{entry.role}</span>
              {entry.input_tokens && (
                <span className="tokens">
                  {entry.input_tokens} in / {entry.output_tokens} out tokens
                </span>
              )}
            </div>

            {entry.role === "assistant" && entry.text && (
              <div className="entry-content">
                <p>{entry.text}</p>
              </div>
            )}

            {entry.role === "tool_call" && (
              <div className="entry-content tool-call">
                <div className="tool-name">{entry.tool_name}</div>
                {entry.tool_input && (
                  <details>
                    <summary>Input</summary>
                    <pre>
                      {typeof entry.tool_input === "string"
                        ? (entry.tool_input as string).slice(0, 500)
                        : JSON.stringify(entry.tool_input, null, 2).slice(0, 500)}
                      {(typeof entry.tool_input === "string"
                        ? (entry.tool_input as string).length
                        : JSON.stringify(entry.tool_input).length) > 500 && "..."}
                    </pre>
                  </details>
                )}
                {entry.tool_result && (
                  <details>
                    <summary>Result</summary>
                    <pre>
                      {entry.tool_result.slice(0, 500)}
                      {entry.tool_result.length > 500 && "..."}
                    </pre>
                  </details>
                )}
              </div>
            )}
          </div>
        ))}
      </div>
    </div>
  );
}
