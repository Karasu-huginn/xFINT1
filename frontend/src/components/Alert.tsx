import type { ReactNode } from "react";

const TONE_CLASSES = {
  error: "border-status-refused bg-status-refused-tint text-status-refused",
  success: "border-status-validated bg-status-validated-tint text-status-validated",
} as const;

interface AlertProps {
  tone: keyof typeof TONE_CLASSES;
  children: ReactNode;
}

export default function Alert({ tone, children }: AlertProps) {
  return (
    <div
      role={tone === "error" ? "alert" : "status"}
      className={`mb-4 rounded border px-3 py-2 text-sm ${TONE_CLASSES[tone]}`}
    >
      {children}
    </div>
  );
}
