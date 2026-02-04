import { HypothesisTree } from '../../types/investigation';

export default function EvidencePanel({ logs }: { logs: string }) {
  return (
    <div className="p-4">
      <div className="bg-bg-deep rounded-lg border border-border-subtle overflow-hidden">
        <div className="flex items-center justify-between px-4 py-2 bg-bg-surface border-b border-border-subtle">
          <span className="text-sm text-text-muted">error.log</span>
          <div className="flex items-center gap-2">
            <span className="text-xs px-2 py-1 bg-semantic-danger/10 text-semantic-danger rounded">
              3 errors
            </span>
          </div>
        </div>
        <pre className="p-4 text-xs font-mono text-text-main overflow-x-auto whitespace-pre-wrap">
          {logs.split('\n').map((line, i) => (
            <div
              key={i}
              className={`${
                line.includes('ERROR')
                  ? 'bg-semantic-danger/10 text-semantic-danger'
                  : line.includes('WARN')
                  ? 'bg-semantic-warning/10 text-semantic-warning'
                  : ''
              } px-2 -mx-2`}
            >
              <span className="text-text-muted mr-4 select-none">
                {String(i + 1).padStart(3, ' ')}
              </span>
              {line}
            </div>
          ))}
        </pre>
      </div>
    </div>
  );
}
