import { useEffect } from "react";
import type { ReactNode } from "react";

interface DialogProps {
  title: string;
  onClose: () => void;
  footer?: ReactNode;
  children: ReactNode;
}

export default function Dialog({ title, onClose, footer, children }: DialogProps) {
  useEffect(() => {
    function handleKeyDown(event: KeyboardEvent) {
      if (event.key === "Escape") {
        onClose();
      }
    }
    window.addEventListener("keydown", handleKeyDown);
    return () => window.removeEventListener("keydown", handleKeyDown);
  }, [onClose]);

  return (
    <div className="fixed inset-0 z-50 flex items-start justify-center overflow-y-auto bg-black/40 p-4 sm:p-8">
      <div
        role="dialog"
        aria-modal="true"
        aria-label={title}
        className="w-full max-w-2xl rounded bg-sheet shadow-dialog"
      >
        <header className="flex items-center justify-between border-b border-sheet-border px-5 py-3">
          <h2 className="text-base font-medium text-ink">{title}</h2>
          <button
            type="button"
            aria-label="Fermer"
            onClick={onClose}
            className="rounded px-2 text-xl leading-none text-muted hover:bg-canvas hover:text-ink"
          >
            &times;
          </button>
        </header>
        <div className="px-5 py-4">{children}</div>
        {/* Odoo aligns dialog buttons left, which is why this footer is not
            right-aligned the way a generic web modal would be. */}
        {footer !== undefined && (
          <footer className="flex flex-wrap gap-2 border-t border-sheet-border px-5 py-3">
            {footer}
          </footer>
        )}
      </div>
    </div>
  );
}
