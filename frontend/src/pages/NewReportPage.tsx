import { useState } from "react";
import type { ChangeEvent, FormEvent } from "react";
import { useNavigate } from "react-router-dom";

import { ApiError } from "../api/client";
import { submitReport } from "../api/reports";
import Alert from "../components/Alert";
import Button from "../components/Button";
import ControlPanel from "../components/ControlPanel";
import Field, { INPUT_CLASSES } from "../components/Field";
import Sheet from "../components/Sheet";
import { describeApiError, formatFileSize } from "../labels/fr";

// This filters the file picker as a convenience. It is not a check: the browser
// still allows any file through, and the real type is decided from the magic
// bytes server-side.
const ACCEPTED_TYPES = "application/pdf,image/jpeg,image/png";

export default function NewReportPage() {
  const navigate = useNavigate();
  const [title, setTitle] = useState("");
  const [comment, setComment] = useState("");
  const [documents, setDocuments] = useState<File[]>([]);
  const [failureMessage, setFailureMessage] = useState<string | null>(null);
  const [isSubmitting, setIsSubmitting] = useState(false);

  function handleFileChange(event: ChangeEvent<HTMLInputElement>) {
    setDocuments(Array.from(event.target.files ?? []));
  }

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setFailureMessage(null);
    if (documents.length === 0) {
      setFailureMessage("Joignez au moins une pièce justificative.");
      return;
    }
    setIsSubmitting(true);
    try {
      await submitReport(title, comment, documents);
      navigate("/expenses", { replace: true });
    } catch (error) {
      setFailureMessage(
        error instanceof ApiError
          ? describeApiError(error.code, "L'envoi a échoué, merci de réessayer.")
          : "L'envoi a échoué, merci de réessayer.",
      );
    } finally {
      setIsSubmitting(false);
    }
  }

  return (
    <>
      <ControlPanel title="Nouvelle note de frais" />
      <main className="mx-auto max-w-6xl p-4">
        <Sheet>
          {failureMessage !== null && <Alert tone="error">{failureMessage}</Alert>}
          <form onSubmit={handleSubmit} noValidate>
            <Field label="Titre" htmlFor="title">
              <input
                id="title"
                type="text"
                required
                maxLength={120}
                className={INPUT_CLASSES}
                value={title}
                onChange={(event) => setTitle(event.target.value)}
              />
            </Field>
            <Field
              label="Commentaire"
              htmlFor="comment"
              hint="Facultatif, 2000 caractères maximum."
            >
              <textarea
                id="comment"
                rows={4}
                maxLength={2000}
                className={INPUT_CLASSES}
                value={comment}
                onChange={(event) => setComment(event.target.value)}
              />
            </Field>
            <Field
              label="Pièces justificatives"
              htmlFor="files"
              hint="PDF, JPEG ou PNG. 10 fichiers au maximum, 5 Mo par fichier."
            >
              <input
                id="files"
                type="file"
                multiple
                required
                accept={ACCEPTED_TYPES}
                onChange={handleFileChange}
                className="w-full text-sm text-ink file:mr-3 file:rounded file:border file:border-sheet-border file:bg-white file:px-3 file:py-1.5 file:text-sm file:text-ink hover:file:bg-canvas"
              />
            </Field>
            {documents.length > 0 && (
              <ul className="mb-4 divide-y divide-sheet-border rounded border border-sheet-border">
                {documents.map((document) => (
                  <li
                    key={document.name}
                    className="flex items-center justify-between px-3 py-2 text-sm"
                  >
                    <span className="break-all text-ink">{document.name}</span>
                    <span className="whitespace-nowrap text-xs text-muted">
                      {formatFileSize(document.size)}
                    </span>
                  </li>
                ))}
              </ul>
            )}
            <div className="flex gap-2">
              <Button type="submit" variant="primary" disabled={isSubmitting}>
                {isSubmitting ? "Envoi..." : "Soumettre"}
              </Button>
              <Button type="button" onClick={() => navigate("/expenses")}>
                Annuler
              </Button>
            </div>
          </form>
        </Sheet>
      </main>
    </>
  );
}
