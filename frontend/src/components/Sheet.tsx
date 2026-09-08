import type { ReactNode } from "react";

interface SheetProps {
  title?: string;
  children: ReactNode;
}

export default function Sheet({ title, children }: SheetProps) {
  return (
    <section className="mx-auto w-full max-w-2xl rounded border border-sheet-border bg-sheet p-5 shadow-sheet sm:p-8">
      {title !== undefined && (
        <h2 className="mb-6 border-b border-sheet-border pb-3 text-lg font-medium text-ink">
          {title}
        </h2>
      )}
      {children}
    </section>
  );
}
