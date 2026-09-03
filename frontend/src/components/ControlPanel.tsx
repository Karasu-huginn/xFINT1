import type { ReactNode } from "react";

interface ControlPanelProps {
  title: string;
  actions?: ReactNode;
  count?: number;
}

// The strip carrying the breadcrumb on the left and the record count on the right
// is the element that makes an interface read as business software rather than as
// a generic web page.
export default function ControlPanel({ title, actions, count }: ControlPanelProps) {
  return (
    <div className="border-b border-sheet-border bg-white">
      <div className="mx-auto flex max-w-6xl flex-wrap items-center gap-3 px-4 py-3">
        <h1 className="text-base font-medium text-ink">{title}</h1>
        {actions !== undefined && (
          <div className="flex flex-wrap gap-2">{actions}</div>
        )}
        {count !== undefined && (
          <span className="ml-auto text-xs text-muted">
            {count} {count === 1 ? "enregistrement" : "enregistrements"}
          </span>
        )}
      </div>
    </div>
  );
}
